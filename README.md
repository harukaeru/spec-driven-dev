# spec-driven-dev

サーバー永続化（RDB）に対応した、シンプルなタスク管理アプリ。
フロントエンドは React（Vite）、バックエンドは Python 標準ライブラリ（`http.server` + `sqlite3`）で実装。

## 起動

```bash
npm install
npm run server   # バックエンド (http://localhost:8000)
npm run dev      # フロントエンド (http://localhost:5173) ※別ターミナル
```

## ドキュメント

開発・改変の方針は `docs/` に集約しています。起点は **[docs/steering.md](./docs/steering.md)**。

- [プロジェクト憲章](./docs/project-charter.md)
- [PRD](./docs/prd.md)
- [要求仕様](./docs/requirements.md)
- [開発ガイドライン](./docs/development-guidelines.md)
- [リポジトリ構造定義書](./docs/repository-structure.md)
- [アーキテクチャ設計書](./docs/architecture.md)
