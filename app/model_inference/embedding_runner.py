from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
from app.github_crawling.embedding import MODEL_NAME

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def get_qdrant_collection(collection_type: str) -> str:
    if collection_type == "team":
        return os.getenv("QDRANT_COLLECTION_TEAM", "github_docs_team")
    elif collection_type == "summary":
        return os.getenv("QDRANT_COLLECTION_SUMMARY", "summary_docs")
    else:
        raise ValueError(f"Unknown collection_type: {collection_type}")

def get_vectorstore(collection_type: str):
    embedding_model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        encode_kwargs={"normalize_embeddings": True}
    )

    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    collection_name = get_qdrant_collection(collection_type)

    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embedding_model,
        content_payload_key="document",
    )

embedding_model = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    encode_kwargs={"normalize_embeddings": True}
)

def get_embedding_model():
    return embedding_model