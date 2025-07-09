# app/services/team_chat_service.py

import torch
import requests
import warnings
import re
import os

MODEL_NAME = "sunnyanna/hyperclovax-sft-1.5b-v4"
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/completions")

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.pytorch_utils")

class VLLMClient:
    def __init__(self, api_url):
        self.api_url = api_url

    def generate(self, prompt, **kwargs):
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "do_sample": True,
            "temperature": 0.1,
            "top_p": 0.2,
            "max_tokens": 230,
            **kwargs
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "").strip()
        except Exception as e:
            print(f"[ERROR] vLLM API 호출 실패: {e}")
            return "⚠️ 챗봇 서버 쉬는중!"

class TeamChatService:
    def __init__(self):
        self.vllm_client = VLLMClient(VLLM_API_URL)

    def generate_answer(self, prompt: str) -> str:
        print("[DEBUG] generate_answer 진입")
        print("[DEBUG] 프롬프트:", prompt)

        raw_output = self.vllm_client.generate(prompt)
        print("🧾 My model full response (for debug):", repr(raw_output.replace('\n', '\\n')))

        match = re.search(r"[가-힣][^a-zA-Z0-9]{0,10}", raw_output)
        if match:
            cleaned = raw_output[match.start():]
        else:
            cleaned = raw_output
        return cleaned
