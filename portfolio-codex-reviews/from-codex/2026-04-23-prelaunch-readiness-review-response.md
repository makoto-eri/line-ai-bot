# Pre-launch Readiness Review 返信

## サマリ

- 判定: LINE実機テストは Go。Render URLを本番Webhookとして使う前は条件付き Go。
- ブロッカー: 1件。公開GitHubへpushする前に `HANDOFF.md` の非公開実名を消すこと。
- 主要懸念: Render Free cold start と reply token 1分制限、Claude呼び出しの実行時間上限なし、複数イベントを逐次処理する設計。

## Findings

### [High] 公開前ドキュメントに非公開方針の実名が残っている

- 対象: `HANDOFF.md:115`, `HANDOFF.md:117`
- 問題: `HANDOFF.md` に本名が明記されていた。公開GitHubリポジトリへpushすると、まさに非公開にしたい実名が履歴に残る。`.gitignore` では防げない。
- 提案: push前に実名を削除し、「本名は公開しない」「個人名は記載しない」などの抽象表現へ置換する。すでにコミット済み履歴に含まれる場合は履歴修正も検討する。

### [High] Render Free をLINE Webhookにすると初回応答がreply token期限に近すぎる

- 対象: `render.yaml:5`, `app/main.py:95`, `app/main.py:103`, `README.md:51`
- 問題: Render Freeは15分アイドル後にスピンダウンし、次回HTTPリクエストでスピンアップに約1分かかる。LINEのreply tokenはWebhook受信後1分以内の使用が必要で、実際の有効時間はネットワーク遅延等で変動する。Free cold start + Opus応答 + LINE返信API呼び出しは、初回メッセージで失敗しやすい。
- 提案: RenderにWebhook URLを向ける段階では `plan: starter` 以上にする。Freeで試すなら「初回は失敗する可能性が高い」前提で、事前に `/health` を叩いて起こしてからLINE送信する運用に限定する。READMEにもこの制約を明記する。

### [Medium] Claude生成にアプリ側の短いタイムアウトがない

- 対象: `app/claude_client.py:18`, `app/main.py:95`
- 問題: `generate_reply()` は同期API呼び出しを行い、`callback` はその完了を待ってからLINEへreplyする。SDK側のデフォルト挙動に依存しており、このアプリとして「何秒以内に諦めてフォールバック返信するか」が定義されていない。Opus 4.7は高品質だがレイテンシはModerateで、reply token制限と相性が悪い。
- 提案: Anthropic client作成時または呼び出し時に明示的な短めのtimeoutを設定する。Day 1なら20-30秒程度でフォールバック文言を返す設計が現実的。長時間処理を許すなら、replyではなくpush message方式へ設計変更する。

### [Medium] 1つのWebhookに複数テキストイベントが入ると逐次処理で後続replyが遅れる

- 対象: `app/main.py:73`, `app/main.py:95`, `app/main.py:103`
- 問題: LINE仕様上、1つのWebhookに複数イベントが入ることがある。現在はイベントを順番に処理し、各イベントごとにClaude生成を待つ。2件以上のテキストイベントが同梱されると、後続イベントのreply token消費が遅れ、1分制限に近づく。
- 提案: Day 1では「1 webhook内の複数テキストイベントは先頭のみ処理」または「各イベントを並行処理し、短いtimeoutを設ける」のどちらかに決める。少なくとも複数イベントケースのテストを追加して挙動を固定する。

### [Medium] LINE返信テキスト長の上限対策がない

- 対象: `app/claude_client.py:26`, `app/line_client.py:29`, `README.md:52`
- 問題: Claudeの返答をそのまま `TextMessage(text=reply_text)` に渡している。`CLAUDE_MAX_TOKENS=1024` なので通常は大きく外れにくいが、LINEテキストメッセージの文字数上限を超えると返信APIが400になり、ユーザーには何も返らない。
- 提案: LINE送信前に安全な長さでtruncateするか、Claude system promptと送信前処理の両方で短文制約を固定する。テストで長文応答時にLINE送信可能な長さへ収まることを確認する。

### [Medium] `render.yaml` にhealth check pathがない

- 対象: `render.yaml:1`
- 問題: アプリには `/health` があるが、Blueprintに `healthCheckPath: /health` がない。RenderはBlueprintでhealth check pathを設定でき、ゼロダウンタイムdeployや稼働判定に使える。現状でも起動はできるが、Render側が明示的にアプリの健全性を確認しない。
- 提案: `render.yaml` のWeb Service定義に `healthCheckPath: /health` を追加する。

### [Low] `render.yaml` が旧フィールド `env` を使っている

- 対象: `render.yaml:4`
- 問題: Renderの現行Blueprint仕様では `runtime` が推奨で、`env` はサポートされるが discouraged。今すぐ壊れる可能性は低いが、これから作るBlueprintとしては古い書き方。
- 提案: `env: python` を `runtime: python` に置き換える。

### [Low] Python実行バージョンが固定されていない

- 対象: `render.yaml:8`, `requirements.txt:1`
- 問題: 依存は範囲指定だが、Render側のPythonバージョンが明示されていない。ローカルはPython 3.13.5でpytest済みだが、Renderのデフォルト変更で挙動差が出る余地がある。
- 提案: `.python-version` か Render環境変数 `PYTHON_VERSION` で使用バージョンを固定する。Day 1ならローカルと同じ3.13系、または依存互換性重視で3.12系を選ぶ。

### [Low] READMEが実機テスト時のLINE側設定を十分に固定していない

- 対象: `README.md:26`, `HANDOFF.md:97`
- 問題: READMEにはWebhook URL設定はあるが、「Webhook利用ON」「応答メッセージOFF」「Webhook再送ON」「検証ボタンで200確認」など、実機テストで詰まりやすい設定がHANDOFF側に分散している。将来READMEだけ読んだ人が再セットアップすると漏れやすい。
- 提案: READMEのローカル確認手順にLINE Developers側の設定チェックリストを追加する。

### [Low] テストはDay 1として妥当だが、READMEで宣言している挙動の一部が未固定

- 対象: `tests/test_webhook.py:69`, `README.md:48`
- 問題: 7件はDay 1として過剰ではなく妥当。ただしREADMEが明記する「非テキストイベントは無視」「空テキストは無視」、LINE仕様上あり得る「events: []」、複数イベント、Claude失敗時フォールバック、LINE返信失敗時200継続は未テスト。
- 提案: 実機テスト前に最低限、空メッセージ、非テキスト、Claude例外時フォールバック、LINE返信例外時200継続を追加する。複数イベントは設計判断後に追加する。

## 評価できる点（そのまま良いと判断したところ）

- `.env.example`, `app/config.py`, `render.yaml` の主要環境変数名は整合している。
- `CLAUDE_MODEL=claude-opus-4-7` は公式Claude API docs上のClaude API IDとして確認できる。
- `PORT` はRender起動コマンドで `$PORT` を使っており、Render向けの受け方として問題ない。`Settings.port` が未使用なのは現状では害がない。
- LINE署名検証はSDKの `WebhookParser` に委譲しており、署名不正時は処理前に400へ落ちる。
- `webhookEventId` と `deliveryContext.isRedelivery` はLINE仕様と対応している。単一worker前提のインメモリidempotencyはDay 1として妥当。
- ログに本文やuser IDを明示出力していない点は良い。例外ログにSDKがどの程度詳細を含めるかは実機で確認する。
- `.env`, `.venv`, `.pytest_cache`, `__pycache__` は `.gitignore` に入っている。`git ls-files` 上も `.env` は追跡されていない。
- ngrokローカル実機テストに進むためのコード上のブロッカーはない。

## 次アクション推奨順

1. `HANDOFF.md` から非公開実名を削除する。公開前に必須。
2. `render.yaml` に `healthCheckPath: /health` を追加し、`env` を `runtime` に置き換える。
3. RenderをLINE Webhookに使うならFreeではなくStarter以上を選ぶ方針にする。READMEにも明記する。
4. Claude呼び出しのtimeout方針を決める。Day 1は20-30秒でフォールバック返信が現実的。
5. テストを4件程度追加する: 空テキスト、非テキスト、Claude例外、LINE返信例外。
6. 複数イベント同梱時の方針を決め、必要ならテストと実装を追加する。
7. READMEにLINE Developers設定チェックリストを集約する。
8. 上記後にngrok実機テストへ進む。

## 参照した外部仕様

- Claude API Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- LINE Messaging API reference: https://developers.line.biz/en/reference/messaging-api/nojs/
- Render Blueprint YAML Reference: https://render.com/docs/blueprint-spec
- Render Free instances: https://render.com/docs/free
