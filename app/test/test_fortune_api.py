# app/test/test_fortune_api.py

from chromadb import PersistentClient

client = PersistentClient(path="./chroma_db")
collection = client.get_collection(name="github_docs")

result = collection.get(include=["metadatas"], limit=50)

for m in result["metadatas"]:
    print(m.get("team_id"))
