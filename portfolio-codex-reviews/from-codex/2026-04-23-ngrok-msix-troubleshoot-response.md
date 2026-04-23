# ngrok MSIX Troubleshoot 返信

## 推奨ルート

**B: MSIX版を使わず、公式zip版 ngrok.exe に差し替える**のが最短かつ最安全。

理由:

- 現象は `update_channel` 空値だけでなく、「保存したと言っている config 実体が見つからない」ことが本質。MSIX/WindowsApps の仮想化または実行エイリアスに巻き込まれており、C の config 直編集は探索コストが高い。
- A は試す価値はあるが、`config check` が invalid config で落ちているため、`ngrok http 8000` も同じ config 読み込みで落ちる可能性が高い。
- D の `--authtoken` は公式CLI上は使えるが、token を毎回扱う運用になり、履歴・画面表示・誤貼り付けのリスクが増える。緊急回避としては可、本線にはしない。
- B なら公式ドキュメント通り、Windows の標準 config は `%LocalAppData%\ngrok\ngrok.yml` に固定でき、`--config` で明示して MSIX 側の不可視 config を完全に避けられる。

## 手順（具体コマンド）

PowerShell 7 で実行。

### 1. 公式zip版をユーザーディレクトリへ展開

```powershell
$installDir = Join-Path $env:USERPROFILE "Tools\ngrok"
$zipPath = Join-Path $env:TEMP "ngrok-v3-stable-windows-amd64.zip"

New-Item -ItemType Directory -Force $installDir | Out-Null
Invoke-WebRequest `
  -Uri "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip" `
  -OutFile $zipPath
Expand-Archive -LiteralPath $zipPath -DestinationPath $installDir -Force

& "$installDir\ngrok.exe" version
```

ARM版Windowsなら `amd64` ではなく ngrok公式Downloadページの Windows ARM64 zip を使う。

### 2. 現シェルではzip版を優先

```powershell
$env:Path = "$installDir;$env:Path"
Get-Command ngrok -All
```

先頭が `C:\Users\<user>\Tools\ngrok\ngrok.exe` になっていればよい。

恒久的にも優先したい場合:

```powershell
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
  [Environment]::SetEnvironmentVariable("Path", "$installDir;$userPath", "User")
}
```

新しいターミナルを開いたあと、再度:

```powershell
Get-Command ngrok -All
ngrok version
```

### 3. config を明示パスで作る

token を履歴に残さないため、コマンド行に直書きしない。

```powershell
$configDir = Join-Path $env:LOCALAPPDATA "ngrok"
$configPath = Join-Path $configDir "ngrok.yml"
New-Item -ItemType Directory -Force $configDir | Out-Null

$token = Read-Host "Paste ngrok authtoken"
& "$installDir\ngrok.exe" config add-authtoken $token --config $configPath
Remove-Variable token

& "$installDir\ngrok.exe" config check --config $configPath
Get-Content $configPath
```

`config check` が通ればOK。`Get-Content` で token が表示されるため、画面共有中なら実行しない。

### 4. uvicorn を起動

別ターミナル:

```powershell
cd "C:\Users\えりっぺ\Documents\line-ai-bot"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

疎通確認:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 5. ngrok を起動

ngrok 用ターミナル:

```powershell
$installDir = Join-Path $env:USERPROFILE "Tools\ngrok"
$configPath = Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"
& "$installDir\ngrok.exe" http 8000 --config $configPath
```

表示された `https://...ngrok-free.app` などのURLに `/callback` を付けて、LINE Developers の Webhook URL に設定する。

## リスクと回避策

- **PATH衝突**: `WindowsApps\ngrok.exe` が先に拾われるとMSIX版が再度起動する。回避策は、必ず `& "$installDir\ngrok.exe" ...` のフルパスで呼ぶこと。恒久運用は user PATH の先頭へ `$installDir` を追加する。
- **Store/MSIX版が残る**: 残っていてもフルパス起動なら問題ない。後で整理するなら Windows 設定 → アプリ → インストールされているアプリ、または「アプリ実行エイリアス」で ngrok を無効化する。
- **token露出**: `Read-Host` で受ければ PowerShell履歴に token 文字列は残らない。`Get-Content $configPath` は token を表示するので必要時だけ実行。
- **config check がまだ `update_channel` で落ちる**: zip版をフルパスで実行できていない可能性が高い。`& "$installDir\ngrok.exe" version` が `msix` を含まないことを確認する。

## 追加で確認してほしいコマンド

まずはMSIX版で A を深追いせず、zip版のフルパス確認を優先する。

```powershell
Get-Command ngrok -All
& "$env:USERPROFILE\Tools\ngrok\ngrok.exe" version
& "$env:USERPROFILE\Tools\ngrok\ngrok.exe" config check --config "$env:LOCALAPPDATA\ngrok\ngrok.yml"
```

緊急回避として D を使う場合だけ:

```powershell
$installDir = Join-Path $env:USERPROFILE "Tools\ngrok"
$token = Read-Host "Paste ngrok authtoken"
& "$installDir\ngrok.exe" http 8000 --authtoken $token
Remove-Variable token
```

ただしこれは一時回避。Day 1 実機テスト後も使うなら、B の明示 config 方式に戻す。

## 参照

- ngrok Agent Config: Windows の標準 config は `%LocalAppData%\ngrok\ngrok.yml`
- ngrok CLI: `config add-authtoken`, `config check`, `http --config`, `http --authtoken` が公式CLIに存在
