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
        "content" : "Fastapi로 빠르게 서빙한것이 인상 깊었습니다."

        """
        return Gemma_prompt

##fortune

def build_fortune_prompt(name: str, course: str, date: str) -> str:
    return f"""
You are an AI that only outputs a single JSON object—nothing else.
Personalize it for user: {name}.
Do NOT output any prose, markdown, rename any keys, or repeated prompts.
overall에는 전반적인 하루 운세를 적고, devLuck에는 course별 개발자용 운세 각각 짧은 한 문장씩 적어줘.
Output exactly this JSON structure with values in Korean.
## Examples
```json
{{
  "overall": "오늘은 코드 리뷰가 잘 풀려 팀원들과 협업이 원활히 진행될 것입니다.",
  "devLuck": "새로운 프레임워크를 시도해볼 기회가 찾아오니, 적극적으로 도전하세요."
}}
// 예시
{{
  "overall": "오늘은 집중력이 높아 작은 실수도 바로 캐치할 수 있는 날입니다.",
  "devLuck": "코드 리팩토링에 도전해보세요. 클린 코드 작성이 한층 수월해질 것입니다."
}}
// 예시
{{
  "overall": "오늘은 사람들과의 협업이 순조롭게 풀리는 날입니다.",
  "devLuck": "페어 프로그래밍을 시도해보세요. 동료와 아이디어를 교환하며 큰 성장을 경험할 수 있습니다."
}}
// 예시
{{
  "overall": "오늘은 작은 성과가 모여 큰 보람으로 돌아오는 날입니다.",
  "devLuck": "자동화 스크립트를 작성해보세요. 반복 업무를 줄여 더욱 중요한 일에 집중할 수 있습니다."
}}


Course: {course}  
Date: {date}  
""".strip()