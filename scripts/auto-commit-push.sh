#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
cd "$REPO"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD || echo main)"
[ "$branch" = "HEAD" ] && branch="main"

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git add -A || true
  git commit -m "chore(init): initial commit [skip ci]" || true
fi

if git remote | grep -qx "origin"; then
  git pull --rebase origin "$branch" || true
fi

if ! git diff-index --quiet HEAD --; then
  ts="$(date +'%Y-%m-%d %H:%M:%S')"
  git add -A
  git commit -m "auto: save work @ $ts [skip ci]"
  if git remote | grep -qx "origin"; then
    git push origin "$branch"
  fi
  echo "Pushed changes at $ts"
else
  echo "No changes."
fi
