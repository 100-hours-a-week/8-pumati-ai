# app/model_inference/rag_chat_runner.py

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from app.context_construction.question_router import is_structured_question, classify_question_type
from app.context_construction.prompts.chat_prompt import build_prompt_template, general_prompt_template
from app.model_inference.loaders.gemini import GeminiLangChainLLM
from langsmith import traceable
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_core.runnables import RunnableLambda
import os
from dotenv import load_dotenv

FILTERED_RESPONSE = """\
💭 저는 팀 프로젝트 전용 AI, 품앗이(pumati)의 마티예요! 
팀 프로젝트와 관련된 질문에만 응답할 수 있어요.

예:
• "이 팀의 프로젝트는 어떤 프로젝트야?"
• "어떤 기능들이 있어?"
• "최근에는 어떤 기능 추가했어?"

이런 식으로 질문해 주시면 열심히 도와드릴게요! ☺️"""

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
        async for token in self.llm.astream(input, config=config):
            yield token

# 임베딩 모델 및 벡터스토어 로딩
embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    encode_kwargs={"normalize_embeddings": True}
)

# Qdrant client 및 LangChain vectorstore 래퍼
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=QDRANT_COLLECTION,
    embeddings=embedding_model,
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
    docs = retriever.get_relevant_documents(question)
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
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 40,
            "filter": Filter(
                must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]
            )
        }
    )

    # 관련 문서 검색
    docs = retriever.get_relevant_documents(question)
    if not docs or docs[0].metadata.get("adjusted_score", 0) < 0.6:
        for line in FILTERED_RESPONSE.strip().splitlines():
            yield line
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
    full_response_content = []
    async for chunk in chain.astream(prompt_input, config=config):
        full_response_content.append(chunk)
        yield chunk