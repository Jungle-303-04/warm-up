"""repo-rag 하이브리드 검색 서비스.

uow로 저장소 resolve를, retriever_factory(세션)로 검색을 수행한다.
application 계층은 포트/팩토리에만 의존하고 인프라 구현을 직접 import 하지 않는다.
"""

from dataclasses import dataclass

from app.repo_rag.api.schemas import RepoRagSearchRequest
from app.repo_rag.application.types import RetrieverFactory, UowFactory
from app.repo_rag.domain.retrieval import SearchHit


@dataclass(slots=True)
class RepoRagSearchService:
    uow_factory: UowFactory
    retriever_factory: RetrieverFactory

    def search(self, request: RepoRagSearchRequest) -> list[SearchHit]:
        source = (request.repository_url or request.repository).strip()
        with self.uow_factory() as uow:
            repository_id = uow.repo_rag.find_repository_id(f"{source}:{request.branch}")
            if repository_id is None:
                raise ValueError("인덱싱된 저장소를 찾을 수 없습니다")
            retriever = self.retriever_factory(uow.session)
            return retriever.search(repository_id, request.query, request.limit)
