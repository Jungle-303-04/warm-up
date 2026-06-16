# TeamLog 프론트엔드 / 백엔드 / DB 흐름도

현재 TeamLog는 크게 인증, 캘린더 조회, 회의/회고 생성, 상세 조회/수정, AI 챗봇 RAG 흐름으로 나뉩니다.

## 전체 구조

```mermaid
flowchart LR
  U[사용자] --> FE[Frontend React]
  FE --> API[Backend FastAPI]
  API --> DB[(PostgreSQL + pgvector)]
  API --> OAI[OpenAI API]

  DB --> API
  API --> FE
  FE --> U
```

## 1. 로그인 흐름

```mermaid
sequenceDiagram
  participant U as 사용자
  participant FE as Frontend
  participant BE as Backend
  participant DB as DB

  U->>FE: 이메일/비밀번호 입력
  FE->>BE: POST /auth/login
  BE->>DB: users에서 이메일 조회
  DB-->>BE: user 정보 반환
  BE->>BE: 비밀번호 검증
  BE-->>FE: access_token 반환
  FE->>FE: localStorage에 token 저장
  FE->>BE: GET /auth/me
  BE-->>FE: 현재 사용자 정보(id, nickname)
  FE->>U: 캘린더 화면 표시
```

프론트는 로그인 후 `currentUser`를 React state에 저장합니다.

```ts
currentUser = {
  id,
  email,
  nickname,
  created_at
}
```

이 값은 상단바 닉네임 표시와 회의/회고 수정 권한 판단에 사용됩니다.

## 2. 캘린더 조회 흐름

```mermaid
sequenceDiagram
  participant FE as Frontend CalendarPage
  participant BE as Backend /pages/calendar
  participant DB as pages table

  FE->>BE: GET /pages/calendar?year=2026&month=6
  BE->>DB: 해당 월의 모든 pages 조회
  DB-->>BE: 회의/회고 목록 반환
  BE-->>FE: CalendarPageItem[]
  FE->>FE: FullCalendar 이벤트로 변환
  FE->>FE: selectedDate 기준 오른쪽 패널 필터링
```

현재 캘린더는 팀 전체 기록을 보여줍니다.

```python
# 예전 개인 조회 조건은 제거됨
# .where(Page.author_id == current_user.id)
```

`pages` 테이블은 회의/회고의 기본 정보를 저장합니다.

```text
pages
- id
- type: MEETING / RETROSPECTIVE
- title
- date
- start_time
- end_time
- author_id
- participants
```

오른쪽 패널은 `selectedDate`와 같은 날짜만 보여줍니다.

```ts
calendarItems.filter((item) => item.date === selectedDate)
```

## 3. 오늘 버튼 흐름

```mermaid
flowchart TD
  A[오늘 버튼 클릭] --> B[FullCalendar today 실행]
  B --> C[캘린더가 오늘 날짜가 있는 달로 이동]
  A --> D[selectedDate = todayKey]
  D --> E[오른쪽 패널도 오늘 날짜로 변경]
```

오늘 버튼은 캘린더만 이동시키지 않고, 오른쪽 패널의 선택 날짜도 오늘로 바꿉니다.

## 4. 회의/회고 생성 흐름

```mermaid
sequenceDiagram
  participant U as 사용자
  participant FE as Frontend
  participant BE as Backend
  participant DB as DB
  participant OAI as OpenAI

  U->>FE: 새로 만들기 클릭
  FE->>FE: selectedDate가 오늘인지 확인
  alt 오늘 아님
    FE-->>U: 오늘 날짜에만 작성 가능 alert
  else 오늘
    FE-->>U: 작성 모달 표시
    U->>FE: 제목/참여자/본문 입력
    FE->>BE: POST /pages
    BE->>BE: payload.date == 오늘인지 검사
    BE->>DB: pages 저장
    BE->>DB: page_blocks 저장
    BE->>OAI: embedding 생성 요청
    OAI-->>BE: embedding 반환
    BE->>DB: page_embeddings 저장
    BE-->>FE: 생성된 PageResponse 반환
    FE->>BE: 캘린더 목록 다시 조회
  end
```

생성은 오늘 날짜에만 가능합니다.

프론트에서 한 번 막습니다.

```ts
selectedDate === todayKey
```

백엔드에서도 한 번 더 막습니다.

```python
if payload.date != today:
    raise HTTPException(400)
```

그래서 API를 직접 호출해도 오늘이 아닌 날짜로는 생성할 수 없습니다.

## 5. 오른쪽 패널 카드 표시 흐름

```mermaid
flowchart TD
  A[calendarItems] --> B[selectedDate 기준 필터링]
  B --> C[회의록 목록]
  B --> D[회고록 목록]

  C --> E{item.author_id == currentUser.id?}
  D --> F{item.author_id == currentUser.id?}

  E -->|예| G[연필 아이콘 표시]
  E -->|아니오| H[> 아이콘 표시]

  F -->|예| I[연필 아이콘 표시]
  F -->|아니오| J[> 아이콘 표시]
```

오른쪽 패널 카드에서는 다음처럼 보입니다.

```text
내가 쓴 기록: 연필 아이콘
팀원이 쓴 기록: > 아이콘
```

판단 기준은 프론트에서 현재 로그인 사용자와 작성자를 비교하는 것입니다.

```ts
currentUser?.id === item.author_id
```

## 6. 상세 조회 / 수정 흐름

```mermaid
sequenceDiagram
  participant U as 사용자
  participant FE as PageDetailModal
  participant BE as Backend
  participant DB as DB

  U->>FE: 오른쪽 패널 카드 클릭
  FE->>BE: GET /pages/{page_id}
  BE->>DB: Page + blocks + author 조회
  DB-->>BE: 상세 데이터 반환
  BE-->>FE: PageResponse

  FE->>FE: currentUser.id와 page.author_id 비교

  alt 작성자 본인
    FE-->>U: 수정 가능한 폼 표시
    U->>FE: 내용 수정 후 저장
    FE->>BE: PATCH /pages/{page_id}
    BE->>BE: check_page_owner()
    BE->>DB: pages 수정
    BE->>DB: 기존 page_blocks 삭제 후 새 blocks 저장
    BE->>DB: embeddings 갱신
    BE-->>FE: 수정된 PageResponse
    FE->>BE: 캘린더 목록 다시 조회
  else 다른 팀원
    FE-->>U: 읽기 전용 상세 화면 표시
    FE-->>U: 저장 버튼 없음
  end
```

정책은 다음과 같습니다.

```text
조회: 팀원 모두 가능
수정: 작성자만 가능
삭제: 작성자만 가능
```

프론트는 버튼을 숨기지만, 실제 권한은 백엔드가 막습니다.

```python
check_page_owner(page, current_user)
```

다른 사람이 API로 직접 `PATCH`를 보내도 `403`이 됩니다.

## 7. DB 테이블 관계

```mermaid
erDiagram
  users ||--o{ pages : writes
  pages ||--o{ page_blocks : has
  pages ||--o{ comments : has
  pages ||--o{ page_embeddings : indexed_as
  users ||--o{ comments : writes
  users ||--o{ chat_sessions : owns
  chat_sessions ||--o{ chat_messages : has

  users {
    int id PK
    string email
    string password_hash
    string nickname
    datetime created_at
  }

  pages {
    int id PK
    enum type
    string title
    date date
    time start_time
    time end_time
    int author_id FK
    json participants
    text ai_summary
    datetime created_at
    datetime updated_at
  }

  page_blocks {
    int id PK
    int page_id FK
    enum type
    text content
    bool checked
    int order_index
    datetime created_at
    datetime updated_at
  }

  page_embeddings {
    int id PK
    int page_id FK
    int chunk_index
    text chunk_text
    vector embedding
    datetime created_at
  }
```

## 8. AI 챗봇 / RAG 흐름

```mermaid
sequenceDiagram
  participant U as 사용자
  participant FE as Chatbot
  participant BE as Backend AI
  participant DB as page_embeddings
  participant OAI as OpenAI

  U->>FE: 질문 입력
  FE->>BE: 질문 전송
  BE->>OAI: 질문 embedding 생성
  OAI-->>BE: 질문 vector 반환
  BE->>DB: page_embeddings와 유사도 검색
  DB-->>BE: 관련 회의/회고 chunk 반환
  BE->>OAI: 참고 기록 + 질문 전달
  OAI-->>BE: 답변 생성
  BE-->>FE: 답변 + 참고 기록 반환
  FE-->>U: 챗봇 답변 표시
```

현재 RAG는 팀 전체 기록을 대상으로 검색합니다.

```python
# 제거됨
# .where(Page.author_id == current_user_id)
```

그래서 팀원이 만든 회의/회고도 AI가 참고할 수 있습니다.

## 현재 정책 요약

```text
로그인
→ JWT 토큰 저장
→ /auth/me로 현재 사용자 확인

캘린더
→ 팀 전체 회의/회고 조회

새로 만들기
→ 오늘 날짜만 가능
→ 작성자는 현재 로그인 사용자

오른쪽 패널
→ 선택 날짜의 회의/회고 표시
→ 내가 쓴 기록은 연필 아이콘
→ 남이 쓴 기록은 > 아이콘

상세/수정
→ 모두 조회 가능
→ 작성자만 수정 가능

AI 챗봇
→ 팀 전체 임베딩 기록 기반 답변
```

한 줄로 말하면, TeamLog는 팀 전체 회의/회고를 함께 보고, 작성자만 수정하며, AI는 팀 전체 기록을 검색해서 답변하는 구조입니다.
