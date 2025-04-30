#HyperCLOVA_loader.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from huggingface_hub import login
from dotenv import load_dotenv
import re

# .env 로드
load_dotenv()

hf_token = os.getenv("HF_AUTH_TOKEN")
if hf_token:
    login(token=hf_token)
else:
    raise ValueError("HF_AUTH_TOKEN is not set in your .env file!")

model_id = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    use_fast=True,             # ⚠️ Fast tokenizer 강제 사용
    trust_remote_code=True,   # 커스텀 파이썬 코드는 없으므로 꺼둠
    use_auth_token=hf_token,   # HF 인증 토큰
)


# device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
device = torch.device("cpu")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    use_auth_token=hf_token,
    torch_dtype=torch.float32,
).to(device)
# print(f"🗄️ Model is on: {next(model.parameters()).device}")  # ← 여기 추가

def generate_fortune_text(prompt: str) -> str:
    # inputs = tokenizer(prompt, return_tensors="pt").to(device)
    # print(f"📥 Inputs are on: {inputs.input_ids.device}")
    # with torch.no_grad():
    #     outputs = model.generate(
    #         **inputs,
    #         max_new_tokens=300,
    #         do_sample=True,
    #         temperature=0.7,
    #         top_p=0.9
    #     )
    # return tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 1) 토큰화 & 디바이스 이동
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # 2) 생성
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )[0]
    # 3) 프롬프트 길이만큼 슬라이스해서 '생성된 부분만' 취한다
    gen_ids = output_ids[ inputs["input_ids"].shape[-1] : ]

    # 4) JSON block 추출 (기존 로직)
    raw = tokenizer.decode(gen_ids, skip_special_tokens=True)
    match = re.search(r"\{[\s\S]*?\}", raw)
    return match.group() if match else raw