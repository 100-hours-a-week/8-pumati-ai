# app/model_inference/loaders/hyperclova_langchain_llm.py

from typing import Optional, List
from langchain_core.language_models.llms import LLM
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from dotenv import load_dotenv

class HyperClovaLangChainLLM(LLM):
    model_id: str = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
    max_new_tokens: int = 150
    temperature: float = 0.3
    top_p: float = 0.7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        load_dotenv()
        hf_token = os.getenv("HF_AUTH_TOKEN")

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_id, trust_remote_code=True, token=hf_token
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id, trust_remote_code=True, token=hf_token
        )

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        self._model.eval()

    @property
    def _llm_type(self) -> str:
        return "hyperclova"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)

        with torch.inference_mode():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                top_p=self.top_p,
                temperature=self.temperature,
                eos_token_id=self._tokenizer.eos_token_id
            )

        return self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
