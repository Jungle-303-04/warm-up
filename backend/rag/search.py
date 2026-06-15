# 사용자 입력 -> 임베딩 생성 -> 유사도 비교 -> top k 반환
import chromadb

from rag.embedding import embed_query

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "font_guides"

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

# chunk 읽기
def search_guides(query: str, top_k: int = 3)-> list[dict]:
    # 사용자 입력 벡터 생성 (1536차원)
    query_embedding = embed_query(query)

    # db에서 해당 백터와 가까운 문서 top3 만큼 찾기 요청
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances"]
    )

    # 결과를 dict 구조로 변경
    searched_guides = []

    for i in range(len(results["ids"][0])):
        searched_guides.append(
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    
    return searched_guides