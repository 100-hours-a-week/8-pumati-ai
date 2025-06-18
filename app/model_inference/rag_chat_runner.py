# app/model_inference/rag_chat_runner.py

import os
from typing import List
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, SearchRequest

from langchain_core.runnables import RunnableConfig, RunnableLambda, Runnable
from langchain_core.retrievers import BaseRetriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from langsmith import traceable, client

from app.context_construction.question_router import is_structured_question, classify_question_type
from app.context_construction.prompts.chat_prompt import build_prompt_template, general_prompt_template
from app.model_inference.loaders.gemini import GeminiLangChainLLM

os.environ["TOKENIZERS_PARALLELISM"] = "false"

FILTERED_RESPONSE = """\
💭 저는 팀 프로젝트 전용 AI, 품앗이(pumati)의 마티예요!\n팀 프로젝트와 관련된 질문에만 응답할 수 있어요.\n\n예:\n• "이 팀의 프로젝트는 어떤 프로젝트야?"\n• "어떤 기능들이 있어?"\n• "최근에는 어떤 기능 추가했어?"\n\n이런 식으로 질문해 주시면 열심히 도와드릴게요! ☺️"""

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "github_docs")

# 스트리밍 처리를 위한 LLM 래퍼 (SSE 용도)
class StreamingLLMWrapper(Runnable):
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, input, config=None):
        raise NotImplementedError("Only streaming is supported in this wrapper.")

    async def astream(self, input, config=None):
        async for token_chunk_from_llm in self.llm.astream(input, config=config):
            
            for char in token_chunk_from_llm:
                if char == '\n':
                    yield '\\n'
                else:
                    yield char

class WeightedQdrantRetriever(BaseRetriever):
    vectorstore: QdrantVectorStore
    top_k: int = 5
    project_id: int

    def _get_relevant_documents(self, query: str, *, config=None) -> List[Document]:
        # 쿼리 임베딩 생성
        query_embedding = self.vectorstore.embeddings.embed_query(query)
        
        results = self.vectorstore.client.search(
            collection_name=self.vectorstore.collection_name,
            query_vector=query_embedding,
            limit=self.top_k,
            with_payload=True,
            query_filter=Filter(
                must=[FieldCondition(key="project_id", match=MatchValue(value=self.project_id))]
            )
        )
        
        docs = []
        for item in results:
            payload = item.payload or {}
            distance = item.score
            cosine_score = 1 - distance
            weight = payload.get("weight", 1.0)
            adjusted_score = cosine_score * weight
            metadata = {
                **payload,
                "raw_distance": distance,
                "cosine_score": cosine_score,
                "adjusted_score": adjusted_score
            }
            docs.append(Document(page_content=payload.get("document", ""), metadata=metadata))
        # docs = sorted(docs, key=lambda d: d.metadata.get("adjusted_score", 0.0), reverse=True)
        docs = sorted(docs, key=lambda d: d.metadata.get("cosine_score", 0.0), reverse=True)
        return docs

# 임베딩 모델 및 벡터스토어 로딩
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True}
)

# Qdrant client 및 LangChain vectorstore 래퍼
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=QDRANT_COLLECTION,
    embedding=embedding_model,
    content_payload_key="document",
)

# LLM (HyperCLOVA)
# llm = HyperClovaLangChainLLM()
llm = GeminiLangChainLLM()

document_prompt = PromptTemplate(
    input_variables=["page_content"],
    template="- {page_content}"
)

# 실행 함수
@traceable
def run_rag(question: str, project_id: int) -> str:
    # 벡터 DB에서 관련 문서 검색
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 40,
            "filter": Filter(
                must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]
            )
        }
    )

    # 프롬프트 선택: 구조화된 질문이면 유형에 따라 맞춤 프롬프트 사용
    if is_structured_question(question):
        q_type = classify_question_type(question)
        prompt = build_prompt_template(q_type)
    else:
        prompt = general_prompt_template

    # 문서 + LLM 조합 체인 생성
    combine_docs_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
        document_prompt=document_prompt,
    )
    rag_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine_docs_chain)

    # 문서 검색 수행
    docs = retriever.invoke(question)
    if not docs:
        return FILTERED_RESPONSE

    # 기준 이하 점수이면 응답 필터링
    top_score = docs[0].metadata.get("adjusted_score", 1.0)
    if top_score < 0.6:
        return FILTERED_RESPONSE

    # 체인 실행
    result = rag_chain.invoke({"input": question, "question": question, "context": docs})
    answer = result.get("answer", "")
    return answer.split("답변:", 1)[-1].strip() if "답변:" in answer else answer.strip()

@traceable
async def run_rag_streaming(question: str, project_id: int):
    # 문서 검색기 구성 (project_id 필터 포함)
    retriever = WeightedQdrantRetriever(
        vectorstore=vectorstore,
        project_id=project_id,
        top_k=40
    )

    # 관련 문서 검색
    docs = retriever.invoke(question)
    
    # LangSmith에 문서 정보 traceable하게 남기기
    retrieved_doc_metadata = [
    {
        **doc.metadata, # 모든 메타데이터 포함
        "page_content": doc.page_content[:300] # 선택적으로 일부 내용 포함
    }
    for doc in docs
]

    config = RunnableConfig(tags=["run_rag_streaming"])

    if config and config.get("callbacks"):
        run_id = config.get("callbacks")[0].current_run_id
        if run_id:
            ls_client = client.Client()
            retrieved_doc_metadata = [
                {
                    **doc.metadata,
                    "page_content": doc.page_content[:300]
                }
                for doc in docs
            ]
            ls_client.update_run(
                run_id,
                inputs={
                    "question": question,
                    "retrieved_docs": retrieved_doc_metadata
                }
            )
        
    adjusted_scores = [doc.metadata.get("adjusted_score", 0.0) for doc in docs[:5]]
    avg_adjusted_scores = sum(adjusted_scores) / max(len(adjusted_scores), 1)
    print(f"➗ avg_adjusted_scores: {avg_adjusted_scores}")
    if not docs or avg_adjusted_scores < 0.3:
        # FILTERED_RESPONSE의 각 글자를 순회하며 yield하되, 줄바꿈은 치환
        for char in FILTERED_RESPONSE:
            if char == '\n':
                yield '\\n' # 줄바꿈 문자를 특정 문자열로 치환하여 yield
            else:
                yield char
        return

    # 프롬프트 구성
    if is_structured_question(question):
        q_type = classify_question_type(question)
        prompt_template = build_prompt_template(q_type)
    else:
        prompt_template = general_prompt_template

    # 프롬프트 입력 구성
    context = "\n".join([doc.page_content for doc in docs])
    prompt_input = {
        "question": question,
        "context": context
    }

    # LangSmith 추적용 config
    config = RunnableConfig(tags=["run_rag_streaming"])

    # 스트리밍 LLM 체인 구성
    chain = (
        RunnableLambda(lambda x: prompt_template.format(**x)) |
        StreamingLLMWrapper(llm)
    )

    # 응답 스트리밍 처리
    async for char_chunk in chain.astream(prompt_input, config=config):
        yield char_chunk