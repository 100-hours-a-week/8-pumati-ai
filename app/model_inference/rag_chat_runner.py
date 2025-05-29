# app/model_inference/rag_chat_runner.py

from app.model_inference.loaders.hyperclova_loader import HyperClovaLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import torch

load_dotenv()

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"

# 1. 모델 불러오기
loader = HyperClovaLoader(MODEL_NAME)
tokenizer, model, device = loader.load()

# 2. 벡터 DB 준비
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")
vectorstore = Chroma(
    collection_name="github_docs",
    persist_directory="./chroma_db_e5_base",
    embedding_function=embedding_model,
)

# 3. 실행 함수
def run_rag(question: str, project_id: int) -> str:
    # context 검색
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10, "filter": {"project_id": project_id}})
    docs = retriever.get_relevant_documents(question)
    context = "\n".join([doc.page_content for doc in docs])

    #  chat template 구성
    chat = [
        {"role": "tool_list", "content": ""},
        {"role": "system", "content": "- 너는 GitHub 기반 문서 요약 전문가야.\n- 문서 내용을 바탕으로 핵심 정보를 간단히 정리해줘."},
        {"role": "user", "content": f"질문: {question}\n문서 내용:\n{context}\n답변:"}
    ]

    # 토크나이즈 + 추론 + 디토크나이즈
    inputs = tokenizer.apply_chat_template(chat, add_generation_prompt=True, return_dict=True, return_tensors="pt").to(device)
    output_ids = model.generate(**inputs, max_length=1024, stop_strings=["<|endofturn|>", "<|stop|>"], tokenizer=tokenizer)
    decoded = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]

    return decoded.strip()
