#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: watch-auto-commit-push.sh [repo-path]

Monitors the repository for file changes and runs auto-commit-push.sh
whenever tracked files differ from HEAD. Falls back to polling when
neither fswatch nor watchexec is available.
USAGE
}

	while (( "$#" )); do
	  case "$1" in
	    -h|--help)
	      usage
	      exit 0
	      ;;
	    --)
	      shift
	      break
	      ;;
	    -*)
	      echo "Unknown option: $1" >&2
	      usage >&2
	      exit 1
	      ;;
	    *)
	      break
	      ;;
	  esac
	  shift
	done

REPO="${1:-.}"
REPO="$(cd "$REPO" && pwd)"

cd "$REPO"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_COMMIT_SCRIPT="${AUTO_COMMIT_SCRIPT:-$SCRIPT_DIR/auto-commit-push.sh}"

if [[ ! -x "$AUTO_COMMIT_SCRIPT" ]]; then
  echo "Missing or non-executable auto-commit script: $AUTO_COMMIT_SCRIPT" >&2
  exit 1
fi

POLL_INTERVAL="${POLL_INTERVAL:-15}"
QUIET_PERIOD="${QUIET_PERIOD:-5}"

run_auto_commit() {
  # Debounce rapid sequences of change notifications.
  sleep "$QUIET_PERIOD"
  if git status --porcelain | grep -q .; then
    "$AUTO_COMMIT_SCRIPT" "$REPO"
  fi
}

start_fswatch() {
  fswatch --allow-overflow --latency=1 \
    --one-per-batch --recursive --timestamp \
    --exclude='\.git/' --exclude='logs/' \
    "$REPO" |
  while IFS= read -r _; do
    run_auto_commit
  done
}

start_polling() {
  echo "watch-auto-commit: falling back to polling every ${POLL_INTERVAL}s" >&2
  while true; do
    if git status --porcelain | grep -q .; then
      run_auto_commit
    fi
    sleep "$POLL_INTERVAL"
  done
}

if command -v fswatch >/dev/null 2>&1; then
  start_fswatch
else
  start_polling
fi
