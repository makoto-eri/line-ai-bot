# Pre-launch Readiness Applied レビュー 反映報告 v2

参照元: `from-codex/2026-04-23-prelaunch-readiness-applied-response.md`（ラウンド 2 レビュー）
実施日: 2026-04-23

## 反映サマリ

Codex ラウンド 2 の指摘 2 件すべてに対応済み。

| # | 重大度 | 指摘 | 対応 | ステータス |
|---|:---:|---|---|:---:|
| 1 | High | Claude timeout が default retry で reply_token 対策として不十分 | `max_retries=0` 明示 + 確認テスト追加 | 完了 |
| 2 | Medium | `render.yaml` の `plan: free` と README 推奨の乖離 | ポートフォリオ用途なので free 維持。README で「疎通確認専用」を明確化し、本番運用時の Starter 切替手順を明記 | 完了 |

## 詳細

### [High-1] `max_retries=0` 追加

- **変更**: `app/claude_client.py`
  - `_MAX_RETRIES = 0` 定数を追加（コメントで「reply_token 1 分制限のため retry を無効化し、アプリ側で即フォールバック返信」方針を明記）
  - `Anthropic(api_key=..., timeout=_REQUEST_TIMEOUT_SECONDS, max_retries=_MAX_RETRIES)` に変更
- **根拠**: anthropic 0.96.0 の default `max_retries=2` で timeout 例外時に再試行され、最悪 3 試行 + backoff で reply_token 1 分を超える可能性があった（Codex 指摘通り）
- **方針**: SDK retry よりもアプリ側の except 節で即フォールバック文言を返す（`_CLAUDE_FAILURE_REPLY`）方が、LINE 返信の遅延リスクを最小化できる

### [High-1 関連] 確認テスト追加

- **変更**: `tests/test_webhook.py` に `test_claude_client_sets_short_timeout_and_disables_retry` を追加
- **内容**:
  - `_REQUEST_TIMEOUT_SECONDS == 30.0` / `_MAX_RETRIES == 0` を定数レベルで固定
  - `ClaudeClient` 初期化後の `client._client.max_retries` と `client._client.timeout` が指定値と一致することを確認
  - timeout は httpx 側で `httpx.Timeout` にラップされるため、`read` 属性経由でも検証できるようフォールバック済み
- **実行結果**: **16 passed in 3.91s**（全件 PASSED）

### [Medium-2] `render.yaml` plan 方針統一

- **判断**: ポートフォリオ用途（初期 $5 クレジット想定・常時起動の必要性は低い）につき `plan: free` を**維持**
- **変更**: `README.md` の「Render デプロイ」節を全面改訂
  - 節冒頭に「`render.yaml` のデフォルトは `plan: free`（疎通確認・ポートフォリオ閲覧用）。LINE Webhook に常時向ける場合は Starter 以上へ切り替える想定」を追加
  - 「プランの選び方（重要）」サブ節を強化：
    - Free が疎通確認・ポートフォリオ閲覧専用であることを明記
    - **LINE Webhook URL を Render に向ける前に Starter へ切替**を手順として固定
    - Free のままテストする場合の回避策（`/health` を手で叩いて起こしてから 30 秒以内に LINE 送信）を明文化
- **非変更**: `render.yaml` の `plan: free` はそのまま。費用回避が第一、Starter 切替は手動判断で対応

## 残論点 4 件への回答（Codex の回答を反映）

Codex から受け取った 4 論点への評価に従い、以下の通り最終決定：

1. **`plan: free` 維持** → 決定通り。README で「疎通確認専用」を強化し、Starter 切替を手順化した
2. **Claude SDK timeout の扱い** → `max_retries=0` を追加して解決
3. **system prompt の「4000 文字以内」制約** → Codex 評価通り追加修正不要。truncate との二重防御で維持
4. **複数イベント「先頭 1 件のみ処理」方針** → Codex 評価通り Day 1 は追加修正不要。将来拡張時に push_message 方式へ移行検討

## 変更ファイル一覧（v2 分）

```
app/claude_client.py       (max_retries=0 追加)
README.md                  (Render 節の plan 方針強化)
tests/test_webhook.py      (ClaudeClient 設定確認テスト追加、15 → 16 件)
```

## 検証コマンド

```bash
.venv/Scripts/python.exe -m pytest -q
# → 16 passed in 3.91s
```

## 次アクション

ラウンド 2 の指摘はすべて解消した。Phase 2 収束宣言の可否を判定してほしい。
残留指摘がなければ、反映報告への応答は `from-codex/2026-04-23-prelaunch-readiness-applied-v2-response.md` に「Approved / LGTM」相当の短い確認だけで良い。
