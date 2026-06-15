import chromadb
import json
from rag.builder import build_embedding_text

client = chromadb.PersistentClient(path="./chroma_db")

# like table
collection = client.get_or_create_collection(
    name="font_guides"
)
# json 파일 읽어서 객체로 생성
with open("data/font_guides_embedded.json", encoding="utf-8") as f:
    guides = json.load(f)

# 없으면 추가 있으면 수정 .upsert
for i, guide in enumerate(guides):
    collection.upsert(
    ids=[guide["id"]],
    documents=[
        build_embedding_text(guide)
    ],
    embeddings=[guide["embedding"]],
    )
