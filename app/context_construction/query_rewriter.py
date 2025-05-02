# app/context_construction/query_rewriter.py

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
