"""하위호환용 re-export.

RepoRagStore 포트는 domain/ports.py로 이동했다. 기존 import 경로
(app.repo_rag.infrastructure.store)를 유지하기 위해 여기서 다시 내보낸다.
신규 코드는 app.repo_rag.domain.ports 를 사용한다.
"""

from app.repo_rag.domain.ports import RepoRagStore

__all__ = ["RepoRagStore"]
