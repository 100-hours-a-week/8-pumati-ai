# app/services/fortune_service.py

import re
import torch
from app.model_inference.loaders.hyperclova_loader import HyperClovaLoader
import warnings

# 운세 모델 설정값
MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
MAX_NEW_TOKENS = 45
TEMPERATURE = 0.7
TOP_P = 0.7
warnings.filterwarnings("ignore", category=UserWarning, module="transformers.pytorch_utils") #transformers 라이브러리 내부에서 발생하는 에러. 동작에는 영향을 주지 않으므로 숨김 처리

class FortuneService:
    """
    HyperClovaLoader를 이용해 운세 텍스트를 생성하는 서비스 클래스.
    """
    def __init__(self):
        loader = HyperClovaLoader(MODEL_NAME)
        self.tokenizer, self.model, self.device = loader.load()

    def generate_fortune(self, prompt: str) -> str:
        """
        프롬프트를 입력받아 운세 텍스트(JSON 형태 포함)를 생성합니다.
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                top_p=TOP_P,
                temperature=TEMPERATURE,
                eos_token_id=self.tokenizer.eos_token_id,
            )[0]

        # 프롬프트 길이 이후의 생성된 토큰만 디코딩
        gen_ids = output_ids[inputs["input_ids"].shape[-1]:]
        raw = self.tokenizer.decode(gen_ids, skip_special_tokens=True)

        # 텍스트에서 JSON 부분만 추출
        match = re.search(r"\{[\s\S]*?\}", raw)
        return match.group() if match else raw