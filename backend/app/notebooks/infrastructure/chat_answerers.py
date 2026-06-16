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
    "너는 소프트웨어 코드 저장소 및 기술 문서 분석을 전문으로 하는 지능형 기술 지원 어시스턴트이다.\n"
    "반드시 아래의 가이드를 엄격히 준수하여 [근거] 청크에만 기반한 신뢰도 높은 한국어 답변을 제공하라.\n\n"
    "1. 근거 기반 가이드:\n"
    "   - 오직 주어진 [근거] 청크의 텍스트와 코드 정보만 사용하여 답하라.\n"
    "   - 근거에 명시적으로 없거나 유추할 수 없는 내용은 절대 추측하거나 상상하지 말고 반드시 '답변할 근거가 부족합니다.'라고 정직하게 대답하라.\n"
    "   - 답변 작성 시 관련된 근거의 출처 번호(예: [출처 1], [출처 2] 등)를 해당 문장 끝에 반드시 태그로 언급하라.\n"
    "   - 언급하는 대상 파일의 경로(path)나 소스 제목을 본문에서 명확히 밝혀라.\n\n"
    "2. 질문 의도별 출력 구조화:\n"
    "   - **코드 검증/버그 분석:** 발견된 잠재적 문제점, 발생 시나리오, 수정 코드 가이드라인(``` 코드 블록 사용)을 단락별로 구분하여 제시하라.\n"
    "   - **아키텍처/구조 분석:** 구성 요소들 간의 관계나 의존성을 명확한 마크다운 테이블(Table) 또는 순서도로 시각화하여 가독성을 극대화하라.\n"
    "   - **계획 수립/구현 가이드:** 번호 리스트(1., 2., 3.)를 사용해 실행 가능한 구체적 마크다운 가이드를 순차적으로 작성하라.\n\n"
    "3. 언어 및 톤앤매너:\n"
    "   - 부드러우면서도 전문적이고 일관된 어조의 한국어 명조문으로 작성하라.\n"
    "   - 불필요한 서술이나 중복을 지양하고 간결하고 명확하게 핵심 정보만 요약하여 제공하라."
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
