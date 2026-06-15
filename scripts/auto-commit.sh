#!/usr/bin/env bash
# 안정적 커밋 — 이 워크스페이스 마운트는 unlink를 막아 git이 .git/index.lock '묘비'(0바이트)를
# 남기고 일반 git add/commit이 막힌다. 그래서 /tmp 인덱스 + plumbing(write-tree/commit-tree/update-ref)
# 으로 .git/index.lock 을 우회해 커밋한다. 변경 없으면 스킵. push는 하지 않는다.
#
# 사용: bash scripts/auto-commit.sh "커밋 메시지" [경로 ...]   (경로 생략 시 apps/web/src docs/woonyong)
set -uo pipefail
cd "$(dirname "$0")/.."

MSG="${1:?커밋 메시지가 필요합니다}"; shift || true
PATHS=("$@"); [ ${#PATHS[@]} -eq 0 ] && PATHS=("apps/web/src" "docs/woonyong")

BR="$(git rev-parse --abbrev-ref HEAD)"
TMPIDX="/tmp/repolm.idx.$$"; rm -f "$TMPIDX" "$TMPIDX.lock"

GIT_INDEX_FILE="$TMPIDX" git read-tree HEAD
GIT_INDEX_FILE="$TMPIDX" git add -- "${PATHS[@]}"
TREE="$(GIT_INDEX_FILE="$TMPIDX" git write-tree)"

if [ "$TREE" = "$(git rev-parse 'HEAD^{tree}')" ]; then
  echo "변경 없음 — 커밋 스킵"; rm -f "$TMPIDX"; exit 0
fi

COMMIT="$(git commit-tree "$TREE" -p HEAD -m "$MSG")"
# 스테일 ref 락(묘비) 치우기 — rename은 허용됨
for L in ".git/HEAD.lock" ".git/refs/heads/$BR.lock"; do
  [ -f "$L" ] && mv -f "$L" "$L.junk.$(date +%s%N)" 2>/dev/null
done
git update-ref "refs/heads/$BR" "$COMMIT"
cp -f "$TMPIDX" .git/index 2>/dev/null
rm -f "$TMPIDX"
echo "커밋됨: $(git log --oneline -1)"
