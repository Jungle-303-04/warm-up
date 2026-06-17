import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from jwt import InvalidTokenError

from .routers.ai import router as ai_router
from .routers.integrations_github import router as github_router
from .routers.integrations_notion import router as notion_router
from .schemas import (
    CommentCreate,
    CommentRead,
    CommentUpdate,
    DBHealthResponse,
    LoginRequest,
    PostCreate,
    PostListResponse,
    PostRead,
    PostUpdate,
    SignupRequest,
    TokenResponse,
    UserRead,
)
from .security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://frontend-60c58s9bl-hydromel.vercel.app",
]
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notion_router)
app.include_router(github_router)
app.include_router(ai_router)


@app.get("/health")
def health():
    return "ok"


@app.get("/db-health", response_model=DBHealthResponse)
def db_health():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()

    return DBHealthResponse(status="ok", db="ok", result=row[0])


@app.post("/auth/signup", response_model=UserRead, status_code=201)
def signup(signup_data: SignupRequest):
    email = signup_data.email.strip().lower()
    nickname = signup_data.nickname.strip()
    github_username = (
        signup_data.github_username.strip()
        if signup_data.github_username
        else None
    )

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname is required")

    hashed_password = get_password_hash(signup_data.password)

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            existing_user = cur.fetchone()

            if existing_user is not None:
                raise HTTPException(status_code=409, detail="Email already exists")

            cur.execute(
                """
                INSERT INTO users (
                    email,
                    password_hash,
                    nickname,
                    github_username
                )
                VALUES (%s, %s, %s, %s)
                RETURNING
                    id,
                    email,
                    nickname,
                    github_username,
                    role,
                    created_at
                """,
                (
                    email,
                    hashed_password,
                    nickname,
                    github_username,
                ),
            )
            created_user = cur.fetchone()

    return created_user


@app.post("/auth/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    email = login_data.email.strip().lower()

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    email,
                    password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    is_valid_password = verify_password(
        login_data.password,
        user["password_hash"],
    )

    if not is_valid_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(subject=str(user["id"]))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


def get_current_user(authorization: str | None = Header(default=None)):
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    email,
                    nickname,
                    github_username,
                    role,
                    created_at
                FROM users
                WHERE id = %s
                """,
                (user_id_int,),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []

    normalized_tags = []
    seen = set()

    for tag in tags:
        name = tag.strip().lower()

        if name and name not in seen:
            normalized_tags.append(name)
            seen.add(name)

    return normalized_tags


def sync_post_tags(cur, post_id: int, tags: list[str]) -> list[str]:
    normalized_tags = normalize_tags(tags)

    cur.execute(
        """
        DELETE FROM post_tags
        WHERE post_id = %s
        """,
        (post_id,),
    )

    for tag_name in normalized_tags:
        cur.execute(
            """
            INSERT INTO tags (name)
            VALUES (%s)
            ON CONFLICT (name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (tag_name,),
        )
        tag = cur.fetchone()

        cur.execute(
            """
            INSERT INTO post_tags (post_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (post_id, tag["id"]),
        )

    return normalized_tags


def attach_tags_to_posts(cur, posts: list[dict]) -> list[dict]:
    if not posts:
        return posts

    post_ids = [post["id"] for post in posts]

    cur.execute(
        """
        SELECT
            pt.post_id,
            t.name
        FROM post_tags pt
        JOIN tags t ON t.id = pt.tag_id
        WHERE pt.post_id = ANY(%s)
        ORDER BY t.name ASC
        """,
        (post_ids,),
    )
    tag_rows = cur.fetchall()

    tags_by_post_id = {}

    for row in tag_rows:
        tags_by_post_id.setdefault(row["post_id"], []).append(row["name"])

    for post in posts:
        post["tags"] = tags_by_post_id.get(post["id"], [])

    return posts


def attach_tags_to_post(cur, post: dict | None) -> dict | None:
    if post is None:
        return None

    posts = attach_tags_to_posts(cur, [post])

    return posts[0]


@app.get("/auth/me", response_model=UserRead)
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/posts", response_model=PostListResponse)
def get_posts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = None,
    type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    user_id: int | None = None,
    due_soon: bool = False,
    sort: str = Query(default="latest"),
):
    where_clauses = []
    params = []

    if keyword:
        keyword_like = f"%{keyword.strip()}%"
        where_clauses.append("(title ILIKE %s OR content ILIKE %s)")
        params.extend([keyword_like, keyword_like])

    if type:
        where_clauses.append("type = %s")
        params.append(type)

    if status:
        where_clauses.append("status = %s")
        params.append(status)

    if priority:
        where_clauses.append("priority = %s")
        params.append(priority)

    if tag:
        where_clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM post_tags pt
                JOIN tags t ON t.id = pt.tag_id
                WHERE pt.post_id = posts.id
                AND t.name = %s
            )
            """
        )
        params.append(tag.strip().lower())

    if user_id:
        where_clauses.append("user_id = %s")
        params.append(user_id)

    if due_soon:
        where_clauses.append(
            """
            due_date IS NOT NULL
            AND due_date >= CURRENT_DATE
            AND due_date <= CURRENT_DATE + INTERVAL '7 days'
            AND status != 'done'
            """
        )

    where_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    offset = (page - 1) * size
    order_sql = {
        "latest": "created_at DESC, id DESC",
        "updated": "updated_at DESC, id DESC",
        "due_date": "due_date IS NULL ASC, due_date ASC, id DESC",
        "priority": """
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END ASC,
            updated_at DESC,
            id DESC
        """,
    }.get(sort, "created_at DESC, id DESC")

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM posts
                {where_sql}
                """,
                tuple(params),
            )
            total = cur.fetchone()["total"]

            cur.execute(
                f"""
                SELECT
                    id,
                    user_id,
                    title,
                    content,
                    type,
                    status,
                    priority,
                    due_date,
                    created_at,
                    updated_at
                FROM posts
                {where_sql}
                ORDER BY {order_sql}
                LIMIT %s OFFSET %s
                """,
                tuple(params + [size, offset]),
            )
            posts = cur.fetchall()
            posts = attach_tags_to_posts(cur, posts)

    total_pages = (total + size - 1) // size if total > 0 else 1

    return {
        "items": posts,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }

@app.post("/posts", response_model=PostRead, status_code=201)
def create_post(
    post: PostCreate,
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO posts (
                    user_id,
                    title,
                    content,
                    type,
                    status,
                    priority,
                    due_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    user_id,
                    title,
                    content,
                    type,
                    status,
                    priority,
                    due_date,
                    created_at,
                    updated_at
                """,
                (
                    current_user["id"],
                    post.title,
                    post.content,
                    post.type,
                    post.status,
                    post.priority,
                    post.due_date,
                ),
            )
            created_post = cur.fetchone()

            sync_post_tags(cur, created_post["id"], post.tags)
            created_post = attach_tags_to_post(cur, created_post)

    return created_post


@app.get("/posts/{post_id}", response_model=PostRead)
def get_post(post_id: int):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    user_id,
                    title,
                    content,
                    type,
                    status,
                    priority,
                    due_date,
                    created_at,
                    updated_at
                FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )
            post = cur.fetchone()

            if post is not None:
                post = attach_tags_to_post(cur, post)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@app.patch("/posts/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    post: PostUpdate,
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id
                FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )
            existing_post = cur.fetchone()

            if existing_post is None:
                raise HTTPException(status_code=404, detail="Post not found")

            if existing_post["user_id"] != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You can only update your own posts",
                )

            cur.execute(
                """
                UPDATE posts
                SET
                    title = COALESCE(%s, title),
                    content = COALESCE(%s, content),
                    type = COALESCE(%s, type),
                    status = COALESCE(%s, status),
                    priority = COALESCE(%s, priority),
                    due_date = COALESCE(%s, due_date),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    user_id,
                    title,
                    content,
                    type,
                    status,
                    priority,
                    due_date,
                    created_at,
                    updated_at
                """,
                (
                    post.title,
                    post.content,
                    post.type,
                    post.status,
                    post.priority,
                    post.due_date,
                    post_id,
                ),
            )
            updated_post = cur.fetchone()

            if post.tags is not None:
                sync_post_tags(cur, post_id, post.tags)

            updated_post = attach_tags_to_post(cur, updated_post)

    return updated_post


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id
                FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )
            existing_post = cur.fetchone()

            if existing_post is None:
                raise HTTPException(status_code=404, detail="Post not found")

            if existing_post["user_id"] != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete your own posts",
                )

            cur.execute(
                """
                DELETE FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )

    return Response(status_code=204)


@app.get("/comments/post/{post_id}", response_model=list[CommentRead])
def get_comments_by_post(post_id: int):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )
            post = cur.fetchone()

            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")

            cur.execute(
                """
                SELECT
                    id,
                    post_id,
                    user_id,
                    content,
                    created_at,
                    updated_at
                FROM comments
                WHERE post_id = %s
                ORDER BY id ASC
                """,
                (post_id,),
            )
            comments = cur.fetchall()

    return comments


@app.post("/comments/post/{post_id}", response_model=CommentRead, status_code=201)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    content = comment.content.strip()

    if not content:
        raise HTTPException(status_code=400, detail="Comment content is required")

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM posts
                WHERE id = %s
                """,
                (post_id,),
            )
            post = cur.fetchone()

            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")

            cur.execute(
                """
                INSERT INTO comments (
                    post_id,
                    user_id,
                    content
                )
                VALUES (%s, %s, %s)
                RETURNING
                    id,
                    post_id,
                    user_id,
                    content,
                    created_at,
                    updated_at
                """,
                (
                    post_id,
                    current_user["id"],
                    content,
                ),
            )
            created_comment = cur.fetchone()

    return created_comment


@app.patch("/comments/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: dict = Depends(get_current_user),
):
    if comment.content is None:
        raise HTTPException(status_code=400, detail="Comment content is required")

    content = comment.content.strip()

    if not content:
        raise HTTPException(status_code=400, detail="Comment content is required")

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    user_id
                FROM comments
                WHERE id = %s
                """,
                (comment_id,),
            )
            existing_comment = cur.fetchone()

            if existing_comment is None:
                raise HTTPException(status_code=404, detail="Comment not found")

            if existing_comment["user_id"] != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You can only update your own comments",
                )

            cur.execute(
                """
                UPDATE comments
                SET
                    content = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    post_id,
                    user_id,
                    content,
                    created_at,
                    updated_at
                """,
                (
                    content,
                    comment_id,
                ),
            )
            updated_comment = cur.fetchone()

    return updated_comment


@app.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    user_id
                FROM comments
                WHERE id = %s
                """,
                (comment_id,),
            )
            existing_comment = cur.fetchone()

            if existing_comment is None:
                raise HTTPException(status_code=404, detail="Comment not found")

            if existing_comment["user_id"] != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete your own comments",
                )

            cur.execute(
                """
                DELETE FROM comments
                WHERE id = %s
                """,
                (comment_id,),
            )

    return Response(status_code=204)
