# app/model_inference/loaders/HyperCLOVA_loader.py

import os
import re
import json
import logging
import platform
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import torch
import warnings

# ----------------------------
# 로깅 설정
# ----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)  # PyTorch 워닝 무시 설정

# ----------------------------
# 상수 정의
# ----------------------------

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
MAX_NEW_TOKENS = 45
TEMPERATURE = 0.7
TOP_P = 0.7

# ----------------------------
# ClovaxFortuneModel 클래스
# ----------------------------

class ClovaxFortuneModel:
    """
    HyperCLOVA 모델을 이용한 운세 생성기
    """
    _is_authenticated = False

    def __init__(self):
        self._authenticate_huggingface()
        self.model_name = MODEL_NAME
        self.device = self._get_device()
        self.tokenizer = None
        self.model = None
        logger.info(f"✅ 디바이스 설정 완료: {self.device}")

    def _authenticate_huggingface(self) -> None:
        if ClovaxFortuneModel._is_authenticated:
            logger.info("Hugging Face 인증 이미 완료됨.")
            return

        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)
        ClovaxFortuneModel._is_authenticated = True
        logger.info("Hugging Face 인증 완료.")

    def _get_device(self):
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def load_model(self):
        hf_token = os.getenv("HF_AUTH_TOKEN")
        self.tokenizer = AutoTokenizer.from_pretrained( 
            self.model_name,
            trust_remote_code=True,
            token=hf_token
        )

        if self.device.type == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                token=hf_token,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            try:
                from optimum.bettertransformer import BetterTransformer
                # self.model = BetterTransformer.transform(self.model)
                self.model = torch.compile(self.model)
            except ImportError:
                logger.warning("optimum 설치되지 않음. BetterTransformer 생략.")
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                token=hf_token,
                torch_dtype=torch.float32
            ).to(self.device)

        logger.info("모델 및 토크나이저 로드 완료.")

    def generate_fortune(self, prompt: str) -> str:
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

        gen_ids = output_ids[inputs["input_ids"].shape[-1]:]
        raw = self.tokenizer.decode(gen_ids, skip_special_tokens=True)

        match = re.search(r"\{[\s\S]*?\}", raw)
        return match.group() if match else raw


# ----------------------------
# 외부 모듈용 래퍼 함수 (FastAPI 등에서 import)
# ----------------------------

model_instance = ClovaxFortuneModel()
model_instance.load_model()

def generate_fortune_text(prompt: str) -> str:
    return model_instance.generate_fortune(prompt)
