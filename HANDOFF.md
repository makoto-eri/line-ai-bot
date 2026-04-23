# HANDOFF — line-ai-bot

最終更新: 2026-04-24 未明（Day 1 実機テスト成功、GitHub push 済み、Render デプロイ待ち）

## プロジェクト概要

LINE Messaging API + Claude API（Opus 4.7）で業務相談 Bot を作る。FastAPI + uvicorn + Render デプロイ。

## 🎉 ここまでの達成

### 完了

- Day 1 最小実装（`app/` 一式）
- Codex レビュー 3 ラウンド収束（Approved / LGTM）
  - 初回実装レビュー（3 指摘反映）
  - Pre-launch Readiness ラウンド 1（High×2, Medium×4, Low×4 の 10 件反映）
  - Pre-launch Readiness ラウンド 2（High×1, Medium×1 の 2 件反映）
  - ngrok MSIX 問題トラブルシューティング
- テスト 16 件全パス
- ngrok 公式 zip 版を `~/Tools/ngrok/` に導入、authtoken 設定済み
- LINE Developers 設定完了（Webhook URL は ngrok 仮 URL のまま）
- **ローカル実機テスト成功**（LINE → ngrok → uvicorn → Claude Opus → LINE 往復 OK）
- **GitHub push 完了**: https://github.com/makoto-eri/line-ai-bot （private）
  - コミット: `e51fa51 feat: pre-launch hardening and device-test readiness`
  - コミット: `3fe33f0 chore: adopt codex-bridge folder layout`
  - コミット: `319a236 initial commit: minimal LINE bot with Claude Opus 4.7`

### 未着手（朝やる）

- Render デプロイ（下記「朝の作業手順」）
- LINE Webhook URL を ngrok → Render に切替
- Render 側で実機再テスト
- 必要なら GitHub repo を private → public に変更（ポートフォリオ公開用）

---

## 朝の作業手順（所要 10〜15 分）

### Step 1: Render アカウント作成（初回のみ）

1. https://render.com/ にアクセス
2. 「**Get Started for Free**」→ **GitHub でサインアップ**を選ぶ（GitHub 連携で作業を最短化）
3. Render が GitHub リポジトリへのアクセス権を求めてきたら、`makoto-eri/line-ai-bot` だけに限定して許可（全 repo に権限を渡す必要なし）

### Step 2: Blueprint でデプロイ

1. Render ダッシュボード左上「**+ New**」→「**Blueprint**」
2. GitHub リポジトリ一覧から `makoto-eri/line-ai-bot` を選択
3. Render が自動で `render.yaml` を検出して設定を読み込む
4. 「**Blueprint name**」は `line-ai-bot` のまま OK
5. 下にスクロールすると「**Sync Blueprint**」ボタン → クリック

### Step 3: 環境変数入力

Render が `sync: false` の 3 変数の入力を求めてくる。ローカル `C:\Users\えりっぺ\Documents\line-ai-bot\.env` を Notepad などで開いて、以下 3 つの値をコピー & ペースト：

| 変数名 | 値（.env からコピー） |
|---|---|
| `LINE_CHANNEL_SECRET` | `.env` の `LINE_CHANNEL_SECRET=` の右側 |
| `LINE_CHANNEL_ACCESS_TOKEN` | `.env` の `LINE_CHANNEL_ACCESS_TOKEN=` の右側 |
| `ANTHROPIC_API_KEY` | `.env` の `ANTHROPIC_API_KEY=` の右側（`sk-ant-api03-...` で始まる長い文字列） |

残りの `CLAUDE_MODEL` / `CLAUDE_MAX_TOKENS` / `PYTHON_VERSION` は `render.yaml` に固定値が書かれているので入力不要。

### Step 4: デプロイ開始・完了待ち

1. 「**Apply**」または「**Deploy**」ボタン → デプロイ開始
2. ログ画面で `Build succeeded` → `Your service is live` 相当のメッセージを待つ（5〜10 分）
3. 画面上部に **Render URL** が表示される（例: `https://line-ai-bot-xxxx.onrender.com`）

### Step 5: 疎通確認

ブラウザかターミナルで：

```bash
curl https://<Render URL>/health
# → {"status":"ok"} が返れば成功
```

### Step 6: LINE Webhook URL を Render に切替

1. https://developers.line.biz/console/ で「Claude業務相談」チャネル → **Messaging API 設定**
2. Webhook URL を `https://<Render URL>/callback` に更新
3. 「**検証**」ボタン → 「成功」が出れば OK
4. **重要**: Render **Free** プランだとコールドスタートの影響で最初のメッセージが失敗しやすい
   - すぐに使う場合は Render ダッシュボード → Settings → Plan で **Starter** にアップグレード（$7/月）
   - もしくは、LINE からメッセージ送信直前に `curl https://<Render URL>/health` を叩いてインスタンスを起こしてから送る

### Step 7: 実機再テスト

LINE アプリから Bot にメッセージ送信 → Claude Opus からの応答を確認。

### Step 8（任意）: GitHub repo を public に

ポートフォリオに URL を載せるなら：
1. https://github.com/makoto-eri/line-ai-bot の Settings
2. General タブ最下部「**Danger Zone**」→「**Change visibility**」
3. **Private → Public** に変更

これで完成。

---

## ローカル環境の現状

### 稼働プロセス

いずれも停止済み。再起動する場合：

**uvicorn**:
```bash
cd "C:/Users/えりっぺ/Documents/line-ai-bot"
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

**ngrok**（Render 側で動き出したら不要）:
```powershell
& "$env:USERPROFILE\Tools\ngrok\ngrok.exe" http 8000 --config "$env:LOCALAPPDATA\ngrok\ngrok.yml"
```

### 秘密情報（ローカルのみ、git には一切含まれない）

- `C:/Users/えりっぺ/Documents/line-ai-bot/.env` — LINE 2 値、Anthropic API Key（`.gitignore` 済み）
- `C:/Users/えりっぺ/AppData/Local/ngrok/ngrok.yml` — ngrok authtoken
- `C:/Users/えりっぺ/Documents/line-ai-bot/.claude/settings.local.json` — Claude Code 権限（authtoken 文字列を含む、`.gitignore` 済み）

### 重要な設計メモ

- プロバイダー名「えりっぺ」のみ Bot 利用者に公開、本名は非公開設計
- モデル: `claude-opus-4-7` 固定
- `max_tokens=1024`、Claude timeout 30 秒、`max_retries=0`
- LINE 5000 文字 truncate
- 1 Webhook に複数テキストイベントが入った場合は先頭のみ処理（Day 1 方針）
- idempotency はインメモリ（OrderedDict + threading.Lock、TTL 300 秒、10000 件上限）
- 単一 uvicorn worker 前提。複数インスタンス化時は Redis 化が必要

### Codex ブリッジ

- `portfolio-codex-reviews/` に to-codex / from-codex フォルダで履歴保存
- Phase 2 Approved 済みなので、普段使いで再起動は不要

### Gitリポジトリ

- リモート: `origin` → `https://github.com/makoto-eri/line-ai-bot` （private）
- ブランチ: `main`
- コミット 3 件 push 済み

---

## 困った時のトラブルシュート早見表

| 症状 | 原因 | 対処 |
|---|---|---|
| LINE 送信して無反応 | Render がスリープ中 | `curl https://<url>/health` で起こす |
| 「応答できません」がずっと返る | Anthropic クレジット不足 or API キー間違い | Anthropic Console で残高確認、Render の env 変数再確認 |
| 「検証」ボタンで失敗 | Webhook URL 誤り or uvicorn/Render 未起動 | URL 末尾 `/callback` 確認、`/health` 疎通確認 |
| 二重返信が来る | LINE Official Account Manager の「応答メッセージ」が ON のまま | OFF にする |
| Render ビルド失敗 | `requirements.txt` か `render.yaml` の問題 | Render のログ画面で `Build failed` 詳細確認 |

---

## Next Steps After Render Deploy（時間ある時）

- 会話履歴を保持するよう設計変更（現状は 1 メッセージ = 1 Claude 呼び出しで履歴なし）
- Redis で idempotency 共有、複数 worker 化
- 応答時間の長いメッセージを push_message 方式に変更
- Sentry などでエラーモニタリング
- README をポートフォリオ向けに整形（スクリーンショット追加、使用技術バッジなど）
