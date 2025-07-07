from app.model_inference.loaders.gemini import GeminiLangChainLLM

SYSTEM_PROMPT = (
    """
    너는 팀의 GitHub 활동과 프로젝트에 관한 질문만을 판별하는 분류기야.\n
    아래의 질문이 팀의 GitHub 활동, 코드, 이슈, PR, 개발 관련 질문인지 판단해.\n
    - 만약 팀/프로젝트와 관련된 질문이면 'yes'만 출력해.\n    - 관련이 없다면 'no'만 출력해.\n    - 추가 설명, 이유, 기타 문장은 절대 쓰지 마.\n    - 오직 yes 또는 no만 반환해.\n    - 예시: '오늘 점심 뭐 먹지?' → no, '이 PR에 버그 있나요?' → yes\n    """
)

llm = GeminiLangChainLLM()

def is_project_related(question: str) -> bool:
    """
    질문이 팀/프로젝트(GitHub 활동) 관련인지 Gemini LLM으로 판별한다.
    관련 있으면 True, 없으면 False 반환.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n질문: {question}\n답변:"
    result = llm._call(prompt).strip().lower()
    return result == "yes" 