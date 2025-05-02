import requests

url = "http://127.0.0.1:8000/api/generate-comment/ai-project-123"  # 여기에 서버 주소와 프로젝트 ID

data = {
    "comment_type": "칭찬",
    "team_projectName": "AI 이력서 생성기",
    "team_shortIntro": "LLM 기반 이력서 자동 생성",
    "team_deployedUrl": "https://resume.site",
    "team_githubUrl": "https://github.com/example",
    "team_description": "FastAPI + React 기반 프로젝트",
    "team_tags": ["AI", "LLM", "FastAPI"]
}

response = requests.post(url, json=data)

print("응답 상태 코드:", response.status_code)
print("응답 본문:", response.json())