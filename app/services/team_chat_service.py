# app/services/team_chat_service.py

import torch
from app.model_inference.loaders.hyperclova_loader import HyperClovaLoader
import warnings

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
MAX_NEW_TOKENS = 150
TEMPERATURE = 0.2
TOP_P = 0.7
TOP_K = 1

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.pytorch_utils")

class TeamChatService:
    def __init__(self):
        loader = HyperClovaLoader(MODEL_NAME)
        self.tokenizer, self.model, self.device = loader.load()

    def generate_answer(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                top_p=TOP_P,
                top_k=TOP_K,
                temperature=TEMPERATURE,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        return self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
