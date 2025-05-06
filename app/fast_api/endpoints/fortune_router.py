# app/fast_api/endpoints/fortune_router.py

from fastapi import APIRouter, HTTPException
from app.fast_api.schemas.fortune_schema import FortuneRequest, FortuneResponse
from app.model_inference.inference_runner import run_fortune_model
import time

router = APIRouter()

@router.post(
    "/fortune",                                 
    response_model=FortuneResponse,             
    summary="Create Fortune",
    tags=["Fortune"],
)
async def create_fortune(request: FortuneRequest):
    # 1) 시작 시간 기록
    start = time.perf_counter()

    # 2) 모델 호출 (name 추가)
    result: dict = run_fortune_model(
        request.name,    # ← 새로 추가된 name
        request.course,
        request.date
    )

    # 3) 종료 시간 기록 & elapsed 출력
    elapsed = time.perf_counter() - start
    print(f"⏱️ Endpoint elapsed: {elapsed:.2f} sec")

    # (디버그) raw log
    print("🔥 RAW MODEL OUTPUT BEGIN 🔥")
    print(result)
    print("🔥 RAW MODEL OUTPUT END 🔥")

    # 4) 이미 dict 이므로 바로 반환
    return {
        "message": "generateFortuneSuccess",
        "data": result
    }
