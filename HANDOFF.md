# HANDOFF — line-ai-bot

作成日時: 2026-04-23

## プロジェクト概要

LINE Messaging API + Claude API（Opus 4.7）で業務相談Botを作る。FastAPI + ngrok + Renderデプロイ。3つの並行プロジェクトのうちの1つ。

## 現在の状態

**Day 1の骨組みは完成、ローカルテスト通過済み**。次はGit管理 → LINE実機テスト → Renderデプロイ。

### できていること

- プロジェクトファイル一式（`app/`, `tests/`, Procfile, render.yaml, README.md 他）を作成済み
- `requirements.txt` の依存をvenvにインストール済み（`.venv/`）
- `pytest` 4件パス（署名検証の正常/異常系 + `/health` + ハッピーパス）
- モデルは `claude-opus-4-7` で設定（max_tokens=1024）
- 環境変数は `pydantic-settings` で起動時バリデーション済み

### できていないこと

- Gitリポジトリ未初期化（`git init` から）
- GitHubリポジトリ未作成
- LINE Developers設定未実施（Channel Secret / Access Token未取得）
- ngrok実機テスト未実施
- Renderデプロイ未実施
- `.env` ファイル未作成（`.env.example` のみ存在）

## ファイル構成

```
line-ai-bot/
├── app/
│   ├── __init__.py
│   ├── main.py          # Webhookエンドポイント (/callback, /health)
│   ├── line_client.py   # LINE署名検証＋返信
│   ├── claude_client.py # Claude Opus 4.7呼び出し
│   └── config.py        # pydantic-settings 環境変数管理
├── tests/
│   ├── __init__.py
│   └── test_webhook.py  # 4件パス済み
├── .env.example
├── .gitignore
├── Procfile
├── render.yaml
├── requirements.txt
├── README.md
└── HANDOFF.md (このファイル)
```

## 次にやること（優先順）

1. **Git初期化**
   ```bash
   cd "C:/Users/えりっぺ/Documents/line-ai-bot"
   git init
   git add .
   git commit -m "initial commit: minimal LINE bot with Claude Opus 4.7"
   ```

2. **Codexレビューの反映**
   - 右のCodexターミナルから提案内容を保存したファイル（例: `codex-review-01.md`）を確認
   - 提案を検討→適用→再テスト→コミット

3. **LINE Developers設定 → ローカル実機テスト**
   - LINE Developers ConsoleでMessaging APIチャネル作成
   - Channel Secret / Access Token取得
   - `.env.example` を `.env` にコピーして値を記入
   - `uvicorn app.main:app --reload` 起動
   - 別シェルで `ngrok http 8000`
   - LINE Developers の Webhook URL を `<ngrok_url>/callback` に設定
   - LINEから自分のBotに送信 → Opusが応答することを確認

4. **Renderデプロイ**
   - GitHubリポジトリ作成 → push
   - Render で Blueprint（`render.yaml` 使用）または Web Service 作成
   - 環境変数をダッシュボードで設定
   - デプロイ後、LINE Developers の Webhook URL を Render URL に更新

## 技術判断メモ

- **モデルはOpus 4.7固定**（ユーザー要望）。コスト感は haikuの15倍だが品質優先
- **max_tokens=1024** で応答時間とコストのバランスを取っている
- **`CLAUDE_MAX_TOKENS` 環境変数で調整可能**
- **Render Free プラン**はスリープ復帰遅延あり（最大30秒程度）。実運用で問題になれば有料プランor定期ping
- **reply_token 1分制限**: Opusの応答が長引いて切れるケースが出たら `push_message` 方式に変更

## Codexのレビュー観点（当初計画から）

1. 署名検証の正しさ
2. Webhookタイムアウト対策
3. 環境変数の取り扱い
4. エラーハンドリングの穴（画像・スタンプ・空メッセージ等）
5. Renderデプロイ設定
6. 過剰設計になっていないか
7. テストカバレッジ

## 今セッションで触った設定（参考）

- グローバル `~/.claude/CLAUDE.md` に「モデル委譲ルール」セクション追加（サブエージェントのみSonnet/Haiku、メインはOpus固定）
- `~/.claude/rules/*.md` を整理（progress-trackingはスキル化、revision-logはnatural-japanese-writingスキルの参照配下へ移動）
- グローバル読み込み量を 6.8KB → 4.0KB に圧縮済み

## 作業再開プロンプト例

新セッションで以下のように指示すると即座に続きが始められます：

```
C:/Users/えりっぺ/Documents/line-ai-bot/ プロジェクトの続きをやる。
HANDOFF.md を読んで現状把握してから、「次にやること」の項目に着手して。
Codex提案のファイル（codex-review-01.md など）があれば先に反映して。
```
