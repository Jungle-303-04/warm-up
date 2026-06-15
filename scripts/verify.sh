#!/usr/bin/env bash
# RepoLM 품질 게이트 — 결정이 필요 없는 작업은 이 게이트가 녹색일 때까지 반복한다.
# 사용:
#   bash scripts/verify.sh           # 1회 실행(프론트 tsc + 백엔드 ruff/pytest)
#   bash scripts/verify.sh --full    # + 프론트 next build
#   bash scripts/verify.sh --watch   # 변경 감지 시 반복(짧은 주기 루프)
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
FULL=0; WATCH=0
for a in "$@"; do
  [ "$a" = "--full" ] && FULL=1
  [ "$a" = "--watch" ] && WATCH=1
done

run_once() {
  local fail=0
  echo "── 1) 프론트 타입체크 (tsc) ─────────────"
  ( cd "$ROOT/apps/web" && ./node_modules/.bin/tsc --noEmit ) || fail=1

  echo "── 2) 백엔드 lint (ruff) ────────────────"
  ( cd "$ROOT/backend" && ruff check . && ruff format --check . ) || fail=1

  echo "── 3) 백엔드 테스트 (pytest) ────────────"
  ( cd "$ROOT/backend" && pytest -q ) || fail=1

  if [ "$FULL" = "1" ]; then
    echo "── 4) 프론트 빌드 (next build) ──────────"
    ( cd "$ROOT/apps/web" && pnpm build ) || fail=1
  fi

  if [ "$fail" = "0" ]; then
    echo "✅ ALL GREEN"
  else
    echo "❌ FAILED — 위 로그 확인"
  fi
  return $fail
}

if [ "$WATCH" = "1" ]; then
  echo "watch 모드: 5초마다 재검증 (Ctrl+C 종료)"
  while true; do
    run_once || true
    sleep 5
  done
else
  run_once
fi
