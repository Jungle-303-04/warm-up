from dataclasses import dataclass
from typing import Any

from app.shared.collections import get_list_value


@dataclass(frozen=True)
class VectorResultRow:
    """Chroma가 별도 배열로 주는 검색 결과를 한 행 단위로 묶은 값 객체."""

    id: str
    document: str
    metadata: dict[str, Any]
    distance: float | None


def parse_vector_result(result: dict[str, Any]) -> list[VectorResultRow]:
    """ids, documents, metadata, distance 배열을 같은 index 기준의 row 목록으로 변환한다."""

    ids = get_first_result_list(result, "ids")
    documents = get_first_result_list(result, "documents")
    metadatas = get_first_result_list(result, "metadatas")
    distances = get_first_result_list(result, "distances")

    return [
        VectorResultRow(
            id=chunk_id,
            document=get_list_value(documents, index, ""),
            metadata=get_list_value(metadatas, index, {}) or {},
            distance=get_list_value(distances, index, None),
        )
        for index, chunk_id in enumerate(ids)
    ]


def get_first_result_list(result: dict[str, Any], key: str) -> list[Any]:
    """Chroma query 결과의 첫 번째 query batch만 안전하게 꺼낸다."""

    values = result.get(key) or [[]]
    return values[0] or []
