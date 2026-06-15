import logging

from openai import OpenAI, OpenAIError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.page import Page
from app.models.page_embedding import PageEmbedding

SIMILARITY_DISTANCE_THRESHOLD = 0.45  # cosine_distance, 낮을수록 관련이 있다
MAX_CONTEXT_CHUNKS = 8  # 관련 있는 건 가져오되, 최대 8개까지만 사용


RAG_INSTRUCTIONS = """
너는 TeamLog의 회의록/회고록 기반 RAG 답변 도우미다.

반드시 아래 규칙을 지켜라.

1. 제공된 [참고 기록]만 근거로 답변한다.
2. 참고 기록에 없는 내용은 추측하지 않는다.
3. 사용자가 "왜"를 물으면 참고 기록에 적힌 이유만 사용한다.
4. 기록이 여러 날짜에 걸쳐 있으면 날짜순으로 정리한다.
5. 이전 결정과 이후 변경사항을 구분한다.
6. 서로 다른 결정이 충돌하면 더 최신 날짜의 결정을 현재 기준 결론으로 판단한다.
7. 답변 마지막에는 가능한 경우 "현재 기준 결론"을 적는다.
8. 참고 기록에서 답을 찾을 수 없으면 "저장된 기록에서 찾을 수 없습니다."라고 답한다.
9. 답변은 한국어로 작성한다.
"""

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def block_to_text(block) -> str:
    """
    page_blocks 한 개를 RAG용 텍스트 한 줄로 바꾼다.
    """

    block_type = block.type.value if hasattr(block.type, "value") else str(block.type)
    content = (block.content or "").strip()

    if not content:
        return ""

    if block_type == "HEADING":
        return f"## {content}"

    if block_type == "BULLET":
        return f"- {content}"

    if block_type == "CHECKLIST":
        checked = getattr(block, "checked", False)
        status = "완료" if checked else "미완료"
        return f"- [{status}] {content}"

    if block_type == "CODE":
        return f"```code\n{content}\n```"

    return content


def build_page_header(page: Page) -> str:
    """
    chunk마다 앞에 붙일 메타 정보.
    이 chunk가 어떤 회의/회고에서 나온 내용인지 알려준다.
    """

    page_type = page.type.value if hasattr(page.type, "value") else str(page.type)

    return (
        f"제목: {page.title}\n"
        f"날짜: {page.date}\n"
        f"종류: {page_type}\n"
        f"참여자: {', '.join(page.participants)}\n\n"
    )


def build_page_chunks(page: Page, max_chars: int = 1200) -> list[str]:
    """
    Page 하나를 RAG 검색용 chunk 여러 개로 나눈다.

    기준:
    1. 제목/날짜/참여자 header를 모든 chunk에 붙인다.
    2. page_blocks를 order_index 순서대로 합친다.
    3. max_chars를 넘으면 새 chunk로 나눈다.
    """

    header = build_page_header(page)
    chunk_prefix = header + "내용:\n"

    chunks: list[str] = []
    current_chunk = chunk_prefix

    sorted_blocks = sorted(page.blocks, key=lambda block: block.order_index)

    for block in sorted_blocks:
        block_text = block_to_text(block)

        if not block_text:
            continue

        piece = block_text + "\n\n"

        if (
            len(current_chunk) + len(piece) > max_chars
            and current_chunk != chunk_prefix
        ):
            chunks.append(current_chunk.strip())
            current_chunk = chunk_prefix + piece
        else:
            current_chunk += piece

    if current_chunk.strip() != chunk_prefix.strip():
        chunks.append(current_chunk.strip())

    return chunks


def get_embedding(text: str) -> list[float]:
    text = text.strip()

    if not text:
        raise ValueError("embedding할 텍스트가 비어 있습니다.")

    try:
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
    except OpenAIError:
        logger.exception("Failed to create page embedding.")
        raise

    return response.data[0].embedding


def delete_page_embeddings(db: Session, page_id: int) -> None:
    db.execute(delete(PageEmbedding).where(PageEmbedding.page_id == page_id))


def refresh_page_embeddings(db: Session, page_id: int) -> int:
    """
    특정 page의 RAG 검색 데이터를 새로 만든다.

    흐름:
    1. Page + blocks 조회
    2. Page를 chunk로 나눔
    3. 각 chunk를 embedding으로 변환
    4. 기존 embedding 삭제
    5. 새 embedding 저장

    return:
    생성된 chunk 개수
    """

    page = db.execute(
        select(Page)
        .options(
            selectinload(Page.blocks),
        )
        .where(Page.id == page_id)
    ).scalar_one_or_none()

    if page is None:
        return 0

    chunks = build_page_chunks(page)

    if not chunks:
        delete_page_embeddings(db, page_id)
        return 0

    new_embedding_rows: list[PageEmbedding] = []

    for chunk_index, chunk_text in enumerate(chunks):
        embedding = get_embedding(chunk_text)

        new_embedding_rows.append(
            PageEmbedding(
                page_id=page.id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                embedding=embedding,
            )
        )

    delete_page_embeddings(db, page_id)

    for row in new_embedding_rows:
        db.add(row)

    return len(new_embedding_rows)


def try_refresh_page_embeddings(db: Session, page_id: int) -> None:
    """
    embedding 갱신을 시도한다.
    실패해도 회의/회고 저장 자체는 실패시키지 않는다.
    """

    try:
        count = refresh_page_embeddings(db, page_id)
        db.commit()
        logger.info("page_id=%s embedding 갱신 완료: %s chunks", page_id, count)

    except Exception:
        db.rollback()
        logger.exception("page_id=%s embedding 갱신 실패", page_id)


# 질문 embedding을 page_embedding 전체와 distance 비교
# distance가 0.45 이하 인 것만 가져옴


# 사용자 질문과 관련 있는 page_embedding chunk들을 찾는다.
def search_relevant_chunks(
    db: Session,
    question: str,
    current_user_id: int,
    threshold: float = SIMILARITY_DISTANCE_THRESHOLD,
    max_chunks: int = MAX_CONTEXT_CHUNKS,
):
    """
    사용자 질문과 관련 있는 page_embedding chunk들을 찾는다.

    흐름:
    1. 질문을 embedding으로 변환
    2. page_embeddings.embedding과 cosine distance 계산
    3. threshold 이하인 chunk만 선택
    4. 최대 max_chunks개까지만 가져옴
    """

    question_embedding = get_embedding(question)

    distance_expr = PageEmbedding.embedding.cosine_distance(question_embedding)

    rows = db.execute(
        select(
            PageEmbedding,
            Page,
            distance_expr.label("distance"),
        )
        .join(Page, Page.id == PageEmbedding.page_id)
        .where(Page.author_id == current_user_id)
        .where(distance_expr <= threshold)
        .order_by(distance_expr.asc())
        .limit(max_chunks)
    ).all()

    return rows


# 검색된 chunk들을 OpenAI에게 전달할 입력 텍스트로 만든다.
# search_rows 예시 : 뭐가 어떻게 결정되었어?(질문)
def build_rag_input(question: str, search_rows) -> str:

    # ex) search_rows = [embedding_row1, page1, 0.1823], [embedding_row2, page2, 0.2234], ...]
    sorted_rows = sorted(
        search_rows,
        key=lambda row: (row[1].date, row[0].chunk_index),
    )

    context_parts: list[str] = []

    for index, (embedding_row, page, distance) in enumerate(sorted_rows, start=1):
        context_parts.append(
            f"[참고 기록 {index}]\n"
            f"제목: {page.title}\n"
            f"날짜: {page.date}\n"
            f"종류: {page.type.value}\n"
            f"관련도 거리: {float(distance):.4f}\n"
            f"내용:\n{embedding_row.chunk_text}\n"
        )

    context = "\n---\n".join(context_parts)

    return f"""
[참고 기록]
{context}

[사용자 질문]
{question}
"""


def generate_rag_answer(question: str, search_rows) -> str:
    """
    검색된 참고 기록과 사용자 질문을 OpenAI에 보내 답변을 생성한다.
    """

    if not search_rows:
        return "저장된 기록에서 찾을 수 없습니다."

    rag_input = build_rag_input(question, search_rows)

    response = client.responses.create(
        model=settings.OPENAI_ANSWER_MODEL,
        instructions=RAG_INSTRUCTIONS,
        input=rag_input,
    )

    return response.output_text


def build_references(search_rows) -> list[dict]:
    """
    프론트에 보여줄 참고 기록 목록을 만든다.
    같은 page의 여러 chunk가 검색될 수 있으므로 중복 page는 제거한다.
    """

    references: list[dict] = []
    seen_page_ids: set[int] = set()

    sorted_rows = sorted(
        search_rows,
        key=lambda row: (row[1].date, row[0].chunk_index),
    )

    for embedding_row, page, distance in sorted_rows:
        if page.id in seen_page_ids:
            continue

        seen_page_ids.add(page.id)

        references.append(
            {
                "page_id": page.id,
                "title": page.title,
                "date": page.date,
                "type": page.type,
                "chunk_index": embedding_row.chunk_index,
                "distance": round(float(distance), 4),
            }
        )

    return references


def answer_rag_question(
    db: Session,
    question: str,
    current_user_id: int,
) -> dict:
    """
    RAG 질문 전체 흐름을 처리한다.

    1. 관련 chunk 검색
    2. OpenAI 답변 생성
    3. 참고 기록 생성
    """

    question = question.strip()

    if not question:
        return {
            "answer": "질문을 입력해 주세요.",
            "references": [],
        }

    # page_embedding db 테이블에서 distance 이하인 row들 다 가져옴
    search_rows = search_relevant_chunks(
        db=db,
        question=question,
        current_user_id=current_user_id,
    )

    # 검색된 참고 기록과 사용자 질문을 OpenAI에 보내 답변을 생성한다.
    answer = generate_rag_answer(
        question=question,
        search_rows=search_rows,
    )

    references = build_references(search_rows)

    return {
        "answer": answer,
        "references": references,
    }
