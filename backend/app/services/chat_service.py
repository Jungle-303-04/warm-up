from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.page import Page
from app.models.page_embedding import PageEmbedding
from app.models.user import User
from app.services.rag_service import search_relevant_chunks

# OpenAI API를 호출할 때 사용할 클라이언트.
# 실제 API key는 backend/.env의 OPENAI_API_KEY에서 settings를 통해 들어온다.
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# 후속 질문을 이해하기 위해 OpenAI/RAG 검색에 같이 넘길 최근 메시지 개수.
# 예: 사용자가 "그 방식은?"이라고 물으면 직전 대화를 같이 봐야 의미를 알 수 있다.
RECENT_CHAT_MESSAGE_LIMIT = 4


# AI에게 주는 시스템 지시문.
# 답변할 때 회의/회고 기록을 우선 근거로 삼고, 없는 내용은 지어내지 않도록 제한한다.
CHAT_INSTRUCTIONS = """
너는 TeamLog의 회의록/회고록 기반 AI 챗봇이다.

규칙:
1. 제공된 [회의/회고 참고 기록]을 우선 근거로 답변한다.
2. 참고 기록에 없는 내용은 단정하지 않는다.
3. 기록 기반 내용과 추론/제안은 구분해서 답변한다.
4. 여러 날짜의 기록이 있으면 날짜순으로 정리한다.
5. 서로 충돌하는 결정이 있으면 최신 날짜의 기록을 현재 기준 결론으로 판단한다.
6. 사용자가 "그 방식", "방금 말한 것"처럼 말하면 [최근 대화]를 참고해 의미를 파악한다.
7. 답을 찾을 수 없으면 "저장된 회의/회고 기록에서는 찾을 수 없습니다."라고 답한다.
8. 한국어로 답변한다.
"""


def get_or_create_chat_session(
    db: Session,
    current_user_id: int,
    session_id: int | None,
    first_message: str,
) -> ChatSession:
    """
    session_id가 있으면 기존 채팅방을 가져오고,
    없으면 새 채팅방을 만든다.
    """

    # session_id가 넘어왔다는 것은 기존 채팅방에 이어서 질문한다는 뜻이다.
    if session_id is not None:
        session = db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == current_user_id)
        ).scalar_one_or_none()

        # 현재 로그인한 사용자의 채팅방이 아니거나 없는 ID면 접근을 막는다.
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채팅방을 찾을 수 없습니다.",
            )

        return session

    # session_id가 없으면 첫 질문 내용을 이용해서 새 채팅방 제목을 만든다.
    title = first_message.strip()
    if len(title) > 30:
        title = title[:30] + "..."

    # 아직 commit 전이지만 flush를 하면 DB에서 id가 발급되어 바로 사용할 수 있다.
    session = ChatSession(
        user_id=current_user_id,
        title=title or "새 AI 대화",
    )

    db.add(session)
    db.flush()

    return session


def get_recent_messages(
    db: Session,
    session_id: int,
    limit: int = RECENT_CHAT_MESSAGE_LIMIT,
) -> list[ChatMessage]:
    """
    최근 메시지 limit개를 가져온다.
    DB에서는 최신순으로 가져온 뒤,
    OpenAI에 넣기 위해 시간순으로 다시 뒤집는다.
    """

    # DB에서는 최신 메시지를 빠르게 찾기 위해 created_at/id 내림차순으로 조회한다.
    recent_desc = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    # OpenAI에게는 실제 대화 순서대로 보여줘야 하므로 오래된 메시지가 먼저 오게 뒤집는다.
    return list(reversed(recent_desc))


def save_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    references: list[dict[str, Any]] | None = None,
) -> ChatMessage:
    """
    사용자 질문 또는 AI 답변을 저장한다.
    """

    # role은 "user" 또는 "assistant"처럼 누가 보낸 메시지인지 나타낸다.
    # references는 AI 답변 메시지일 때 참고한 회의/회고 목록을 저장하는 용도다.
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        references=references,
    )

    db.add(message)
    db.flush()

    return message


def format_recent_messages(messages: list[ChatMessage]) -> str:
    """
    최근 대화를 OpenAI에게 넘길 텍스트로 변환한다.
    """

    # 이전 대화가 없는 첫 질문이면 "없음"이라고 명시해 prompt에 넣는다.
    if not messages:
        return "없음"

    lines: list[str] = []

    # DB row 형태의 메시지를 OpenAI가 읽기 쉬운 "user: ...", "assistant: ..." 형식으로 바꾼다.
    for message in messages:
        role_label = "user" if message.role == "user" else "assistant"
        lines.append(f"{role_label}: {message.content}")

    return "\n".join(lines)


def build_retrieval_query(
    recent_messages: list[ChatMessage],
    current_message: str,
) -> str:
    """
    RAG 검색용 query를 만든다.

    후속 질문 예:
    '그 방식의 단점은?'

    이런 질문은 현재 문장만 보면 애매하므로
    최근 대화와 현재 질문을 합쳐서 embedding 검색한다.
    """

    recent_text = format_recent_messages(recent_messages)

    # embedding 검색은 이 문자열 전체를 기준으로 수행된다.
    # 최근 대화를 합쳐야 짧은 후속 질문도 이전 맥락에 맞게 검색된다.
    return f"""
[최근 대화]
{recent_text}

[현재 질문]
{current_message}
""".strip()


def format_reference_context(search_rows) -> str:
    """
    검색된 회의/회고 chunk들을 OpenAI에게 넘길 참고 기록 텍스트로 만든다.
    """

    # 검색된 기록이 없으면 OpenAI 입력에 "없음"으로 넣는다.
    if not search_rows:
        return "없음"

    # 여러 기록이 섞여 있으면 날짜순, 같은 page 안에서는 chunk 순서대로 정렬한다.
    sorted_rows = sorted(
        search_rows,
        key=lambda row: (row[1].date, row[0].chunk_index),
    )

    parts: list[str] = []

    # search_rows의 각 row는 (PageEmbedding, Page, distance) 형태다.
    # distance는 질문 embedding과 page chunk embedding 사이의 거리이며, 작을수록 더 관련 있다.
    for index, (embedding_row, page, distance) in enumerate(sorted_rows, start=1):
        parts.append(
            f"[회의/회고 참고 기록 {index}]\n"
            f"제목: {page.title}\n"
            f"날짜: {page.date}\n"
            f"종류: {page.type.value}\n"
            f"관련도 거리: {float(distance):.4f}\n"
            f"내용:\n{embedding_row.chunk_text}\n"
        )

    return "\n---\n".join(parts)


def build_chat_input(
    recent_messages: list[ChatMessage],
    reference_context: str,
    current_message: str,
) -> str:
    """
    OpenAI 답변 모델에 넣을 전체 입력 텍스트를 만든다.
    """

    recent_text = format_recent_messages(recent_messages)

    # 최종적으로 OpenAI에게 넘길 사용자 입력.
    # 최근 대화, RAG 참고 기록, 현재 질문을 한 번에 넣는다.
    return f"""
[최근 대화]
{recent_text}

[회의/회고 참고 기록]
{reference_context}

[현재 사용자 질문]
{current_message}
""".strip()


def build_references(search_rows) -> list[dict[str, Any]]:
    """
    프론트와 DB에 저장할 참고 기록 목록을 만든다.
    같은 page가 여러 chunk로 검색될 수 있으므로 page_id 기준으로 중복 제거한다.
    """

    references: list[dict[str, Any]] = []
    seen_page_ids: set[int] = set()

    # 프론트에는 사용자가 읽기 편하게 날짜순으로 참고 기록을 내려준다.
    sorted_rows = sorted(
        search_rows,
        key=lambda row: (row[1].date, row[0].chunk_index),
    )

    for embedding_row, page, distance in sorted_rows:
        # 같은 page에서 여러 chunk가 검색될 수 있으므로 page 하나당 한 번만 references에 넣는다.
        if page.id in seen_page_ids:
            continue

        seen_page_ids.add(page.id)

        references.append(
            {
                "page_id": page.id,
                "title": page.title,
                "date": page.date.isoformat() if page.date else None,
                "chunk_index": embedding_row.chunk_index,
                "distance": round(float(distance), 4),
            }
        )

    return references


def generate_chat_answer(chat_input: str, has_references: bool) -> str:
    """
    OpenAI 답변을 생성한다.
    참고 기록이 없으면 OpenAI 호출 없이 고정 답변을 반환한다.
    """

    # 참고 기록이 없는데 OpenAI를 부르면 모델이 추측할 수 있으므로 바로 고정 답변을 반환한다.
    if not has_references:
        return "저장된 회의/회고 기록에서는 찾을 수 없습니다."

    # 참고 기록이 있을 때만 OpenAI에게 답변 생성을 요청한다.
    response = client.responses.create(
        model=settings.OPENAI_ANSWER_MODEL,
        instructions=CHAT_INSTRUCTIONS,
        input=chat_input,
    )

    return response.output_text


def handle_chat_message(
    db: Session,
    current_user: User,
    session_id: int | None,
    message: str,
) -> dict[str, Any]:
    """
    챗봇 루프 전체.

    1. 채팅방 확인/생성
    2. 최근 대화 조회
    3. user 메시지 저장
    4. 최근 대화 + 현재 질문으로 RAG 검색
    5. OpenAI 답변 생성
    6. assistant 메시지 저장
    7. 응답 반환
    """

    # 공백만 들어온 요청은 실제 질문이 아니므로 400 에러로 막는다.
    clean_message = message.strip()

    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="메시지를 입력해 주세요.",
        )

    # 기존 채팅방이면 가져오고, 첫 질문이면 새 채팅방을 만든다.
    session = get_or_create_chat_session(
        db=db,
        current_user_id=current_user.id,
        session_id=session_id,
        first_message=clean_message,
    )

    # 현재 user 메시지를 저장하기 전에 최근 대화를 가져온다.
    # 그래야 현재 메시지가 recent에 중복으로 들어가지 않는다.
    recent_messages = get_recent_messages(
        db=db,
        session_id=session.id,
        limit=RECENT_CHAT_MESSAGE_LIMIT,
    )

    # 사용자가 보낸 현재 질문을 먼저 DB에 저장한다.
    save_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=clean_message,
    )

    # RAG 검색용 질문은 최근 대화 + 현재 질문을 합쳐서 만든다.
    retrieval_query = build_retrieval_query(
        recent_messages=recent_messages,
        current_message=clean_message,
    )

    # page_embeddings 테이블에서 현재 사용자 기록 중 질문과 가까운 chunk를 찾는다.
    search_rows = search_relevant_chunks(
        db=db,
        question=retrieval_query,
        current_user_id=current_user.id,
    )

    # 검색된 chunk를 OpenAI prompt에 넣기 좋은 텍스트로 바꾼다.
    reference_context = format_reference_context(search_rows)

    # OpenAI에게 넘길 최종 입력을 만든다.
    chat_input = build_chat_input(
        recent_messages=recent_messages,
        reference_context=reference_context,
        current_message=clean_message,
    )

    # 참고 기록이 있으면 OpenAI 답변 생성, 없으면 고정 안내 문구 반환.
    answer = generate_chat_answer(
        chat_input=chat_input,
        has_references=bool(search_rows),
    )

    # 프론트와 DB에 남길 참고 기록 목록을 만든다.
    references = build_references(search_rows)

    # AI 답변도 같은 채팅방의 메시지로 저장한다.
    save_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
        references=references,
    )

    # 채팅방 목록에서 최근에 사용한 대화가 위로 오도록 수정 시간을 갱신한다.
    session.updated_at = datetime.now(timezone.utc)

    # 지금까지 만든 채팅방, 사용자 메시지, AI 메시지를 한 번에 DB에 확정 저장한다.
    db.commit()

    # API 응답으로 프론트에 내려갈 데이터.
    return {
        "session_id": session.id,
        "message": answer,
        "references": references,
    }
