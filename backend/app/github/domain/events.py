"""GitHub 웹훅 이벤트 파싱 (순수 로직).

push 이벤트에서 동기화에 필요한 저장소/브랜치/커밋 정보를 뽑는다.
브랜치 push가 아니거나 필수 정보가 없으면 ValueError(=400)로 처리한다.
"""

from dataclasses import dataclass

BRANCH_REF_PREFIX = "refs/heads/"


@dataclass(frozen=True, slots=True)
class PushEvent:
    repository_full_name: str
    repository_url: str
    branch: str
    commit_sha: str


def parse_push_event(payload: dict) -> PushEvent:
    ref = payload.get("ref", "")
    if not ref.startswith(BRANCH_REF_PREFIX):
        raise ValueError("브랜치 push 이벤트가 아닙니다")

    repository = payload.get("repository") or {}
    full_name = repository.get("full_name")
    clone_url = repository.get("clone_url") or repository.get("html_url")
    if not full_name or not clone_url:
        raise ValueError("repository 정보가 없습니다")

    return PushEvent(
        repository_full_name=full_name,
        repository_url=clone_url,
        branch=ref[len(BRANCH_REF_PREFIX) :],
        commit_sha=payload.get("after", ""),
    )
