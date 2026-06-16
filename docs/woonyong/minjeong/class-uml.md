# 민정 warm-up 현재 클래스 UML

이 문서는 `origin/minjeong`의 `842d495 fix: skip duplicate RAG index storage`
기준 클래스 구조를 요약한다. 코드 클래스명과 주요 필드명은 실제 구현명을
유지하고, 해석 문장은 한국어로 적는다.

기준 파일은 `backend/app/container.py`, `backend/app/main.py`,
`backend/app/board`, `backend/app/auth`, `backend/app/github`,
`backend/app/rag`, `backend/app/agent` 하위 구현이다.

## 전체 모듈 조립 구조

```mermaid
classDiagram
    direction LR

    class FastAPIApp {
        <<main.py>>
        +lifespan()
        +include_router(board_router)
        +include_router(auth_router)
        +include_router(rag_router)
        +include_router(agent_router)
    }

    class AppContainer {
        <<dependency_injector>>
        +db_session
        +board_service
        +auth_service
        +github_service
        +rag_index_service
        +rag_answer_service
        +agent_chat_service
    }

    class BoardService {
        +create_board(db, create_request)
        +get_boards(db, search_params)
        +get_board(db, board_id)
        +update_board(db, board_id, update_request)
        +delete_board(db, board_id)
    }

    class AuthService {
        +build_github_login_url()
        +handle_github_callback(code)
        +get_current_user(token)
    }

    class GitHubService {
        +get_file(owner, repo, path, ref)
    }

    class RagIndexService {
        +index_repository_and_store(request, user)
        +index_and_store(result)
        +find_existing_run(repository_full_name, branch, commit_sha)
        +build_stored_index_response(run, reused)
    }

    class RagAnswerService {
        +answer(request, user)
    }

    class AgentChatService {
        +create_session(request)
        +get_session(session_id)
        +send_message(session_id, request)
    }

    FastAPIApp --> AppContainer : uses
    AppContainer --> BoardService
    AppContainer --> AuthService
    AppContainer --> GitHubService
    AppContainer --> RagIndexService
    AppContainer --> RagAnswerService
    AppContainer --> AgentChatService
```

해석:

- `main.py`는 router 연결과 startup DB/vector DB 확인을 담당한다.
- `AppContainer`는 service, repository, GitHub client, OpenAI/Chroma adapter를 조립한다.
- 현재 구조는 `domains/*`에서 top-level `board`, `auth`, `github`, `rag`,
  `agent` module로 이동했다.

## Board/Auth SQL 모델

```mermaid
classDiagram
    direction LR

    class Base {
        <<SQLAlchemy DeclarativeBase>>
    }

    class IdMixin {
        +id
    }

    class TimestampMixin {
        +created_at
        +updated_at
    }

    class User {
        <<table: user>>
        +id
    }

    class GitHubOAuthAccount {
        <<table: github_oauth_account>>
        +int user_id
        +int github_user_id
        +str login
        +str? name
        +str? email
        +str? avatar_url
        +str access_token
        +str token_type
        +str? scope
        +datetime? token_expires_at
    }

    class Board {
        <<table: board>>
        +int board_type
        +str title
        +str content
        +str? tag
        +int user_id
    }

    class ScheduleBoardDetail {
        <<table: schedule_board_detail>>
        +int board_id
        +datetime start_at
        +datetime end_at
        +int importance
    }

    class ScheduleBoardTask {
        <<table: schedule_board_task>>
        +int board_id
        +str task_name
        +int task_status
    }

    class ProceedingsBoardDetail {
        <<table: proceedings_board_detail>>
        +int board_id
        +datetime meeting_date
    }

    class BoardCarbonCopy {
        <<table: board_carbon_copy>>
        +int board_id
        +int user_id
    }

    class BoardAssignee {
        <<table: board_assignee>>
        +int board_id
        +int user_id
    }

    class BoardParticipant {
        <<table: board_participant>>
        +int board_id
        +int user_id
    }

    Base <|-- User
    Base <|-- GitHubOAuthAccount
    Base <|-- Board
    Base <|-- ScheduleBoardDetail
    Base <|-- ScheduleBoardTask
    Base <|-- ProceedingsBoardDetail
    Base <|-- BoardCarbonCopy
    Base <|-- BoardAssignee
    Base <|-- BoardParticipant

    IdMixin <|.. User
    IdMixin <|.. GitHubOAuthAccount
    IdMixin <|.. Board
    IdMixin <|.. ScheduleBoardTask
    TimestampMixin <|.. GitHubOAuthAccount
    TimestampMixin <|.. Board

    User "1" <-- "0..*" Board : user_id
    User "1" <-- "0..1" GitHubOAuthAccount : user_id
    Board "1" <-- "0..1" ScheduleBoardDetail : board_id
    ScheduleBoardDetail "1" <-- "0..*" ScheduleBoardTask : board_id
    Board "1" <-- "0..1" ProceedingsBoardDetail : board_id
    Board "1" <-- "0..*" BoardCarbonCopy : board_id
    Board "1" <-- "0..*" BoardAssignee : board_id
    Board "1" <-- "0..*" BoardParticipant : board_id
    User "1" <-- "0..*" BoardCarbonCopy : user_id
    User "1" <-- "0..*" BoardAssignee : user_id
    User "1" <-- "0..*" BoardParticipant : user_id
```

해석:

- Board 모델은 초기 작업의 중심이고, `board_type`에 따라 일정/회의록 detail을 분리한다.
- GitHub OAuth 정보는 `GitHubOAuthAccount`로 `User`와 1:1에 가깝게 묶인다.
- 아직 `relationship()`이 풍부하게 잡힌 구조라기보다는 FK와 repository query 중심 구조다.

## RAG SQL/vector 저장 구조

```mermaid
classDiagram
    direction LR

    class RagIndexRun {
        <<table: rag_index_run>>
        +str? repository_full_name
        +str? branch
        +str commit_sha
        +datetime indexed_at
        +int total_files
        +int indexed_files
        +int skipped_files
        +int total_chunks
    }

    class RagFileSnapshot {
        <<table: rag_file_snapshot>>
        +int run_id
        +str path
        +str? name
        +str? sha
        +str commit_sha
        +str language
        +str source_type
        +str content_hash
        +str citation
        +int? size
        +str? html_url
    }

    class RagChunk {
        <<table: rag_chunk>>
        +int run_id
        +int file_snapshot_id
        +str external_chunk_id
        +str chunk_hash
        +int chunk_index
        +str path
        +str commit_sha
        +str language
        +str source_type
        +str chunk_type
        +str? symbol_name
        +int? start_line
        +int? end_line
        +str citation
        +str chunk_text
        +dict metadata_json
        +bool direct_implementation_evidence
    }

    class RagSkippedFile {
        <<table: rag_skipped_file>>
        +int run_id
        +str path
        +str reason
    }

    class RagSqlRepository {
        +save_index_result(result)
        +find_latest_run(repository_full_name, branch)
        +find_exact_run(repository_full_name, branch, commit_sha)
        +get_run_detail(run_id)
        +search_chunks(...)
    }

    class RagVectorRepository {
        +save_chunks(run_id, chunks)
        +search(query_embedding, filters)
        +count_run_chunks(run_id)
    }

    RagIndexRun "1" <-- "0..*" RagFileSnapshot : run_id
    RagIndexRun "1" <-- "0..*" RagChunk : run_id
    RagIndexRun "1" <-- "0..*" RagSkippedFile : run_id
    RagFileSnapshot "1" <-- "0..*" RagChunk : file_snapshot_id
    RagSqlRepository --> RagIndexRun
    RagSqlRepository --> RagFileSnapshot
    RagSqlRepository --> RagChunk
    RagSqlRepository --> RagSkippedFile
    RagVectorRepository ..> RagChunk : metadata copy
```

해석:

- SQL은 인덱싱 실행 이력, 파일 스냅샷, chunk 원문, skip 사유를 보관한다.
- Chroma vector DB는 `RagChunk`의 embedding 검색용 복제 데이터를 가진다.
- 최신 커밋은 `repository_full_name + branch + commit_sha` 기준 기존 run을 찾아
  중복 저장을 건너뛰지만, DB unique constraint는 아직 없다.

## RAG 인덱싱 파이프라인

```mermaid
classDiagram
    direction LR

    class GitHubRepositoryClient {
        +get_repository_tree(owner, repo, ref)
        +get_file_content(owner, repo, path, ref)
        +resolve_ref(owner, repo, ref)
    }

    class GitHubFileSnapshotBuilder {
        +build(file_response)
    }

    class GitHubContentDecoder {
        +decode(content, encoding)
    }

    class GitHubLanguageDetector {
        +detect(path)
    }

    class GitHubFileCitationBuilder {
        +build(repository, path, commit_sha, start_line, end_line)
    }

    class GitHubRagPipelineService {
        +index_repository(request)
        +build_artifacts(snapshots)
    }

    class SnapshotValidator {
        +validate(snapshot)
    }

    class ChunkingService {
        +chunk_snapshot(snapshot)
    }

    class ChunkerRegistry {
        +get(language)
    }

    class LanguageChunker {
        <<abstract>>
        +chunk(snapshot)
    }

    class PythonChunker {
        +chunk(snapshot)
    }

    class MarkdownChunker {
        +chunk(snapshot)
    }

    class TextSplitter {
        +split(text)
    }

    class PythonChunkClassifier {
        +classify(node)
    }

    class ChunkFactory {
        +create(...)
    }

    class ChunkIdentityService {
        +build_chunk_id(...)
        +build_chunk_hash(...)
    }

    class ChunkCitationService {
        +build(...)
    }

    class OpenAIEmbeddingService {
        +embed_texts(texts)
    }

    class RagIndexService {
        +index_repository_and_store(request, user)
        +index_and_store(result)
        +find_existing_run(repository_full_name, branch, commit_sha)
    }

    RagIndexService --> GitHubRagPipelineService
    RagIndexService --> RagSqlRepository
    RagIndexService --> RagVectorRepository
    RagIndexService --> OpenAIEmbeddingService
    GitHubRagPipelineService --> GitHubRepositoryClient
    GitHubRagPipelineService --> GitHubFileSnapshotBuilder
    GitHubFileSnapshotBuilder --> GitHubContentDecoder
    GitHubFileSnapshotBuilder --> GitHubLanguageDetector
    GitHubFileSnapshotBuilder --> GitHubFileCitationBuilder
    GitHubRagPipelineService --> SnapshotValidator
    GitHubRagPipelineService --> ChunkingService
    ChunkingService --> ChunkerRegistry
    ChunkerRegistry --> LanguageChunker
    LanguageChunker <|-- PythonChunker
    LanguageChunker <|-- MarkdownChunker
    PythonChunker --> PythonChunkClassifier
    PythonChunker --> TextSplitter
    MarkdownChunker --> TextSplitter
    PythonChunker --> ChunkFactory
    MarkdownChunker --> ChunkFactory
    ChunkFactory --> ChunkIdentityService
    ChunkFactory --> ChunkCitationService
```

해석:

- GitHub 파일 수집과 RAG chunk 생성이 별도 service/domain class로 분해됐다.
- Python과 Markdown chunker를 분리한 점은 코드 RAG 품질에서 중요한 결정이다.
- `RagIndexService`가 중복 run 확인, pipeline 실행, SQL/vector 저장을 묶는다.

## RAG 답변 그래프와 Agent scaffold

```mermaid
classDiagram
    direction LR

    class RagAskRequestDTO {
        +str repository_full_name
        +str branch
        +str? commit_sha
        +str question
        +int top_k
    }

    class RagAnswerService {
        +answer(request, user)
    }

    class RagAnswerGraph {
        +build_graph()
        +retrieve_vector(state)
        +route_by_evidence(state)
        +generate_answer(state)
        +build_no_evidence_answer(state)
        +build_response(state)
    }

    class RagLlm {
        +answer(question, evidence)
    }

    class PromptBuilder {
        +build(question, evidence)
    }

    class EvidenceFormatter {
        +format(evidence)
    }

    class OpenAIGenerator {
        +generate(prompt)
    }

    class AgentChatService {
        +create_session(request)
        +get_session(session_id)
        +send_message(session_id, request)
    }

    class InMemoryChatStore {
        +create_session(...)
        +get_session(session_id)
        +append_message(...)
    }

    class EchoAgentResponder {
        +respond(turns)
    }

    RagAnswerService --> RagAnswerGraph
    RagAnswerService --> RagSqlRepository : find run
    RagAnswerGraph --> RagVectorRepository : search with filters
    RagAnswerGraph --> RagLlm : when evidence exists
    RagLlm --> PromptBuilder
    RagLlm --> EvidenceFormatter
    RagLlm --> OpenAIGenerator
    RagAskRequestDTO --> RagAnswerService
    AgentChatService --> InMemoryChatStore
    AgentChatService --> EchoAgentResponder
```

해석:

- `/rag/ask`는 repository/branch/commit 범위로 SQL run을 찾고, 같은 범위의
  vector evidence를 검색한 뒤 답변한다.
- `RagAnswerGraph`는 evidence가 없을 때 별도 no-evidence 응답을 만들도록 분기한다.
- `AgentChatService`는 현재 echo responder 기반 scaffold라, RAG answer graph와
  같은 수준의 agent runtime으로 보면 안 된다.

## 현재 구조 평가

- 좋은 점: Board, Auth, GitHub, RAG, Agent의 책임을 module 단위로 나누기 시작했다.
- 좋은 점: RAG chunk identity, citation, SQL 저장, vector 저장, commit scope를 모두 고려했다.
- 좋은 점: LangGraph를 통해 evidence 유무 분기를 코드 구조로 드러냈다.
- 위험: RAG indexing, vector 저장, `/rag/ask`, auth callback에 대한 테스트가 부족하다.
- 위험: SQL transaction과 vector DB 저장이 함께 실패/성공해야 하는데 보상 전략이 명확하지 않다.
- 위험: 중복 저장 방지는 application check만으로는 동시 요청 race condition을 막기 어렵다.
- 개선: `repository_full_name + branch + commit_sha` unique constraint, idempotency test,
  SQL/vector partial failure test, `.env.example`, agent/RAG 경계 문서화가 필요하다.
