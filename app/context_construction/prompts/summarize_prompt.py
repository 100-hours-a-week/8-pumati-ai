# app/context_construction/prompts/summarize_prompt.py

from langchain.prompts import PromptTemplate

PREFIX = """아래는 팀의 개발 활동 기록입니다.
- 절대 없는 말은 지어내지 말 것.
- 요약은 핵심 사항을 최대 3~5줄로 정리해 주세요.
- 중복되거나 불필요한 내용이나 너무 기술적인 내용은 생략해 주세요.
- 활동 기록이 짧거나 해당 파트에 맞는 내용이 없다면 해당 파트는 생략해 주세요.
""".strip()

SUFFIX = """---
아래는 요약할 원문입니다:

{input}
""".strip()

gemini_summarize_prompt_template = PromptTemplate(
    input_variables=["input"],
    template=f"{PREFIX}\n\n{SUFFIX}"
)