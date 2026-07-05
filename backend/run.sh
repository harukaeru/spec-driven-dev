#!/usr/bin/env bash
# バックエンドを起動する。
# リポジトリ同梱の自己完結型 Python (.python/) があればそれを優先し、
# 無ければシステムの python3 を使う。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT/.python/bin/python3" ]; then
  PY="$ROOT/.python/bin/python3"
else
  PY="python3"
fi

exec "$PY" "$ROOT/backend/server.py"
