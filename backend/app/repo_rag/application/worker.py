from dataclasses import dataclass, field

from app.repo_rag.domain.chunking import ChunkingService
from app.repo_rag.domain.diff import RepoDiffService, change_summary
from app.repo_rag.api.schemas import RepoRagSyncResponse
from app.repo_rag.infrastructure.store import RepoRagStore
from app.repository_source import RepoSyncService


@dataclass(slots=True)
class SyncWorker:
    store: RepoRagStore
    repo_sync: RepoSyncService = field(default_factory=RepoSyncService)
    diff: RepoDiffService = field(default_factory=RepoDiffService)
    chunking: ChunkingService = field(default_factory=ChunkingService)

    def run(self, job_id: str) -> RepoRagSyncResponse:
        job = self.store.start_job(job_id)

        try:
            self.store.claim_job_lock(job.id)
            self.store.record_event(job.id, "fetch_started", "fetching repository snapshot")
            snapshot = self.repo_sync.sync(job.request)
            self.store.record_event(
                job.id,
                "fetch_completed",
                f"{snapshot.repository}@{snapshot.commit_sha}",
            )

            repository = self.store.upsert_repository(job.request, snapshot)
            self.store.attach_job_repository(job.id, repository.id)
            previous_files = self.store.active_files(repository.id)
            snapshot_record = self.store.record_snapshot(repository.id, snapshot)

            changes = self.diff.compare(previous_files, snapshot)
            self.store.record_event(job.id, "diff_completed", change_summary(changes))

            file_records = self.store.apply_file_changes(
                repository.id,
                snapshot_record.id,
                snapshot,
                changes,
            )
            self.store.record_event(job.id, "files_persisted", f"{len(file_records)} active files")

            chunks = self.chunking.chunk_changed_files(snapshot, changes)
            chunk_records = self.store.upsert_chunks(
                repository.id,
                snapshot_record.id,
                file_records,
                chunks,
            )
            self.store.record_event(job.id, "chunks_upserted", f"{len(chunk_records)} chunks")

            job = self.store.finish_job(job.id)
            return RepoRagSyncResponse(
                job=job.to_view(),
                repository=snapshot,
                changes=changes,
                active_chunks=self.store.active_chunks(repository.id),
                events=[event.to_view() for event in self.store.job_events(job.id)],
            )
        except Exception as exc:
            self.store.fail_job(job.id, str(exc))
            raise
