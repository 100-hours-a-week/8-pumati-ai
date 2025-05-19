# import os
# import logging
# from dotenv import load_dotenv
# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# from sentence_transformers import SentenceTransformer
# import torch
# from huggingface_hub import login
# from fast_api.schemas.comment_schemas import CommentRequest
# from context_construction.prompt.comment_prompt import GemmaPrompt

# # ----------------------------
# # 로깅 설정
# # ----------------------------

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ----------------------------
# # 상수 정의
# # ----------------------------

# #gemma로 모델 변경
# MODEL_NAME ="google/gemma-3-1b-it" #"naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"
# FALLBACK_COMMENT = "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌"
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"#"intfloat/multilingual-e5-small"
# CPU_DEVICE = torch.device("cpu")
# MAX_NEW_TOKENS = 80
# MAX_NEW_TOKENS_SUMMARY = 50
# TEMPERATURE = 0.9
# TOP_P = 0.9
# REPETITION_PENALTY = 1.2
# MAX_RETRY = 60


# # ----------------------------
# # GemmaModel 클래스
# # ----------------------------

# class GemmaModel:
#     """
#     Gemma 모델을 사용해 댓글 생성을 담당하는 클래스
#     """
#     _is_authenticated = False
#     def __init__(self):
#         self._authenticate_huggingface()
#         self.model_name = MODEL_NAME
#         self.device = CPU_DEVICE
#         self.tokenizer = None
#         self.model = None
#         self.pipe = None
#         logger.info(f"Device 설정: Device는 의도적으로 CPU로 고정됩니다.")
#         self.embed_model = None
        
    
#     def _authenticate_huggingface(self) -> None:
#         """
#         .env 파일에서 HF_AUTH_TOKEN을 로드하고 로그인한다.
#         인증 최적화를 위해 _is_authenticated가 False일 경우만 로그인한다.
#         """
#         if GemmaModel._is_authenticated:
#             logger.info("Hugging Face 인증 이미 완료됨.")
#             return  # 이미 인증됨 → 그냥 넘어감

#         load_dotenv()
#         token = os.getenv("HF_AUTH_TOKEN")
#         if not token:
#             raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
#         login(token=token)

#         GemmaModel._is_authenticated = True  # 인증 완료 처리
#         logger.info("Hugging Face 인증 완료.")


#     def load_gemma(self) -> None:
#         """
#         모델과 토크나이저를 로드하여 파이프라인을 초기화합니다.
#         이미 초기화된 경우 아무 작업도 하지 않습니다.
#         """
#         if self.pipe is None: 
#             self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
#             self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
#             self.pipe = pipeline(
#                 "text-generation", 
#                 model=self.model, 
#                 tokenizer=self.tokenizer, 
#                 device=-1, 
#                 temperature=TEMPERATURE, 
#                 top_p=TOP_P, 
#                 do_sample=True,
#                 repetition_penalty=REPETITION_PENALTY
#             )
#             self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device = self.device)
#             logger.info("Gemma 모델 로드 완료.")
#             logger.info("임베딩 기반 검열 모델 로드 완료.")

   
# # 싱글턴 인스턴스 생성 (서버 시작 시 1회만 실행)
# # 생성 목적: 댓글기능은 4번 모델을 호출하며, 호출시마다 인스턴스를 생성할 필요 없음. 불필요한 인스턴스 생성을 줄이고자 함.
# comment_creator = GemmaModel()
# comment_creator.load_gemma()

import os, logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
from huggingface_hub import login
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "google/gemma-3-1b-it"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TEMPERATURE = 0.9
TOP_P = 0.9
REPETITION_PENALTY = 1.2

class GemmaModel:
    _is_authenticated = False

    def __init__(self):
        self._authenticate_huggingface()
        self.model_name = MODEL_NAME
        self.device = torch.device("cpu")
        self.pipe = None
        self.embed_model = None
        self._load_model()

    def _authenticate_huggingface(self):
        if GemmaModel._is_authenticated:
            return
        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)
        GemmaModel._is_authenticated = True

    def _load_model(self):
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
        self.pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            do_sample=True,
            repetition_penalty=REPETITION_PENALTY
        )
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=self.device)
        logger.info("Gemma 모델 및 임베딩 모델 로드 완료")

comment_creator = GemmaModel()


# 📁 auth/huggingface_auth.py (필요 시 따로 분리 가능)
# 현재는 comment_loader 내부에 인증 포함돼 있으므로 생략 가능
# 하지만 추후 auth 모듈로 나누고 싶다면 이 위치로 함수 분리하세요
