# app/model_inference/rag_chat_runner.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langsmith import traceable
from app.context_construction.question_router import is_structured_question, classify_question_type
from app.context_construction.prompts.chat_prompt import build_prompt_template, general_prompt_template
from app.model_inference.loaders.hyperclova_langchain_llm import HyperClovaLangChainLLM
from langchain.schema import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.retrievers import BaseRetriever
from typing import List, Optional, Callable, Any
from pydantic import Field
from app.model_inference.loaders.gemini import GeminiLangChainLLM
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain_core.runnables import RunnableLambda, RunnableMap, RunnableSequence, Runnable
from langchain_core.output_parsers import StrOutputParser
import asyncio
import re

FILTERED_RESPONSE = """\
💭 저는 팀 프로젝트 전용 AI, 품앗이(pumati)의 마티예요! 
팀 프로젝트와 관련된 질문에만 응답할 수 있어요.

예:
• "이 팀의 프로젝트는 어떤 프로젝트야?"
• "어떤 기능들이 있어?"
• "최근에는 어떤 기능 추가했어?"

이런 식으로 질문해 주시면 열심히 도와드릴게요! ☺️"""

class StreamingLLMWrapper(Runnable):
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, input, config=None):
        # 스트리밍만 쓸 경우라도 필수 구현
        raise NotImplementedError("Only streaming is supported in this wrapper.")

    async def astream(self, input, config=None):
        async for token in self.llm.astream(input, config=config):
            yield token

class WeightedChromaRetriever(BaseRetriever):
    chroma_collection: Any = Field(exclude=True)
    embedding_fn: Callable[[str], List[float]] = Field(exclude=True)
    top_k: int = 5
    project_id: Optional[int] = None

    def _get_relevant_documents(self, query: str, *, config: RunnableConfig = None) -> List[Document]:
        query_embedding = self.embedding_fn(query)
        filter_by_project = {"project_id": self.project_id} if self.project_id else {}

        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=50,
            include=["documents", "metadatas", "distances"],
            where=filter_by_project
        )

        scored_docs = []
        for doc_text, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            weight = float(metadata.get("weight", 1.0))
            score = 1.0 - distance
            adjusted_score = score * weight

            doc = Document(
                page_content=doc_text,
                metadata={
                    **metadata,
                    "cosine_score": score,
                    "adjusted_score": adjusted_score,
                    "raw_distance": distance
                }
            )
            scored_docs.append((adjusted_score, doc))

        # 점수 기준 정렬 후 Document만 반환
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:self.top_k]]


from dotenv import load_dotenv
load_dotenv()

# 임베딩 모델 및 벡터스토어 로딩
embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    encode_kwargs={"normalize_embeddings": True}
)
vectorstore = Chroma(
    collection_name="github_docs",
    persist_directory="./chroma_db_weight",
    embedding_function=embedding_model,
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
    # 1. 문서 검색기 구성
    retriever = WeightedChromaRetriever(
        chroma_collection=vectorstore._collection,  # Chroma 내부의 raw collection
        embedding_fn=embedding_model.embed_query,   # query embedding 함수
        top_k=40,
        include=["documents", "distances", "metadatas"],
        project_id=project_id
    )

    # 2. 프롬프트 선택 (하이브리드 방식)
    if is_structured_question(question):
        q_type = classify_question_type(question)
        prompt = build_prompt_template(q_type)
    else:
        prompt = general_prompt_template

    # 3. 체인 구성
    combine_docs_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
        document_prompt=document_prompt,
    )
    rag_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine_docs_chain)
    
    # 필터링1: 문서 검색
    retrieved_docs = retriever._get_relevant_documents(question)
    if not retrieved_docs:
        return FILTERED_RESPONSE

    # 필터링2: 가장 높은 adjusted_score 기준
    top_score = retrieved_docs[0].metadata.get("adjusted_score", 0)
    if top_score < 0.6:
        return FILTERED_RESPONSE

    # 4. 실행
    result = rag_chain.invoke({
        "input": question,
        "question": question,
        "context": retrieved_docs
    })

    # 5. answer 키에서 문자열만 추출
    raw_answer = result.get("answer", "")
    if "답변:" in raw_answer:
        return raw_answer.split("답변:", 1)[1].strip()
    return raw_answer.strip()

@traceable
async def run_rag_streaming(question: str, project_id: int):
    # 1. 문서 검색
    retriever = WeightedChromaRetriever(
        chroma_collection=vectorstore._collection,
        embedding_fn=embedding_model.embed_query,
        top_k=40,
        project_id=project_id
    )
    retrieved_docs = retriever._get_relevant_documents(question)
    if not retrieved_docs or retrieved_docs[0].metadata.get("adjusted_score", 0) < 0.6:
        for line in FILTERED_RESPONSE.strip().splitlines():
            yield f"data: {line}\n"
        yield "\n"
        yield "data: [END]\n\n"
        return

    # 2. 프롬프트 구성
    if is_structured_question(question):
        q_type = classify_question_type(question)
        prompt_template = build_prompt_template(q_type)
    else:
        prompt_template = general_prompt_template

    context = "\n".join([doc.page_content for doc in retrieved_docs])
    prompt_input = {
        "question": question,
        "context": context
    }

    # 3. LangSmith metadata 기록
    config = RunnableConfig(
        tags=["run_rag_streaming"],
        metadata={
            "retrieved_docs": [
                {
                    "content": doc.page_content[:100],
                    "adjusted_score": doc.metadata.get("adjusted_score", 0)
                }
                for doc in retrieved_docs
            ]
        }
    )

    # 4. 전체 체인을 구성
    chain = (
        RunnableLambda(lambda x: prompt_template.format(**x))  # 프롬프트 포맷팅
        | StreamingLLMWrapper(llm)  # LLM 스트리밍 실행
    )

    # 5. 실행 및 SSE 출력
    async for chunk in chain.astream(prompt_input, config=config):
        words = re.findall(r'\s+|\S+', chunk)
        sse_lines = [f"data: {word}" for word in words if word.strip() or word == " "]
        if sse_lines:
            yield "\n".join(sse_lines) + "\n\n"

    yield "data: [END]\n\n"