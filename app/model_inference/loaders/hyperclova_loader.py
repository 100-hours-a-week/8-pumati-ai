# app/model_inference/loaders/HyperCLOVA_loader.py

import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
from app.utils.auth import authenticate_huggingface

logger = logging.getLogger(__name__)

class HyperClovaLoader:
    """
    HyperCLOVA 모델을 로드하고 토크나이저, 모델 객체, 디바이스 정보를 반환합니다.
    """
    def __init__(self, model_name: str):
        authenticate_huggingface()  # Hugging Face 인증 수행
        self.model_name = model_name
        self.device = self._get_device()

    def _get_device(self):
        # GPU > MPS > CPU 순으로 디바이스를 선택
        if torch.cuda.is_available():
            return torch.device("cuda")
        # elif torch.backends.mps.is_available():
        #     return torch.device("mps")
        return torch.device("cpu")

    def load(self):
        """
        모델과 토크나이저를 로드하여 반환합니다.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)

        if self.device.type == "cuda":
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            try:
                model = torch.compile(model)  # 성능 최적화를 위한 torch.compile 시도
            except ImportError:
                logger.warning("optimum 설치되지 않음. BetterTransformer 생략.")
        else:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32
            ).to(self.device)

        logger.info("모델 및 토크나이저 로드 완료.")
        return tokenizer, model, self.device