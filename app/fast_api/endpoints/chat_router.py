# app/fast_api/endpoints/chat_router.py

from fastapi import APIRouter
from app.fast_api.schemas.chat_schemas import ChatRequest, ChatResponse
from app.model_inference.chat_response_generator import generate_team_response

router = APIRouter()

@router.post("/chat/projectId/{project_id}")
async def chat_team(project_id: int, request: ChatRequest):
    answer = generate_team_response(request.question, project_id)
    return {"answer": answer}
