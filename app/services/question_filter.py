from app.context_construction.prompts.question_filter_prompt import SYSTEM_PROMPT
from app.model_inference.loaders.gemini import GeminiLangChainLLM

llm = GeminiLangChainLLM()

def is_project_related(question: str) -> bool:
    """
    질문이 팀/프로젝트(GitHub 활동) 관련인지 Gemini LLM으로 판별한다.
    관련 있으면 True, 없으면 False 반환.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n질문: {question}\n답변:"
    result = llm._call(prompt).strip().lower()
    return result == "yes" 