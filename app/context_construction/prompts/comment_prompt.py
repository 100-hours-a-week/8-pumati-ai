from fast_api.schemas.comment_schemas import CommentRequest
import json
import logging
import re

logger = logging.getLogger(__name__)

# JSON 데이터 모델 정의
class GemmaPrompt:
    """
    프로젝트 정보를 기반으로 Gemma 프롬프트를 생성하는 클래스
    """
    def __init__(self, data: CommentRequest):
        self.comment_type = self._escape(data.commentType)
        self.title = self._escape(data.projectSummary.title)
        self.introduction = self._escape(data.projectSummary.introduction)
        self.detailedDescription = self._escape(self._clean(data.projectSummary.detailedDescription))
        self.deploymentUrl = self._escape(data.projectSummary.deploymentUrl)
        self.githubUrl = self._escape(data.projectSummary.githubUrl)
        self.tags = data.projectSummary.tags
        #self.teamId = self._escape(data.projectSummary.teamId)
    # JSON 파일 로드 함수

    def _escape(self, text: str) -> str:
        """
        문자열을 JSON 안전하게 escape 처리합니다.
        (따옴표를 포함한 특수 문자를 안전하게 변환합니다.)
        """
        return json.dumps(text, ensure_ascii=False)[1:-1]  # 양쪽 따옴표 제거
    
    def _clean(self, text: str) -> str:
        try:
            logger.info(f"5-2) detailed Description의 문자열을 최소화 하기 위해 cleaning작업을 진행합니다.")
            logger.info(f"5-2-1) 특수문자 제거 완료.")
            text = re.sub(r"[#\-]", " ", text)       # 특수문자 제거
            logger.info(f"5-2-2) 개행 문자를 마침표와 공백으로 변환 완료.")
            text = re.sub(r"\n+", "\n ", text)        # 줄바꿈을 마침표+공백으로
            logger.info(f"5-2-3) 연속된 공백은 하나의 공백으로 변환 완료.")
            text = re.sub(r"\s+", " ", text)         # 연속된 공백을 하나로
            return text.strip() # 앞뒤 공백 제거
        
        except:
            return text                      
    
    def generate_prompt(self) -> str:
        """
        프로젝트 정보를 기반으로 LLM 프롬프트 문자열 생성
        """
        gemma_prompt = f"""
        너는 한국인 웹 서비스 사용 후기 작성자야.
        아래 **프로젝트 정보**를 보고'{self.comment_type}'유형의 의견을 다양하게 작성해줘. 
        comment키를 가진 JSON 형식으로만 댓글을 출력해줘.
        반드시 **프로젝트 정보에 명확히 나온 사실**에 대한 의견을 작성해줘.
        참고로 카테부는 카카오 테크 부트캠프의 줄임말이야.
        
        **프로젝트 정보**
        - projectName: {self.title}
        - shortIntro: {self.introduction}
        - detailedInfo: {self.detailedDescription}

        **출력 예시 (Json)**
        {{ "comment": "React로 직관적이어서 유지보수도 쉬울듯!🤗💕}} 
        {{ "comment": FastAPI와 React 조합 덕분에 속도와 UI 모두 잡았네요. 😍" }}
        """.strip()
        logger.info(f"prompt: {gemma_prompt}")
        return gemma_prompt
    