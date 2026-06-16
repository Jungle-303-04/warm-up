from datetime import datetime, timedelta
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def read_demo_user_id() -> int:
    value = os.getenv("CALENDAR_SEED_USER_ID")
    if value is None or not value.strip():
        raise SystemExit(
            "CALENDAR_SEED_USER_ID is required. "
            "Use the internal DB user_id from the logged-in GitHub account."
        )

    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit("CALENDAR_SEED_USER_ID must be an integer.") from exc


API_BASE_URL = os.getenv("CALENDAR_SEED_API_BASE_URL", "http://localhost:8000")
DEMO_TAG = "calendar-demo"
DEMO_USER_ID = read_demo_user_id()


def main() -> None:
    delete_existing_demo_boards()
    created_boards = [create_board(payload) for payload in build_demo_payloads()]

    print(f"calendar demo boards seeded through API: {len(created_boards)}")
    for board in created_boards:
        print(f"- #{board['id']} {board['title']}")


def delete_existing_demo_boards() -> None:
    query = urlencode(
        {
            "user_id": DEMO_USER_ID,
            "tag": DEMO_TAG,
            "page": 1,
            "size": 100,
        }
    )
    payload = request_json("GET", f"/board/?{query}")

    for board in payload.get("items", []):
        delete_query = urlencode({"user_id": DEMO_USER_ID})
        request_json("DELETE", f"/board/{board['id']}?{delete_query}", expect_json=False)


def create_board(payload: dict) -> dict:
    return request_json("POST", "/board/", payload)


def request_json(
    method: str,
    path: str,
    payload: dict | None = None,
    expect_json: bool = True,
):
    body = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{API_BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    with urlopen(request) as response:
        if not expect_json:
            return None
        response_body = response.read().decode("utf-8")
        return json.loads(response_body) if response_body else None


def build_demo_payloads() -> list[dict]:
    today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7)

    return [
        {
            "board_type": 2,
            "title": "RAG 캘린더 UI 구현",
            "content": "보드 일정 데이터를 달력 막대로 표시하는 3일짜리 작업입니다.",
            "tag": DEMO_TAG,
            "user_id": DEMO_USER_ID,
            "assignee_user_ids": [DEMO_USER_ID],
            "schedule_board_detail": {
                "start_at": to_iso(next_monday),
                "end_at": to_iso(next_monday + timedelta(days=2, hours=8)),
                "importance": 8,
            },
            "schedule_board_tasks": [
                {
                    "task_name": "캘린더 이벤트 매핑",
                    "task_status": 2,
                },
                {
                    "task_name": "게시글 상세 패널 연결",
                    "task_status": 1,
                },
            ],
        },
        {
            "board_type": 2,
            "title": "백엔드 API 계약 주석 정리",
            "content": "프론트 이벤트 함수 위에 백엔드 요청/응답 구조를 정리합니다.",
            "tag": DEMO_TAG,
            "user_id": DEMO_USER_ID,
            "participant_user_ids": [DEMO_USER_ID],
            "schedule_board_detail": {
                "start_at": to_iso(today + timedelta(days=4, hours=1)),
                "end_at": to_iso(today + timedelta(days=4, hours=5)),
                "importance": 5,
            },
        },
        {
            "board_type": 3,
            "title": "주간 진행 회의록",
            "content": "이번 주 RAG ask 흐름과 캘린더 화면 우선순위를 확인했습니다.",
            "tag": DEMO_TAG,
            "user_id": DEMO_USER_ID,
            "participant_user_ids": [DEMO_USER_ID],
            "proceedings_board_detail": {
                "meeting_date": to_iso(today + timedelta(days=1, hours=5)),
            },
        },
        {
            "board_type": 3,
            "title": "프론트 목업 점검 회의록",
            "content": "메인 화면에서 달력이 먼저 보이도록 레이아웃을 조정하기로 했습니다.",
            "tag": DEMO_TAG,
            "user_id": DEMO_USER_ID,
            "carbon_copy_user_ids": [DEMO_USER_ID],
            "proceedings_board_detail": {
                "meeting_date": to_iso(next_monday + timedelta(days=3, hours=4)),
            },
        },
    ]


def to_iso(value: datetime) -> str:
    return value.isoformat()


if __name__ == "__main__":
    main()
