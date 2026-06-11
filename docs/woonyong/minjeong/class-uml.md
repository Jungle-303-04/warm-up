# Minjeong Board Class UML

This UML reflects the implemented SQLAlchemy models on `origin/minjeong`, based
on `backend/app/db/base.py` and `backend/app/domains/board/model.py`.

## Class UML

```mermaid
classDiagram
    direction LR

    class Base {
        <<SQLAlchemy DeclarativeBase>>
    }

    class IdMixin {
        <<mixin>>
        +int id PK autoincrement
    }

    class TimestampMixin {
        <<mixin>>
        +datetime created_at not null default utcnow
        +datetime updated_at not null default utcnow onupdate utcnow
    }

    class Board {
        <<table: board>>
        +int id PK autoincrement
        +datetime created_at not null default utcnow
        +datetime updated_at not null default utcnow onupdate utcnow
        +int board_type not null
        +str title not null
        +text content not null
        +str? tag nullable
        +int user_id FK user.id not null
    }

    class ScheduleBoardDetail {
        <<table: schedule_board_detail>>
        +int board_id PK FK board.id not null
        +datetime start_at not null default utcnow
        +datetime end_at not null default utcnow
        +int importance not null
        +constraint importance between 1 and 10
    }

    class ScheduleBoardTask {
        <<table: schedule_board_task>>
        +int id PK autoincrement
        +int board_id FK board.id not null
        +str task_name not null
        +int task_status not null
        +constraint task_status between 1 and 4
    }

    class ProceedingsBoardDetail {
        <<table: proceedings_board_detail>>
        +int board_id PK FK board.id not null
        +datetime meeting_date not null default utcnow
    }

    class BoardCarbonCopy {
        <<table: board_carbon_copy>>
        +int board_id PK FK board.id not null
        +int user_id PK FK user.id not null
    }

    class BoardAssignee {
        <<table: board_assignee>>
        +int board_id PK FK board.id not null
        +int user_id PK FK user.id not null
    }

    class BoardParticipant {
        <<table: board_participant>>
        +int board_id PK FK board.id not null
        +int user_id PK FK user.id not null
    }

    class User {
        <<external unresolved table: user>>
        +int id referenced by FK
    }

    Base <|-- Board
    Base <|-- ScheduleBoardDetail
    Base <|-- ScheduleBoardTask
    Base <|-- ProceedingsBoardDetail
    Base <|-- BoardCarbonCopy
    Base <|-- BoardAssignee
    Base <|-- BoardParticipant

    IdMixin <|.. Board
    TimestampMixin <|.. Board
    IdMixin <|.. ScheduleBoardTask

    Board "1" <-- "0..1" ScheduleBoardDetail : board_id
    Board "1" <-- "0..*" ScheduleBoardTask : board_id
    Board "1" <-- "0..1" ProceedingsBoardDetail : board_id
    Board "1" <-- "0..*" BoardCarbonCopy : board_id
    Board "1" <-- "0..*" BoardAssignee : board_id
    Board "1" <-- "0..*" BoardParticipant : board_id

    User "1" <-- "0..*" Board : user_id
    User "1" <-- "0..*" BoardCarbonCopy : user_id
    User "1" <-- "0..*" BoardAssignee : user_id
    User "1" <-- "0..*" BoardParticipant : user_id
```

## Notes

- `Board` is the common parent table for board records. The code comments map
  `board_type` value `1` to `ScheduleBoardDetail` and `2` to
  `ProceedingsBoardDetail`; no database constraint enforces that mapping yet.
- `ScheduleBoardDetail` and `ProceedingsBoardDetail` use `board_id` as both the
  primary key and foreign key, so each board can have at most one matching detail
  row of each type.
- `BoardCarbonCopy`, `BoardAssignee`, and `BoardParticipant` are join tables with
  composite primary keys of `(board_id, user_id)`.
- The models reference `ForeignKey("user.id")`, but `origin/minjeong` does not
  include an implemented `User` ORM class or `user` table definition.
- The implementation declares foreign keys but does not define SQLAlchemy
  `relationship()` attributes.
