# app/context_construction/query_rewriter.py

from app.fast_api.schemas.comment_schemas import CommentRequest

# JSON 데이터 모델 정의
class GemmaPrompt:
    def __init__(self, data: CommentRequest):

        self.comment_type = data.comment_type
        self.team_projectName = data.team_projectName
        self.team_shortIntro = data.team_shortIntro
        self.team_deployedUrl = data.team_deployedUrl
        self.team_githubUrl = data.team_githubUrl
        self.team_description = data.team_description
        self.team_tags = data.team_tags
    # JSON 파일 로드 함수
    
    def generate_prompt(self):
        Gemma_prompt = f"""
        너는 3년차 친근한 개발자야.
        아래 **프로젝트 정보**를 참고해서 '{self.comment_type}'유형의 댓글을 20자 이내로 조금은 개성있게 혹은 약간 유머있게 다양한 댓글을 작성해줘.
        반드시 JSON 형식으로만 출력하고 프로젝트 정보등 다른 문장은 쓰지 마.

        **프로젝트 정보**
        - projectName: {self.team_projectName}
        - shortIntro: {self.team_shortIntro}
        - deployedUrl: {self.team_deployedUrl}
        - githubUrl: {self.team_githubUrl}
        - description: {self.team_description}
        - tags: {self.team_tags}

        **출력 예시 (Json)**
        {{ "content": "React로 직관적이어서 유지보수도 쉬울듯!🤗💕 FastAPI와 React 조합 덕분에 속도와 UI 모두 잡았네요. 😍" }}
        """

        return Gemma_prompt

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