# app/context_construction/prompts/chat_prompt_timeline.py

def build_prompt(context: str, question: str) -> str:
    return f"""
{context}

질문: {question}

GitHub 활동 날짜를 기준으로 이번주에 진행된 주요 기능이나 작업을 요약해줘.
중요한 활동만 간결하게 정리해줘.
""".strip()
