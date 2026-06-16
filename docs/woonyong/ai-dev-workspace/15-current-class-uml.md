# 현재 구현 클래스 UML

이 문서는 2026-06-13 기준 RepoLM 최소 구현의 Python 백엔드 클래스와 서비스 관계를 한눈에 보기 위한 UML이다. 다음 구현 순서는 `16-repo-rag-implementation-plan.md`를 기준으로 한다.

현재 구현은 두 흐름으로 나뉜다.

1. `/pipeline/run`: 요청을 즉시 처리하는 최소 데모 파이프라인
2. `/pipeline/sync`: Repo RAG 증분 동기화를 job 중심으로 처리하는 파이프라인

## 전체 구조

```mermaid
classDiagram
    direction LR

    class FastAPIApp {
        +include_router(api_router)
    }

    class ApiRouter {
        +include_router(health_router)
        +include_router(pipeline_router)
    }

    class PipelineRoute {
        +pipeline() dict
        +run_pipeline(request) PipelineResponse
        +sync_repo_rag(request) RepoRagSyncResponse
    }

    class PipelineService {
        +run(request) PipelineResponse
        -_collect_artifacts(request) PipelineArtifacts
        -_stage_details(artifacts) dict
    }

    class RepoRagSyncService {
        +store InMemoryRepoRagStore
        +producer SyncJobProducer
        +worker SyncWorker
        +cleanup RetentionCleanupService
        +run(request) RepoRagSyncResponse
    }

    FastAPIApp --> ApiRouter
    ApiRouter --> PipelineRoute
    PipelineRoute --> PipelineService : "/pipeline/run"
    PipelineRoute --> RepoRagSyncService : "/pipeline/sync"
```

## 최소 데모 파이프라인

`PipelineService`는 port/protocol을 통해 각 단계를 느슨하게 연결한다. 실제 구현체는 `RepoSyncService`, `CodeIndexService`, `RagIndexService`, `AgentProposalService`, `ApprovalService`, `PublishService`다.

```mermaid
classDiagram
    direction LR

    class PipelineService {
        +repo_sync RepoSyncPort
        +code_index CodeIndexPort
        +rag_index RagIndexPort
        +agent AgentProposalPort
        +approval ApprovalPort
        +publish PublishPort
        +run(request) PipelineResponse
    }

    class RepoSyncPort {
        <<interface>>
        +sync(request) RepoSnapshot
    }

    class CodeIndexPort {
        <<interface>>
        +index(snapshot) list~CodeReference~
    }

    class RagIndexPort {
        <<interface>>
        +index(snapshot, references) list~RetrievalChunk~
    }

    class AgentProposalPort {
        <<interface>>
        +propose(references, chunks) list~AgentProposal~
    }

    class ApprovalPort {
        <<interface>>
        +approve(proposals) list~AgentProposal~
    }

    class PublishPort {
        <<interface>>
        +publish(snapshot, chunks, proposals) PublishSnapshot
    }

    class RepoSyncService {
        +sync(request) RepoSnapshot
        -_sync_request_files(request) RepoSnapshot
        -_sync_local_repository(request) RepoSnapshot
        -_sync_remote_repository(request) RepoSnapshot
    }

    class CodeIndexService {
        +index(snapshot) list~CodeReference~
        -_extract_symbols(content) list
    }

    class RagIndexService {
        +index(snapshot, references) list~RetrievalChunk~
    }

    class AgentProposalService {
        +propose(references, chunks) list~AgentProposal~
    }

    class ApprovalService {
        +approve(proposals) list~AgentProposal~
    }

    class PublishService {
        +publish(snapshot, chunks, proposals) PublishSnapshot
    }

    PipelineService --> RepoSyncPort
    PipelineService --> CodeIndexPort
    PipelineService --> RagIndexPort
    PipelineService --> AgentProposalPort
    PipelineService --> ApprovalPort
    PipelineService --> PublishPort

    RepoSyncPort <|.. RepoSyncService
    CodeIndexPort <|.. CodeIndexService
    RagIndexPort <|.. RagIndexService
    AgentProposalPort <|.. AgentProposalService
    ApprovalPort <|.. ApprovalService
    PublishPort <|.. PublishService
```

## Repo RAG 증분 동기화

`RepoRagSyncService`는 job producer, worker, store, cleanup을 묶는 상위 서비스다. `manual`, `schedule`, `webhook`은 모두 producer 입구만 다르고 같은 job queue로 들어간다.

```mermaid
classDiagram
    direction LR

    class RepoRagSyncService {
        +store InMemoryRepoRagStore
        +producer SyncJobProducer
        +worker SyncWorker
        +cleanup RetentionCleanupService
        +run(request) RepoRagSyncResponse
    }

    class SyncJobProducer {
        +store InMemoryRepoRagStore
        +enqueue(request) SyncJobRecord
        +enqueue_manual(request) SyncJobRecord
        +enqueue_schedule(request) SyncJobRecord
        +enqueue_webhook(request, requested_commit_sha) SyncJobRecord
    }

    class SyncWorker {
        +store InMemoryRepoRagStore
        +repo_sync RepoSyncService
        +diff RepoDiffService
        +chunking ChunkingService
        +run(job_id) RepoRagSyncResponse
    }

    class InMemoryRepoRagStore {
        +create_job(request) SyncJobRecord
        +start_job(job_id) SyncJobRecord
        +claim_job_lock(job_id)
        +finish_job(job_id) SyncJobRecord
        +fail_job(job_id, error) SyncJobRecord
        +record_snapshot(repository_id, snapshot) SnapshotRecord
        +apply_file_changes(repository_id, snapshot_id, snapshot, changes) dict
        +upsert_chunks(repository_id, snapshot_id, file_records, chunks) list~ChunkRecord~
        +active_chunks(repository_id) list~RetrievalChunk~
        +hard_delete_inactive(batch_size, cutoff) int
    }

    class RepoDiffService {
        +compare(previous_files, snapshot) list~RepoFileChange~
    }

    class ChunkingService {
        +chunk_changed_files(snapshot, changes) list~RetrievalChunk~
    }

    class RetentionCleanupService {
        +store InMemoryRepoRagStore
        +cleanup(batch_size, cutoff) int
    }

    class RepoSyncService {
        +sync(request) RepoSnapshot
    }

    RepoRagSyncService --> SyncJobProducer
    RepoRagSyncService --> SyncWorker
    RepoRagSyncService --> InMemoryRepoRagStore
    RepoRagSyncService --> RetentionCleanupService

    SyncJobProducer --> InMemoryRepoRagStore
    SyncWorker --> InMemoryRepoRagStore
    SyncWorker --> RepoSyncService
    SyncWorker --> RepoDiffService
    SyncWorker --> ChunkingService
    RetentionCleanupService --> InMemoryRepoRagStore
```

## Repo RAG 저장 레코드

현재 런타임 저장소는 `InMemoryRepoRagStore`다. Postgres DDL은 `docker/postgres/init/002_repo_rag.sql`에 준비되어 있지만, SQLAlchemy/Postgres repository 구현은 다음 단계다.

```mermaid
classDiagram
    direction TB

    class RepositoryRecord {
        +id str
        +source_key str
        +name str
        +branch str
        +repository_url str?
        +created_at datetime
        +updated_at datetime
    }

    class SnapshotRecord {
        +id str
        +repository_id str
        +branch str
        +commit_sha str
        +file_count int
        +created_at datetime
    }

    class FileRecord {
        +id str
        +repository_id str
        +snapshot_id str
        +path str
        +content_hash str
        +status str
        +is_active bool
        +last_seen_at datetime
        +deleted_at datetime?
    }

    class ChunkRecord {
        +id str
        +repository_id str
        +file_id str
        +snapshot_id str
        +source_path str
        +chunk_hash str
        +text str
        +citation str
        +is_active bool
        +created_at datetime
        +deleted_at datetime?
        +to_chunk() RetrievalChunk
    }

    class SyncJobRecord {
        +id str
        +trigger_type str
        +branch str
        +idempotency_key str
        +lock_key str
        +repository_id str?
        +status str
        +error str?
        +to_view() SyncJobView
    }

    class SyncEventRecord {
        +id str
        +job_id str
        +stage str
        +detail str
        +created_at datetime
        +to_view() SyncEventView
    }

    RepositoryRecord "1" --> "*" SnapshotRecord
    RepositoryRecord "1" --> "*" FileRecord
    SnapshotRecord "1" --> "*" FileRecord
    FileRecord "1" --> "*" ChunkRecord
    SyncJobRecord "1" --> "*" SyncEventRecord
```

## API DTO

```mermaid
classDiagram
    direction LR

    class PipelineRequest {
        +repository str
        +branch str
        +repository_path str?
        +repository_url str?
        +files list~RepoFile~
    }

    class RepoRagSyncRequest {
        +trigger_type str
        +requested_commit_sha str?
    }

    class PipelineResponse {
        +repository RepoSnapshot
        +code_references list~CodeReference~
        +retrieval_chunks list~RetrievalChunk~
        +proposals list~AgentProposal~
        +publish_snapshot PublishSnapshot
        +stages list~StageResult~
    }

    class RepoRagSyncResponse {
        +job SyncJobView
        +repository RepoSnapshot
        +changes list~RepoFileChange~
        +active_chunks list~RetrievalChunk~
        +events list~SyncEventView~
    }

    class RepoSnapshot {
        +repository str
        +branch str
        +commit_sha str
        +files list~RepoFile~
    }

    PipelineRequest <|-- RepoRagSyncRequest
    PipelineResponse --> RepoSnapshot
    RepoRagSyncResponse --> RepoSnapshot
```

## 읽는 순서

처음 보는 사람은 아래 순서로 보면 좋다.

1. `backend/app/api/routes/pipeline.py`: API 진입점
2. `backend/app/services/pipeline.py`: 기존 최소 파이프라인
3. `backend/app/services/repo_sync.py`: 파일 snapshot 생성
4. `backend/app/services/repo_rag_sync.py`: job, diff, chunk, soft delete 흐름
5. `docker/postgres/init/002_repo_rag.sql`: 다음 단계 DB 구조
6. `docs/woonyong/ai-dev-workspace/16-repo-rag-implementation-plan.md`: Repo RAG 다음 구현 계획
