# app/context_construction/prompts/chat_prompt.py

from langchain.prompts import PromptTemplate

# 공통 prefix + suffix
PREFIX = """문서를 읽고 아래 질문에 답하는 챗봇이야.
줄바꿈(\n)과 마크다운으로 가독성 좋게 나타내줘.
답변은 핵심 정보만 2~3문장으로 간결하게 작성해. 문서에 없는 내용은 절대 지어내지 마.
""".strip()

SUFFIX = """---
💬 이제 위 질문에 대한 답변을 작성해줘:

답변:""".strip()

# 멀티 프롬프트 지시문
MIDDLE_PROMPTS = {
    "summary": "이 팀의 GitHub 활동을 기능 단위로 요약해줘. 기술 용어는 쉽게 풀어서 설명해.",
    "timeline": "이 팀의 GitHub 활동을 시간 순으로 정리해줘.",
    "owner": "각 팀원이 어떤 기능에 주로 기여했는지 알려줘.",
    "project": """wiki를 참고한 것은 정확한 정보가 아니니 "~하는 것이 목적이다. "라는 말처럼 예상 형식으로 써줘. 
- 각 기능 또는 문장은 `-` 기호로 시작해줘.
""",
    "function": "기술용어는 넣지 마. ",
}

# 멀티프롬프트 템플릿 생성 함수
def build_prompt_template(q_type: str) -> PromptTemplate:
    instruction = MIDDLE_PROMPTS.get(q_type, MIDDLE_PROMPTS["summary"])
    template = f"""{PREFIX}

Context:
{{context}}

{instruction}

{SUFFIX}"""
    return PromptTemplate(
        input_variables=["context"],
        template=template.strip()
    )

# 자유 질문 대응용 템플릿
general_prompt_template = PromptTemplate(
    input_variables=["question", "context"],
    template=f"""{PREFIX}

Context:
{{context}}

질문: {{question}}  
이 질문에 대해 위 Context만 참고해서 간결하게 답변해줘.

{SUFFIX}.strip()"""
)
