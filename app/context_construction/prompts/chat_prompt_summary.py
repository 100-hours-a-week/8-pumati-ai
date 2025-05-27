# app/context_construction/prompts/chat_prompt_summary.py

# def build_prompt(context: str, question: str) -> str:
#     return f"""
# {context}

# 질문: {question}

# 이 팀의 GitHub 활동을 바탕으로 주요 기능을 요약해줘.
# 기능 단위로 묶고, 기술 용어는 풀어서 쉽게 설명해줘.
# """.strip()

from app.context_construction.prompts.chat_prompt_common import PREFIX, SUFFIX

# 공통 지침(prompt prefix), 질문 유형별로 후행 추가(prompt suffix)
def build_prompt(context: str, question: str) -> str:
    return f"""{PREFIX}

Context:
{context}

Question:
{question}

큰 기능 단위로 묶어서 요약해줘. 

{SUFFIX}
""".strip()
