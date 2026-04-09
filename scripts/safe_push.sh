#!/usr/bin/env bash
# safe_push.sh — race-condition-safe git commit + push for GitHub Actions
# Usage: bash scripts/safe_push.sh "commit message"
#
# Strategy:
#   1. Stash any Python-modified files BEFORE pulling (fixes "unstaged changes" error)
#   2. Pull latest from origin
#   3. Pop stash (reapplies our changes on top of latest)
#   4. Stage posts.csv, commit, then retry push up to 4 times with random backoff
#      (handles concurrent workflow pushes gracefully)

set -e

COMMIT_MSG="${1:-chore: update posts.csv}"
MAX_RETRIES=4

git config user.name  "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

echo "→ Stashing local changes before pull..."
git stash --include-untracked || true

echo "→ Pulling latest from origin/main..."
git pull origin main

echo "→ Restoring our changes..."
git stash pop || true

echo "→ Staging posts.csv..."
git add social/posts.csv

if git diff --cached --quiet; then
  echo "→ No changes to commit. Done."
  exit 0
fi

git commit -m "$COMMIT_MSG"

for i in $(seq 1 $MAX_RETRIES); do
  echo "→ Push attempt $i/$MAX_RETRIES..."
  if git push origin main; then
    echo "✅ Push succeeded."
    exit 0
  fi
  if [ "$i" -lt "$MAX_RETRIES" ]; then
    SLEEP_SEC=$(( (RANDOM % 8) + 4 ))
    echo "  Push rejected — another workflow pushed first. Rebasing and retrying in ${SLEEP_SEC}s..."
    sleep $SLEEP_SEC
    git pull --rebase origin main
  fi
done

echo "❌ Push failed after $MAX_RETRIES attempts." >&2
exit 1
