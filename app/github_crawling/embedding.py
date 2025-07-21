# app/github_crawling/embedding.py

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"
_model = None

def get_st_model():
    global _model
    if _model is None:
        print("💡 Caching sentence-transformers model")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(text: str):
    model = get_st_model()
    return model.encode(text)
