from langchain_core.language_models import LLM
from langchain_core.outputs import LLMResult, Generation
from typing import List, Optional
import google.generativeai as genai
import os
import asyncio
from pydantic import PrivateAttr
from typing import List, Optional, AsyncGenerator
from langchain_core.callbacks import CallbackManagerForLLMRun
import threading
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

        buffer = ""

        for chunk in stream:
            new_text = chunk.text or ""
            buffer += new_text

            # 문장 단위로 끊어서 보내기
            while True:
                match = re.search(r"(.+?[.?!])(\s+|$)", buffer)
                if match:
                    sentence = match.group(1)
                    buffer = buffer[match.end():]
                    print("🟢 Gemini sentence:", repr(sentence))
                    yield sentence
                else:
                    break

            # 문장이 없어도 일정 길이 넘으면 보내기 (단어 깨짐 방지)
            if len(buffer) >= 20:
                split_point = buffer.rfind(" ")
                if split_point != -1:
                    partial = buffer[:split_point + 1]
                    buffer = buffer[split_point + 1:]
                    print("⚠️ Gemini buffer partial:", repr(partial))
                    yield partial

        # 남은 버퍼 처리
        if buffer.strip():
            print("🔚 Gemini buffer flush:", repr(buffer))
            yield buffer



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