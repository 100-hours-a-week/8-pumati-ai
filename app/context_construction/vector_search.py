# app/context_construction/vector_search.py

from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Tuple

# Sentence Transformer 모델 로딩 (한 번만 로드)
model = SentenceTransformer("BAAI/bge-m3")

# Chroma DB 연결
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs_team")
collection = client.get_or_create_collection(name="summary_docs")

def search_similar_docs(
    question: str,
    team_id: str,
    top_k: int = 3
) -> Tuple[List[str], List[dict], List[float]]:
    """
    사용자 질문과 팀 ID를 기반으로 유사 문서를 검색
    Returns: (문서 리스트, 메타데이터 리스트, 거리 점수 리스트)
    """
    # 질문 임베딩
    embedding = model.encode([question], normalize_embeddings=True).tolist()

    # ChromaDB 검색
    results = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
        where={"repo": team_id}
    )
    print(f"[DEBUG] 전체 결과: {results}")


    return results["documents"][0], results["metadatas"][0], results["distances"][0]
