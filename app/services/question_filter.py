from app.context_construction.prompts.question_filter_prompt import SYSTEM_PROMPT
from app.model_inference.loaders.gemini import GeminiLangChainLLM

llm = GeminiLangChainLLM()

def is_project_related(question: str, docs: list[str]) -> bool:
    """
    질문이 문서 내용과 관련 있는지 판단.
    관련 있으면 True, 없으면 False.
    """
    # 문서 목록 포맷팅
    context_str = "\n".join([f"{i+1}. {doc}" for i, doc in enumerate(docs)])
    prompt = f"{SYSTEM_PROMPT}\n\n질문:\n{question}\n\n문서 목록:\n{context_str}\n\n정답:"
    
    result = llm._call(prompt).strip().lower()
    return result == "yes"