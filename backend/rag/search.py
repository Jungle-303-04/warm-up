# 사용자 입력 -> 임베딩 생성 -> 유사도 비교 -> top k 반환

import json
import math
from pathlib import Path

from rag.embedding import embed_query

BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDED_GUIDES_PATH = BASE_DIR / "data" / "font_guides_embedded.json"

def load_embedded_guides() -> list[dict]:
    with open(EMBEDDED_GUIDES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def cosine_similarity(a: list[float], b: list[float])-> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)

def search_guides(query: str, top_k: int = 3)-> list[dict]:
    guides = load_embedded_guides()
    query_embedding = embed_query(query)

    scored_guides = []

    for guide in guides:
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