# app/context_construction/prompts/wiki_summarize_prompt.py
from langchain.prompts import PromptTemplate

wiki_summarize_prompt_template = PromptTemplate(
    input_variables=["input"],
    template="""아래는 프로젝트의 Wiki 문서입니다.
- 이 문서는 팀 전체가 작성한 기획/설계 문서입니다.
- 핵심 목적과 설계 방향 위주로 요약해 주세요.
- 너무 짧거나 중복된 내용은 생략해도 됩니다.
- 기술적인 내용은 그것만 보고도 다른 사람이 이해할 수 있어야 해.
- wiki는 기획단계에서 설계했던 것이므로 ~하는 것이 목적이다라고만 써도 충분해.
- 100-hours-a-week은 팀이 아닌, 카카오테크 부트캠프의 organization명이니까 적지마.
- 절대 없는 말은 지어내지 말 것.

---
{input}
""".strip()
)
