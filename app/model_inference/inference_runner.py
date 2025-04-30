#inference_runner.py

from context_construction.query_rewriter import build_fortune_prompt
from model_inference.loaders.HyperCLOVA_loader import generate_fortune_text

def run_fortune_model(course: str, date: str) -> str:
    prompt = build_fortune_prompt(course, date)
    return generate_fortune_text(prompt)
