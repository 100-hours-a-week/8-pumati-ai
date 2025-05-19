# app/model_inference/fortune_inference_runner.py

# -------------------
# 이 모듈은 운세 모델 실행 파이프라인을 담당합니다.
# 1. 입력값(name, course, date) 기반으로 프롬프트 생성
# 2. HyperCLOVA 모델 호출
# 3. 결과 JSON 파싱 및 정제
# 4. 실패 시 fallback 응답 반환
# -------------------

import re
import random
from time import sleep
from app.context_construction.prompts.fortune_prompt import build_fortune_prompt
from app.services.fortune_service import FortuneService
from langchain_core.output_parsers import JsonOutputParser

fortune_service = FortuneService()  # 운세 생성 서비스 인스턴스
parser = JsonOutputParser()         # JSON 파싱을 위한 LangChain 파서
MAX_RETRY = 3                        # 최대 재시도 횟수

# 추론 실패 시 기본으로 제공할 fallback 운세 메시지 목록
FALLBACKS = [
    {"overall": "오늘은 집중력과 몰입도가 높은 하루가 될 것입니다. 오래 미뤄둔 기술 문서를 읽어보세요. 의외의 인사이트를 얻을 수 있습니다."},
    {"overall": "복잡한 문제가 깔끔하게 풀릴 수 있는 날입니다. 작은 리팩토링이라도 시도해보세요. 코드 품질이 한층 올라갑니다."},
    {"overall": "배움과 성장이 조화를 이루는 날입니다. 기존 코드를 리뷰하며 개선 아이디어를 떠올려보세요. 더 나은 구조가 보일지도 몰라요."}
]

def run_fortune_model(name: str, course: str, date: str) -> dict:
    """
    사용자 입력(name, course, date)을 받아 운세 모델을 호출하고,
    결과를 JSON으로 파싱해 반환합니다. 실패 시 fallback 메시지를 사용합니다.
    """
    for attempt in range(1, MAX_RETRY + 1):
        # 프롬프트에 난수 기반 노이즈 추가 (모델 응답 다양성 확보)
        noise = f"<!-- retry_seed={random.randint(0,9999)} -->"
        prompt = build_fortune_prompt(name, course, date) + f"\n{noise}"

        raw = fortune_service.generate_fortune(prompt)

        try:
            # 모델 응답 파싱 시도
            result = parser.parse(str(raw))
            # 키를 소문자로 정규화
            normalized = {k.lower(): v for k, v in result.items()}
            if "overall" not in normalized:
                raise ValueError("Missing 'overall'")

            return {"overall": normalized["overall"]}

        except Exception as e:
            print(f"[{attempt}회차 ❗️ JSON 파싱 실패]: {e}")
            sleep(1)  # 1초 대기 후 재시도

    # 모든 시도 실패 시 fallback 반환
    print("⚠️ JSON 응답 실패로 fallback 운세 제공")
    return random.choice(FALLBACKS)
