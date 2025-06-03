from langchain_core.language_models import LLM
from langchain_core.outputs import LLMResult, Generation
from typing import List, Optional
import google.generativeai as genai
import os
from pydantic import PrivateAttr

# Gemini API 키 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiLangChainLLM(LLM):
    model_name: str = "gemini-1.5-flash"  # 또는 "models/gemini-1.5-flash"

    _model: genai.GenerativeModel = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model = genai.GenerativeModel(self.model_name)

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None) -> LLMResult:
        generations = []

        for prompt in prompts:
            response = self._model.generate_content(prompt)
            output = response.text
            generations.append([Generation(text=output)])

        return LLMResult(generations=generations)

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = self._model.generate_content(prompt)
        return response.text

    @property
    def _llm_type(self) -> str:
        return "gemini"
