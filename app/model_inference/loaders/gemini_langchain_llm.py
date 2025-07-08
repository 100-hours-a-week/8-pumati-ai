# app/model_inference/chains/gemini_langchain_llm.py

from app.model_inference.loaders.gemini import GeminiLangChainLLM
from app.context_construction.prompts.summarize_prompt import summarize_prompt_template

# Gemini LLM 인스턴스
llm = GeminiLangChainLLM()

# 요약 기능: prompt | llm 체인 구성
summarize_chain = summarize_prompt_template | llm