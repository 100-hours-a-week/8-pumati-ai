# app/model_inference/chains/gemini_langchain_llm.py

from langchain.chains import LLMChain
from app.model_inference.loaders.gemini import GeminiLangChainLLM
from app.context_construction.prompts.gemini_summarize_prompt import gemini_summarize_prompt_template

# Gemini LLM 인스턴스
llm = GeminiLangChainLLM()

# 요약 기능 LLMChain
summarize_chain = LLMChain(
    llm=llm,
    prompt=gemini_summarize_prompt_template
)