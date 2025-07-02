# app/services/team_chat_service.py

import torch
from app.model_inference.loaders.hyperclova_loader import HyperClovaLoader
import warnings
import re

MODEL_NAME = "sunnyanna/hyperclovax-sft-1.5b-v2"
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
        print("[DEBUG] generate_answer 진입")
        print("[DEBUG] 프롬프트:", prompt)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_length = inputs["input_ids"].shape[1]

        print("[DEBUG] 추론 시작 전")
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
        print("[DEBUG] 추론 완료")
        generated_tokens = output[0][input_length:]
        decoded = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip() # prompt 이후에 새로 생성한 부분만
        print("🧾 HyperClova full response (for debug):", repr(decoded.replace('\n', '\\n')))
        match = re.search(r"[가-힣][^a-zA-Z0-9]{0,10}", decoded)
        if match:
            cleaned = decoded[match.start():]
        else:
            cleaned = decoded
        return cleaned
