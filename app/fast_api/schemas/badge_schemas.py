from pydantic import BaseModel
from typing import List

class BadgeRequest(BaseModel):
    title: str
    introduction: str
    detailedDescription: str
    deploymentUrl: str
    githubUrl: str
    tags: List[str]
    teamId: int
    term: int
    teamNumber: int