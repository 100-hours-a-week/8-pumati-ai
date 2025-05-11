from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 댓글 하나만 받을 모델
class CommentRequest(BaseModel):
    content: str
    authorName: str
    authorNickname: str

@app.post("/api/projects/{project_id}/comments/ai")
async def receive_comment(project_id: str, comment: CommentRequest):
    
    # 받은 댓글 출력
    print(f"- {comment.authorName} ({comment.authorNickname}) : {comment.content}")

    return {
        "status": "received",
        "project_id": project_id,
        "received_comment": comment.dict()  # 받은 댓글 그대로 돌려줌
    }
