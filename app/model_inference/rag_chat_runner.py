# app/model_inference/rag_chat_runner.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langsmith import traceable

from app.model_inference.loaders.hyperclova_langchain_llm import HyperClovaLangChainLLM
from app.context_construction.question_router import classify_question_type
from app.context_construction.prompts import (
    chat_prompt_summary,
    chat_prompt_timeline,
    chat_prompt_owner,
)

from dotenv import load_dotenv
load_dotenv()

# 질문 유형별 프롬프트 매핑
prompt_map = {
    "summary": chat_prompt_summary,
    "timeline": chat_prompt_timeline,
    "owner": chat_prompt_owner,
}

# 임베딩 모델 및 벡터스토어 로딩
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")
vectorstore = Chroma(
    collection_name="github_docs",
    persist_directory="./chroma_db_e5_base",
    embedding_function=embedding_model,
)

# LLM (HyperCLOVA)
llm = HyperClovaLangChainLLM()

# 실행 함수
@traceable
def run_rag(question: str, project_id: int) -> str:
    # 1. 문서 검색기 구성
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10, "filter": {"project_id": project_id}})

    # 2. 질문 유형에 따라 프롬프트 선택 및 조합
    q_type = classify_question_type(question)
    prompt_builder = prompt_map[q_type].build_prompt
    full_prompt_template = prompt_builder(context="{context}", question="{input}")  # {input}은 question에 매핑됨

    # 3. PromptTemplate 구성
    dynamic_prompt = PromptTemplate(
        input_variables=["context", "input"],
        template=full_prompt_template
    )

    # 4. 최신 방식으로 체인 구성
    combine_docs_chain = create_stuff_documents_chain(llm=llm, prompt=dynamic_prompt)
    rag_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine_docs_chain)

    # 5. 실행
    return rag_chain.invoke({"input": question})

