import os
import re
import logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from huggingface_hub import login
from app.context_construction.query_rewriter import GemmaPrompt
from app.fast_api.schemas.comment_schemas import CommentRequest
from typing import Optional

# ----------------------------
# 로깅 설정
# ----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 상수 정의
# ----------------------------

MODEL_NAME = "google/gemma-3-1b-it"
FALLBACK_COMMENT = '{\n"content": "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌" \n}'
CPU_DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 200
TEMPERATURE = 0.9
TOP_P = 0.9

# ----------------------------
# GemmaModel 클래스
# ----------------------------

class GemmaModel:
    """
    Gemma 모델을 사용해 댓글 생성을 담당하는 클래스
    """
    _is_authenticated = False
    def __init__(self):
        self._authenticate_huggingface()
        self.model_name = MODEL_NAME
        self.device = CPU_DEVICE
        self.tokenizer = None
        self.model = None
        self.pipe = None
        logger.info("Device 설정: Device는 의도적으로 CPU로 고정됩니다.")
    
    def _authenticate_huggingface(self) -> None:
        """
        .env 파일에서 HF_AUTH_TOKEN을 로드하고 로그인한다.
        인증 최적화를 위해 _is_authenticated가 False일 경우만 로그인한다.
        """
        if GemmaModel._is_authenticated:
            logger.info("Hugging Face 인증 이미 완료됨.")
            return  # 이미 인증됨 → 그냥 넘어감

        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)

        GemmaModel._is_authenticated = True  # 인증 완료 처리
        logger.info("Hugging Face 인증 완료.")

    def load_gemma(self) -> None:
        """
        모델과 토크나이저를 로드하여 파이프라인을 초기화합니다.
        이미 초기화된 경우 아무 작업도 하지 않습니다.
        """
        if self.pipe is None: 
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
            self.pipe = pipeline(
                "text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=-1, 
                temperature=TEMPERATURE, 
                top_p=TOP_P, 
                do_sample=True
            )
            logger.info("Gemma 모델 로드 완료.")

    # 댓글 생성
    def generate_comment(self, request_data: CommentRequest) -> str:
        """
        프롬프트를 기반으로 댓글을 생성하고 JSON 포맷으로 후처리합니다.
        생성된 결과가 유효하지 않으면 fallback 메시지를 반환합니다.
        """
        prompt_builder = GemmaPrompt(request_data)
        prompt: str = prompt_builder.generate_prompt()

        logger.info("댓글 생성을 시작합니다.")
        outputs = self.pipe(prompt, max_new_tokens = MAX_NEW_TOKENS)[0]["generated_text"]
        output_text = outputs[len(prompt):].strip()

        #JSON 블록 추출
        try:
            logger.info("llm 댓글 추출 성공 : %s", output_text)
            find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
            generated_comment = find_comment[0].strip()
            logger.info("JSON 형식의 댓글 추출 성공.")
        except IndexError:
            logger.warning("JSON 추출 실패 → fallback 메시지 사용.")
            generated_comment = FALLBACK_COMMENT
    
        return generated_comment
    

# 싱글턴 인스턴스 생성 (서버 시작 시 1회만 실행)
gemma_model_instance = GemmaModel()
gemma_model_instance.load_gemma()

# ----------------------------
# 테스트 코드
# ---------------------------- 

if __name__ == "__main__":
    import time

    dummy_data = CommentRequest(
        comment_type="칭찬",
        team_projectName="품앗이 서비스",
        team_shortIntro="서로의 프로젝트 웹페이지를 방문하여 트래픽을 늘려줌",
        team_deployedUrl="https://resume.site",
        team_githubUrl="https://github.com/example",
        team_description="FastAPI + React 기반 프로젝트",
        team_tags=["AI", "Gemma", "GCP", "UI 친근함"],
    )
    

    start = time.time()
    logger.info("테스트 시작.")
    gemma = GemmaModel(dummy_data)
    gemma.load_gemma()
    comment = gemma.model_inference()
    logger.info("생성된 댓글: %s", comment)
    logger.info("실행 시간: %.2f초", time.time() - start)