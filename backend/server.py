"""タスク管理アプリのバックエンド。

標準ライブラリのみ（http.server + sqlite3）で実装した REST API サーバー。
RDB には SQLite を使用する。追加の依存パッケージは不要。

エンドポイント:
  GET    /api/tasks              タスク一覧を取得
  POST   /api/tasks              タスクを作成          body: {"title": str, "priority"?: str}
  PATCH  /api/tasks/{id}         タスクを更新          body: {"title"?: str, "completed"?: bool, "priority"?: str}
  DELETE /api/tasks/{id}         タスクを削除
  DELETE /api/tasks/completed    完了済みタスクを一括削除

`priority` は "high" / "medium" / "low" のいずれか（既定値: "medium"）。
"""

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "tasks.db"))

PRIORITIES = ("high", "medium", "low")
DEFAULT_PRIORITY = "medium"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                completed  INTEGER NOT NULL DEFAULT 0,
                priority   TEXT    NOT NULL DEFAULT 'medium',
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # 既存DB（priority カラム未追加）向けのマイグレーション。
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        if "priority" not in columns:
            conn.execute(
                f"ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT '{DEFAULT_PRIORITY}'"
            )


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "priority": row["priority"],
        "created_at": row["created_at"],
    }


def list_tasks():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    return [row_to_task(r) for r in rows]


def create_task(title, priority=DEFAULT_PRIORITY):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)", (title, priority)
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_task(row)


def update_task(task_id, fields):
    sets, values = [], []
    if "title" in fields:
        sets.append("title = ?")
        values.append(fields["title"])
    if "completed" in fields:
        sets.append("completed = ?")
        values.append(1 if fields["completed"] else 0)
    if "priority" in fields:
        sets.append("priority = ?")
        values.append(fields["priority"])
    if not sets:
        return get_task(task_id)
    values.append(task_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row) if row else None


def get_task(task_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row) if row else None


def delete_task(task_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount > 0


def clear_completed():
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE completed = 1")
    return cur.rowcount


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def _route(self):
        """パスから ('tasks', <id|'completed'|None>) を返す。API 外なら None。"""
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/api/tasks":
            return ("tasks", None)
        if path.startswith("/api/tasks/"):
            return ("tasks", path[len("/api/tasks/"):])
        return None

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        route = self._route()
        if route == ("tasks", None):
            self._send(200, list_tasks())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self._route() != ("tasks", None):
            self._send(404, {"error": "not found"})
            return
        data = self._read_json()
        if data is None:
            self._send(400, {"error": "invalid JSON"})
            return
        title = (data.get("title") or "").strip()
        if not title:
            self._send(422, {"error": "title is required"})
            return
        priority = data.get("priority", DEFAULT_PRIORITY)
        if priority not in PRIORITIES:
            self._send(422, {"error": "priority must be one of: high, medium, low"})
            return
        self._send(201, create_task(title, priority))

    def do_PATCH(self):
        route = self._route()
        if not route or route[1] is None:
            self._send(404, {"error": "not found"})
            return
        try:
            task_id = int(route[1])
        except ValueError:
            self._send(404, {"error": "not found"})
            return
        data = self._read_json()
        if data is None:
            self._send(400, {"error": "invalid JSON"})
            return
        fields = {}
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                self._send(422, {"error": "title cannot be empty"})
                return
            fields["title"] = title
        if "completed" in data:
            fields["completed"] = bool(data["completed"])
        if "priority" in data:
            priority = data.get("priority")
            if priority not in PRIORITIES:
                self._send(422, {"error": "priority must be one of: high, medium, low"})
                return
            fields["priority"] = priority
        task = update_task(task_id, fields)
        if task is None:
            self._send(404, {"error": "not found"})
            return
        self._send(200, task)

    def do_DELETE(self):
        route = self._route()
        if not route or route[1] is None:
            self._send(404, {"error": "not found"})
            return
        if route[1] == "completed":
            self._send(200, {"deleted": clear_completed()})
            return
        try:
            task_id = int(route[1])
        except ValueError:
            self._send(404, {"error": "not found"})
            return
        if delete_task(task_id):
            self._send(204)
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[api] {self.address_string()} - {fmt % args}")


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"タスク管理 API を起動しました: http://{HOST}:{PORT}  (DB: {DB_PATH})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止します")
        server.shutdown()


if __name__ == "__main__":
    main()
