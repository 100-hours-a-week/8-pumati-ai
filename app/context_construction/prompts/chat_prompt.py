# app/context_construction/prompts/chat_prompt.py

from langchain.prompts import PromptTemplate

# 공통 prefix + suffix
PREFIX = """너는 팀의 GitHub 활동을 분석하는 AI야.
아래 문서 내용을 참고해서 질문에 답변해줘.
답변은 핵심 정보만 2~3문장으로 간결하게 작성하고, 문서에 없는 내용은 절대 지어내지 마.
""".strip()

SUFFIX = """---
💬 이제 위 질문에 대한 답변을 작성해줘:

답변:""".strip()

# 멀티 프롬프트 지시문
MIDDLE_PROMPTS = {
    "summary": "이 팀의 GitHub 활동을 기능 단위로 요약해줘. 기술 용어는 쉽게 풀어서 설명해.",
    "timeline": "이 팀의 GitHub 활동을 시간 순으로 정리해줘.",
    "owner": "각 팀원이 어떤 기능에 주로 기여했는지 알려줘.",
    "project": """wiki문서만 참고해.home, vision 부분을 주로 참고해서 알려줘.
문서 전체 흐름을 요약하는 방식으로, 특정 키워드 하나에만 집중하지 말고 전체 프로젝트를 설명해줘.
개발자가 누구인지는 말하지마.
아직 진행중인 프로젝트이니 부하테스트 관련은 빼줘.
TanStack Query, Prometheus, FastAPI, CI/CD 같은 내부 기술 용어나 개발 도구 이름은 모두 제외하고,
사용자가 실제 사용할 수 있는 기능 중심(예: 추천, 커뮤니티, 장소 공유 등)으로 설명해줘.
누구나 쉽게 이해할 수 있는 문장으로, 홍보문처럼 친절하게 설명해줘.""",
}

# 멀티프롬프트 템플릿 생성 함수
def build_prompt_template(q_type: str) -> PromptTemplate:
    instruction = MIDDLE_PROMPTS.get(q_type, MIDDLE_PROMPTS["summary"])
    template = f"""{PREFIX}

📄 Context:
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

📄 Context:
{{context}}

질문: {{question}}  
이 질문에 대해 위 Context만 참고해서 간결하게 답변해줘.

{SUFFIX}"""
)
