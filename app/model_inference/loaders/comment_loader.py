import os
import re
import json
import logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from huggingface_hub import login
from context_construction.query_rewriter import ClovaxPrompt
from fast_api.schemas.comment_schemas import CommentRequest
from pathlib import Path

# ----------------------------
# 로깅 설정
# ----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 상수 정의
# ----------------------------

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"#"google/gemma-3-1b-it"
MODEL_PATH = model_path = Path(__file__).parent.parent.parent / "models" / "hyperclovax"
FALLBACK_COMMENT = '{\n"content": "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌" \n}'
CPU_DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 200
TEMPERATURE = 0.7
TOP_P = 0.8
REPETITION_PENALTY = 1.2
MAX_RETRY = 10


# ----------------------------
# ClovaxModel 클래스
# ----------------------------

class ClovaxModel:
    """
    Clovax 모델을 사용해 댓글 생성을 담당하는 클래스
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
        if ClovaxModel._is_authenticated:
            logger.info("Hugging Face 인증 이미 완료됨.")
            return  # 이미 인증됨 → 그냥 넘어감

        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)

        ClovaxModel._is_authenticated = True  # 인증 완료 처리
        logger.info("Hugging Face 인증 완료.")

    def load_clovax(self) -> None:
        """
        모델과 토크나이저를 로드하여 파이프라인을 초기화합니다.
        이미 초기화된 경우 아무 작업도 하지 않습니다.
        """
        if self.pipe is None: 
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name) #.to(self.device)
            self.pipe = pipeline(
                "text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=-1, 
                temperature=TEMPERATURE, 
                top_p=TOP_P, 
                do_sample=True,
                repetition_penalty=REPETITION_PENALTY
            )
            logger.info("Clovax 모델 로드 완료.")

    # 댓글 생성
    def validate_generated_comment(self, generated_comment_dict: dict) -> bool:
        """
        생성된 댓글 JSON이 유효한지 검사.
        필수 필드(content)가 없거나 값이 비어있으면 False
        """
        if "content" not in generated_comment_dict:
            return False

        content = generated_comment_dict["content"]

        if not isinstance(content, str) or not content.strip():
            return False
        
        if len(content.split()) <= 2:
            return False

        return True


    def generate_comment(self, request_data: CommentRequest) -> dict:
        prompt_builder = ClovaxPrompt(request_data)
        prompt: str = prompt_builder.generate_prompt()

        for attempt in range(1, MAX_RETRY + 1):
            logger.info(f"댓글 생성 시도 {attempt}회")
            outputs = self.pipe(prompt, max_new_tokens=MAX_NEW_TOKENS)[0]["generated_text"]
            output_text = outputs[len(prompt):].strip()

            try:
                find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
                generated_comment_str = find_comment[0].strip()
                generated_comment_dict = json.loads(generated_comment_str)

                # 유효성 검사 추가
                if self.validate_generated_comment(generated_comment_dict):
                    logger.info("JSON 파싱 + 유효성 검사 성공.")
                    generated_comment = generated_comment_dict.get("content", "").strip()
                    return generated_comment
                else:
                    raise ValueError("생성된 JSON에 content가 없거나 비어 있음")

            except (IndexError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"댓글 생성 실패 (시도 {attempt}회): {e}")

                if attempt < MAX_RETRY:
                    continue
                else:
                    logger.warning("최대 재시도 도달 → fallback 사용.")
                    return json.loads(FALLBACK_COMMENT)


    

# 싱글턴 인스턴스 생성 (서버 시작 시 1회만 실행)
clovax_model_instance = ClovaxModel()
clovax_model_instance.load_clovax()

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
        team_tags=["AI", "Clovax", "GCP", "UI 친근함"],
    )
    

    start = time.time()
    logger.info("테스트 시작.")
    comment = clovax_model_instance.generate_comment(dummy_data)
    logger.info("생성된 댓글: %s", comment)
    logger.info("실행 시간: %.2f초", time.time() - start)