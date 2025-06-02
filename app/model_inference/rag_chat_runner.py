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

        docs = []
        for doc_text, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            weight = float(metadata.get("weight", 1.0))
            score = 1.0 - distance
            adjusted_score = score * weight
            docs.append((adjusted_score, Document(page_content=doc_text, metadata=metadata)))

        docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in docs[:self.top_k]]

from dotenv import load_dotenv
load_dotenv()

# 임베딩 모델 및 벡터스토어 로딩
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")
vectorstore = Chroma(
    collection_name="github_docs",
    persist_directory="./chroma_db_weight",
    embedding_function=embedding_model,
)

# LLM (HyperCLOVA)
llm = HyperClovaLangChainLLM()

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
    
    # 4. 실행
    result = rag_chain.invoke({
        "input": question,
        "question": question
    })

    # 5. answer 키에서 문자열만 추출
    raw_answer = result.get("answer", "")
    if "답변:" in raw_answer:
        return raw_answer.split("답변:", 1)[1].strip()
    return raw_answer.strip()

