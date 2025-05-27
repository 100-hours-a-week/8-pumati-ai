# app/context_construction/prompts/chat_prompt.py

from langchain.prompts import PromptTemplate

# 공통 prefix + suffix
PREFIX = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.
관련된 문서를 찾지 못하면 관련된 내용을 찾을 수 없다고 지어내지 말고 솔직하게 말해줘.
""".strip()

SUFFIX = """
Please generate your response based only on the context.
""".strip()

# 멀티 프롬프트 중간 내용
MIDDLE_PROMPTS = {
    "summary": "Question: {question}\nContext:\n{context}\n\n이 팀의 GitHub 활동을 기능 단위로 요약해줘. 기술 용어는 쉽게 설명해줘.",
    "timeline": "Question: {question}\nContext:\n{context}\n\nGitHub 활동을 시간 순으로 정리해줘.",
    "owner": "Question: {question}\nContext:\n{context}\n\n각 팀원이 어떤 기능에 주로 기여했는지 알려줘.",
}

# 멀티프롬프트 템플릿 생성
def build_prompt_template(q_type: str) -> PromptTemplate:
    middle = MIDDLE_PROMPTS.get(q_type, MIDDLE_PROMPTS["summary"])
    template = f"""{PREFIX}

{middle}

{SUFFIX}"""
    return PromptTemplate(
        input_variables=["question", "context"],
        template=template.strip()
    )

# 자유 질문 대응용 general 프롬프트
general_prompt_template = PromptTemplate(
    input_variables=["question", "context"],
    template=f"""{PREFIX}

Question: {{question}}
Context:
{{context}}

{SUFFIX}"""
)
