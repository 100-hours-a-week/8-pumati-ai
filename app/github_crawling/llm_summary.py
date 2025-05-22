# app/github_crawling/llm_summary.py

import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv

load_dotenv()
MODEL_ID = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"

# 모델 로딩
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, trust_remote_code=True)
model.to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

def generate_summary(text: str) -> str:
    prompt = f"""
아래는 팀의 GitHub 활동 로그입니다. 이 활동들을 기반으로 아래 내용을 요약해 주세요:

1. 어떤 기능을 개발했는지
2. 어떤 이슈를 해결했는지
3. 핵심 작업 흐름을 정리할 것

길이는 너무 짧지 않아도 괜찮고, 챗봇에서 검색되기 위해 핵심 키워드가 포함되도록 작성해 주세요.

{text}
"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=False
        )

    result = tokenizer.decode(output[0], skip_special_tokens=True)
    # 필요 시 후처리
    return result.replace(prompt.strip(), "").strip()
