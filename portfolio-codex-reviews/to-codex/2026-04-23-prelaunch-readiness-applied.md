# Pre-launch Readiness レビュー 反映報告

参照元: `from-codex/2026-04-23-prelaunch-readiness-review-response.md`
実施日: 2026-04-23

Codex の 10 件の指摘すべてに対応済み。各指摘への反映内容と変更ファイル、検証方法をまとめる。

## 反映サマリ

| # | 重大度 | 指摘 | 対応 | ステータス |
|---|:---:|---|---|:---:|
| 1 | High | `HANDOFF.md` 実名 | 全関連ファイルから削除（抽象表現に置換） | 完了 |
| 2 | High | Render Free cold start | README で Free 非推奨を明記、Starter 以上を推奨 | 完了 |
| 3 | Medium | Claude timeout なし | 30 秒 timeout を SDK client に明示 | 完了 |
| 4 | Medium | 複数イベント逐次処理 | Day 1 は先頭 1 件のみ処理へ変更 | 完了 |
| 5 | Medium | LINE テキスト長上限 | 5000 文字で truncate + 末尾省略 | 完了 |
| 6 | Medium | `healthCheckPath` 不足 | `render.yaml` に `/health` を追加 | 完了 |
| 7 | Low | `env` 旧フィールド | `runtime: python` に置換 | 完了 |
| 8 | Low | Python バージョン未固定 | `.python-version` と `PYTHON_VERSION` 追加 | 完了 |
| 9 | Low | README に LINE 設定集約 | チェックリスト形式で README に集約 | 完了 |
| 10 | Low | テスト網羅不足 | テスト 7 → 15 件に拡充 | 完了 |

## 詳細

### [High-1] 実名削除

- **変更**: `HANDOFF.md:117` の「本名『尾崎 真』は公開しない設計」を「個人名（本名）は公開リポジトリ・Bot UI のいずれにも出さない設計」に置換
- **同時修正**: 同じ実名が入っていた `portfolio-codex-reviews/to-codex/2026-04-23-prelaunch-readiness-review.md` と `from-codex/2026-04-23-prelaunch-readiness-review-response.md` からも削除
- **git 履歴確認**: `git log -p --all | grep -c "尾崎"` → 0。コミット済み履歴には流出していない（HANDOFF.md は modified 状態のまま未コミットだった）
- **検証**: `grep -r "尾崎" .` → 該当なし

### [High-2] Render Free と reply_token 制限

- **変更**: `README.md` の「Render デプロイ」節に「プランの選び方」サブ節を追加
  - Free プランは LINE Webhook 本番運用に非推奨と明記
  - 理由（15 分アイドル → 約 1 分のコールドスタート → reply_token 1 分制限抵触）も併記
  - Starter 以上を推奨と明記
  - Free で試す場合の回避策（事前に `/health` を叩く運用）も併記
- **備考**: `render.yaml` は `plan: free` のまま残している（Blueprint 初回デプロイで Starter を選ぶかは手動判断）。必要なら更新候補

### [Medium-3] Claude timeout

- **変更**: `app/claude_client.py`
  - `Anthropic(api_key=..., timeout=30.0)` で SDK client レベルに timeout 指定
  - 定数 `_REQUEST_TIMEOUT_SECONDS = 30.0` としてコメント付きで明示
  - タイムアウトや他の例外は `app/main.py` の `except Exception` で捕捉され、フォールバック文言返信に自動フォールバック
- **システムプロンプト**: 「回答は 4000 文字以内に収めてください」の制約を追加（LINE 上限 5000 との二重防御）

### [Medium-4] 複数イベント同梱

- **方針決定**: Day 1 は「1 Webhook 内の複数テキストイベントは先頭 1 件のみ処理」を採用
  - 理由: シンプル / reply_token 1 分制限に確実に間に合う / LINE 実運用で複数イベント同梱はレアケース
- **変更**: `app/main.py` callback ループに `handled` フラグを追加。先頭を処理した後の追加テキストイベントはログだけ残してスキップ
- **テスト**: `test_callback_handles_only_first_text_event_in_batch` を追加

### [Medium-5] LINE テキスト長

- **変更**: `app/line_client.py`
  - `_LINE_TEXT_MAX_CHARS = 5000` 定数化
  - `_truncate_for_line(text)` ヘルパーで上限超過時に末尾 `…（以下省略）` を付けて切り詰め
  - `reply_text()` が送信直前に truncate を通す
- **テスト**: `test_line_client_truncates_long_text`, `test_line_client_does_not_truncate_short_text` を追加

### [Medium-6] `healthCheckPath`

- **変更**: `render.yaml` に `healthCheckPath: /health` を追加
- **効果**: Render 側が起動失敗を検知できる、ゼロダウンタイムデプロイで新インスタンスの健全性確認に使われる

### [Low-7] `env` → `runtime`

- **変更**: `render.yaml` の `env: python` を `runtime: python` に置換

### [Low-8] Python バージョン固定

- **変更**:
  - `.python-version` ファイル新規作成（内容: `3.13.5`） — pyenv 等ローカル用
  - `render.yaml` の `envVars` に `PYTHON_VERSION: 3.13.5` を追加 — Render 用
- **選定理由**: ローカル環境と同じ `3.13.5`。pytest 15 件パス実績あり

### [Low-9] README に LINE Developers 設定チェックリスト集約

- **変更**: `README.md` の「ローカル確認」節に以下を明記
  - Webhook 利用 ON
  - Webhook 再送 ON
  - 応答メッセージ OFF（LINE Official Account Manager 側、**これが最も詰まりやすい**）
  - あいさつメッセージ任意
  - Webhook URL 右の「検証」ボタンで 200 確認
- **効果**: `HANDOFF.md` に分散していた情報を README に集約し、将来の再セットアップ時も README 1 箇所で完結

### [Low-10] テスト追加

- **変更**: `tests/test_webhook.py`
  - 旧 7 件 → 新 15 件（+8 件）
  - 追加分:
    1. `test_callback_returns_200_when_events_empty` — events: [] ケース
    2. `test_callback_skips_empty_text` — 空白のみテキスト
    3. `test_callback_ignores_non_text_message` — 非テキスト MessageEvent
    4. `test_callback_sends_fallback_when_claude_raises` — Claude 例外時フォールバック
    5. `test_callback_returns_200_when_line_reply_raises` — LINE 返信 API 例外時 200 継続
    6. `test_callback_handles_only_first_text_event_in_batch` — 複数イベント先頭のみ処理
    7. `test_line_client_truncates_long_text` — 長文 truncate
    8. `test_line_client_does_not_truncate_short_text` — 短文非 truncate
- **実行結果**: `pytest -v` → **15 passed in 3.75s**（全件 PASSED）

## 変更ファイル一覧

```
.python-version                                                    (新規)
HANDOFF.md                                                         (実名削除)
README.md                                                          (大幅改訂)
app/claude_client.py                                               (timeout + system prompt)
app/line_client.py                                                 (truncate 追加)
app/main.py                                                        (複数イベント先頭のみ)
render.yaml                                                        (healthCheckPath, runtime, PYTHON_VERSION)
tests/test_webhook.py                                              (7→15 件)
portfolio-codex-reviews/to-codex/2026-04-23-prelaunch-readiness-review.md         (実名削除)
portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-review-response.md (実名削除)
```

## 残論点（次ラウンドで確認してほしい観点）

1. `render.yaml` の `plan: free` を維持している点（README で非推奨と明記だが YAML デフォルトは Free のまま）。Blueprint 初回デプロイ時に手動で Starter を選ぶ運用でよいか
2. Claude SDK の `timeout=30.0` が SDK 側でどう扱われるか（接続/読み取りそれぞれに 30 秒か、合計か）。公式ドキュメント照合が必要なら指摘してほしい
3. システムプロンプトの「4000 文字以内」指示は意図通りモデルを制約できるか（モデルが従わない可能性は truncate でカバー済みだが、一応）
4. 複数イベント「先頭 1 件のみ処理」方針が LINE 運用上問題ないか（他に推奨パターンがあれば）

## 検証コマンド

```bash
.venv/Scripts/python.exe -m pytest -v
# → 15 passed in 3.75s

grep -r "尾崎" .
# → 該当なし
```
