# 사용자 입력 -> 임베딩 생성 -> 유사도 비교 -> top k 반환

import json
import math
from pathlib import Path

from rag.embedding import embed_query

BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDED_GUIDES_PATH = BASE_DIR / "data" / "font_guides_embedded.json"

# 파이썬 객체로 읽기
def load_embedded_guides() -> list[dict]:
    with open(EMBEDDED_GUIDES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# 사용자, chunk 벡터 입력받기 (비슷한 방향인지 확인)
def cosine_similarity(a: list[float], b: list[float])-> float:
    # 내적 계산
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    # 벡터 길의이 영향을 제거하기 위해
    # 내적 값을 각 벡터의 크기(norm)로 나누어서 (정규화)
    # 방향 유사도를 계산
    return dot / (norm_a * norm_b)

# chunk 읽기
def search_guides(query: str, top_k: int = 3)-> list[dict]:
    # 임베딩 한 원문 load
    guides = load_embedded_guides()
    # 사용자 입력 벡터 생성 (1536차원)
    query_embedding = embed_query(query)
    scored_guides = []

    # 모든 chunk 순회
    for guide in guides:
        # 입력값과 chunk의 유사도 계산 후 점수 반환
        # 결과는 -1 ~ 1 사이의 score로 반환
        score = cosine_similarity(query_embedding, guide["embedding"])

        scored_guides.append({
            "score": score,
            "id": guide["id"],
            "title": guide["title"],
            "content": guide["content"],
            "topic": guide.get("topic"),
            "tags": guide.get("tags", []),
            "recommended_categories": guide.get("recommended_categories", []),
            "tone": guide.get("tone", [])
        })

    # 높은 유사도 순서로 정렬
    scored_guides.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_guides[:top_k]