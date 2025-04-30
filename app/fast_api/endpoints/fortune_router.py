# app/fast_api/endpoints/fortune_router.py

from fastapi import APIRouter, HTTPException
from fast_api.schemas.fortune_schema import FortuneRequest
from model_inference.inference_runner import run_fortune_model
import json
import re

router = APIRouter()

@router.post("/api/llm/fortune")
async def create_fortune(request: FortuneRequest):
    model_output = run_fortune_model(request.course, request.date)

    print("🔥 RAW MODEL OUTPUT BEGIN 🔥")
    print(model_output)
    print("🔥 RAW MODEL OUTPUT END 🔥")

    # JSON 블록 추출 & 파싱
    try:
        match = re.search(r"\{[\s\S]*?\}", model_output)
        if not match:
            raise HTTPException(status_code=500, detail="No JSON found in model output.")
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Model output is not a valid JSON.")


    return {"message": "generateFortuneSuccess", "data": parsed}
