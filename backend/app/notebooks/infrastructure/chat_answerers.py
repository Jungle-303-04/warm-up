"""채팅 답변기(ChatAnswerer) 어댑터.

ChatService.answerer로 주입되는 LLM 답변 생성기를 제공한다.

- ChatOpenAIAnswerer: LangChain ChatOpenAI로 (question, chunks)→답변 본문을 생성한다.
  강한 한국어 시스템 프롬프트로 "주어진 [근거]만 사용"하도록 유도하고, 질문 의도
  (설명/요약/코드 검증/버그 점검/계획 수립/구조 분석 등)에 맞춰 행위를 달리하게 한다.
  citation은 LLM이 만들지 않으며(검색된 chunks에서 ChatService가 생성), 본문만 생성한다.
- build_chat_openai_answerer: 키/모델을 주입받아 위 어댑터를 만드는 빌더(지연 import).

토큰 과다 방지: 컨텍스트 청크 상한(MAX_CONTEXT_CHUNKS)과 청크당 길이 상한
(MAX_CHARS_PER_CHUNK)을 둔다. 호출/파싱 실패 시 예외를 밖으로 던지지 않고 빈 문자열을
돌려 ChatService가 결정론 폴백으로 안전하게 전환하게 한다(런타임 에러 0).

artifact_generators.ChatOpenAIArtifactGenerator와 동일한 build 패턴(지연 import,
키/모델 주입, 실패 시 안전 폴백)을 따른다. 헥사고날 경계상 langchain/openai는
함수 내 지연 import 한다.
"""

from __future__ import annotations

from app.notebooks.application.chat_service import TextChunk

# 컨텍스트로 LLM에 넘길 청크 개수 상한(토큰 과다 방지).
MAX_CONTEXT_CHUNKS = 5
# 청크당 본문 길이 상한(문자 단위, 초과 시 잘라서 표기).
MAX_CHARS_PER_CHUNK = 1500

# 강한 한국어 시스템 프롬프트.
# - 주어진 [근거]만 사용, 근거에 없으면 추측 금지("근거가 부족하다").
# - 질문 의도(설명/요약/코드 검증/버그 점검/계획 수립/구조 분석 등)에 맞춰 행위 변경.
# - 답변 언어는 사용자 질문 언어를 따른다. 간결·정확, 가능하면 파일/경로 언급.
SYSTEM_PROMPT = (
    "너는 코드 저장소·문서 기반 어시스턴트다. 주어진 [근거] 청크만 사용해 "
    "사용자의 질문/요청에 답하라. 질문의 의도(설명/요약/코드 검증/버그 점검/"
    "계획 수립/구조 분석 등)에 맞춰 행위를 달리하라. 예를 들어 코드 검증·버그 "
    "점검이면 근거 코드의 문제점을 짚고, 계획 수립이면 단계를 제시하고, 구조 "
    "분석이면 구성요소와 관계를 설명하라. 근거에 없으면 추측하지 말고 '근거가 "
    "부족하다'고 답하라. 답변 언어는 사용자 질문 언어를 따른다. 간결하고 "
    "정확하게, 가능하면 파일/경로를 함께 언급하라. 근거는 [출처 i] 형식으로 "
    "번호가 매겨져 제공되며, 필요하면 답변에서 해당 출처 번호를 참조해도 된다."
)


def build_chat_openai_answerer(
    provider: str,
    model: str,
    api_key: str | None,
    *,
    temperature: float = 0.0,
):
    """LangChain ChatOpenAI 기반 ChatAnswerer를 만든다(지연 import).

    artifact_generators._build_artifact_generator와 동일하게 chat_models 팩토리로
    BaseChatModel을 만든 뒤 ChatOpenAIAnswerer로 감싼다.
    """

    from app.pipeline.infrastructure.chat_models import build_chat_model

    chat_model = build_chat_model(
        provider,
        model,
        api_key,
        temperature=temperature,
    )
    return ChatOpenAIAnswerer(chat_model)


class ChatOpenAIAnswerer:
    """LangChain ChatOpenAI 기반 채팅 답변기.

    __call__(question, chunks) 시그니처라 ChatService.answerer(ChatAnswerer)로 바로
    주입된다. 호출/파싱 실패 시 빈 문자열을 돌려 ChatService가 결정론 폴백으로 전환한다.
    """

    def __init__(self, chat_model: object) -> None:
        self._chat_model = chat_model

    def __call__(self, question: str, chunks: list[TextChunk]) -> str:
        try:
            prompt = _build_messages(question, chunks)
            response = self._chat_model.invoke(prompt)  # type: ignore[attr-defined]
            return _coerce_text(getattr(response, "content", response)).strip()
        except Exception:
            # 네트워크/타임아웃/키/파싱 오류 등은 빈 문자열로 흡수 → 결정론 폴백.
            return ""


def _build_messages(question: str, chunks: list[TextChunk]) -> list[tuple[str, str]]:
    """system + human 메시지(role, content) 튜플 목록을 만든다.

    LangChain ChatModel.invoke는 (role, content) 튜플 리스트를 받아준다.
    컨텍스트는 chunks를 [출처 i] 형식으로 번호 매겨 제공한다.
    """

    context = _format_context(chunks)
    human = f"[근거]\n{context}\n\n[질문]\n{question}"
    return [("system", SYSTEM_PROMPT), ("human", human)]


def _format_context(chunks: list[TextChunk]) -> str:
    """근거 청크를 [출처 i] 번호 형식으로 직렬화한다(상한 적용)."""

    if not chunks:
        return "(근거 없음)"
    parts: list[str] = []
    for index, chunk in enumerate(chunks[:MAX_CONTEXT_CHUNKS], start=1):
        where = chunk.path or chunk.source_title
        body = chunk.text.strip()
        if len(body) > MAX_CHARS_PER_CHUNK:
            body = body[:MAX_CHARS_PER_CHUNK] + "..."
        parts.append(f"[출처 {index}] {where}\n{body}")
    return "\n\n".join(parts)


def _coerce_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(part) for part in content)
    return str(content)
