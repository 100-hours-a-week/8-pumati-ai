from langchain_core.language_models import LLM
from typing import List, Optional
import google.generativeai as genai
import os
from pydantic import PrivateAttr
from typing import List, Optional
from langchain_core.callbacks import CallbackManagerForLLMRun
import re


# Gemini API 키 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiLangChainLLM(LLM):
    model_name: str = "gemini-1.5-flash"
    _model: genai.GenerativeModel = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model = genai.GenerativeModel(self.model_name)

    async def astream(self, prompt: str, **kwargs):
        chat = self._model.start_chat()
        stream = chat.send_message(prompt, stream=True)

        for chunk in stream:
            new_text = chunk.text or ""
            yield new_text # LLM이 반환하는 원본 문자열 청크를 그대로 전달

        # 전체 결과 누적해서 한 번에 보기 (디버깅용)
        final_full_response = chat.history[-1].parts[0].text if chat.history else ""
        print("🧾 Gemini full response (for debug):", repr(final_full_response.replace('\n', '\\n')))
            
    @property
    def streaming(self) -> bool:
        return True

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs) -> str:
        chat = self._model.start_chat()
        response = chat.send_message(prompt)
        return response.text