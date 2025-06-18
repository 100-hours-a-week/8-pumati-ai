# app/context_construction/prompts/chat_prompt.py

from langchain.prompts import PromptTemplate

# 공통 prefix + suffix
PREFIX = """너는 팀의 GitHub 활동을 분석하는 AI야.
아래 문서 내용을 참고해서 질문에 답변해줘.
줄바꿈(\n)과 마크다운으로 가독성 좋게 나타내줘. 하지만 답변의 가장 마지막 문장에는 절대 줄바꿈 넣지 마. 만약 마지막 문장인데 마지막에 줄바꿈이 있다면 제거해줘. 그리고 줄바꿈을 한번에 3개 이상 넣지 않도록 해.
`-` 기호로 시작하는 목록 형식으로 나열하거나, 문단 구분 적절하게 해줘.
답변은 핵심 정보만 2~3문장으로 간결하게 작성하고, 문서에 없는 내용은 절대 지어내지 마.
모든 팀들은 설계 완료 후 개발 진행중이야. wiki는 설계 문서이고 실제 개발 진행상황은 pr, issue, 데일리스크럼, 타운홀 미팅 등을 봐.

""".strip()

SUFFIX = """---
💬 이제 위 질문에 대한 답변을 작성해줘:

답변:""".strip()

# 멀티 프롬프트 지시문
MIDDLE_PROMPTS = {
    "summary": "이 팀의 GitHub 활동을 기능 단위로 요약해줘. 기술 용어는 쉽게 풀어서 설명해.",
    "timeline": "이 팀의 GitHub 활동을 시간 순으로 정리해줘.",
    "owner": "각 팀원이 어떤 기능에 주로 기여했는지 알려줘.",
    "project": """wiki문서만 참고해.home, vision 부분을 주로 참고해서 알려줘. wiki를 참고한 것은 정확한 정보가 아니니 "~하는 것이 목적이다. "라는 말처럼 예상 형식으로 써줘. 
- 각 기능 또는 문장은 `-` 기호로 시작해줘.
문서 전체 흐름을 요약하는 방식으로, 특정 키워드 하나에만 집중하지 말고 전체 프로젝트를 설명해줘.
개발자가 누구인지, 개발자 닉네임을 말하지 마.
아직 진행중인 프로젝트이니 부하테스트 관련은 빼줘.
TanStack Query, Prometheus, FastAPI, CI/CD 같은 내부 기술 용어나 개발 도구 이름은 모두 제외하고,
사용자가 실제 사용할 수 있는 기능 중심(예: 추천, 커뮤니티, 공유 등)으로 설명해줘.
누구나 쉽게 이해할 수 있는 문장으로, 홍보문처럼 친절하게 설명해줘.

""",
    "function": "큰 기능들 위주로 요약해줘. fe, be, ai의 기능들을 합해서 실제 구현된 기능들을 알려줘. 기술용어는 넣지 마. ",
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
