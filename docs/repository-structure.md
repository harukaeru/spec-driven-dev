# リポジトリ構造定義書

- ドキュメント種別: リポジトリ構造定義書
- 最終更新: 2026-07-05
- ステータス: ドラフト v0.1

本書は、ファイル・ディレクトリの **配置ルールと責務** を定義する。
新規ファイルを追加する際は本書の分類に従い、逸脱する場合は本書を更新する。

---

## 1. ディレクトリツリー

```
spec-driven-dev/
├── .devcontainer/          # Dev Container 定義（Node 環境）
│   └── devcontainer.json
├── .github/                # GitHub 設定
│   └── dependabot.yml
├── backend/                # Python バックエンド（REST API + RDB）
│   ├── server.py           # APIサーバー本体（http.server + sqlite3）
│   ├── run.sh              # 起動ランチャー（同梱/システムPythonを自動選択）
│   └── tasks.db            # SQLite データ実体（自動生成・gitignore）
├── docs/                   # ステアリングドキュメント一式
│   ├── steering.md         # 索引（起点）
│   ├── project-charter.md  # プロジェクト憲章
│   ├── prd.md              # PRD
│   ├── requirements.md     # 要求仕様
│   ├── development-guidelines.md  # 開発ガイドライン
│   ├── repository-structure.md    # 本書
│   └── architecture.md     # アーキテクチャ設計書
├── src/                    # フロントエンド（React SPA）
│   ├── main.jsx            # エントリポイント（React マウント）
│   ├── App.jsx             # 画面・状態・API連携の中心
│   └── index.css           # スタイル
├── dist/                   # ビルド成果物（自動生成・gitignore対象）
├── .python/                # 同梱Pythonランタイム（自動配置・gitignore）
├── node_modules/           # npm依存（自動生成・gitignore）
├── index.html              # Vite のHTMLエントリ
├── vite.config.js          # Vite設定（/api プロキシ含む）
├── package.json            # スクリプト・依存定義
├── package-lock.json       # 依存ロック
├── .gitignore
└── README.md
```

## 2. 配置ルール（どこに何を置くか）

| 種別 | 置き場所 | 備考 |
|---|---|---|
| React コンポーネント/画面ロジック | `src/` | 当面は `App.jsx` に集約 |
| グローバルスタイル | `src/index.css` | |
| バックエンドのコード | `backend/` | Python標準ライブラリのみ |
| バックエンド起動スクリプト | `backend/run.sh` | npm から `npm run server` で呼ぶ |
| 仕様・設計ドキュメント | `docs/` | 本ステアリング群 |
| ビルド/CI/コンテナ設定 | ルート・`.github/`・`.devcontainer/` | |

## 3. 命名規約

- ドキュメント: `kebab-case.md`（例: `project-charter.md`）。
- React ファイル: コンポーネントは `PascalCase.jsx`（例: `App.jsx`）、その他は用途に応じる。
- Python: モジュール・関数は `snake_case`。
- スクリプト: `kebab-case.sh` もしくは用途が明確な名前。

## 4. バージョン管理対象（コミットする/しない）

### コミットする
- `src/`, `backend/server.py`, `backend/run.sh`, `docs/`, ルートの設定ファイル群。

### コミットしない（`.gitignore` 済み）
| パス | 理由 |
|---|---|
| `node_modules/` | npm 依存（再取得可能） |
| `dist/` | ビルド生成物 |
| `.python/` | 同梱ランタイム（環境依存・再取得可能） |
| `backend/*.db` | データ実体（環境ごとに異なる） |
| `__pycache__/`, `*.pyc` | Python キャッシュ |

## 5. エントリポイント早見表

| 目的 | 入口 |
|---|---|
| フロント開発起動 | `npm run dev`（Vite → `index.html` → `src/main.jsx` → `src/App.jsx`） |
| バックエンド起動 | `npm run server`（→ `backend/run.sh` → `backend/server.py`） |
| ビルド | `npm run build`（→ `dist/`） |
| ドキュメントの起点 | `docs/steering.md` |

## 6. 追加時の判断フロー

1. フロントの見た目/操作 → `src/`。
2. データ/API/永続化 → `backend/`。
3. 仕様・方針・設計 → `docs/`（該当文書を更新、無ければ新設し `steering.md` に追記）。
4. 生成物・環境依存物 → 追加前に `.gitignore` を確認。
