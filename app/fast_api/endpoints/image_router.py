from fastapi import APIRouter
from pydantic import BaseModel
from services.badge_service import BadgeService

router = APIRouter()
badge_service = BadgeService()

class BadgeRequest(BaseModel):
    number: int
    filename: str = "badge.png"

@router.post("/generate-badge")
def generate_badge(request: BadgeRequest):
    path = badge_service.generate_and_save_badge(request.number, request.filename)
    return {"status": "success", "file_path": path}