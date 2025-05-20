# app/model_inference/chatbot_response_generator.py

from app.context_construction.vector_search import search_similar_docs
from app.services.team_chat_service import TeamChatService

team_chat_service = TeamChatService()

FALLBACK_CHAT = "팀 활동 내용을 바탕으로 답변을 생성하지 못했어요. 다시 시도해 주세요."

def run_team_chat_model(prompt: str) -> str:
    try:
        return team_chat_service.generate_answer(prompt)
    except Exception as e:
        print(f"❗ 챗봇 추론 실패: {e}")
        return FALLBACK_CHAT


def generate_team_response(question: str, team_id: str) -> str:
    docs, _, _ = search_similar_docs(question, team_id)
    context = "\n\n".join([doc for doc in docs if doc.strip()])

    prompt = f"""다음은 팀의 최근 GitHub 활동 내용입니다:\n\n{context}\n\n사용자 질문: "{question}"\n\n위 활동 내용을 바탕으로 친절하고 자연스럽게 답변해 주세요."""

    return run_team_chat_model(prompt)