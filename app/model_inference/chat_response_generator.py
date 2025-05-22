# app/model_inference/chatbot_response_generator.py

################################
# 임베딩 모델 multilingual-e5-small
################################
# from app.services.team_chat_service import TeamChatService
# import chromadb
# from sentence_transformers import SentenceTransformer

# # 초기 세팅
# team_chat_service = TeamChatService()
# FALLBACK_CHAT = "팀 활동 내용을 바탕으로 답변을 생성하지 못했어요. 다시 시도해 주세요."
# model = SentenceTransformer("intfloat/multilingual-e5-small")  # 저장에 사용한 것과 동일 모델
# client = chromadb.PersistentClient(path="./chroma_db")
# collection = client.get_or_create_collection(name="github_docs")

# def run_team_chat_model(prompt: str) -> str:
#     try:
#         return team_chat_service.generate_answer(prompt)
#     except Exception as e:
#         print(f"❗ 챗봇 추론 실패: {e}")
#         return FALLBACK_CHAT


# def generate_team_response(question: str, team_id: str, top_k: int = 3) -> str:
#     # 1. 질문 임베딩 생성
#     embedding = model.encode([question], normalize_embeddings=True).tolist()

#     # 2. team_id 기준 유사 문서 검색
#     result = collection.query(
#         query_embeddings=embedding,
#         n_results=top_k,
#         where={"team_id": team_id},  # team_id 필드를 기준으로 필터링
#         include=["documents", "distances", "metadatas"]
#     )

#     # 3. context 구성
#     docs = result.get("documents", [[]])[0]
#     context = "\n\n".join([doc for doc in docs if doc.strip()])

#     # 4. prompt 구성
#     prompt = f"""다음은 팀의 최근 GitHub 활동 내용입니다:\n\n{context}\n\n사용자 질문: "{question}"\n\n위 활동 내용을 바탕으로 친절하고 자연스럽게 답변해 주세요."""

#     # 5. 모델 추론 실행
#     return run_team_chat_model(prompt)

################################
# 임베딩 모델 paraphrase-multilingual-MiniLM-L12-v2
################################
from app.services.team_chat_service import TeamChatService
import chromadb
from transformers import AutoTokenizer, AutoModel
import torch

# 0. 모델 준비
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
device = torch.device("cpu")
model.to(device)
model.eval()

# 1. 기타 서비스 준비
team_chat_service = TeamChatService()
FALLBACK_CHAT = "팀 활동 내용을 바탕으로 답변을 생성하지 못했어요. 다시 시도해 주세요."
client = chromadb.PersistentClient(path="./chroma_db_no_llm")
collection = client.get_or_create_collection(name="github_docs")

def run_team_chat_model(prompt: str) -> str:
    try:
        return team_chat_service.generate_answer(prompt)
    except Exception as e:
        print(f"❗ 챗봇 추론 실패: {e}")
        return FALLBACK_CHAT


def embed_with_transformers(text: str) -> list:
    instruction = "passage: " + text.strip()
    inputs = tokenizer(instruction, return_tensors="pt", truncation=True, padding=True).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state[:, 0, :]  # CLS 토큰
    return embedding.squeeze().cpu().numpy().tolist()


def generate_team_response(question: str, project_id: int, top_k: int = 3) -> str:
    # 2. 질문 임베딩
    embedding = embed_with_transformers(question)

    # 3. Chroma에서 project_id 기준 유사 문서 검색
    result = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where={"project_id": project_id},
        include=["documents", "distances", "metadatas"]
    )
    

    # 4. context 구성
    docs = result.get("documents", [[]])[0]
    context = "\n\n".join([doc for doc in docs if doc.strip()])

    print("✅ 검색된 문서 개수:", len(docs))
    for i, d in enumerate(docs):
        print(f"[{i+1}] {d[:100]}...")

    # 5. 프롬프트 구성
    prompt = f"""다음은 팀의 최근 GitHub 활동 내용입니다:\n\n{context}\n\n사용자 질문: "{question}"\n\n위 활동 내용을 바탕으로 친절하고 자연스럽게 답변해 주세요."""

    # 6. 모델 추론
    return run_team_chat_model(prompt)
