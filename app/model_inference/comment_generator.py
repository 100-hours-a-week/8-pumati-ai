from sentence_transformers import util
from context_construction.query_rewriter import GemmaPrompt
from fast_api.schemas.comment_schemas import CommentRequest
from model_inference.loaders.comment_loader import comment_creator
from summa.summarizer import summarize
import logging
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FALLBACK_COMMENT = "개발자 입장에서 정말 필요한 서비스 같아요, 대단합니다! 🙌"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" #"intfloat/multilingual-e5-small"
MAX_NEW_TOKENS = 80
MAX_NEW_TOKENS_SUMMARY = 50
TEMPERATURE = 0.9
TOP_P = 0.9
REPETITION_PENALTY = 1.2
MAX_RETRY = 40

class GenerateComment:
    def __init__(self):

        self.pipe = comment_creator.pipe
        self.model = comment_creator.model
        self.embed_model = comment_creator.embed_model


    # 형태 기반 유효성 검사
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
        
        for word in ['추가', '코딩', '코드', '맞춤', '카테그램', '카테브', '앱', '어플리케이션', '설치', '알림']:
            if word in comment:
                return False
        
        if len(comment.split()) <= 2:
            return False

        return True

    # 의미 기반 유효성 검사
    def is_semantically_relevant(self, comments: str, context: str, threshold: float = 0.69) -> bool:
        """
        시멘틱 검사 검열함수 생성. 생성된 댓글이 프로젝트 정보와 의미적으로 관련 있는지 유사도로 판단
        """
        comment_emb = self.embed_model.encode(comments, convert_to_tensor=True, show_progress_bar=False)
        context_emb = self.embed_model.encode(context, convert_to_tensor=True, show_progress_bar=False)
        similarity = util.cos_sim(comment_emb, context_emb).item()

        logger.info(f"의미 유사도: {similarity:.4f}")
        return similarity >= threshold

    # 댓글 생성
    def generate_comment(self, request_data: CommentRequest) -> dict:
        prompt_builder = GemmaPrompt(request_data)
        prompt: str = prompt_builder.generate_prompt()


        # 시멘틱 검사를 위한 유사도 검색 text생성.
        context_text = " ".join(["서비스 이름은",
            prompt_builder.title, "이다. 프로젝트 슬로건은",
            prompt_builder.introduction, "이다.",
            prompt_builder.detailedDescription 
        ])

        # AI댓글 생성 할루시네이션 방지 목적. 1000자 이내로 받은 detailedDescription을 요약
        summary = summarize(prompt_builder.detailedDescription, ratio=0.7) or prompt_builder.detailedDescription
        summary = summarize(summary, ratio=0.7) or summary
        prompt_builder.detailedDescription = summary
        #request_data.projectSummary.detailedDescription = summary

        # 💡 검열 기준 텍스트 생성 (요약, 설명, 태그 등 조합)
        for attempt in range(1, MAX_RETRY + 1):
            logger.info(f"댓글 생성 시도 {attempt}회")

            #댓글 생성 모델 실행.
            outputs = self.pipe(prompt, max_new_tokens=MAX_NEW_TOKENS)[0]["generated_text"]
            output_text = outputs[len(prompt):].strip()

            try:
                # JSON형식 파싱 후 첫번째 JSON을 댓글로 지정
                find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
                generated_comment_str = find_comment[0].strip()
                generated_comment_dict = json.loads(generated_comment_str)

                # 형식 기반 유효성 검사 추가
                # JSON형식 내에 comment키가 있는지, 길이가 너무 짧지는 않은지 확인
                # 형식 기반, 단어 기반, 의미 기반 유효성 검사를 모두 통과하면 댓글 생성 완료.
                if self.validate_generated_comment(generated_comment_dict):
                    generated_comment = generated_comment_dict.get("comment", "").strip()

                    # 단어 기반 유효성 검사 추가: 아래 리스트의 단어가 들어 있는 댓글은 유효성 검사 통과.
                    # 목적: 의미 기반 유효성 검사 전, 관련 있는 댓글을 일차적으로 걸러내어, 불필요한 모델 사용 줄임.
                    positive_words = ["디자인", "UI", "UX", "좋아요", "인터페이스"] + prompt_builder.tags
                    for word in positive_words:
                        if word in generated_comment:
                            return generated_comment

                    # 의미 기반 유효성 검사 추가.
                    # 목적: 할루시네이션 방지 목적.
                    if self.is_semantically_relevant(generated_comment, context_text):
                        logger.info("JSON 파싱 + 의미 필터링 통과.")
                        return generated_comment

                    else:
                        raise ValueError("의미 검열에 의해 댓글 재 생성 필요.")
                else:
                    raise ValueError("생성된 JSON에 comment가 없거나 비어 있음. 형식에 벗어남.")

            except (IndexError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"댓글 생성 실패 (시도 {attempt}회): {e}")

                if attempt < MAX_RETRY:
                    continue
                else:
                    logger.warning("최대 재시도 도달 → fallback 사용.")
                    return FALLBACK_COMMENT
                
comment_generator_instance = GenerateComment()

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
            teamId= 4
        )
    )
    

    start = time.time()
    logger.info("테스트 시작.")
    correct = []
    for _ in range(4):
        comment = comment_generator_instance.generate_comment(dummy_data)
        correct.append(comment)
        logger.info("생성된 댓글: %s", comment)
        logger.info("실행 시간: %.2f초", time.time() - start)

    print(correct)