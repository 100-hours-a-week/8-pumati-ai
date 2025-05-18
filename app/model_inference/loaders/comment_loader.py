import os
import re
import json
import logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer, util
import torch
from huggingface_hub import login
from context_construction.query_rewriter import ClovaxPrompt
from fast_api.schemas.comment_schemas import CommentRequest
from summa.summarizer import summarize

# ----------------------------
# 로깅 설정
# ----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 상수 정의
# ----------------------------

#gemma로 모델 변경
MODEL_NAME = "google/gemma-3-1b-it"#""naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B" #"google/gemma-3-1b-it" 
FALLBACK_COMMENT = '{\n"comment": "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌" \n}'
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"#"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CPU_DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 80
MAX_NEW_TOKENS_SUMMARY = 50
TEMPERATURE = 0.85
TOP_P = 0.8
REPETITION_PENALTY = 1.2
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
        
        for word in ['추가', '혁신적', '코딩', '코드', '맞춤']:
            if word in comment:
                return False
        
        if len(comment.split()) <= 2:
            return False

        return True


    def generate_comment(self, request_data: CommentRequest) -> dict:
        prompt_builder = ClovaxPrompt(request_data)
        prompt: str = prompt_builder.generate_prompt()


        summary = summarize(prompt_builder.detailedDescription, ratio=0.7)
        summary = summarize(summary, ratio=0.7)
        request_data.projectSummary.detailedDescription = summary
        print(summary)

        # 💡 검열 기준 텍스트 생성 (요약, 설명, 태그 등 조합)
        context_text = " ".join(["서비스 이름은",
            prompt_builder.title, "이다. 프로젝트 슬로건은",
            prompt_builder.introduction, "이다.",
            prompt_builder.detailedDescription #, "이 프로젝트의 핵심적인 특징은"
            #",".join(ClovaxPrompt.projectSummary.tags), "이다"
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


    def is_semantically_relevant(self, comments: str, context: str, threshold: float = 0.86) -> bool:
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
    from fast_api.schemas.comment_schemas import ProjectSummary

    dummy_data = CommentRequest(
        commentType="칭찬",
        projectSummary=ProjectSummary(
            title= "모아",
            introduction= "JUST SWIPE! 카테부 사람들과 익명으로 재밌고 빠르게 소통해요",
            detailedDescription= "### 모아(Moa) - 모두의 아젠다\n\n- 스와이프로 투표, AI가 지켜주는 투표 공간\n- 누구나 쉽게 만들고 투표하는, AI 로 더 쾌적한 투표 공간\n\n### 서비스 소개\n\n“에어컨을 켜자!”부터\n\n“이번 주 야근 하시는 분?”까지\n\n모아는 일상 속 모든 선택을 간편한 스와이프 한번으로 모아주는 투표 플랫폼입니다.\n\n- 스와이프로 빠른 투표 참여\n- AI 가 비속어, 스팸 자동 검열\n- 그룹 단위 투표 생성과 참여\n- 결과는 그룹별, 참여, 생성별로 한눈에\n\n복잡한 UI, 거친 표현, 공개된 게시판은 이제 그만,\n\n모아에서는 모든 투표가 부드럽고 안전하게 흐릅니다.\n\n---\n\n### 모아는 이런 분께!\n\n- 모임이나 동아리에서 빠르게 의견을 모을 때\n- 커뮤니티에서 건강한 의견 수렴 문화를 만들고 싶을 때\n- 팀 프로젝트 중 합리적 의사 결정을 내리고 싶을 때\n\n모든 아젠다를 위한,\n\n모두의 선택을 위한 공간, 모아",
            deploymentUrl= "https://moagenda.com/",
            githubUrl= "https://github.com/100-hours-a-week/4-bull4zo-wiki/wiki",
            tags= ["카테부","투표","스와이프","소통","커뮤니티"],
            teamId= 6
        )
    )
    

    start = time.time()
    logger.info("테스트 시작.")
    # clovax_model_instance.summary_detailed(dummy_data)
    correct = []
    for _ in range(4):
        comment = clovax_model_instance.generate_comment(dummy_data)
        correct.append(comment)
        logger.info("생성된 댓글: %s", comment)
        logger.info("실행 시간: %.2f초", time.time() - start)

    print(correct)