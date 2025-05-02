# app/model_inference/inference_runner.py

import json
import re
from context_construction.query_rewriter import build_fortune_prompt
from model_inference.loaders.HyperCLOVA_loader import generate_fortune_text

def run_fortune_model(course: str, date: str) -> dict:
    # 1) JSON 전용 프롬프트 생성
    prompt = build_fortune_prompt(course, date)

    # 2) 모델에 프롬프트만 전달
    raw = generate_fortune_text(prompt)

    # 3) { … } 블록 모두 찾고, 마지막 블록만 취함
    blocks = re.findall(r"\{[\s\S]*?\}", raw)
    if not blocks:
        raise RuntimeError(f"모델 출력에 JSON 블록이 없습니다:\n{raw}")
    last = blocks[-1]

    # 4) JSON 파싱
    try:
        return json.loads(last)
    except json.JSONDecodeError as e:
        # 디버그용 전체 raw 및 추출 블록 출력
        raise RuntimeError(
            f"JSON 파싱 실패: {e}\n"
            f"추출된 블록:\n{last}\n\n"
            f"원본 출력:\n{raw}"
        )
