# app/context_construction/prompts/chat_prompt_summary.py

def build_prompt(context: str, question: str) -> str:
    return f"""
{context}

질문: {question}

이 팀의 GitHub 활동을 바탕으로 주요 기능을 요약해줘.
기능 단위로 묶고, 기술 용어는 풀어서 쉽게 설명해줘.
""".strip()
