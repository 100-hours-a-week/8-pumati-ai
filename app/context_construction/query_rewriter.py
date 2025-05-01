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
        너는 개발자 커뮤니티에서 활동하는 AI 커뮤니티 회원이야.
        아래 **프로젝트 정보:**를 바탕으로, '{self.comment_type}' 유형의 댓글을 작성해줘.

        **프로젝트 정보:**
        - projectName: {self.team_projectName}
        - shortIntro: {self.team_shortIntro}
        - deployedUrl: {self.team_deployedUrl} 
        - githubUrl: {self.team_githubUrl}
        - description: {self.team_description}
        - tags: {self.team_tags}

        개발자 커뮤니티에 어울리는 스타일의 말투로 기술적 특성이나 장점을 녹여내서 아래 Json형태로 한국어로 작성해줘. 댓글은 문자열 형태로, 최대 30자 이내로 한문장만 작성해줘. **프로젝트 정보**, **질문**처럼 댓글과 상관없는 문자는 모두 빼줘.

        **출력 JSON 형식 (예시):**
        "content" : "Fastapi로 빠르게 서빙한것이 인상깊었습니다."

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
{{
  "overall": "",
  "devLuck": ""
}}

Course: {course}  
Date: {date}  
""".strip()