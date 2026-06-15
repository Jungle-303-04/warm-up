from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.rag_schema import RagQueryRequest, RagQueryResponse
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.rag_service import answer_rag_question
from app.services.chat_service import handle_chat_message

router = APIRouter(
    # 이 파일의 모든 API는 /ai 로 시작한다.
    prefix="/ai",
    tags=["AI"],
)


# 프론트에서 사용자가 AI 채팅 메시지를 보내면 실행되는 API.
# 예: POST /ai/chat
@router.post("/chat", response_model=ChatResponse)
def chat(
    # 클라이언트가 보낸 요청 body.
    # 예:
    # {
    #   "session_id": 3,
    #   "message": "방금 말한 회의 내용 다시 요약해줘"
    # }
    #
    # session_id가 있으면 기존 채팅방에 이어서 질문하고,
    # session_id가 없으면 새 채팅방을 만든다.
    payload: ChatRequest,
    # 요청 하나 동안 사용할 DB 세션.
    # FastAPI가 get_db()를 실행해서 자동으로 넣어준다.
    db: Session = Depends(get_db),
    # Authorization Bearer 토큰을 검사해서 현재 로그인한 사용자를 가져온다.
    # 이 값으로 다른 사용자의 채팅방/회의록을 조회하지 못하게 막는다.
    current_user: User = Depends(get_current_user),
):
    # 실제 채팅 처리 로직은 service 계층에 위임한다.
    # 여기서 하는 일은 API 요청값을 service 함수에 넘기는 것뿐이다.
    return handle_chat_message(
        db=db,
        current_user=current_user,
        session_id=payload.session_id,
        message=payload.message,
    )


# 프론트에서 사용자가 질문을 보내면, 백엔드가 RAG 검색하고 OPENAI로 답변까지 만들어서 반환
@router.post("/rag/query", response_model=RagQueryResponse)
def query_rag(
    # 클라이언트가 보낸 질문 body.
    # 예: {"question": "지난 회의에서 결정한 내용 알려줘"}
    payload: RagQueryRequest,
    # 요청 하나 동안 사용할 DB 세션.
    # FastAPI가 get_db()를 실행해서 자동으로 넣어준다.
    db: Session = Depends(get_db),
    # Authorization 토큰을 검사해서 현재 로그인한 User를 가져온다.
    # 이 값으로 다른 사용자의 기록이 검색되지 않게 필터링한다.
    current_user: User = Depends(get_current_user),
):
    # 실제 RAG 처리는 service 계층에 위임한다.
    # 여기서는 API 입력값을 넘기고, service가 만든 결과를 그대로 응답한다.
    result = answer_rag_question(
        db=db,
        question=payload.question,
        current_user_id=current_user.id,
    )

    return result
