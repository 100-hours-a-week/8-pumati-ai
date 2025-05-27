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


from dotenv import load_dotenv
load_dotenv()

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

    # 2. 프롬프트 선택 (하이브리드 방식)
    if is_structured_question(question):
        q_type = classify_question_type(question)
        prompt = build_prompt_template(q_type)
    else:
        prompt = general_prompt_template

    # 3. 체인 구성
    combine_docs_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    rag_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine_docs_chain)

    # 4. 실행
    return rag_chain.invoke({
        "input": question, # for retriever
        "question": question  # for prompt template
    })