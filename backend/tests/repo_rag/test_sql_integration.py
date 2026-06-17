"""Postgres+pgvector 통합 테스트.

POSTGRES_DATABASE_URL이 설정된 경우에만 실행된다(예: 테스트 전용 DB).
테이블을 생성하고 실제 sync + 하이브리드 검색을 end-to-end로 검증한다.

실행 예:
    POSTGRES_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/repolm_test \
        pytest tests/repo_rag/test_sql_integration.py
"""

import os

import pytest

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="POSTGRES_DATABASE_URL이 설정된 경우에만 실행합니다",
)


def _bootstrap_schema():
    from sqlalchemy import text

    from app.repo_rag.infrastructure import models  # noqa: F401  (모델 등록)
    from app.repo_rag.infrastructure.db import Base, create_db_engine, create_session_factory

    assert POSTGRES_DATABASE_URL is not None
    engine = create_db_engine(POSTGRES_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_source_chunks_content_tsv "
                "ON source_chunks USING gin (content_tsv)"
            )
        )
    return create_session_factory(engine)


def test_sync_and_hybrid_search_end_to_end() -> None:
    from sqlalchemy import select

    from app.pipeline.router import RepoFile
    from app.repo_rag.api.schemas import RepoRagSyncRequest
    from app.repo_rag.application.service import RepoRagSyncService
    from app.repo_rag.infrastructure.embeddings import DeterministicEmbeddingClient
    from app.repo_rag.infrastructure.models import RepositoryModel
    from app.repo_rag.infrastructure.sql_retriever import SqlHybridRetriever
    from app.repo_rag.infrastructure.sql_unit_of_work import SqlUnitOfWork

    session_factory = _bootstrap_schema()
    embeddings = DeterministicEmbeddingClient(dimension=1536)

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    # UoW가 트랜잭션 경계를 잡는다(sync 전체 원자적)
    service = RepoRagSyncService(uow_factory=uow_factory, embedder=embeddings)
    response = service.run(
        RepoRagSyncRequest(
            repository="team/repo",
            branch="main",
            files=[
                RepoFile(
                    path="auth.py",
                    content="def login(user):\n    return issue_token(user)\n",
                ),
                RepoFile(
                    path="README.md",
                    content="# Auth\n\nLogin issues a JWT token.\n",
                ),
            ],
        )
    )

    assert response.job.status == "succeeded"
    assert {chunk.source_path for chunk in response.active_chunks} == {
        "auth.py",
        "README.md",
    }

    with session_factory() as session:
        repository = session.scalars(select(RepositoryModel)).first()
        assert repository is not None
        repository_id = repository.id
        retriever = SqlHybridRetriever(
            session,
            embeddings,
            vector_weight=0.7,
            keyword_weight=0.3,
            text_config="simple",
            candidate_limit=50,
        )
        hits = retriever.search(repository_id, "login token", limit=5)

    assert hits
    assert hits[0].score >= 0.0
    assert hits[0].chunk.source_path in {"auth.py", "README.md"}


def test_poller_processes_queued_job() -> None:
    from app.pipeline.router import RepoFile
    from app.repo_rag.api.schemas import RepoRagSyncRequest
    from app.repo_rag.infrastructure.sql_store import SqlRepoRagStore
    from app.repo_rag.infrastructure.sql_unit_of_work import SqlUnitOfWork
    from app.repo_rag.poller import SyncJobPoller

    session_factory = _bootstrap_schema()

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    with uow_factory() as uow:
        uow.repo_rag.create_job(
            RepoRagSyncRequest(
                repository="team/poll",
                branch="main",
                files=[RepoFile(path="m.py", content="def f():\n    return 1\n")],
            )
        )

    poller = SyncJobPoller(uow_factory)
    job_id = poller.run_once()

    assert job_id is not None
    with session_factory() as session:
        assert SqlRepoRagStore(session).get_job(job_id).status == "succeeded"
    assert poller.run_once() is None  # 큐가 비었다
