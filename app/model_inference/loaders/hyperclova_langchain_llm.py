# app/model_inference/loaders/hyperclova_langchain_llm.py

from langchain_core.language_models.llms import LLM
from typing import Optional, List, AsyncGenerator
from langchain_core.callbacks import CallbackManagerForLLMRun
from transformers import TextIteratorStreamer
from app.services.team_chat_service import TeamChatService
from pydantic import PrivateAttr

class HyperClovaLangChainLLM(LLM):
    """LangChain LLM wrapper for HyperCLOVA using vLLM API"""

    model_name: str = "HyperClovaLangChain"
    
    _service: TeamChatService = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = TeamChatService()

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        return self._service.generate_answer(prompt)

    @property
    def _llm_type(self) -> str:
        return "hyperclova_custom"