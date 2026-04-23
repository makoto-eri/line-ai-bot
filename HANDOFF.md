# HANDOFF — line-ai-bot

最終更新: 2026-04-24 朝（**Render 本番稼働成功・全工程完了・GitHub public 化済み**）

## 本番 URL

- **LINE Bot**: LINE アプリで「Claude業務相談」を友だち追加 → メッセージ送信
- **Render Webhook**: https://line-ai-bot-phya.onrender.com/callback
- **Render 管理ダッシュボード**: https://dashboard.render.com/
- **GitHub リポジトリ（public）**: https://github.com/makoto-eri/line-ai-bot

## プロジェクト概要

LINE Messaging API + Claude API（Opus 4.7）で業務相談 Bot を作る。FastAPI + uvicorn + Render デプロイ。

## 🎉 達成内容

### 実装・レビュー

- 最小実装（`app/` 一式、4 ファイル）
- 外部 AI（Codex）による 3 ラウンドのコードレビュー全て収束（Approved / LGTM）
  - 初回実装レビュー（3 指摘反映）
  - Pre-launch Readiness ラウンド 1（High×2, Medium×4, Low×4 の 10 件反映）
  - Pre-launch Readiness ラウンド 2（High×1, Medium×1 の 2 件反映）
  - ngrok MSIX 版トラブルシューティング
- 自動テスト 16 件全パス
- Codex とのやり取りログは `portfolio-codex-reviews/` に保存

### 本番稼働

- 2026-04-24 07:26 (JST) Render 初回デプロイ成功
- `/health` エンドポイント疎通確認
- LINE Webhook URL を Render URL に設定
- 実機テスト: 「おはよう」→「おはようございます。ご相談内容をどうぞ」の Claude 応答を確認

### コミット履歴

```
7682321 docs: clarify Free-plan wake-up workaround wording
b9d6825 docs: record production deploy completion
574348e docs: add morning pickup guide for Render deploy
e51fa51 feat: pre-launch hardening and device-test readiness
3fe33f0 chore: adopt codex-bridge folder layout
319a236 initial commit: minimal LINE bot with Claude Opus 4.7
```

---

## 任意の追加作業（必要になったら）

- **Render Starter プランへアップグレード**（$7/月、常時稼働、コールドスタート解消）
  - Render Dashboard → line-ai-bot → Settings → Instance Type
- **README をポートフォリオ向けに整形**
  - スクリーンショット、QR コード、使用技術バッジ、工夫ポイントの説明など

---

## ローカル環境の現状

### 稼働プロセス

すべて停止済み（本番は Render 上で稼働中）。再起動する場合：

**uvicorn（Python 開発サーバー）**:
```bash
cd "C:/Users/えりっぺ/Documents/line-ai-bot"
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

**ngrok（ローカルを外部公開するトンネル）**（Render 本番稼働中は不要）:
```powershell
& "$env:USERPROFILE\Tools\ngrok\ngrok.exe" http 8000 --config "$env:LOCALAPPDATA\ngrok\ngrok.yml"
```

### 秘密情報（ローカルのみ、GitHub には一切含まれない）

| ファイル | 中身 | 管理 |
|---|---|---|
| `C:/Users/えりっぺ/Documents/line-ai-bot/.env` | LINE Channel Secret、LINE Access Token、Anthropic API Key | `.gitignore` 済み |
| `C:/Users/えりっぺ/AppData/Local/ngrok/ngrok.yml` | ngrok authtoken | Render 利用時は不要 |
| `C:/Users/えりっぺ/Documents/line-ai-bot/.claude/settings.local.json` | Claude Code の権限設定（authtoken 文字列を含む） | `.gitignore` 済み |

### 重要な設計メモ

- プロバイダー名「えりっぺ」のみ Bot 利用者に公開、本名は非公開設計
- 使用モデルは `claude-opus-4-7` に固定
- `max_tokens=1024`、Claude API 呼び出しタイムアウト 30 秒、リトライ無効（`max_retries=0`）
- LINE テキストメッセージは 5000 文字で末尾省略
- 1 回の Webhook に複数のテキストメッセージが含まれる場合は先頭 1 件のみ処理（Day 1 方針）
- 重複イベント検出はメモリ上の辞書（TTL 300 秒、最大 10000 件）
- 現在は 1 台のサーバーで動かす前提。将来サーバーを増やす場合は重複排除を共有ストレージ（Redis など）に移す必要あり

### Codex ブリッジ

- `portfolio-codex-reviews/` に to-codex / from-codex フォルダで履歴保存
- 実装レビューは収束済みなので再起動不要

### Git リポジトリ

- リモート: `origin` → `https://github.com/makoto-eri/line-ai-bot` （**public**）
- ブランチ: `main`
- Render の Auto-Deploy が有効なので、`main` へ push すれば自動で再デプロイされる

---

## 困った時のトラブルシュート早見表

| 症状 | 原因 | 対処 |
|---|---|---|
| LINE に送信しても無反応 | Render Free プランのスリープ中（15 分放置でスリープ） | ブラウザで `https://line-ai-bot-phya.onrender.com/health` を開いて起こしてから送る。または Starter プランへ切替 |
| 「応答できません」がずっと返る | Anthropic のクレジット不足 または API キー誤り | Anthropic Console で残高確認、Render の環境変数を再確認 |
| LINE Developers の「検証」ボタンで失敗 | Webhook URL 誤り、または Render 未起動 | URL の末尾が `/callback` になっているか確認、`/health` が `{"status":"ok"}` を返すか確認 |
| 同じ内容が二重に返信される | LINE Official Account Manager の「応答メッセージ」が ON のまま | LINE Official Account Manager 側で OFF にする |
| Render デプロイが失敗する | `requirements.txt` か `render.yaml` の設定に問題 | Render のログ画面で `Build failed` の詳細を確認 |

---

## Next Steps（時間ある時の改善候補）

- 会話履歴を保持するよう設計変更（現状は 1 メッセージごとに独立した Claude 呼び出し）
- 重複排除メモリを Redis に移して複数サーバー対応
- 応答時間が長くなるケースに備えて LINE の `push_message` API（reply_token 不要で任意タイミングで送信）方式へ切替
- Sentry などでエラー監視の導入
- README をポートフォリオ向けに整形（スクリーンショット追加、使用技術バッジなど）

---

## 参考：デプロイ手順（完了済みの記録）

上記はすべて完了しているが、将来また同様の構成を組む場合や、トラブルで再デプロイが必要になった場合のための記録。

### 1. Render アカウント作成

1. https://render.com/ にアクセス → **Get Started for Free**
2. **GitHub でサインアップ**（連携で作業を最短化）
3. Render が GitHub リポジトリへのアクセス権を求めてきたら、`makoto-eri/line-ai-bot` だけに限定して許可

### 2. Blueprint でデプロイ

1. Render ダッシュボード左上「**+ New**」→「**Blueprint**」
2. GitHub リポジトリ一覧から `makoto-eri/line-ai-bot` を選択
3. Render が自動で `render.yaml` を検出して設定を読み込む
4. 「**Sync Blueprint**」ボタン

### 3. 環境変数入力

Render が `sync: false` の 3 変数の入力を求めてくる。ローカル `.env` を Notepad 等で開いて値をコピー & ペースト：

| 変数名 | 値の取得元 |
|---|---|
| `LINE_CHANNEL_SECRET` | `.env` の `LINE_CHANNEL_SECRET=` の右側 |
| `LINE_CHANNEL_ACCESS_TOKEN` | `.env` の `LINE_CHANNEL_ACCESS_TOKEN=` の右側 |
| `ANTHROPIC_API_KEY` | `.env` の `ANTHROPIC_API_KEY=` の右側（`sk-ant-api03-...` で始まる長い文字列） |

### 4. デプロイ完了待ち（5〜10 分）

1. デプロイ開始ボタン
2. ログ画面で `Build succeeded` → `Your service is live` を待つ
3. 画面上部に Render の公開 URL（例: `https://line-ai-bot-xxxx.onrender.com`）が表示される

### 5. 疎通確認

ブラウザで `https://<Render URL>/health` を開く → `{"status":"ok"}` が返れば成功

### 6. LINE Webhook URL を Render に切替

1. https://developers.line.biz/console/ → 「Claude業務相談」チャネル → **Messaging API 設定**
2. Webhook URL を `https://<Render URL>/callback` に更新
3. 「**検証**」ボタン → 「成功」が出れば OK
4. **重要**: Render Free プランのコールドスタート対策
   - 常時稼働させたい場合は Starter プランへアップグレード（$7/月）
   - もしくは、LINE からメッセージ送信直前に、ブラウザで `https://<Render URL>/health` を開く（または `curl` で呼び出す）→ インスタンスが起動してから送る
