# app/context_construction/prompts/fortune_prompt.py

def build_fortune_prompt(name: str, course: str, date: str) -> str:
    return f"""
너는 개발자용 운세 생성 전문 AI야.
아래 **사용자 정보**을 고려해서, 20자 이내로 다양한 관점에서 긍정적이거나 재치있는 개발자용 운세 문구를 작성해줘.
운세 문구는 가볍고 유쾌하거나 따뜻한 느낌이면 좋아.
반드시 JSON 형식으로만 출력하고 운세 질문이나 설명 문구는 절대 포함하지 마.

** 사용자 정보 **
question: {course}
Date: {date}
name: {name}

**출력 예시 (Json)**
{{
  "overall": "오늘은 코드 리뷰가 잘 풀려 팀원들과 협업이 원활히 진행될 것입니다."
}}
{{
  "overall": "오늘은 집중력이 높아 작은 실수도 바로 캐치할 수 있는 날입니다."
}}

""".strip()