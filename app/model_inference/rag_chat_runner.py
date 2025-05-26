# app/model_inference/rag_chat_runner.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from app.model_inference.loaders.hyperclova_langchain_llm import HyperClovaLangChainLLM

# 1. 임베딩 모델 세팅 (E5-Base)
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")

# 2. Chroma 로드 (DB 위치 및 컬렉션 이름 지정)
vectorstore = Chroma(
    collection_name="github_docs",
    persist_directory="./chroma_db_no_llm_e5_base",
    embedding_function=embedding_model
)

# 3. 프로젝트별 필터링 retriever 설정 (k값 증가)
def get_retriever(project_id: int):
    return vectorstore.as_retriever(search_kwargs={
        "k": 30,
        "filter": {"project_id": project_id}
    })

# 4. 질문 재작성 함수 (간단한 규칙 기반)
def rewrite_question(original: str) -> str:
    if "AI" in original:
        return "운세 생성, AI 모델 연동, API 개발과 관련된 기능을 알려줘"
    return original

# 5. 프롬프트 템플릿
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
아래는 한 팀의 GitHub 활동 내역입니다:

{context}

사용자 질문: {question}

이 팀의 활동을 기반으로 핵심적인 답변을 자연스럽게 해줘.
큰 기능 단위로 정리하고, 너무 기술적이지 않게 설명해줘.
"""
)

# 6. LLM 설정 (HyperCLOVA)
llm = HyperClovaLangChainLLM()

# 7. RAG 실행 함수
def run_rag(question: str, project_id: int):
    retriever = get_retriever(project_id)
    rewritten_q = rewrite_question(question)

    # 디버깅용 정보 출력
    print("\n🧩 존재하는 컬렉션 목록:", vectorstore._client.list_collections())
    print("🔍 메타데이터 예시:", vectorstore._collection.get(limit=3)["metadatas"])

    # 문서 내 '운세' 포함 여부 확인
    docs = vectorstore._collection.get(limit=100)["documents"]
    for i, doc in enumerate(docs):
        if "운세" in doc:
            print(f"✅ 운세 관련 문서 발견! [Doc {i+1}]\n{doc[:300]}")

    # 검색된 문서 확인
    results = retriever.get_relevant_documents(rewritten_q)
    print(f"\n🔍 검색된 문서 수: {len(results)}")
    for i, doc in enumerate(results):
        print(f"\n📄 Doc {i+1}")
        print("Content:", doc.page_content[:100])
        print("Metadata:", doc.metadata)

    # RetrievalQA 체인 실행
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template}
    )


    return qa_chain.run(rewritten_q)

# 예시 실행
if __name__ == "__main__":
    q = "AI는 어떤 기능 개발했어?"
    answer = run_rag(q, project_id=1)
    print("\n🧠 Answer:\n", answer)



# PYTHONPATH=. python app/model_inference/rag_chat_runner.py
