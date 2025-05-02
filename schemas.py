from pydantic import BaseModel
from typing import List

class CommentItem(BaseModel):
    content: str
    authorName: str
    authorNickname: str

class CommentResponse(BaseModel):
    count: int
    commentsData: List[CommentItem]