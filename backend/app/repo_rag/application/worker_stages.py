import logging
from typing import Protocol

from app.pipeline.domain import AgentProposalService, CodeIndexService
from app.pipeline.service import RepoSyncPort
from app.repo_rag.application.indexing import IndexingService
from app.repo_rag.application.unit_of_work import UnitOfWork
from app.repo_rag.domain.diff import RepoDiffService
from app.repo_rag.domain.ports import EmbeddingClient
from app.repository_source import RepoSyncService

logger = logging.getLogger(__name__)


class PipelineStageProcessor(Protocol):
    @property
    def stage_id(self) -> str: ...

    @property
    def target_status(self) -> str: ...

    @property
    def next_status(self) -> str: ...

    def process(self, job_id: str, uow: UnitOfWork) -> None: ...


class RepoSyncStageProcessor:
    def __init__(self, repo_sync: RepoSyncPort | None = None) -> None:
        self.repo_sync = repo_sync or RepoSyncService()

    @property
    def stage_id(self) -> str:
        return "repo-sync"

    @property
    def target_status(self) -> str:
        return "queued"

    @property
    def next_status(self) -> str:
        return "running_code_index"

    def process(self, job_id: str, uow: UnitOfWork) -> None:
        job = uow.repo_rag.start_job_stage(job_id, "running_sync")
        try:
            uow.repo_rag.claim_job_lock(job.id)
            uow.repo_rag.record_event(job.id, "fetch_started", "fetching repository snapshot")
            snapshot = self.repo_sync.sync(job.request)
            uow.repo_rag.record_event(
                job.id,
                "fetch_completed",
                f"{snapshot.repository}@{snapshot.commit_sha}",
            )

            repository = uow.repo_rag.upsert_repository(job.request, snapshot)
            uow.repo_rag.attach_job_repository(job.id, repository.id)
            uow.repo_rag.record_snapshot(repository.id, snapshot)
            uow.repo_rag.update_job_status(job.id, "running_code_index")
        except Exception as exc:
            uow.repo_rag.fail_job(job.id, str(exc))
            raise


class CodeIndexStageProcessor:
    def __init__(
        self,
        repo_sync: RepoSyncPort | None = None,
        diff: RepoDiffService | None = None,
    ) -> None:
        self.repo_sync = repo_sync or RepoSyncService()
        self.diff = diff or RepoDiffService()

    @property
    def stage_id(self) -> str:
        return "code-index"

    @property
    def target_status(self) -> str:
        return "running_code_index"

    @property
    def next_status(self) -> str:
        return "running_rag_index"

    def process(self, job_id: str, uow: UnitOfWork) -> None:
        job = uow.repo_rag.start_job_stage(job_id, "running_code_index")
        try:
            repository_id = job.repository_id
            if not repository_id:
                raise ValueError("repository_id is missing for code indexing")

            snapshot = self.repo_sync.sync(job.request)
            previous_files = uow.repo_rag.active_files(repository_id)
            snapshot_record = uow.repo_rag.record_snapshot(repository_id, snapshot)

            changes = self.diff.compare(previous_files, snapshot)
            uow.repo_rag.record_event(job.id, "diff_completed", f"compared files: {len(changes)} changes")

            file_records = uow.repo_rag.apply_file_changes(
                repository_id,
                snapshot_record.id,
                snapshot,
                changes,
            )
            uow.repo_rag.record_event(job.id, "files_persisted", f"{len(file_records)} active files")
            uow.repo_rag.update_job_status(job.id, "running_rag_index")
        except Exception as exc:
            uow.repo_rag.fail_job(job.id, str(exc))
            raise


class RagIndexStageProcessor:
    def __init__(
        self,
        repo_sync: RepoSyncPort | None = None,
        diff: RepoDiffService | None = None,
        embedder: EmbeddingClient | None = None,
    ) -> None:
        self.repo_sync = repo_sync or RepoSyncService()
        self.diff = diff or RepoDiffService()
        self.indexing = IndexingService(embedder=embedder)

    @property
    def stage_id(self) -> str:
        return "rag-index"

    @property
    def target_status(self) -> str:
        return "running_rag_index"

    @property
    def next_status(self) -> str:
        return "running_agent_proposal"

    def process(self, job_id: str, uow: UnitOfWork) -> None:
        job = uow.repo_rag.start_job_stage(job_id, "running_rag_index")
        try:
            repository_id = job.repository_id
            if not repository_id:
                raise ValueError("repository_id is missing for RAG indexing")

            snapshot = self.repo_sync.sync(job.request)
            previous_files = uow.repo_rag.active_files(repository_id)
            snapshot_record = uow.repo_rag.record_snapshot(repository_id, snapshot)

            changes = self.diff.compare(previous_files, snapshot)
            file_records = uow.repo_rag.apply_file_changes(
                repository_id,
                snapshot_record.id,
                snapshot,
                changes,
            )

            embedded_chunks = self.indexing.index_changes(snapshot, changes)
            chunk_records = uow.repo_rag.upsert_chunks(
                repository_id,
                snapshot_record.id,
                file_records,
                embedded_chunks,
            )
            uow.repo_rag.record_event(job.id, "chunks_upserted", f"{len(chunk_records)} chunks indexed")
            uow.repo_rag.update_job_status(job.id, "running_agent_proposal")
        except Exception as exc:
            uow.repo_rag.fail_job(job.id, str(exc))
            raise


class AgentProposalStageProcessor:
    def __init__(
        self,
        repo_sync: RepoSyncPort | None = None,
        agent_proposal_service: AgentProposalService | None = None,
    ) -> None:
        self.repo_sync = repo_sync or RepoSyncService()
        self.code_index = CodeIndexService()
        self.agent_proposal_service = agent_proposal_service or AgentProposalService()

    @property
    def stage_id(self) -> str:
        return "agent-proposal"

    @property
    def target_status(self) -> str:
        return "running_agent_proposal"

    @property
    def next_status(self) -> str:
        return "succeeded"

    def process(self, job_id: str, uow: UnitOfWork) -> None:
        job = uow.repo_rag.start_job_stage(job_id, "running_agent_proposal")
        try:
            repository_id = job.repository_id
            if not repository_id:
                raise ValueError("repository_id is missing for agent proposal")

            snapshot = self.repo_sync.sync(job.request)
            references = self.code_index.index(snapshot)
            chunks = uow.repo_rag.active_chunks(repository_id)

            proposals = self.agent_proposal_service.propose(references, chunks)
            uow.repo_rag.record_event(
                job.id,
                "agent_proposal_completed",
                f"generated {len(proposals)} agent proposals",
            )
            uow.repo_rag.finish_job(job.id)
        except Exception as exc:
            uow.repo_rag.fail_job(job.id, str(exc))
            raise
