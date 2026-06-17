"""승인된 제안을 GitHub 코멘트 마크다운으로 변환 (순수 로직)."""

from app.proposals.domain import ProposalRecord


def format_proposal_comment(record: ProposalRecord) -> str:
    lines = [
        "## 🤖 RepoLM 제안",
        "",
        f"- **대상 파일**: `{record.target_path}`",
        f"- **신뢰도**: {record.confidence:.0%}",
        f"- **상태**: {record.status.value}",
        "",
        record.proposed_change,
    ]
    if record.evidence:
        lines.append("")
        lines.append("**근거**")
        lines.extend(f"- {item}" for item in record.evidence)
    return "\n".join(lines)
