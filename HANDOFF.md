# HANDOFF — line-ai-bot

最終更新: 2026-04-23（セッション再開後・Anthropic復旧確認済み）

## プロジェクト概要

LINE Messaging API + Claude API（Opus 4.7）で業務相談Botを作る。FastAPI + ngrok + Renderデプロイ。3つの並行プロジェクトのうちの1つ。

## 現在の進捗

### 完了（Day 1 コード）

- `app/` 一式作成・pytest 7件パス（元4件 + Codex指摘反映で3件追加）
- Codex初回レビュー → High/Medium/Lowの3指摘を全反映・承認済み（ブロッカーなし）
  - 詳細: `portfolio-codex-reviews/from-codex/2026-04-23-codex-fixes-applied-response.md`
- コミット: `319a236`（initial）, `3fe33f0`（codex-bridge layout）

### 完了（LINE Developers設定）

- **プロバイダー名**: えりっぺ
- **LINE Official Account作成済み**: アカウント名「Claude業務相談」
- **Messaging APIチャネル作成済み**（LINE Official Account Manager経由で有効化）
- **Channel Access Token（長期）** 取得済み（ユーザーの手元でコピー済み）
- **Channel Secret** は取得要確認（「チャネル基本設定」タブ最下部）
- Webhook URL: 未設定（ngrok起動後に設定予定）
- 応答メッセージ: OFF にする予定（未実施）

### Anthropic API: 復旧確認済み（2026-04-23 再開セッション）

status.claude.com で全サービス Operational を確認。Console・API・Billing すべて利用可能。
→ ユーザー作業: Billing → Payment Method → $5 クレジット → API Key作成（下記「ユーザー作業待ち」参照）

### 完了（再開セッションで実施）

- `.env` ファイル作成（LINE 2 値は実値、Anthropic キーのみダミー）
- uvicorn ローカル起動確認（`http://127.0.0.1:8000/health` → `{"status":"ok"}`）
- ngrok 未インストール確認（`ngrok: command not found`）
- **Codex Pre-launch Readiness レビュー 2 ラウンドで収束（Phase 2 Approved）**
  - ラウンド 1: 10 件（High 2 / Medium 4 / Low 4）反映
    - 依頼: `portfolio-codex-reviews/to-codex/2026-04-23-prelaunch-readiness-review.md`
    - 返信: `portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-review-response.md`
    - 反映: `portfolio-codex-reviews/to-codex/2026-04-23-prelaunch-readiness-applied.md`
  - ラウンド 2: 追加 2 件（High 1 / Medium 1）反映
    - 返信: `portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-applied-response.md`
    - 反映: `portfolio-codex-reviews/to-codex/2026-04-23-prelaunch-readiness-applied-v2.md`
    - 最終確認: `portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-applied-v2-response.md` → **Approved / LGTM**
  - 主要変更:
    - 実名削除（HANDOFF/review ファイル群）
    - `render.yaml`: `runtime: python` / `healthCheckPath: /health` / `PYTHON_VERSION: 3.13.5` 追加
    - `.python-version` 新規作成
    - `app/claude_client.py`: timeout 30 秒 + `max_retries=0` 明示、system prompt に 4000 文字制約
    - `app/line_client.py`: LINE 5000 字 truncate
    - `app/main.py`: 複数イベントは先頭 1 件のみ処理
    - `README.md`: LINE Developers 設定チェックリスト集約、Render Free は「疎通確認専用」明記・本番は Starter 切替を手順化
    - `tests/test_webhook.py`: 7 → 16 件（events:[]/空テキスト/非テキスト/Claude例外/LINE例外/複数イベント/truncate/client設定確認）

### 未着手

- ngrokインストール・authtoken 設定
- `.env` を実値に差し替え（LINE Channel Secret / Access Token / Anthropic API Key）
- LINE Webhook URL設定（ngrok起動後）
- LINE実機テスト
- Gitリポジトリ作成（GitHub）・push
- Renderデプロイ

## セッション再開手順

新セッションで以下を指示すれば続きから開始できる：

```
C:/Users/えりっぺ/Documents/line-ai-bot/ の続きをやる。
HANDOFF.md を読んで現状把握してから、「次にやること」に進んで。
```

## 次にやること（優先順）

### ユーザー作業待ち（Claude 側は代行不可）

以下 3 つは実値の入力やアカウント登録が必要なため、ユーザー自身で実施する必要がある。

**(A) Anthropic API Key 作成**

1. https://platform.claude.com/ にログイン
2. Billing → Payment Method 追加 → $5 クレジット購入
3. API Keys → Create Key → コピー
4. `.env` の `ANTHROPIC_API_KEY=sk-ant-dummy-...` を実キーに差し替え

**(B) LINE Channel Secret / Access Token を `.env` に反映**

1. LINE Developers Console → Messaging API チャネル → 「チャネル基本設定」タブ最下部 → Channel Secret をコピー
2. 「Messaging API 設定」タブ → Channel Access Token（長期）をコピー（取得済み）
3. `.env` の該当行を実値に差し替え

**(C) ngrok インストール・authtoken 設定**

1. https://ngrok.com/download から Windows 版をダウンロード → インストール
2. ngrok にサインアップ → ダッシュボードで authtoken 取得
3. `ngrok config add-authtoken <token>` を実行

### Claude 側でできる作業（上記 3 つが揃い次第）

**(D) ngrok 起動 & LINE Webhook 設定**

```bash
ngrok http 8000
```

別ターミナルで uvicorn 起動：

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

- LINE Developers Console → Messaging API 設定 → Webhook URL を `<ngrok_url>/callback` に設定
- Webhook 利用: ON、Webhook 再送: ON、応答メッセージ: OFF
- 「検証」ボタンで 200 OK 確認

**(E) LINE 実機テスト**

自分の LINE で Bot を友だち追加 → メッセージ送信 → Opus 応答を確認

**(F) GitHub push → Render デプロイ**

- Git リポジトリ初期化は既に完了（`main` ブランチ、2 コミット）
- GitHub リポジトリ作成 → `git remote add` → `git push`
- Render で `render.yaml` Blueprint 作成
- 環境変数を Render ダッシュボードで設定
- デプロイ後、LINE Webhook URL を Render URL に更新

## 重要な設計メモ（引き継ぎ用）

### プライバシー設計
- プロバイダー名「えりっぺ」（Bot利用者に公開される）
- 個人名（本名）は公開リポジトリ・Bot UI のいずれにも出さない設計
- 会社・事業者名も「えりっぺ」で統一

### コスト設計
- モデル: `claude-opus-4-7` 固定（ユーザー要望）
- `max_tokens=1024`（応答時間・コストバランス）
- 初期$5で100〜500メッセージ想定
- コスト削減したい場合は `CLAUDE_MODEL=claude-haiku-4-5-20251001` に切替可能

### 技術判断
- 非同期I/O対応: `run_in_threadpool` で同期クライアント（Anthropic、LINE SDK）を退避
- idempotency: インメモリ（OrderedDict + threading.Lock、TTL 300秒、10000件上限）
  - 単一uvicorn worker前提。将来複数インスタンス化時はRedisに移行
- リクエストボディのUTF-8デコード失敗は400に畳む
- reply_token 1分制限: Opusの応答が長引いて切れたら `push_message` 方式に変更検討

### Codexレビューフロー
- codex-bridgeスキル利用中（発動ワード: 「コデックスに渡す」等）
- to-codex/ → Claude→Codex依頼、from-codex/ → Codex→Claude返信
- Phase 2（実装レビュー）は収束済み

## 参考コミット履歴

```
3fe33f0 chore: adopt codex-bridge folder layout
319a236 initial commit: minimal LINE bot with Claude Opus 4.7
```

## Anthropic 障害履歴

- 2026-04-23 前半: Console 全般で「一時的なサービス停止」。API キー作成・クレジット購入ともに失敗
- 2026-04-23 再開セッション時点: status.claude.com で All Systems Operational 確認済み。復旧完了
