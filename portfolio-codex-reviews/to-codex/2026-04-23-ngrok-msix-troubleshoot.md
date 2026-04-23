# ngrok MSIX版トラブルシューティング相談

作成日: 2026-04-23
関連プロジェクト: line-ai-bot（Phase 2 Approved 済み、LINE 実機テスト直前）

## Codex へのお願い

Phase 2 の実装レビューは収束済みで、残る手順は

1. Anthropic API Key 取得（ユーザー作業中）
2. **ngrok 起動 → LINE Webhook URL 設定 → 実機テスト** ← ここで詰まっている
3. GitHub push → Render デプロイ

ngrok のインストール自体は済んでいるが、**設定ファイルの `update_channel` が空値**というエラーで `ngrok config check` が通らない状態。**MSIX 版特有のサンドボックスで config ファイルが外から見えない**ため surgical fix も効かない。

下記の「再現状況」を読んで、**どのルートで進めるのが最短で安全か**を判定してほしい。

## 再現状況（事実のみ）

### 環境

- Windows 11 Home 10.0.26200
- シェル: Git Bash (bash) + PowerShell 7
- Python 3.13.5 / uvicorn 既に動作確認済み
- ngrok は `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\ngrok.exe` から起動（= Microsoft Store / MSIX 経由でインストール）

### バージョン

```
ngrok version 3.36.1-msix-stable
```

### 実施コマンドと結果

**1. ngrok config check（authtoken 登録前）**

```
ERROR:  Error reading configuration file 'C:\Users\<user>\AppData\Local/ngrok/ngrok.yml':
open C:\Users\<user>\AppData\Local\ngrok\ngrok.yml: The system cannot find the path specified.
```

→ 設定ファイルがまだ存在しない。

**2. ngrok config add-authtoken `<authtoken>`**

```
Authtoken saved to configuration file: C:\Users\<user>\AppData\Local/ngrok/ngrok.yml
```

→ ngrok 本体は「保存した」と言っている。

**3. 再度 ngrok config check**

```
ERROR:  Invalid configuration property value for 'update_channel', '':
Unrecognized channel. Acceptable values are 'stable', 'beta', or 'unstable'
```

→ `update_channel:` キーが空値で書き込まれている。

**4. 保存先パスの実在確認**

```powershell
Test-Path "$env:LOCALAPPDATA\ngrok\ngrok.yml"
# => False

Test-Path "C:\Users\<user>\AppData\Local\ngrok\ngrok.yml"
# => False

Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter "*ngrok*"
# => 空（UWP パッケージ直下にも見えない）

Get-ChildItem "$env:LOCALAPPDATA" -Filter "*ngrok*"
# => 空

Get-AppxPackage | Where-Object { $_.Name -match "ngrok" }
# => 空（Appx パッケージとしても登録されていない）
```

→ **ngrok が保存したと主張するパスにファイルが存在しない**。MSIX サンドボックスで書き込みがリダイレクトされている可能性が高いが、`AppData\Local\Packages\` 配下でもヒットしない。

### 判明していること

- authtoken 文字列は ngrok 側で受領済み（登録コマンドが Success を返している）
- `config check` が通らないので、`ngrok http 8000` が起動するかは未検証
- `update_channel` の空値は MSIX ビルドの既知不具合報告が散見される（未確認情報）
- ユーザー側の作業可能範囲: Windows 11 の GUI、PowerShell/cmd、Git Bash、管理者権限も可

## 進める候補ルート（Codex に選定してほしい）

### ルート A: 「まず動かしてみる」
`ngrok http 8000` を実際に叩く。`config check` のエラーは warning 止まりで、トンネル起動自体は通る可能性がある。

- 利点: 試すだけなのでコストゼロ
- 懸念: MSIX ビルドが認証フロー中に `update_channel` を参照して死ぬ可能性

### ルート B: MSIX 版をアンインストール → 公式 zip バイナリに差し替え
https://ngrok.com/download から Windows 版 zip を落として、任意ディレクトリ（例: `C:\Users\<user>\ngrok\`）に展開、PATH を通す。

- 利点: MSIX サンドボックス問題から完全に解放される。`%LOCALAPPDATA%\ngrok\ngrok.yml` が実体として生成される
- 懸念: Microsoft Store 経由でインストールした ngrok を事前にアンインストールしないと PATH 優先度で衝突する可能性

### ルート C: 設定ファイルを直接編集
MSIX の sandbox 内 config を特定して Notepad で `update_channel: stable` に書き換える。

- 利点: 最小変更
- 懸念: sandbox 内パス特定が当てずっぽう（`AppData\Local\Packages\*\LocalCache\` 系を Get-ChildItem で舐めたがヒットせず）

### ルート D: config ファイル不要で CLI フラグ指定
`ngrok http 8000 --authtoken <token>` のように毎回 authtoken を渡す。

- 利点: config 問題を回避できる
- 懸念: 毎回 token 貼り付けが必要 / history に残る / 長期運用向きではない（ただし実機テスト用途なら一時的に許容）

## 期待するアウトプット

`portfolio-codex-reviews/from-codex/2026-04-23-ngrok-msix-troubleshoot-response.md` に以下を書いてほしい：

```markdown
# ngrok MSIX Troubleshoot 返信

## 推奨ルート
A / B / C / D のいずれか or 組み合わせ（理由付きで）

## 手順（具体コマンド）
1. ...
2. ...

## リスクと回避策

## 追加で確認してほしいコマンド（あれば）
- `ngrok http 8000` を実際に叩いてほしいか
- `Get-ChildItem` の追加検索パスを提案
```

## 前提・制約

- **セキュリティ**: authtoken は config ファイル内にあれば OK（ローカルのみ）。history 残存や clipboard に出るのは避けたい
- **急ぎ度**: 高。Anthropic API Key と並行して Day 1 中に LINE 実機テストまで到達したい
- **変更したくない**: 既存の `app/` 下コード、`render.yaml`、`README.md`（ngrok は開発用途なのでコード側は触らない想定）

## 参考情報

- 前回までの Codex 往復履歴: `portfolio-codex-reviews/from-codex/` 配下
- 最終的な Phase 2 Approved: `portfolio-codex-reviews/from-codex/2026-04-23-prelaunch-readiness-applied-v2-response.md`
- HANDOFF.md: プロジェクト全体の進捗
