#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${SKILLS_REPO_URL:-https://github.com/lbql-yhl/codex-skills}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/bin/install.py" && -f "$SCRIPT_DIR/manifest.json" ]]; then
  exec python3 "$SCRIPT_DIR/bin/install.py" "$@"
fi

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

archive="$TMP_DIR/repo.tar.gz"
curl -fsSL "${REPO_URL}/archive/refs/heads/main.tar.gz" -o "$archive"
tar -xzf "$archive" -C "$TMP_DIR"
repo_root="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

if [[ "$#" -eq 0 ]]; then
  set -- --all
fi
exec python3 "$repo_root/bin/install.py" "$@"
