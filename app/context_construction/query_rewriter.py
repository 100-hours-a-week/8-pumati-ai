# app/context_construction/query_rewriter.py

from app.fast_api.schemas.comment_schemas import CommentRequest
import json
import logging

logger = logging.getLogger(__name__)

# JSON 데이터 모델 정의
class GemmaPrompt:
    """
    프로젝트 정보를 기반으로 Gemma 프롬프트를 생성하는 클래스
    """
    def __init__(self, data: CommentRequest):

        self.comment_type = self._escape(data.comment_type)
        self.team_projectName = self._escape(data.team_projectName)
        self.team_shortIntro = self._escape(data.team_shortIntro)
        self.team_deployedUrl = self._escape(data.team_deployedUrl)
        self.team_githubUrl = self._escape(data.team_githubUrl)
        self.team_description = self._escape(data.team_description)
        self.team_tags = self._escape(data.team_tags)
    # JSON 파일 로드 함수

    def _escape(self, text: str) -> str:
        """
        문자열을 JSON 안전하게 escape 처리합니다.
        (따옴표를 포함한 특수 문자를 안전하게 변환합니다.)
        """
        return json.dumps(text, ensure_ascii=False)[1:-1]  # 양쪽 따옴표 제거
    
    def generate_prompt(self) -> str:
        """
        프로젝트 정보를 기반으로 LLM 프롬프트 문자열 생성
        """
        gemma_prompt = f"""
        너는 3년차 긍정적인 개발자야.
        아래 **프로젝트 정보**를 고려해서 '{self.comment_type}'유형의 댓글을 20자 이내의 다양한 관점에서 다양한 댓글을 작성해줘.
        반드시 JSON 형식으로만 출력하고 프로젝트 정보등 다른 문장은 쓰지 마.

        **프로젝트 정보**
        - projectName: {self.team_projectName}
        - shortIntro: {self.team_shortIntro}
        - deployedUrl: {self.team_deployedUrl}
        - githubUrl: {self.team_githubUrl}
        - description: {self.team_description}
        - tags: {self.team_tags} 

        **출력 예시 (Json)**
        {{ "content": "React로 직관적이어서 유지보수도 쉬울듯!🤗💕}} 
        {{ "content": FastAPI와 React 조합 덕분에 속도와 UI 모두 잡았네요. 😍" }}
        """

        return gemma_prompt.strip()

##fortune

def build_fortune_prompt(course: str, date: str) -> str:
    return f"""
You are an AI that only outputs a single JSON object—nothing else.
Do NOT output any prose, markdown, rename any keys, or repeated prompts.
Output exactly this JSON structure with values in Korean.
overall, devLuck each short one‐sentence.
overall에는 전반적인 하루 운세를 적고, devLuck에는 course별 개발자용 운세 적어줘.
Output exactly:
```json
{{
  "overall": "",
  "devLuck": ""
}}

Course: {course}  
Date: {date}  
""".strip()