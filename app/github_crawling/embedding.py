# app/github_crawling/embedding.py

# sentence_transformers는 transformers 버전 충돌이 나서 제외
# transformers 기반 embedding 함수 예시 (intfloat/multilingual-e5-small)
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
# from sentence_transformers import SentenceTransformer

# 사용할 임베딩 모델 지정
# MODEL_NAME = "intfloat/multilingual-e5-small"
# MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_NAME = "intfloat/multilingual-e5-large"

# 토크나이저와 모델 로딩
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

device = torch.device("cpu")
model.to(device)
model.eval()

def get_embedding(text: str) -> list:
    """
    하나의 문장을 임베딩하여 Python list 반환 (ChromaDB에 저장 가능)
    """
    instruction = "passage: " + text.strip()
    inputs = tokenizer(instruction, return_tensors="pt", truncation=True, padding=True).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :]  # CLS 토큰 기준

    vec = embeddings.squeeze().cpu().numpy()

    # norm이 0이 아닌 경우에만 normalize
    norm = np.linalg.norm(vec)
    if norm == 0:
        raise ValueError("Embedding vector has zero norm!")
    vec = vec / norm

    return vec.tolist()
