# app/model_inference/loaders/HyperCLOVA_loader.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, platform, os, re
from huggingface_hub import login
from dotenv import load_dotenv

# ─── 1. 환경 변수 & HuggingFace 인증 ───────────────────
load_dotenv()
hf_token = os.getenv("HF_AUTH_TOKEN")
if not hf_token:
    raise ValueError("HF_AUTH_TOKEN is not set in your .env file!")
login(token=hf_token)

model_id = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"

# ─── 2. 토크나이저 로드 (언제나 공용) ────────────────────
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    trust_remote_code=True,
    token=hf_token,
)

# ─── 3. 디바이스 감지 & Full-Precision 모델 로드 ───────────
device = (
    torch.device("cuda")
    if torch.cuda.is_available()
    # else torch.device("mps")
    # if torch.backends.mps.is_available()
    else torch.device("cpu")
)

# 디바이스 및 정밀도 분기
if torch.cuda.is_available():
    # CUDA GPU: FP16 + auto device map
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        token=hf_token,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    device = torch.device("cuda")

# elif torch.backends.mps.is_available():
#     # macOS MPS: FP32
#     model = AutoModelForCausalLM.from_pretrained(
#         model_id,
#         trust_remote_code=True,
#         use_auth_token=hf_token,
#         torch_dtype=torch.float32,
#     ).to("mps")
#     device = torch.device("mps")

else:
    # CPU: FP32
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        token=hf_token,
        torch_dtype=torch.float32,
    ).to("cpu")
    device = torch.device("cpu")

print(f"✅ Loaded full-precision model on {platform.system()} → {device}")

# ─── 4. 운세 생성 함수 ─────────────────────────────────
def generate_fortune_text(prompt: str) -> str:
    # 토큰화 → 바로 디바이스에 올리기
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # 생성
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
        )[0]

    # 프롬프트 길이 이후 토큰만 추출
    gen_ids = output_ids[ inputs["input_ids"].shape[-1] : ]
    raw = tokenizer.decode(gen_ids, skip_special_tokens=True)

    # JSON 블록만 찾아 반환
    match = re.search(r"\{[\s\S]*?\}", raw)
    return match.group() if match else raw
