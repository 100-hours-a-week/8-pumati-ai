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
TEMPERATURE = 0.85
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
        self.model = None
        self.tokenizer = None
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
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=self.device)
        logger.info("Gemma 모델 및 임베딩 모델 로드 완료")

comment_creator = GemmaModel()


# 📁 auth/huggingface_auth.py (필요 시 따로 분리 가능)
