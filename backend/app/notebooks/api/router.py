from fastapi import APIRouter, Depends, Query, Response, status

from app.api.errors import http_error
from app.api.responses import BAD_REQUEST_RESPONSE
from app.auth.dependencies import get_current_claims
from app.notebooks.api.schemas import (
    ChatMessageListResponse,
    ChatMessageView,
    ChatRequest,
    ChatResponse,
    CreateNotebookRequest,
    CreateSourceRequest,
    FileResponse,
    NotebookDetailView,
    NotebookListResponse,
    NotebookView,
    SourceDetailView,
    SourceListResponse,
    SourceView,
    TreeNode,
    TreeResponse,
    UpdateNotebookRequest,
)
from app.notebooks.application.chat_service import ChatService
from app.notebooks.application.service import NotebookService
from app.notebooks.dependencies import get_notebook_chat_service, get_notebook_service

router = APIRouter()

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
) -> Response:
    http_error(lambda: service.delete_source(notebook_id, source_id), NOT_FOUND)
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
