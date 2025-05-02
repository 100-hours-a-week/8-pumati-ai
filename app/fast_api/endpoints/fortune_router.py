# app/fast_api/endpoints/fortune_router.py

from fastapi import APIRouter, HTTPException
from fast_api.schemas.fortune_schema import FortuneRequest, FortuneResponse
from model_inference.inference_runner import run_fortune_model
import json, re
import time

router = APIRouter()

@router.post(
    "/fortune",                                 # ← prefix는 main.py 에서 한 번만 붙여주므로 여기서는 /fortune
    response_model=FortuneResponse,             # ← response_model 지정
    summary="Create Fortune",
    tags=["Fortune"],
)
async def create_fortune(request: FortuneRequest):
    # 1) 시작 시간 기록
    start = time.perf_counter()

    # 2) 모델 호출
    model_output = run_fortune_model(request.course, request.date)

    # 3) 종료 시간 기록 & elapsed 계산
    elapsed = time.perf_counter() - start
    print(f"⏱️ Endpoint elapsed: {elapsed:.2f} sec")


    # (디버그) raw log
    print("🔥 RAW MODEL OUTPUT BEGIN 🔥")
    print(model_output)
    print("🔥 RAW MODEL OUTPUT END 🔥")

    # 2) JSON 블록 추출 & 파싱
    # 이미 dict 로 파싱되어 있으면 그대로, 아니면 문자열에서 JSON 블록 추출
    if isinstance(model_output, dict):
        parsed = model_output
    else:
        try:
            match = re.search(r"\{[\s\S]*?\}", model_output)
            if not match:
                raise HTTPException(status_code=500, detail="No JSON found in model output.")
            parsed = json.loads(match.group())
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Model output is not a valid JSON.")
 

    # 3) FastAPI 가 응답 스키마 검증까지 알아서 해 줌
    return {
        "message": "generateFortuneSuccess",
        "data": parsed
    }
