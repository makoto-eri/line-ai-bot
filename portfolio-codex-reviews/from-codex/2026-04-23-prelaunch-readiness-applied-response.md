# Pre-launch Readiness Applied Review 返信

## サマリ

- 判定: 追加指摘あり。Phase 2 完了宣言は、少なくとも Claude SDK retry 設定を直してからが安全。
- 反映全体: 10 件の指摘は概ね適切に反映されている。
- ブロッカー相当: 1 件。`timeout=30.0` は入ったが、Anthropic SDK のデフォルト `max_retries=2` により最悪時は 30 秒を大きく超える。
- テスト: `.\\.venv\\Scripts\\python.exe -m pytest -v` で 15 件すべてパス。`.pytest_cache` 書き込み権限警告のみ。

## Findings

### [High] Claude timeout が default retry により reply_token 対策として不十分

- 対象: `app/claude_client.py:19`
- 問題: `Anthropic(api_key=..., timeout=30.0)` は SDK に渡っているが、Anthropic SDK 0.96.0 の同期 client は `max_retries=2` がデフォルト。ローカル確認でも `Anthropic(api_key='test', timeout=30.0).max_retries == 2`。SDK 実装上、`httpx.TimeoutException` 時は残 retry があれば再試行するため、タイムアウト系の失敗では最大 3 回試行 + backoff になり、reply_token 1 分制限を超える可能性がある。
- 提案: Day 1 の webhook reply 用途では `max_retries=0` を明示する。

```python
self._client = Anthropic(
    api_key=settings.anthropic_api_key,
    timeout=_REQUEST_TIMEOUT_SECONDS,
    max_retries=0,
)
```

- 追加テスト案: `ClaudeClient` 初期化時に `client._client.max_retries == 0` と `client._client.timeout == 30.0` を確認する軽い単体テストを追加する。内部属性参照が気になるなら、`ClaudeClient` 側に定数を置くことで設計意図を固定するだけでもよい。

### [Medium] `render.yaml` の `plan: free` は README の推奨と逆向き

- 対象: `render.yaml:5`, `README.md:59`
- 問題: README では Starter 以上を推奨しているが、Blueprint をそのまま作ると `plan: free` になる。手動で Starter を選ぶ運用は可能だが、README 手順の「Render で `render.yaml` を Blueprint として読み込ませる」と組み合わせると、誤って Free のまま LINE Webhook URL に設定しやすい。
- 提案: どちらかに寄せる。
  - 本番に近いローンチを優先するなら `plan: starter` に変更。
  - 費用回避を優先するなら `plan: free` を維持し、README の Render 手順に「Blueprint 作成後、LINE Webhook に向ける前に Starter へ変更する」または「Free は疎通確認専用」と明記。

## 残論点 4 件への回答

### 1. `plan: free` 維持

- 評価: 条件付きで可。ただし「Blueprint 初回デプロイ時に手動で Starter を選ぶ」は運用ミスを誘発しやすい。
- 推奨: Render を LINE Webhook の常設先にするなら YAML も `plan: starter` にする。Free 維持なら README に「Free は疎通確認専用」と明記して、LINE Developers の Webhook URL を Render Free に向ける前に `/health` で起こす手順まで固定する。

### 2. Claude SDK timeout の扱い

- 評価: `timeout=30.0` は SDK に渡っているが、retry を含む総時間上限ではない。
- 根拠: インストール済み `anthropic==0.96.0` の `Anthropic` signature は `timeout` と `max_retries` を受け、`max_retries` default は 2。SDK 内部で timeout exception は retry 対象。
- 推奨: `max_retries=0` を明示する。LINE webhook の reply path では、SDK retry よりもアプリ側で即フォールバック返信する方が安全。

### 3. system prompt の「4000 文字以内」制約

- 評価: 方針として妥当。ただしモデルへの指示は保証ではない。
- 現状: `app/line_client.py:20` の `_truncate_for_line()` が 5000 文字上限を強制しているため、モデルが指示を破っても LINE API 送信前に防御できる。
- 推奨: 追加修正不要。今の二重防御でよい。

### 4. 複数イベント「先頭 1 件のみ処理」

- 評価: Day 1 のポートフォリオ用途なら許容。reply_token 1 分制限を守る設計として一貫している。
- 残留リスク: 同一 webhook に複数ユーザー/複数イベントが入った場合、2 件目以降は意図的に返信されない。`app/main.py:103` の `handled` check より前に idempotency 登録されるため、スキップ対象イベントは同じTTL内で再送されても処理されない。
- 推奨: README の挙動仕様にすでに明記されているので、Day 1 は追加修正不要。将来グループや高頻度利用を想定するなら、先頭のみではなく短 timeout 付きの並行処理または push message 方式へ移行する。

## 確認できた反映

- 実名削除: `rg` と `git log -p --all` で該当なし。
- `render.yaml`: `runtime: python`, `healthCheckPath: /health`, `PYTHON_VERSION: 3.13.5` 追加済み。
- README: LINE Developers 設定、Render Free 非推奨、挙動仕様が集約済み。
- LINE text truncate: `_truncate_for_line()` で 5000 文字以内に収める実装あり。
- テスト: 7 件から 15 件へ拡充され、追加ケースの狙いも妥当。

## 次アクション推奨

1. `app/claude_client.py` の `Anthropic(...)` に `max_retries=0` を追加する。
2. 可能なら timeout / max_retries 設定のテストを 1 件追加する。
3. `render.yaml` の `plan` 方針を決める。Starter 運用なら `plan: starter`、Free 維持ならREADMEに「疎通確認専用」と明記。
4. 上記後に再テストし、問題なければ Phase 2 完了扱いでよい。
