# app/model_inference/loaders/hyperclova_langchain_llm.py

from langchain_core.language_models.llms import LLM
from app.services.team_chat_service import TeamChatService
from typing import Optional, List


class HyperClovaLangChainLLM(LLM):
    """LangChain LLM wrapper for HyperCLOVA"""

    model_name: str = "HyperClovaLangChain"
    temperature: float = 0.3

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        service = TeamChatService()
        return service.generate_answer(prompt)

    @property
    def _llm_type(self) -> str:
        return "hyperclova_custom"
