#내가 받아오는 API
from pydantic import BaseModel
from typing import List

class ProjectSummary(BaseModel):
    title: str
    introduction: str
    detailedDescription: str
    deploymentUrl: str
    githubUrl: str
    tags: List[str]
    teamId: int

class CommentRequest(BaseModel):
    commentType: str
    projectSummary: ProjectSummary


'''
**입력**
{
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
'''