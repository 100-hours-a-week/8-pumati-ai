import requests

url = "http://127.0.0.1:8000/api/generate-comment/ai-project-123"  # 여기에 서버 주소와 프로젝트 ID

data = {
  "commentType": "compliment",
  "projectSummary": {
    "title": "프로젝트 제목",
    "introduction": "한 줄 소개",
    "detailedDescription": "프로젝트 상세 설명",
    "projectImageUrl": "{projectImageUrl}",
    "deploymentUrl": "{deploymentUrl}",
    "githubUrl": "{githubUrl}",
    "tags": ["tag1", "tag2", "tag3"],
    "teamId": 8
  }
}

response = requests.post(url, json=data)

print("응답 상태 코드:", response.status_code)
print("응답 본문:", response.json())