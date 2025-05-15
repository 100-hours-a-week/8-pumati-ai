#내가 받아오는 API
from pydantic import BaseModel
from typing import List

class CommentRequest(BaseModel):
    comment_type: str
    team_projectName: str
    team_shortIntro: str
    team_deployedUrl: str
    team_githubUrl: str
    team_description: str
    team_tags: List[str]