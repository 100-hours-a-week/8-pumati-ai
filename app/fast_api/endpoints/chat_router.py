# app/fast_api/endpoints/chat_router.py

from fastapi import APIRouter
from app.fast_api.schemas.chat_schemas import ChatRequest, ChatResponse
from app.model_inference.rag_chat_runner import run_rag
from app.model_inference.rag_chat_runner import run_rag_streaming

router = APIRouter()
# 기존 post 방식
@router.post("/chat/projectId/{project_id}", response_model=ChatResponse)
async def chat_team(project_id: int, request: ChatRequest):
    answer = run_rag(request.question, project_id)
    return {"answer": answer}

########## SSE ##############
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import asyncio

# 세션별 질문 저장소
session_questions = {}

# --- 1. 질문 보내기 ---
class MessageRequest(BaseModel):
    content: str

@router.post("/projects/{projectId}/chatbot/sessions/{sessionId}/message")
async def send_message(projectId: int, sessionId: str, body: MessageRequest):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail={"message": "invalidRequest"})

    session_questions[sessionId] = content
    print(f"[질문 등록] session={sessionId}, question={content}")
    return {"message": "messageAccepted"}


# --- 2. SSE 연결 및 질문 대기 ---
@router.get("/projects/{projectId}/chatbot/sessions/{sessionId}/stream")
async def stream_chatbot(projectId: int, sessionId: str, request: Request):
    async def event_stream():
        yield "event: connect\ndata: 연결되었습니다.\n\n"

        # 최대 30초 동안 질문 도착 기다림
        for _ in range(60):  # 0.5초 x 60 = 30초
            if sessionId in session_questions:
                question = session_questions[sessionId]
                break
            await asyncio.sleep(0.5)
        else:
            yield "event: timeout\ndata: 질문이 도착하지 않았습니다.\n\n"
            return

        try:
            async for chunk in run_rag_streaming(question, projectId):
                yield f"event: message\ndata: {chunk}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

        yield "event: end\ndata: FINISHED\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Transfer-Encoding": "chunked"}
    )


# --- 3. 세션 종료 ---
@router.delete("/projects/{projectId}/sessions/{sessionId}/chatbot/stream")
async def close_stream(projectId: int, sessionId: str):
    session_questions.pop(sessionId, None)
    print(f"[세션 종료] session={sessionId}")
    return {"message": "unsubscribeSuccess"}
