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
    "사용자의 질문 의도를 파악하여 아래 가이드에 따라 가장 적절하고 풍부한 답변을 제공하라.\n\n"
    "1. 질문의 분류 및 답변 가이드:\n"
    "   - **문서/코드 관련 질문:** 사용자의 질문이 제공된 [근거] 문서나 코드에 관련된 내용일 경우, 반드시 [근거] 청크의 텍스트와 코드 정보를 최대한 활용하여 답변하라. 답변 작성 시 관련된 근거의 출처 번호(예: [출처 1], [출처 2] 등)를 문장 끝에 명시하고, 파일 경로(path)나 소스 제목을 본문에서 명확히 밝혀라.\n"
    "   - **일반 상식/개발 지식/일상 대화 질문:** 질문이 제공된 [근거] 문서와 직접적인 관련이 없거나(예: 인사말, 일반적인 프로그래밍 문법, DFS 등 알고리즘 구현 방법, 범용 IT 상식 등), [근거] 문서만으로는 답변할 수 없는 경우에는 '답변할 근거가 부족합니다'라고 딱딱하게 끊지 말고, 너의 풍부한 내장 지식을 바탕으로 친절하고 상세하게 답변을 제공하라. 만약 제공된 문서에 관련 내용이 없어 자신의 지식으로 답하는 경우에는 그 사실을 부드럽게 언급하며 설명하라.\n\n"
    "2. 질문 의도별 출력 구조화:\n"
    "   - **코드 검증/버그 분석:** 발견된 잠재적 문제점, 발생 시나리오, 수정 코드 가이드라인(``` 코드 블록 사용)을 단락별로 구분하여 제시하라.\n"
    "   - **아키텍처/구조 분석:** 구성 요소들 간의 관계나 의존성을 명확한 마크다운 테이블(Table) 또는 순서도로 시각화하여 가독성을 극대화하라.\n"
    "   - **계획 수립/구현 가이드:** 번호 리스트(1., 2., 3.)를 사용해 실행 가능한 구체적 마크다운 가이드를 순차적으로 작성하라.\n\n"
    "3. 언어 및 톤앤매너:\n"
    "   - 전문적이면서도 매우 친절하고 부드러운 한국어 문체로 작성하라.\n"
    "   - 불필요하게 딱딱하거나 기계적인 답변(예: 단답형 '근거 부족')을 피하고, 실제 GPT나 유능한 개발 파트너처럼 자연스러운 대화를 나누어라."
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
        return self.answer(question, chunks, [])

    def answer(self, question: str, chunks: list[TextChunk], history: list[object]) -> str:
        try:
            prompt = _build_messages(question, chunks, history)
            response = self._chat_model.invoke(prompt)  # type: ignore[attr-defined]
            return _coerce_text(getattr(response, "content", response)).strip()
        except Exception:
            return ""

    def reformulate(self, question: str, history: list[object]) -> str:
        try:
            prompt = _build_reformulate_messages(question, history)
            response = self._chat_model.invoke(prompt)  # type: ignore[attr-defined]
            return _coerce_text(getattr(response, "content", response)).strip()
        except Exception:
            return question


REFORMULATE_SYSTEM_PROMPT = (
    "이전 대화 기록과 사용자의 마지막 질문을 바탕으로, "
    "문서 검색(RAG)에 사용할 수 있는 독립적이고 완벽한 한 문장의 한국어 질문으로 재작성하십시오.\n"
    "규칙:\n"
    "- 지시대명사(그것, 이 코드, 저번에 말한 것 등)가 있다면 맥락의 구체적인 명칭으로 바꾸십시오.\n"
    "- 질문의 원래 의도를 절대로 왜곡하지 마십시오.\n"
    "- 추가적인 설명이나 서두 없이 오직 재작성된 질문 문장 한 줄만 출력하십시오."
)


def _build_reformulate_messages(question: str, history: list[object]) -> list[tuple[str, str]]:
    formatted_history = []
    # 최근 6개(3턴) 대화만 사용
    for msg in history[-6:]:
        role_name = "User" if getattr(msg, "role", "") == "user" else "Assistant"
        formatted_history.append(f"{role_name}: {getattr(msg, "content", "")}")
    history_text = "\n".join(formatted_history)
    human = f"[대화 기록]\n{history_text}\n\n[마지막 질문]\n{question}\n\n재작성된 질문:"
    return [("system", REFORMULATE_SYSTEM_PROMPT), ("human", human)]


def _build_messages(
    question: str,
    chunks: list[TextChunk],
    history: list[object] | None = None,
) -> list[tuple[str, str]]:
    """system + human 메시지(role, content) 튜플 목록을 만든다.

    LangChain ChatModel.invoke는 (role, content) 튜플 리스트를 받아준다.
    컨텍스트는 chunks를 [출처 i] 형식으로 번호 매겨 제공한다.
    """

    messages = [("system", SYSTEM_PROMPT)]
    if history:
        # 최근 6개(3턴) 대화만 사용
        for msg in history[-6:]:
            role = "human" if getattr(msg, "role", "") == "user" else "ai"
            messages.append((role, getattr(msg, "content", "")))

    context = _format_context(chunks)
    human = f"[근거]\n{context}\n\n[질문]\n{question}"
    messages.append(("human", human))
    return messages


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
