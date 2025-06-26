# app/model_inference/loaders/hyperclova_langchain_llm.py

from langchain_core.language_models.llms import LLM
from typing import Optional, List, AsyncGenerator
from langchain_core.callbacks import CallbackManagerForLLMRun
from transformers import TextIteratorStreamer
from app.services.team_chat_service import TeamChatService
from pydantic import PrivateAttr

class HyperClovaLangChainLLM(LLM):
    """LangChain LLM wrapper for HyperCLOVA"""

    model_name: str = "HyperClovaLangChain"
    
    _service: TeamChatService = PrivateAttr()
    _tokenizer: any = PrivateAttr()
    _model: any = PrivateAttr()
    _device: any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = TeamChatService()
        self._tokenizer = self._service.tokenizer
        self._model = self._service.model
        self._device = self._service.device

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