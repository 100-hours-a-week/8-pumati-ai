import json, re, logging
from summa.summarizer import summarize
from context_construction.prompts.comment_prompt import GemmaPrompt
from sentence_transformers import util
from model_inference.loaders.comment_loader import comment_creator
from fast_api.schemas.comment_schemas import CommentRequest
from transformers import TextStreamer
import torch

logger = logging.getLogger(__name__)

FALLBACK_COMMENT = "좋아요! 추천합니다! 🙌"

MAX_NEW_TOKENS = 100 #80
MAX_RETRY = 8

class GenerateComment:
    def __init__(self):
        self.pipe = comment_creator.pipe
        self.model = comment_creator.model
        self.tokenizer = comment_creator.tokenizer
        self.embed_model = comment_creator.embed_model

    def validate_generated_comment(self, generated_comment_dict: dict) -> bool:
        comment = generated_comment_dict.get("comment", "")
        if not isinstance(comment, str) or not comment.strip():
            return False
        if len(comment.split()) <= 2:
            return False
        for word in ['추가', '코딩', '코드', '맞춤', '카테그램', '카테브', '앱', '어플리케이션', '설치', '알림']:
            if word in comment:
                return False
        return True

    def is_semantically_relevant(self, comment: str, context: str, threshold: float = 0.60) -> bool:
        logger.info(f"6-5-7) 유사도 측정을 시작합니다. comment: '{comment}'")
        comment_emb = self.embed_model.encode(comment, convert_to_tensor=True, show_progress_bar=False)
        context_emb = self.embed_model.encode(context, convert_to_tensor=True, show_progress_bar=False)
        similarity = util.cos_sim(comment_emb, context_emb).item()
        logger.info(f"6-5-8) 의미 유사도: {similarity:.2f}, threshold: {threshold}")
        return similarity >= threshold
    
    # def detail_summary(self, detail_Description: str) -> str:
    #     detailed_length = len(detail_Description)
    #     if detailed_length < 180:
    #         ratio = 1

    #     elif detailed_length < 500:
    #         ratio = 0.7

    #     else:
    #         ratio = 0.6
        
    #     summary = summarize(detail_Description, ratio=ratio) or detail_Description
    #     summary = summarize(summary, ratio=ratio) or summary

    #     return summary

    def generate_comment(self, request_data: CommentRequest) -> str:
        logger.info(f"5-1) 프롬프트 생성을 위한 데이터 전처리를 진행합니다.")
        prompt_builder = GemmaPrompt(request_data)

        logger.info(f"6-1) 유사도기반 검열 로직을 위해 context를 생성합니다.")
        context_text = " ".join(["다음은 프로젝트의 전반적인 정보이다.",
            "서비스 이름은", prompt_builder.title,
            "이다. 프로젝트 슬로건은", prompt_builder.introduction,
            "이다.", prompt_builder.detailedDescription,
            "프로젝트의 정보에 알맞은 댓글을 생성해주세요."
        ])

        logger.info(f"6-2) 입력 문자의 길이가 긴 경우, 각 경우에 맞도록 요약합니다.")
        prompt_builder.detailedDescription = prompt_builder.detail_summary(prompt_builder.detailedDescription)
        logger.info(f"6-3) 주어진 정보를 바탕으로 프롬프트를 생성합니다.")
        gemma_prompt = prompt_builder.generate_prompt()

        # if len(prompt_builder.detailedDescription) < 180:
        #     pass

        # elif len(prompt_builder.detailedDescription) < 500:
        #     prompt_builder.detailedDescription = self.detail_summary(prompt_builder.detailedDescription, 0.7)
        # else:
        #     prompt_builder.detailedDescription = self.detail_summary(prompt_builder.detailedDescription, 0.6)
        #     #print(summary)

        logger.info(f"6-4) 프롬프트를 토큰ID로 변환합니다.")
        #inputs = self.tokenizer(gemma_prompt, return_tensors="pt").to(self.model.device)

        for attempt in range(1, MAX_RETRY + 1):
            logger.info(f"댓글 생성 시도 {attempt}회")
            logger.info(f"6-5-1) 댓글을 생성합니다.")
            # with torch.inference_mode():
            #     outputs = self.model.generate(
            #         **inputs,
            #         max_new_tokens=MAX_NEW_TOKENS,
            #         temperature= 0.6,#0.7,
            #         top_p=0.9,
            #         repetition_penalty=1.1,
            #         do_sample=True
            #     )

            outputs = comment_creator.pipe(
                gemma_prompt,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
                repetition_penalty=1.1
            )

            logger.info(f"6-5-2) 생성된 output에서 프롬프트 부분을 제거합니다.")
            # output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            # logger.info(f"6-5-3) 생성된 댓글에서 프롬프트 부분을 제거합니다.")
            # output_text = output_text[len(gemma_prompt):].strip()
            output_text = outputs[0]["generated_text"][len(gemma_prompt):].strip()

            try:
                logger.info(f"6-5-3) 생성된 댓글 검열을 시작합니다.")
                find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
                generated_comment_dict = json.loads(find_comment[0].strip())

                if self.validate_generated_comment(generated_comment_dict):
                    logger.info(f"6-5-4) JSON 형태로 출력 성공.")
                    comment = generated_comment_dict.get("comment", "").strip()

                    logger.info(f"6-5-5) JSON에서 '{comment}'를 출력하였습니다.")
                    if any(word in comment for word in ["디자인", "UI", "UX", "좋아요", "인터페이스"]): #prompt_builder.tags +
                        logger.info(f"6-5-6) tags 기반의 댓글생성에 성공하였습니다.")
                        #logger.info(f"댓글 생성 성공: {comment}")
                        return comment
                    if self.is_semantically_relevant(comment, context_text):
                        logger.info(f"6-5-9) 상세내용과 유사도 측정하여, 댓글생성에 성공하였습니다.")
                        logger.info(f"댓글 생성 성공: {comment}")
                        return comment
                    raise ValueError("의미 검열 불통과")
                raise ValueError("JSON 형태 아님.")
            except Exception as e:
                logger.warning(f"댓글 생성 실패 (시도 {attempt}회): {e}")

        logger.warning("최대 재시도 도달 → fallback 사용")
        return FALLBACK_COMMENT