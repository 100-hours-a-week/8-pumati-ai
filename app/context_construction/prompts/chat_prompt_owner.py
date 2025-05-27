# app/context_construction/prompts/chat_prompt_owner.py

def build_prompt(context: str, question: str) -> str:
    return f"""
{context}

질문: {question}

기여자 기록을 참고해 누가 해당 기능을 개발했는지 알려줘.
이슈나 PR의 작성자 정보를 중심으로 답변해줘.
""".strip()
