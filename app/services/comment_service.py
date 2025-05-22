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
MAX_NEW_TOKENS = 80
MAX_RETRY = 10

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

    def is_semantically_relevant(self, comment: str, context: str, threshold: float = 0.69) -> bool:
        comment_emb = self.embed_model.encode(comment, convert_to_tensor=True, show_progress_bar=False)
        context_emb = self.embed_model.encode(context, convert_to_tensor=True, show_progress_bar=False)
        similarity = util.cos_sim(comment_emb, context_emb).item()
        logger.info(f"의미 유사도: {similarity:.4f}")
        return similarity >= threshold
    
    def detail_summary(detail_Description: str, ratio_summ: float = 0.6) -> str:
        summary = summarize(detail_Description, ratio=ratio_summ) or detail_Description
        summary = summarize(summary, ratio=ratio_summ) or summary
        return summary

    def generate_comment(self, request_data: CommentRequest) -> str:
        prompt_builder = GemmaPrompt(request_data)
        prompt = prompt_builder.generate_prompt()

        context_text = " ".join([
            "서비스 이름은", prompt_builder.title,
            "이다. 프로젝트 슬로건은", prompt_builder.introduction,
            "이다.", prompt_builder.detailedDescription
        ])

        if len(prompt_builder.detailedDescription) < 180:
            pass

        elif len(prompt_builder.detailedDescription) < 500:
            prompt_builder.detailedDescription = self.detail_summary(prompt_builder.detailedDescription, 0.7)
        else:
            prompt_builder.detailedDescription = self.detail_summary(prompt_builder.detailedDescription, 0.6)
            #print(summary)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        for attempt in range(1, MAX_RETRY + 1):
            logger.info(f"댓글 생성 시도 {attempt}회")
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    do_sample=True
                )
            output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            output_text = output_text[len(prompt):].strip()

            try:
                find_comment = re.findall(r'{.*?}', output_text, re.DOTALL)
                generated_comment_dict = json.loads(find_comment[0].strip())

                if self.validate_generated_comment(generated_comment_dict):
                    comment = generated_comment_dict.get("comment", "").strip()
                    if any(word in comment for word in (prompt_builder.tags +["디자인", "UI", "UX", "좋아요", "인터페이스"])):
                        logger.info(f"댓글 생성 성공: {comment}")
                        return comment
                    if self.is_semantically_relevant(comment, context_text):
                        logger.info(f"댓글 생성 성공: {comment}")
                        return comment
                    raise ValueError("의미 검열 불통과")
                raise ValueError("형식 검열 실패")
            except Exception as e:
                logger.warning(f"댓글 생성 실패 (시도 {attempt}회): {e}")

        logger.warning("최대 재시도 도달 → fallback 사용")
        return FALLBACK_COMMENT