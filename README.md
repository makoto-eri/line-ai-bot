# line-ai-bot

LINE で受信したテキストメッセージに対して、Claude API（Opus 4.7）で回答を生成して返信する最小構成の Bot です。

## 動作環境

- Python 3.13（ローカル開発・Render デプロイとも `.python-version` / `PYTHON_VERSION` で固定）
- FastAPI + uvicorn
- Anthropic Python SDK
- LINE Messaging API SDK v3

## セットアップ（Windows）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# .env を編集して各トークンを設定
uvicorn app.main:app --reload
```

## 環境変数

| 変数名 | 必須 | 用途 |
|--------|:---:|------|
| `LINE_CHANNEL_SECRET` | ✓ | Webhook 署名検証 |
| `LINE_CHANNEL_ACCESS_TOKEN` | ✓ | LINE への返信 API 認証 |
| `ANTHROPIC_API_KEY` | ✓ | Claude API 認証 |
| `CLAUDE_MODEL` | - | 使用モデル。デフォルト `claude-opus-4-7` |
| `CLAUDE_MAX_TOKENS` | - | 返答の最大トークン数。デフォルト `1024` |

## ローカル確認（ngrok 経由で実機テスト）

1. `uvicorn app.main:app --reload` で起動（ポート 8000）
2. 別シェルで `ngrok http 8000` を実行し、公開 URL を取得
3. LINE Developers Console → Messaging API 設定 → Webhook URL を `https://<ngrok-url>/callback` に設定
4. LINE Developers Console 側のチェックリスト（以下をすべて確認）：
   - **Webhook の利用**: ON
   - **Webhook の再送**: ON（LINE 側が失敗時に自動リトライ）
   - **応答メッセージ**（LINE Official Account Manager 側）: OFF（これを OFF にしないと定型応答と Bot 応答が二重送信される）
   - **あいさつメッセージ**: 任意（友だち追加時のメッセージ）
   - **Webhook URL 右の「検証」ボタン**: 押して `200 OK` を確認
5. 自分の LINE から Bot へメッセージ送信 → 応答確認

## テスト

```bash
pytest
```

## Render デプロイ

`render.yaml` のデフォルトは `plan: free`（疎通確認・ポートフォリオ閲覧用）。LINE Webhook に常時向ける場合は Starter 以上へ切り替える想定。

1. GitHub へ push
2. Render で `render.yaml` を Blueprint として読み込ませて Web Service 作成
3. 環境変数 `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `ANTHROPIC_API_KEY` を Render ダッシュボードで設定
4. デプロイ後、LINE Developers の Webhook URL を `https://<render-url>/callback` に更新

### プランの選び方（重要）

- **`render.yaml` の `plan: free` は疎通確認・ポートフォリオ閲覧専用。** Render Free は 15 分アイドルでスピンダウンし、次回リクエストで約 1 分のコールドスタートが発生する。LINE の `reply_token` は Webhook 受信後 1 分以内に使う必要があるため、Free に Webhook を向けた直後の初回メッセージは失敗しやすい。
- **LINE Webhook URL を Render に向ける前に、Render ダッシュボードで Starter 以上へ変更すること。** 常時起動となり reply_token の 1 分制限に余裕を持って間に合う。
- Free のまま LINE 実機テストをする場合の回避策：
  1. LINE からメッセージ送信する直前に、ブラウザで `https://<render-url>/health` を開く（または `curl` で叩く）→ インスタンスが起動する
  2. その直後（30 秒以内目安）に LINE からメッセージ送信
  - この運用は動作確認専用で、継続利用には向かない

## 挙動仕様

- 署名ヘッダがない／不正な場合は `400` を返す
- 非 UTF-8 のリクエストボディは `400` を返す
- 非テキストイベント（スタンプ・画像など）は無視して `200` を返す
- 空白のみのテキストは無視
- 1 つの Webhook に複数のテキストイベントが入っている場合、**先頭 1 件のみ処理**する（`reply_token` 1 分制限を守るため）
- `webhookEventId` によるインメモリ idempotency（TTL 300 秒、10000 件上限）で重複イベントをスキップ
- `deliveryContext.isRedelivery=true` のイベントは処理しない（LINE 側の再送ループ回避）
- Claude API 呼び出しは 30 秒でタイムアウト。失敗時はフォールバック文言を返信
- Claude の返答が LINE の TextMessage 上限（5000 文字）を超える場合は自動で末尾省略
- LINE 返信 API が失敗しても `200` を返す（LINE 側の再送ループを避ける）

## 既知の制約

- 単一 uvicorn worker 前提。複数インスタンス化する場合、idempotency キャッシュを Redis 等へ外出し要
- 会話履歴は保持しない（1 メッセージ = 1 回の Claude 呼び出し）
- 応答が reply_token 制限に間に合わない場合は将来的に `push_message` への切り替えを検討
