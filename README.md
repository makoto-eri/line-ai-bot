# line-ai-bot

LINEで受信したテキストメッセージに対して、Claude API（Opus 4.7）で回答を生成して返信する最小構成のBotです。

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
| `LINE_CHANNEL_SECRET` | ✓ | Webhook署名検証 |
| `LINE_CHANNEL_ACCESS_TOKEN` | ✓ | LINEへの返信API認証 |
| `ANTHROPIC_API_KEY` | ✓ | Claude API認証 |
| `CLAUDE_MODEL` | - | 使用モデル。デフォルト `claude-opus-4-7` |
| `CLAUDE_MAX_TOKENS` | - | 返答の最大トークン数。デフォルト `1024` |

## ローカル確認

1. `uvicorn app.main:app --reload` で起動（ポート8000）
2. 別シェルで `ngrok http 8000` を実行し、公開URLを取得
3. LINE Developers Console で Webhook URL を `https://<ngrok-url>/callback` に設定、Webhook利用ONに
4. 自分のLINEからBotへメッセージ送信 → 応答確認

## テスト

```bash
pytest
```

## Renderデプロイ

1. GitHubへpush
2. Renderで新規Web Service作成（`render.yaml` を使う場合はBlueprint）
3. 環境変数 `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `ANTHROPIC_API_KEY` をダッシュボードで設定
4. デプロイ後、LINE Developers の Webhook URL を `https://<render-url>/callback` に更新

## 注意点

- 署名ヘッダがない／不正な場合は `400` を返す
- 非テキストイベント（スタンプ・画像など）は無視して `200` を返す
- Claude API失敗時はフォールバック文言を返信、LINE送信失敗時はログのみ
- Render Freeプランは15分アイドルでスリープ。初回リクエストで数十秒の遅延あり
- Opus 4.7は応答に数秒〜十数秒かかる場合あり。長引いて reply token が1分切れる場合は `push_message` への切替を検討
