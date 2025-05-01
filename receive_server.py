from fastapi import FastAPI
from schemas import CommentResponse

app = FastAPI()

@app.post("/api/projects/{project_id}/ai-comments")
async def receive_comment(project_id: str, data: CommentResponse):
    print(f"✅ 댓글 수신 완료! project_id={project_id}")
    print(f"📦 총 수신 댓글 수: {data.count}")

    for comment in data.commentsData:
        print(f"- {comment.authorName} ({comment.authorNickname}) : {comment.content}")

    return {
        "status": "received",
        "project_id": project_id,
        "received_comments": data.count,
        "commentsData": [comment.dict() for comment in data.commentsData]  # 받은 댓글 그대로 응답으로 돌려줌 (옵션)
    }

