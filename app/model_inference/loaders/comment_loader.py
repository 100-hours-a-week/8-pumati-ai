import os
import re
import json
import logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer, util
import torch
from huggingface_hub import login
from app.context_construction.query_rewriter import ClovaxPrompt
from app.fast_api.schemas.comment_schemas import CommentRequest

# ----------------------------
# 로깅 설정
# ----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 상수 정의
# ----------------------------

MODEL_NAME = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B" #"google/gemma-3-1b-it"
FALLBACK_COMMENT = '{\n"comment": "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌" \n}'
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
CPU_DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 80
TEMPERATURE = 0.8
TOP_P = 0.8
REPETITION_PENALTY = 1.1
MAX_RETRY = 50


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
        logger.info(f"Device 설정: Device는 의도적으로 CPU로 고정됩니다.")
        self.embed_model = None
        
    
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
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
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
            self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device = self.device)
            logger.info("Clovax 모델 로드 완료.")
            logger.info("임베딩 기반 검열 모델 로드 완료.")


    # 댓글 생성
    def validate_generated_comment(self, generated_comment_dict: dict) -> bool:
        """
        생성된 댓글 JSON이 유효한지 검사.
        필수 필드(comment)가 없거나 값이 비어있으면 False
        """
        if "comment" not in generated_comment_dict:
            return False

        comment = generated_comment_dict["comment"]

        if not isinstance(comment, str) or not comment.strip():
            return False
        
        for word in ['추가', '혁신적', '코딩', '코드']:
            if word in comment:
                return False
        
        if len(comment.split()) <= 2:
            return False

        return True


    def generate_comment(self, request_data: CommentRequest) -> dict:
        prompt_builder = ClovaxPrompt(request_data)
        prompt: str = prompt_builder.generate_prompt()

        # 💡 검열 기준 텍스트 생성 (요약, 설명, 태그 등 조합)
        context_text = " ".join(["서비스 이름은",
            request_data.projectSummary.title, "이다.",
            request_data.projectSummary.introduction,
            request_data.projectSummary.detailedDescription, "이 프로젝트의 핵심적인 특징은",
            ",".join(request_data.projectSummary.tags), "이다"
        ])

        for attempt in range(1, MAX_RETRY + 1):
            logger.info(f"댓글 생성 시도 {attempt}회")
            outputs = self.pipe(prompt, max_new_tokens=MAX_NEW_TOKENS)[0]["generated_text"]
            output_text = outputs[len(prompt):].strip()

            try:
                find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
                generated_comment_str = find_comment[0].strip()
                generated_comment_dict = json.loads(generated_comment_str)
                print(generated_comment_dict)

                # 유효성 검사 추가
                if self.validate_generated_comment(generated_comment_dict):
                    #logger.info("JSON 파싱 + 유효성 검사 성공.")
                    generated_comment = generated_comment_dict.get("comment", "").strip()

                    if self.is_semantically_relevant(generated_comment, context_text):
                        logger.info("JSON 파싱 + 의미 필터링 통과.")
                        return generated_comment

                    else:
                        logger.info("의미 검열에 의해 댓글 재 생성 필요.")
                else:
                    raise ValueError("생성된 JSON에 comment가 없거나 비어 있음. 형식에 벗어남.")

            except (IndexError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"댓글 생성 실패 (시도 {attempt}회): {e}")

                if attempt < MAX_RETRY:
                    continue
                else:
                    logger.warning("최대 재시도 도달 → fallback 사용.")
                    return json.loads(FALLBACK_COMMENT)


    def is_semantically_relevant(self, comments: str, context: str, threshold: float = 0.85) -> bool:
        """
        검열함수 생성. 생성된 댓글이 프로젝트 정보와 의미적으로 관련 있는지 유사도로 판단
        """
        comment_emb = self.embed_model.encode("query: " + comments, convert_to_tensor=True, show_progress_bar=False)
        context_emb = self.embed_model.encode("passage: " + context, convert_to_tensor=True, show_progress_bar=False)
        similarity = util.cos_sim(comment_emb, context_emb).item()

        logger.info(f"의미 유사도: {similarity:.4f}")
        return similarity >= threshold


    
# 싱글턴 인스턴스 생성 (서버 시작 시 1회만 실행)
clovax_model_instance = ClovaxModel()
clovax_model_instance.load_clovax()

# ----------------------------
# 테스트 코드
# ---------------------------- 

if __name__ == "__main__":
    import time
    import sys
    import os
    from app.fast_api.schemas.comment_schemas import ProjectSummary
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))



    dummy_data = CommentRequest(
        commentType="칭찬",
        projectSummary=ProjectSummary(
            title="품앗이 서비스",
            introduction="서로의 프로젝트 웹페이지를 방문하여 트래픽을 늘려줌",
            detailedDescription="트래픽을 원하는 부트캠프 수강생을 위해 22개의 팀프로젝트를 한번에 모아, 서로의 서비스를 접근하기 편한 플랫폼을 구축함.",
            deploymentUrl="https://resume.site",
            githubUrl="https://github.com/example",
            tags=["React", "clovax", "FastAPI"],
            teamId=8
        )
    )
    

    start = time.time()
    logger.info("테스트 시작.")
    correct = []
    for _ in range(4):
        comment = clovax_model_instance.generate_comment(dummy_data)
        correct.append(comment)
        logger.info("생성된 댓글: %s", comment)
        logger.info("실행 시간: %.2f초", time.time() - start)

    print(correct)