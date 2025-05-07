# app/model_inference/inference_runner.py

import re
from app.context_construction.query_rewriter import build_fortune_prompt
from app.model_inference.loaders.HyperCLOVA_loader import generate_fortune_text
from langchain_core.output_parsers import JsonOutputParser

# 1. JSONOutputParser 초기화
parser = JsonOutputParser()

def run_fortune_model(name: str, course: str, date: str) -> dict:
    """
    name, course, date를 받아 개인화된 운세 JSON을 반환합니다.
    JSONOutputParser를 사용하여 파싱합니다.
    """
    # 1) 프롬프트 생성
    prompt = build_fortune_prompt(name, course, date)

    # 2) 모델 호출
    raw = generate_fortune_text(prompt)

    # 3) 이미 dict인 경우 그대로 반환
    if isinstance(raw, dict):
        return raw

    # 4) 파싱 시도
    try:
        result = parser.parse(str(raw))
    except Exception as e:
        print(f"[❗️ JSON 파싱 실패]: {e}")
        return {}

    return result