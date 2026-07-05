---
name: api-smoke-test
description: Task manager のバックエンド REST API を起動し、全エンドポイント（一覧・作成・更新・削除・完了済み一括削除）とバリデーション/エラー応答を一気通貫で疎通確認する。バックエンドやデータモデル、APIを変更した後の受け入れ確認、「APIの動作確認」「スモークテスト」「疎通確認」を求められたときに使う。
---

# API スモークテスト

`backend/server.py` の REST API を一時的なDBで起動し、要求仕様（`docs/requirements.md` §2）の
全エンドポイントとエラー応答を検証する。既存の `backend/tasks.db` を汚さないため、隔離DBで実行する。

## 前提

- 起動には Python が必要。`backend/run.sh` が同梱ランタイム `.python/` を優先し、無ければ `python3` を使う。
- ポート `8000` を使用する。使用中なら `PORT` を変えて起動する。

## 手順

1. **隔離DBでバックエンドを起動**（既存データを汚さない）。バックグラウンド実行する。

   ```bash
   DB_PATH=$(mktemp -d)/smoke.db PORT=8000 bash backend/run.sh
   ```

2. 起動を待ってから、以下を順に実行し **各期待値と一致するか** を確認する。

   | # | 操作 | コマンド例 | 期待 |
   |---|---|---|---|
   | 1 | 一覧(空) | `curl -s localhost:8000/api/tasks` | `[]` |
   | 2 | 作成 | `curl -s -X POST localhost:8000/api/tasks -H 'Content-Type: application/json' -d '{"title":"牛乳を買う"}'` | 201, `id`付きJSON, `completed:false` |
   | 3 | 作成(空title) | 同上で `-d '{"title":"  "}'` （`-o /dev/null -w '%{http_code}'`） | `422` |
   | 4 | 不正JSON | `-d '{'` （同上） | `400` |
   | 5 | 完了へ更新 | `curl -s -X PATCH localhost:8000/api/tasks/1 -H 'Content-Type: application/json' -d '{"completed":true}'` | 200, `completed:true` |
   | 6 | 存在しないIDを更新 | `PATCH .../api/tasks/999`（`-w '%{http_code}'`） | `404` |
   | 7 | 完了済み一括削除 | `curl -s -X DELETE localhost:8000/api/tasks/completed` | 200, `{"deleted":N}` |
   | 8 | 個別削除 | 事前に1件作成し `DELETE .../api/tasks/<id>`（`-w '%{http_code}'`） | `204` |
   | 9 | 未定義ルート | `curl .../api/unknown`（`-w '%{http_code}'`） | `404` |

3. **後片付け**: 起動したバックエンドプロセスを停止する（バックグラウンドタスクを止める）。
   一時DBは `mktemp -d` 配下なので放置してよい。

## 合否判定

- 上記9項目すべてが期待値と一致 → **PASS**。
- いずれかが不一致 → **FAIL** とし、どの項目がどう食い違ったか（期待/実際のステータス・ボディ）を報告する。
- 期待値の根拠が変わった場合は、実装ではなくまず `docs/requirements.md` を疑い、仕様と実装のどちらが正しいかを確認する。

## 出力

結果は表形式（項目 / 期待 / 実際 / 判定）で簡潔に報告し、最後に PASS / FAIL を明示する。
