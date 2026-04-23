# ローンチ前 Readiness レビュー依頼: line-ai-bot

作成日: 2026-04-23（再開セッション）

## Codex へのお願い

Claude Code 側で Day 1 実装 → Phase 2 の実装レビュー収束まで完了済み（参照: `from-codex/2026-04-23-codex-fixes-applied-response.md`）。

今 **ユーザーが Anthropic API Key 取得で詰まっていて**、そこだけがブロックされている状況。API Key の問題は今回のレビュー対象**外**。

**API Key 以外のすべての領域**について、「この後 LINE 実機テスト → Render デプロイまで進める上で、事前に潰しておくべき問題・見落とし・リスク」を厳しくレビューしてほしい。

## 特に見てほしい観点（API Key 関連は除外）

1. **設定整合性**
   - `.env.example` / `app/config.py` / `render.yaml` の環境変数名・デフォルト値が一致しているか
   - `CLAUDE_MODEL=claude-opus-4-7` の指定が Anthropic SDK 側で有効なモデル ID か（将来リネームや deprecation の懸念）
   - `PORT` の扱い（Render は `$PORT` を動的割り当て、`Procfile` / `uvicorn` 起動コマンドで正しく受けているか）

2. **LINE Webhook 実機テスト前の整合性**
   - `app/main.py` の `/callback` (署名検証・Idempotency・UTF-8 デコード失敗ハンドリング) が LINE の仕様と合致しているか
   - ngrok 経由で叩かれる際の `reply_token` 1 分制限と Opus のレスポンス時間のバランス
   - LINE 側「Webhook 再送」を ON にした場合の挙動（同一 event を二度処理しないか）

3. **Render デプロイ設定**
   - `render.yaml` の内容が Blueprint として妥当か（`envVars`, `buildCommand`, `startCommand`, health check pathなど）
   - Free プラン利用時の cold start 問題（LINE Webhook が 10 秒でタイムアウトする可能性）

4. **セキュリティ / プライバシー**
   - ログに user ID や本文が露出していないか
   - `.gitignore` の網羅性（`.env`, `__pycache__/` などは入っているが抜けはないか）
   - `HANDOFF.md` や `README.md` に個人情報漏洩リスクはないか（プロバイダー名「えりっぺ」のみ公開で本名は非公開という設計方針あり）

5. **テスト網羅性**
   - `tests/test_webhook.py` 7 件で Day 1 としては妥当か
   - LINE 実機テスト前に追加しておくべきテストケースはあるか（例: 空メッセージ、長文、スタンプ、グループ参加など）

6. **運用観点**
   - `README.md` が新規開発者（または将来の自分）が再セットアップできる粒度か
   - ログ設計: 障害時に何が分かるか（現状は `logging.basicConfig` レベル？）
   - idempotency のインメモリ実装（OrderedDict + threading.Lock、TTL 300 秒、10000 件上限）の運用上の落とし穴

7. **ドキュメント**
   - `HANDOFF.md` の手順が他人（または将来の自分）に通じるか
   - `portfolio-codex-reviews/` の履歴が整理されているか

## 期待するアウトプット

`portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-review-response.md` に以下形式で書いてほしい：

```markdown
# Pre-launch Readiness Review 返信

## サマリ
- Go / No-Go 判定（LINE 実機テストに進んでよいか）
- ブロッカー件数・主要懸念

## Findings

### [High] <件名>
- 対象: <file:line もしくはファイル名>
- 問題: <何が問題か>
- 提案: <どう直すか or 代替案>

### [Medium] ...

### [Low] ...

## 評価できる点（そのまま良いと判断したところ）
- ...

## 次アクション推奨順
1. ...
```

## 参考: 対象ファイル

Codex は同リポジトリ内のファイルを直接読めるので、以下をそのまま参照してください。

- `app/__init__.py`
- `app/config.py` (25 行)
- `app/claude_client.py` (28 行)
- `app/line_client.py` (37 行)
- `app/main.py` (110 行) — Webhook エントリ、idempotency、非同期対応
- `tests/test_webhook.py` (170 行)
- `requirements.txt` (8 行)
- `Procfile` (1 行)
- `render.yaml` (18 行)
- `.env.example` (5 行) ※実 `.env` は gitignore 済み
- `.gitignore`
- `README.md`
- `HANDOFF.md` — 進捗ログ
- `portfolio-codex-reviews/from-codex/2026-04-23-codex-fixes-applied-response.md` — 前回 Codex 収束レビュー

## 前提・制約

- モデル固定: `claude-opus-4-7`（ユーザー要望、コスト削減版 Haiku は選択肢として残す）
- 単一 uvicorn worker 前提（複数インスタンスは将来 Redis で idempotency 共有予定）
- デプロイ先: Render（Free or Starter、Blueprint 方式）
- ポートフォリオ用途（商用サービスではない）なので、セキュリティ要件は「最低限＋個人情報が漏れない」ライン

## 今回対象外（レビューしなくて良い領域）

- Anthropic API Key の取得フロー（ユーザー作業中）
- Anthropic Console 側の設定
- `.env` の実値入力
