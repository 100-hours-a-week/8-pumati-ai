# app/context_construction/prompts/summarize_prompt.py

from langchain.prompts import PromptTemplate

PREFIX = """아래는 팀의 개발 활동 기록입니다.
- 절대 없는 말은 지어내지 말 것.
- 요약은 핵심 사항을 정리해 주세요.
- 중복되거나 불필요한 내용은 생략해 주세요.
- 기술적인 내용은 그것만 보고도 다른 사람이 이해할 수 있어야 해.
- 기록이 너무 짧거나 무의미하다면 생략해줘.
- AI, BE, CL파트로 나뉘는데, part나 파트를 보고, ~파트가 ~을 했다라고 써줘.
- 되도록 한국어 이름이 아닌 영어이름이나 닉네임으로 해줘.
- 너무 많은 내용을 생략하지는 말아줘.
- pr, 트러블슈팅, 타운홀 미팅등은 진행상황을 알 수 있는 중요한 지표야.
- wiki는 기획단계에서 설계했던 것이므로 ~하는 것이 목적이다라고만 써도 충분해.
- 같은 기능에 대한 이슈, pr, 트러블슈팅이 있다면, 연관지어서 요약하면 좋아.
- 100-hours-a-week은 팀이 아닌, 카카오테크 부트캠프의 organization명이니까 적지마.
""".strip()

SUFFIX = """---
요약 대상 팀 번호: {team_id}
요약 대상 파트: {part} (이 파트를 중심으로 요약해야 함)

아래는 요약할 원문입니다:

{input}
""".strip()

summarize_prompt_template = PromptTemplate(
    input_variables=["input", "team_id", "part"],
    template=f"{PREFIX}\n\n{SUFFIX}"
)