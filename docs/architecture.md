# アーキテクチャ設計書

- ドキュメント種別: アーキテクチャ設計書
- 最終更新: 2026-07-05
- ステータス: ドラフト v0.1

---

## 1. 全体構成

クライアント（SPA）とバックエンド（REST API）を分離した2層構成。永続化は RDB（SQLite）。

```
┌────────────────────────┐        ┌──────────────────────────┐        ┌──────────────┐
│   ブラウザ (React SPA)   │  HTTP  │  Vite Dev Server (:5173)  │  proxy │  Python API   │
│   src/App.jsx           │──────▶ │  /api/* をプロキシ         │──────▶ │  (:8000)      │
│   fetch('/api/tasks')   │  JSON  │  静的配信 + HMR            │  /api  │  server.py    │
└────────────────────────┘        └──────────────────────────┘        └──────┬───────┘
                                                                              │ sqlite3
                                                                       ┌──────▼───────┐
                                                                       │  SQLite      │
                                                                       │ backend/tasks.db │
                                                                       └──────────────┘
```

- 開発時はフロントの `/api/*` を Vite が `:8000` へ転送するため、ブラウザからは同一オリジンに見える。
- 本番配信を行う場合は `dist/` を静的配信し、別途 `/api` をバックエンドへルーティングする構成を想定（未整備）。

## 2. 技術選定と根拠

| 項目 | 採用 | 根拠 | 代替案 |
|---|---|---|---|
| フロント | React 18 + Vite 5 | 既存実装を踏襲、HMRで開発効率が高い | Svelte/Vue |
| バックエンド | Python 標準ライブラリ（`http.server`） | **追加依存ゼロ**で起動できる。実行環境の制約に強い | FastAPI/Flask |
| DB | SQLite（`sqlite3`） | サーバー不要のRDBで導入が容易。単一ユーザーに十分 | PostgreSQL/MySQL |
| 通信 | REST + JSON | 単純で検証容易 | GraphQL |

> 注: FastAPI 等を採用しなかったのは、実行環境の Python が pip 不可・標準ライブラリ欠落であり、
> 外部依存を前提にできないため。標準ライブラリのみで完結させる方針を優先した。
> （フル機能の同梱ランタイム `.python/` を用いて実行する。詳細は §7）

## 3. バックエンド設計（`backend/server.py`）

### 3.1 責務分離
- **DB層**: `get_conn` / `init_db` / `list_tasks` / `create_task` / `update_task` / `get_task` /
  `delete_task` / `clear_completed`。SQLはすべてパラメータ化。
- **HTTP層**: `Handler`（`BaseHTTPRequestHandler` 派生）。`_send` / `_read_json` / `_route` の補助と
  `do_GET/POST/PATCH/DELETE/OPTIONS`。
- **サーバー**: `ThreadingHTTPServer` で起動（`main`）。

### 3.2 ルーティング
`_route()` がパスを解釈し `("tasks", <id | "completed" | None>)` を返す。

| メソッド | パス | 処理 | 成功 |
|---|---|---|---|
| GET | `/api/tasks` | 一覧 | 200 |
| POST | `/api/tasks` | 作成（title必須, trim, 空は422） | 201 |
| PATCH | `/api/tasks/{id}` | 部分更新（title/completed） | 200 |
| DELETE | `/api/tasks/{id}` | 削除 | 204 |
| DELETE | `/api/tasks/completed` | 完了済み一括削除 | 200 `{deleted}` |
| OPTIONS | `*` | CORSプリフライト | 204 |

### 3.3 設定（環境変数）
| 変数 | 既定 | 用途 |
|---|---|---|
| `HOST` | `127.0.0.1` | バインドアドレス |
| `PORT` | `8000` | 待受ポート |
| `DB_PATH` | `backend/tasks.db` | SQLiteファイルパス |

## 4. データモデル

テーブル: `tasks`

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 一意ID |
| `title` | TEXT | NOT NULL | タスク名 |
| `completed` | INTEGER | NOT NULL DEFAULT 0 | 0=未完了 / 1=完了 |
| `created_at` | TEXT | NOT NULL DEFAULT (datetime('now')) | 作成日時（UTC） |

- API 表現では `completed` を真偽値（`true/false`）へ変換して返す。
- 一覧は `ORDER BY id DESC`（新しい順）。

## 5. フロントエンド設計（`src/App.jsx`）

- 単一コンポーネントに状態を集約: `tasks` / `input` / `filter` / `loading` / `error`。
- 初期化: `useEffect` で `GET /api/tasks` を実行し `tasks` に反映。
- 操作: 各操作が対応APIを呼び、成功時にローカル状態を更新（楽観的ではなくレスポンス反映型）。
- 派生値: `visibleTasks`（フィルタ適用）と `remaining`（残件数）を `useMemo` 等で算出。
- 通信補助: `fetchJSON` が非2xxを検知し、エラーメッセージを抽出して例外化 → `error` 表示。

## 6. 通信・CORS

- 開発時は Vite プロキシ（`vite.config.js`）により同一オリジン化。
- バックエンドは `Access-Control-Allow-Origin: *` を返す（開発容易性のため）。
- **セキュリティ注意**: 全許可CORSは開発前提。外部公開時はオリジン制限・認証の導入を要検討。

## 7. 実行環境に関する設計判断（同梱ランタイム）

- 実行環境のシステム Python は標準ライブラリが大幅に欠落（`http.server`/`sqlite3`/`threading` 不在）し、
  pip も利用不可だった。
- 対応として、自己完結型 Python 3.12 をリポジトリ直下 `.python/` に配置して利用する。
- `backend/run.sh` が `.python/bin/python3` を優先し、無ければシステム `python3` を使う。
- `.python/` は `.gitignore` 済みで配布物には含めない（各環境で用意する）。

## 8. 品質特性と現状の限界

| 特性 | 現状 | 備考 |
|---|---|---|
| 性能 | 個人利用規模で十分 | インデックスは主キーのみ |
| 同時実行 | 単一ユーザー前提 | SQLiteの書き込みは直列。多人数同時は非対応 |
| 可用性 | 単一プロセス | プロセス停止＝停止。監視/再起動は未整備 |
| セキュリティ | 認証なし・CORS全許可 | ローカル利用前提 |
| テスト | 手動 | 自動テスト未整備 |

## 9. 拡張の方向性（Future）

- **DB差し替え**: DB操作関数を境界に PostgreSQL 等へ移行可能な設計。接続部を抽象化する。
- **認証**: 外部公開時にユーザー認証・オリジン制限を追加。
- **機能拡張**: 期限・優先度・編集・検索（PRD Backlog 参照）。スキーマ拡張時はマイグレーション方針を定義。
- **配信**: `dist/` の静的配信 + リバースプロキシで `/api` を集約する本番構成。

## 10. 関連ドキュメント

- 機能の背景・優先度: [PRD](./prd.md)
- 検証可能な要求とAPI仕様: [要求仕様](./requirements.md)
- 配置ルール: [リポジトリ構造定義書](./repository-structure.md)
- 実装規約: [開発ガイドライン](./development-guidelines.md)
