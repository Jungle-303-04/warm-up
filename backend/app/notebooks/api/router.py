import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.notebooks.api.schemas import (
    ArtifactListResponse,
    ArtifactView,
    ChatMessageListResponse,
    ChatMessageView,
    ChatRequest,
    ChatResponse,
    CreateNotebookRequest,
    CreateNoteRequest,
    CreateSourceRequest,
    FileResponse,
    GenerateArtifactRequest,
    IndexProgressView,
    NotebookDetailView,
    NotebookListResponse,
    NotebookView,
    SourceDetailView,
    SourceListResponse,
    SourceView,
    TreeNode,
    TreeResponse,
    UpdateArtifactRequest,
    UpdateNotebookRequest,
)
from app.notebooks.application.artifact_service import ArtifactService
from app.notebooks.application.chat_service import ChatService
from app.notebooks.application.indexing_service import IndexingService
from app.notebooks.application.service import NotebookService
from app.notebooks.dependencies import (
    get_artifact_service,
    get_indexing_service,
    get_notebook_chat_service,
    get_notebook_service,
)
from app.notebooks.domain.indexing_progress import (
    IndexProgressRegistry,
    get_progress_registry,
)

router = APIRouter()

# SSE 폴링 주기/안전 한도.
SSE_POLL_SECONDS = 0.3
SSE_MAX_TICKS = 600  # 약 3분 후 강제 종료(연결 누수 방지)

NOT_FOUND: dict[type[Exception], int] = {KeyError: status.HTTP_404_NOT_FOUND}
NOT_FOUND_OR_BAD_REQUEST: dict[type[Exception], int] = {
    KeyError: status.HTTP_404_NOT_FOUND,
    ValueError: status.HTTP_400_BAD_REQUEST,
}


# --- 노트북 ---


@router.post(
    "/notebooks",
    response_model=NotebookView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def create_notebook(
    request: CreateNotebookRequest,
    service: NotebookService = Depends(get_notebook_service),
) -> NotebookView:
    def run() -> NotebookView:
        record = service.create_notebook(title=request.title, summary=request.summary)
        return NotebookView.from_record(record, source_count=0)

    return http_error(run, {ValueError: status.HTTP_400_BAD_REQUEST})


@router.get(
    "/notebooks",
    response_model=NotebookListResponse,
    dependencies=[Depends(get_current_claims)],
)
def list_notebooks(
    service: NotebookService = Depends(get_notebook_service),
) -> NotebookListResponse:
    records = service.list_notebooks()
    notebooks = [
        NotebookView.from_record(
            record,
            source_count=len(service.store.list_sources(record.id)),
        )
        for record in records
    ]
    return NotebookListResponse(notebooks=notebooks)


@router.get(
    "/notebooks/{notebook_id}",
    response_model=NotebookDetailView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_notebook(
    notebook_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> NotebookDetailView:
    def run() -> NotebookDetailView:
        record = service.get_notebook(notebook_id)
        sources = service.list_sources(notebook_id)
        return NotebookDetailView.from_record(record, sources=sources)

    return http_error(run, NOT_FOUND)


@router.patch(
    "/notebooks/{notebook_id}",
    response_model=NotebookView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def update_notebook(
    notebook_id: str,
    request: UpdateNotebookRequest,
    service: NotebookService = Depends(get_notebook_service),
) -> NotebookView:
    def run() -> NotebookView:
        record = service.update_notebook(
            notebook_id, title=request.title, summary=request.summary
        )
        source_count = len(service.store.list_sources(notebook_id))
        return NotebookView.from_record(record, source_count=source_count)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.delete(
    "/notebooks/{notebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def delete_notebook(
    notebook_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> Response:
    http_error(lambda: service.delete_notebook(notebook_id), NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- 소스 ---


@router.post(
    "/notebooks/{notebook_id}/chat",
    response_model=ChatResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def chat(
    notebook_id: str,
    request: ChatRequest,
    service: ChatService = Depends(get_notebook_chat_service),
) -> ChatResponse:
    def run() -> ChatResponse:
        result = service.ask(
            notebook_id,
            question=request.question,
            source_ids=request.source_ids,
            file_paths=request.file_paths,
        )
        return ChatResponse.from_result(result)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.get(
    "/notebooks/{notebook_id}/chat/messages",
    response_model=ChatMessageListResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def list_chat_messages(
    notebook_id: str,
    service: ChatService = Depends(get_notebook_chat_service),
) -> ChatMessageListResponse:
    def run() -> ChatMessageListResponse:
        messages = service.list_messages(notebook_id)
        return ChatMessageListResponse(
            messages=[ChatMessageView.from_record(message) for message in messages]
        )

    return http_error(run, NOT_FOUND)


@router.post(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def create_source(
    notebook_id: str,
    request: CreateSourceRequest,
    background_tasks: BackgroundTasks,
    service: NotebookService = Depends(get_notebook_service),
    indexing: IndexingService = Depends(get_indexing_service),
) -> SourceView:
    def run() -> SourceView:
        record = service.add_source(
            notebook_id,
            kind=request.kind,
            title=request.title,
            content=request.content,
            url=request.url,
            repository_url=request.repository_url,
            branch=request.branch,
        )
        # 진행 레지스트리에 queued 등록 후 인덱싱은 비동기 실행(응답은 즉시 반환).
        indexing.register(record)
        background_tasks.add_task(indexing.index_source, notebook_id, record.id)
        return SourceView.from_record(record)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.get(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceListResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def list_sources(
    notebook_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> SourceListResponse:
    def run() -> SourceListResponse:
        sources = service.list_sources(notebook_id)
        return SourceListResponse(sources=[SourceView.from_record(s) for s in sources])

    return http_error(run, NOT_FOUND)


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}",
    response_model=SourceDetailView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_source(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> SourceDetailView:
    return http_error(
        lambda: SourceDetailView.from_record(service.get_source(notebook_id, source_id)),
        NOT_FOUND,
    )


@router.delete(
    "/notebooks/{notebook_id}/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def delete_source(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
    indexing: IndexingService = Depends(get_indexing_service),
) -> Response:
    http_error(lambda: service.delete_source(notebook_id, source_id), NOT_FOUND)
    # 소스가 사라지면 청크/진행 상태도 함께 정리.
    indexing.cleanup_source(source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- repo 트리/파일 ---


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/tree",
    response_model=TreeResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_source_tree(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> TreeResponse:
    def run() -> TreeResponse:
        tree_data = service.get_source_tree(notebook_id, source_id)
        tree_nodes = [TreeNode.from_dict(node) for node in tree_data]
        return TreeResponse(tree=tree_nodes)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/file",
    response_model=FileResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_source_file(
    notebook_id: str,
    source_id: str,
    path: str = Query(...),
    service: NotebookService = Depends(get_notebook_service),
) -> FileResponse:
    return http_error(
        lambda: FileResponse(**service.get_source_file(notebook_id, source_id, path)),
        NOT_FOUND_OR_BAD_REQUEST,
    )


# --- 인덱싱 진행 상태 ---


def _require_progress(
    notebook_id: str,
    source_id: str,
    service: NotebookService,
    registry: IndexProgressRegistry,
) -> dict:
    service.get_source(notebook_id, source_id)  # 존재 확인(없으면 KeyError → 404)
    view = registry.get(source_id)
    if view is None:
        raise KeyError(source_id)
    return view


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/index",
    response_model=IndexProgressView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_source_index(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> IndexProgressView:
    registry = get_progress_registry()
    return http_error(
        lambda: IndexProgressView.from_view(
            _require_progress(notebook_id, source_id, service, registry)
        ),
        NOT_FOUND,
    )


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/index/stream",
    dependencies=[Depends(get_current_claims)],
)
def stream_source_index(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> StreamingResponse:
    registry = get_progress_registry()
    # 연결 시작 전에 소스/진행 상태 존재를 확인(없으면 404).
    try:
        service.get_source(notebook_id, source_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    if registry.get(source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    async def event_stream() -> AsyncIterator[str]:
        import asyncio

        for _ in range(SSE_MAX_TICKS):
            view = registry.get(source_id)
            if view is None:
                break
            yield f"data: {json.dumps(view, ensure_ascii=False)}\n\n"
            if view["status"] in ("done", "failed"):
                return
            await asyncio.sleep(SSE_POLL_SECONDS)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/notebooks/{notebook_id}/sources/{source_id}/reindex",
    response_model=IndexProgressView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def reindex_source(
    notebook_id: str,
    source_id: str,
    background_tasks: BackgroundTasks,
    service: NotebookService = Depends(get_notebook_service),
    indexing: IndexingService = Depends(get_indexing_service),
) -> IndexProgressView:
    registry = get_progress_registry()

    def run() -> IndexProgressView:
        record = service.get_source(notebook_id, source_id)
        # 진행 레지스트리를 queued로 리셋(정지/실패한 인덱싱도 이 경로로 복구).
        indexing.register(record)
        # repo 소스면 재클론으로 최신 스냅샷 갱신 후 재인덱싱(resync_repo=True).
        background_tasks.add_task(
            indexing.index_source, notebook_id, source_id, resync_repo=True
        )
        view = registry.get(source_id)
        assert view is not None  # register 직후이므로 항상 존재
        return IndexProgressView.from_view(view)

    return http_error(run, NOT_FOUND)


# --- 산출물(artifacts) ---


@router.post(
    "/notebooks/{notebook_id}/artifacts",
    response_model=ArtifactView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def generate_artifact(
    notebook_id: str,
    request: GenerateArtifactRequest,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactView:
    # 동기 처리. LLM 호출은 짧게 유지하며, 키가 없으면 결정론/골격으로 즉시 반환한다.
    def run() -> ArtifactView:
        record = service.generate(
            notebook_id, type=request.type, source_ids=request.source_ids
        )
        return ArtifactView.from_record(record)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.post(
    "/notebooks/{notebook_id}/artifacts/note",
    response_model=ArtifactView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def create_note(
    notebook_id: str,
    request: CreateNoteRequest,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactView:
    def run() -> ArtifactView:
        record = service.create_note(
            notebook_id, content=request.content, title=request.title
        )
        return ArtifactView.from_record(record)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.get(
    "/notebooks/{notebook_id}/artifacts",
    response_model=ArtifactListResponse,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def list_artifacts(
    notebook_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactListResponse:
    def run() -> ArtifactListResponse:
        records = service.list_artifacts(notebook_id)
        return ArtifactListResponse(
            artifacts=[ArtifactView.from_record(record) for record in records]
        )

    return http_error(run, NOT_FOUND)


@router.get(
    "/notebooks/{notebook_id}/artifacts/{artifact_id}",
    response_model=ArtifactView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def get_artifact(
    notebook_id: str,
    artifact_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactView:
    return http_error(
        lambda: ArtifactView.from_record(
            service.get_artifact(notebook_id, artifact_id)
        ),
        NOT_FOUND,
    )


@router.patch(
    "/notebooks/{notebook_id}/artifacts/{artifact_id}",
    response_model=ArtifactView,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def update_artifact(
    notebook_id: str,
    artifact_id: str,
    request: UpdateArtifactRequest,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactView:
    def run() -> ArtifactView:
        record = service.update_artifact(
            notebook_id,
            artifact_id,
            title=request.title,
            content=request.content,
        )
        return ArtifactView.from_record(record)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.delete(
    "/notebooks/{notebook_id}/artifacts/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=BAD_REQUEST_RESPONSE,
    dependencies=[Depends(get_current_claims)],
)
def delete_artifact(
    notebook_id: str,
    artifact_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> Response:
    http_error(
        lambda: service.delete_artifact(notebook_id, artifact_id), NOT_FOUND
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
