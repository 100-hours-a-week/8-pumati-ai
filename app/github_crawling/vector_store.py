import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs")

def store_document(text: str, metadata: dict, embedding: list):
    collection.add(
        documents=[text], # 실제 요약 텍스트
        metadatas=[metadata], # 커밋/PR/README의 출처 정보
        embeddings=[embedding], # 임베딩 벡터 (list of float)
        ids=[f"{metadata['repo']}_{metadata['date']}"] # 고유 ID (예: 8-pumati-ai_2025-05-01T08:34)
    )

def show_vector_summary():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="github_docs")
    
    print("📦 총 벡터 수:", collection.count())
    
    docs = collection.peek(3)
    print("🔍 일부 문서 미리보기:")
    for doc in docs:
        print("-", doc[:120], "...")