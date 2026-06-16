from fastapi import APIRouter, Depends, Query, Response, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.notebooks.api.schemas import (
    CreateNotebookRequest,
    CreateSourceRequest,
    FileResponse,
    NotebookDetailView,
    NotebookListResponse,
    NotebookView,
    SourceDetailView,
    SourceListResponse,
    SourceView,
    TreeResponse,
    UpdateNotebookRequest,
)
from app.notebooks.application.service import NotebookService
from app.notebooks.dependencies import get_notebook_service

router = APIRouter()

NOT_FOUND = {KeyError: status.HTTP_404_NOT_FOUND}
NOT_FOUND_OR_BAD_REQUEST = {
    KeyError: status.HTTP_404_NOT_FOUND,
    ValueError: status.HTTP_400_BAD_REQUEST,
}


# --- 노트북 ---


@router.post(
    "/notebooks",
    response_model=NotebookView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
)
def create_notebook(
    request: CreateNotebookRequest,
    service: NotebookService = Depends(get_notebook_service),
) -> NotebookView:
    def run() -> NotebookView:
        record = service.create_notebook(title=request.title, summary=request.summary)
        return NotebookView.from_record(record, source_count=0)

    return http_error(run, {ValueError: status.HTTP_400_BAD_REQUEST})


@router.get("/notebooks", response_model=NotebookListResponse)
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
)
def delete_notebook(
    notebook_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> Response:
    http_error(lambda: service.delete_notebook(notebook_id), NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- 소스 ---


@router.post(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceView,
    status_code=status.HTTP_201_CREATED,
    responses=BAD_REQUEST_RESPONSE,
)
def create_source(
    notebook_id: str,
    request: CreateSourceRequest,
    service: NotebookService = Depends(get_notebook_service),
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
        return SourceView.from_record(record)

    return http_error(run, NOT_FOUND_OR_BAD_REQUEST)


@router.get(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceListResponse,
    responses=BAD_REQUEST_RESPONSE,
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
)
def delete_source(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> Response:
    http_error(lambda: service.delete_source(notebook_id, source_id), NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- repo 트리/파일 ---


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/tree",
    response_model=TreeResponse,
    responses=BAD_REQUEST_RESPONSE,
)
def get_source_tree(
    notebook_id: str,
    source_id: str,
    service: NotebookService = Depends(get_notebook_service),
) -> TreeResponse:
    return http_error(
        lambda: TreeResponse(tree=service.get_source_tree(notebook_id, source_id)),
        NOT_FOUND_OR_BAD_REQUEST,
    )


@router.get(
    "/notebooks/{notebook_id}/sources/{source_id}/file",
    response_model=FileResponse,
    responses=BAD_REQUEST_RESPONSE,
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
