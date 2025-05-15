# app/model_inference/inference_runner.py

import re
from time import sleep
from app.context_construction.query_rewriter import build_fortune_prompt
from app.model_inference.loaders.HyperCLOVA_loader import generate_fortune_text
from langchain_core.output_parsers import JsonOutputParser

# 1. JSONOutputParser 초기화
parser = JsonOutputParser()

MAX_RETRY = 3
import random

FALLBACKS = [
    {
        "overall": "오늘은 집중력과 몰입도가 높은 하루가 될 것입니다. 오래 미뤄둔 기술 문서를 읽어보세요. 의외의 인사이트를 얻을 수 있습니다."
    },
    {
        "overall": "복잡한 문제가 깔끔하게 풀릴 수 있는 날입니다. 작은 리팩토링이라도 시도해보세요. 코드 품질이 한층 올라갑니다."
    },
    {
        "overall": "배움과 성장이 조화를 이루는 날입니다. 기존 코드를 리뷰하며 개선 아이디어를 떠올려보세요. 더 나은 구조가 보일지도 몰라요."
    }
]


def run_fortune_model(name: str, course: str, date: str) -> dict:
    for attempt in range(1, MAX_RETRY + 1):
        noise = f"<!-- retry_seed={random.randint(0,9999)} -->" # 노이즈 추가
        prompt = build_fortune_prompt(name, course, date) + f"\n{noise}"

        raw = generate_fortune_text(prompt)

        if isinstance(raw, dict):
            return raw

        try:
            result = parser.parse(str(raw))

            # 필드명 강제 정규화 (소문자화 후 키 재정의)
            normalized = {k.lower(): v for k, v in result.items()}
            if "overall" not in normalized:
                raise ValueError("Missing 'overall'")

            return {
                "overall": normalized["overall"]
            }

        except Exception as e:
            print(f"[{attempt}회차 ❗️ JSON 파싱 실패]: {e}")
            sleep(1)

    print("⚠️ JSON 응답 실패로 fallback 운세 제공")
    return random.choice(FALLBACKS)
