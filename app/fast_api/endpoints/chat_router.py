# app/fast_api/endpoints/chat_router.py

# 표준 라이브러리
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Tuple, Callable, Awaitable

# FastAPI 관련
from fastapi import APIRouter, FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

# Pydantic
from pydantic import BaseModel

# 내부 모듈
from app.fast_api.schemas.chat_schemas import ChatRequest, ChatResponse
from app.model_inference.rag_chat_runner import run_rag, run_rag_streaming

router = APIRouter()
# 기존 post 방식
@router.post("/chat/projectId/{project_id}", response_model=ChatResponse)
async def chat_team(project_id: int, request: ChatRequest):
    answer = run_rag(request.question, project_id)
    return {"answer": answer}

########## SSE ##############

# --- 설정 --- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")
app = FastAPI()

# --- 모델 정의 --- #
class ChatMessage(BaseModel):
    content: str

# --- 세션 큐 매니저 --- #
event_queues: Dict[str, asyncio.Queue[Tuple[str, str]]] = defaultdict(asyncio.Queue)

def session_key(project_id: int, session_id: str) -> str:
    return f"{project_id}:{session_id}"

def get_queue_or_404(key: str):
    if key not in event_queues:
        raise HTTPException(status_code=404, detail="sessionNotFound")
    return event_queues[key]

# --- 공통 SSE 전송 핸들러 (AOP처럼 동작) --- #
async def sse_event_sender(queue: asyncio.Queue, handler: Callable[[], Awaitable[None]]):
    try:
        await queue.put(("typing", "true"))
        await handler()
        await queue.put(("done", "ok"))
    except Exception as e:
        logger.exception("SSE 핸들러 예외 발생")
        await queue.put(("error", "internalServerError"))
        await queue.put(("done", "ok"))

# --- 1. 질문 보내기 ---
class MessageRequest(BaseModel):
    content: str

@router.post("/projects/{projectId}/chatbot/sessions/{sessionId}/message")
async def send_message(projectId: int, sessionId: str, body: MessageRequest, background_tasks: BackgroundTasks):
    key = f"{projectId}:{sessionId}"
    queue = get_queue_or_404(key)

    async def handler():
        async for chunk in run_rag_streaming(body.content.strip(), projectId):
            await queue.put(("message", chunk))

    background_tasks.add_task(sse_event_sender, queue, handler)
    return {"message": "messageAccepted"}


# --- 2. SSE 연결 및 질문 대기 ---
@router.get("/projects/{projectId}/chatbot/sessions/{sessionId}/stream")
async def stream_chatbot(projectId: int, sessionId: str, request: Request):
    key = f"{projectId}:{sessionId}"

    if key in event_queues:
        logger.warning(f"중복 SSE 연결 시도: {key}")
        async def conflict():
            yield "event: error\ndata: sessionConflict\n\n"
            yield "event: done\ndata: ok\n\n"
        return StreamingResponse(conflict(), media_type="text/event-stream", status_code=409)

    queue = asyncio.Queue()
    event_queues[key] = queue

    async def event_generator():
        yield "event: connected\ndata: systemOpened\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE 연결 종료 감지 (클라이언트): {key}")
                    yield "event: stream-end\ndata: disconnected\n\n"
                    break

                try:
                    event_type, data = await asyncio.wait_for(queue.get(), timeout=5.0)
                    # logger.info(f"[SSE 송신] {event_type}: {data}")
                    yield f"event: {event_type}\ndata: {data}\n\n"

                    # stream-end 이벤트 수신 시 명시적으로 종료
                    if event_type == "stream-end":
                        logger.info(f"SSE stream-end 이벤트 감지: {key}")
                        break

                except asyncio.TimeoutError:
                    logger.warning(f"타임아웃: {key}")
                    yield "event: timeout\ndata: streamTimeout\n\n"
                    yield "event: stream-end\ndata: disconnected\n\n"
                    break

        except Exception as e:
            logger.exception("SSE 오류")
            yield "event: error\ndata: internalServerError\n\n"
            yield "event: done\ndata: ok\n\n"
        finally:
            # 세션 종료 시 큐 제거
            event_queues.pop(key, None)
            logger.info(f"SSE 세션 제거됨: {key}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- 3. 세션 종료 ---
@router.delete("/projects/{projectId}/sessions/{sessionId}/chatbot/stream")
async def close_stream(projectId: int, sessionId: str):
    key = f"{projectId}:{sessionId}"

    queue = event_queues.get(key)
    if queue:
        await queue.put(("stream-end", "disconnected"))
        del event_queues[key]
        logger.info(f"SSE 수동 종료 요청 처리됨: {key}")

    return {"message": "disconnected"}

# --- 예외 처리 --- 
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"message": "invalidRequest"})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"message": "internalServerError"})
