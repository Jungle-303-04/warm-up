# 민정 Board 클래스 UML

이 UML은 `origin/minjeong`의 현재 구현을 기준으로 한다. 주요 근거 파일은
`backend/app/db/base.py`와 `backend/app/domains/board/model.py`다.

## 클래스 UML

![민정 Board 클래스 UML](./assets/class-uml.svg)

## Mermaid 원본

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

## 해석 메모

- `Board`는 모든 게시글의 공통 부모 테이블 역할을 한다. 코드 주석상
  `board_type` 값 `1`은 `ScheduleBoardDetail`, 값 `2`는
  `ProceedingsBoardDetail`로 연결될 의도다. 아직 이 매핑을 강제하는 DB
  제약은 없다.
- `ScheduleBoardDetail`과 `ProceedingsBoardDetail`은 `board_id`를 기본키이자
  외래키로 사용한다. 따라서 한 Board는 각 상세 테이블에 최대 1개의 상세
  row만 가질 수 있다.
- `BoardCarbonCopy`, `BoardAssignee`, `BoardParticipant`는 `(board_id,
  user_id)` 복합 기본키를 가진 Board-User 역할 연결 테이블이다.
- 모델은 `ForeignKey("user.id")`를 참조하지만, `origin/minjeong`에는 아직
  구현된 `User` ORM 클래스나 `user` 테이블 정의가 없다.
- 외래키는 선언되어 있지만 SQLAlchemy `relationship()` 속성은 아직
  정의되어 있지 않다.
