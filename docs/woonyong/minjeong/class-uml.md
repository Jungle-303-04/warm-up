# Minjeong Board Class UML

This UML snapshot reflects the current `minjeong` branch implementation and the
next minimal classes needed to make the scaffold executable.

## Current Implementation Signal

- `backend/app/main.py` includes `board_router` under `/boards`.
- `backend/app/domains/board/router.py` is intended to work like a controller.
- `backend/app/domains/board/service.py` is intended to hold business logic.
- `backend/app/domains/board/repository.py` is intended to hold DB access logic.
- `backend/app/domains/board/model.py` is intended to define the SQLAlchemy table model.
- `backend/app/domains/board/schema.py` already imports `BaseModel`, but DTOs are not defined yet.

## Class UML

```mermaid
classDiagram
    direction LR

    class FastAPIApp {
        +include_router(board_router, boards_prefix)
        +root() dict
    }

    class BoardRouter {
        <<module>>
        +router APIRouter
        +list_boards() list~BoardRead~
        +create_board(payload) BoardRead
        +get_board(board_id) BoardRead
    }

    class BoardService {
        <<module>>
        +list_boards() list~BoardRead~
        +create_board(payload) BoardRead
        +get_board(board_id) BoardRead
    }

    class BoardRepository {
        <<module>>
        +find_all() list~BoardModel~
        +find_by_id(board_id) BoardModel
        +save(board) BoardModel
    }

    class BoardModel {
        <<model>>
        +int id
        +str title
        +str content
        +int project_id
        +int author_id
        +datetime created_at
        +datetime updated_at
    }

    class BoardCreate {
        <<schema>>
        +str title
        +str content
        +int project_id
    }

    class BoardRead {
        <<schema>>
        +int id
        +str title
        +str content
        +int project_id
        +int author_id
    }

    FastAPIApp --> BoardRouter : includes
    BoardRouter --> BoardService : delegates request handling
    BoardService --> BoardRepository : coordinates persistence
    BoardRepository --> BoardModel : maps table rows
    BoardRouter ..> BoardCreate : receives
    BoardRouter ..> BoardRead : returns
    BoardService ..> BoardCreate : validates input shape
    BoardService ..> BoardRead : returns response shape
```

## Current Gap

`backend/app/main.py` imports `router` from `backend/app/domains/board/router.py`,
but `router.py` does not define an `APIRouter` instance yet. The next smallest
unblocking step is to add `router = APIRouter()` and one temporary endpoint so the
FastAPI app can boot.

## Recommended Next Step

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_boards():
    return []
```

After that, Minjeong can fill in `BoardCreate`, `BoardRead`, `BoardService`, and
`BoardRepository` one layer at a time.
