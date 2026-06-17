"""근거 신뢰도와 충돌 감지.

RepoLM의 기본 정책은 현재 repo snapshot을 가장 신뢰하되, 다른 소스와 명시적
사실이 충돌하면 조용히 한쪽을 고르지 않는 것이다. 이 모듈은 답변 생성 전에
가벼운 deterministic 검사를 수행한다.
"""

import re
from dataclasses import dataclass

from app.notebooks.domain.chunk_records import ChunkSearchHit
from app.notebooks.domain.records import SourceRecord
from app.notebooks.domain.source_evidence import trust_rank_for_source

_FACT_RE = re.compile(
    r"(?P<subject>[A-Za-z0-9_.\-/가-힣]{2,})\s*(?:=|:|은|는|is)\s*"
    r"(?P<value>true|false|enabled|disabled|on|off|활성|비활성|사용|미사용)",
    re.IGNORECASE,
)

_VALUE_NORMALIZATION = {
    "true": "true",
    "enabled": "true",
    "on": "true",
    "활성": "true",
    "사용": "true",
    "false": "false",
    "disabled": "false",
    "off": "false",
    "비활성": "false",
    "미사용": "false",
}


@dataclass(frozen=True, slots=True)
class EvidenceFact:
    subject: str
    value: str
    source_id: str
    source_title: str
    source_kind: str
    path: str | None
    trust_rank: int


@dataclass(frozen=True, slots=True)
class EvidenceConflict:
    subject: str
    facts: list[EvidenceFact]


def resolve_conflicts(
    hits: list[ChunkSearchHit],
    sources_by_id: dict[str, SourceRecord],
) -> list[EvidenceConflict]:
    facts_by_subject: dict[str, list[EvidenceFact]] = {}
    for hit in hits:
        source = sources_by_id.get(hit.chunk.source_id)
        if source is None:
            continue
        for subject, value in _extract_facts(hit.chunk.text):
            facts_by_subject.setdefault(subject, []).append(
                EvidenceFact(
                    subject=subject,
                    value=value,
                    source_id=source.id,
                    source_title=source.title,
                    source_kind=source.kind,
                    path=hit.chunk.file_path,
                    trust_rank=trust_rank(
                        source,
                        path=hit.chunk.file_path,
                        language=hit.chunk.language,
                    ),
                )
            )

    conflicts: list[EvidenceConflict] = []
    for subject, facts in facts_by_subject.items():
        values = {fact.value for fact in facts}
        locations = {(fact.source_id, fact.path) for fact in facts}
        if len(values) > 1 and len(locations) > 1:
            conflicts.append(
                EvidenceConflict(
                    subject=subject,
                    facts=sorted(
                        facts,
                        key=lambda fact: (-fact.trust_rank, fact.source_title, fact.path or ""),
                    ),
                )
            )
    return conflicts


def trust_rank(
    source: SourceRecord,
    *,
    path: str | None = None,
    language: str | None = None,
) -> int:
    return trust_rank_for_source(source, path=path, language=language)


def format_conflict_answer(conflicts: list[EvidenceConflict]) -> str:
    lines = ["충돌 있음: 선택된 자료 안에서 서로 다른 근거가 확인되었습니다."]
    for conflict in conflicts[:3]:
        lines.append(f"- {conflict.subject}")
        for fact in conflict.facts[:4]:
            where = fact.path or fact.source_title
            lines.append(
                f"  - {fact.value}: {where} "
                f"(source={fact.source_title}, trust={fact.trust_rank})"
            )
    lines.append("한쪽을 임의로 선택하지 않았습니다. 아래 citation을 함께 확인해 주세요.")
    return "\n".join(lines)


def _extract_facts(text: str) -> list[tuple[str, str]]:
    facts: list[tuple[str, str]] = []
    for match in _FACT_RE.finditer(text):
        raw_value = match.group("value").lower()
        value = _VALUE_NORMALIZATION.get(raw_value)
        if value is None:
            continue
        facts.append((match.group("subject").strip().lower(), value))
    return facts
