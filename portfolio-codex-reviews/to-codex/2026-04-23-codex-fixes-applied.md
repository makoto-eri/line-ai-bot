# 反映報告: 2026-04-23 Codex初回コードレビュー指摘の反映

元レビュー: `portfolio-codex-reviews/from-codex/2026-04-23-initial-code-review-response.md`
対象コミット: `319a236`（initial commit: minimal LINE bot with Claude Opus 4.7）
テスト結果: `pytest` 7件すべてパス

## Codex へのお願い

以下3点の指摘について、反映内容が妥当か確認してほしい。
残留リスク・追加指摘があれば `portfolio-codex-reviews/from-codex/2026-04-23-codex-fixes-applied-response.md` に書き出してください。

観点:
- 修正のアプローチが指摘意図と合っているか
- 別の箇所に新しいリスクを作っていないか
- テストケースが十分か
- idempotency キャッシュ（インメモリ、TTL 300秒、最大 10000件、threading.Lock）で問題ないか
  - 将来 Render の複数インスタンス化で破綻するが、現段階は単一 worker 前提でよいという理解

---

## 指摘1（High）: async def callback 内の同期 I/O

**Codex 指摘要旨**: Claude 呼び出し・LINE 返信が同期で走るため、イベントループを塞ぎ、単一 worker の uvicorn では他の webhook まで待たされる。`run_in_threadpool` で逃がすか、非同期クライアントに揃えるべき。

**反映内容**: `fastapi.concurrency.run_in_threadpool` で `claude_client.generate_reply` と `line_client.reply_text` を退避。非同期クライアントへの移行は変更範囲が広いため今回は見送り。

**該当コード**: `app/main.py:99-112`

```python
reply_text = await run_in_threadpool(
    claude_client.generate_reply, user_text
)
...
await run_in_threadpool(
    line_client.reply_text, event.reply_token, reply_text
)
```

---

## 指摘2（Medium）: webhook 重複防止なし

**Codex 指摘要旨**: `webhook_event_id` も `delivery_context.is_redelivery` も見ていないので、LINE が同一イベントを再配信すると同じ内容を二重返信する。少なくとも `event.webhook_event_id` をキーにした短TTLの idempotency を入れるべき。

**反映内容**:
- インメモリ idempotency を `app/main.py` に実装（`OrderedDict` + `threading.Lock`、TTL 300秒、最大 10000件）。`_already_seen(event_id)` で判定
- `delivery_context.is_redelivery` が True のイベントは別経路でスキップ
- 両方とも `getattr` で参照しているため、SDK が該当属性を持たない payload でも例外にはならない

**該当コード**:
- idempotency 実装: `app/main.py:21-40`
- is_redelivery スキップ: `app/main.py:78-83`
- event_id 重複スキップ: `app/main.py:85-88`

---

## 指摘3（Low）: 不正バイト列で 500

**Codex 指摘要旨**: `(await request.body()).decode("utf-8")` が例外処理の外にあるため、不正バイト列（例: `b"\xff"`）で `UnicodeDecodeError` がそのまま 500 になる。400 invalid webhook body に畳むべき。

**反映内容**: body decode を try/except で囲み、`UnicodeDecodeError` 時は `HTTPException(400, "invalid webhook body")` を返す。

**該当コード**: `app/main.py:57-61`

```python
raw_body = await request.body()
try:
    body = raw_body.decode("utf-8")
except UnicodeDecodeError as exc:
    raise HTTPException(status_code=400, detail="invalid webhook body") from exc
```

---

## 追加テストケース

`tests/test_webhook.py` に以下を追加（元4件 → 計7件、すべてパス）:

1. `test_callback_returns_400_when_body_not_utf8`: `b"\xff\xfe"` を送信して 400 + `invalid webhook body` を確認
2. `test_callback_skips_duplicate_event`: 同じ `webhook_event_id="dup-1"` で 2 回 POST → 返信は 1 回だけ
3. `test_callback_skips_redelivered_event`: `is_redelivery=True` のイベント → 返信ゼロ

idempotency キャッシュの漏れ防止のため、`autouse=True` の fixture でテストごとに `_seen_event_expiry` をクリアしている。

---

## 未対応・将来課題

- **複数インスタンス化時の idempotency 破綻**: インメモリなので Render の有料プラン等で worker が複数になった場合に重複判定が効かなくなる。必要になったら Redis 等の外部ストアに載せ替える
- **非同期クライアントへの全面移行**: `AsyncAnthropic` + `httpx` への移行は未実施。現時点では `run_in_threadpool` で十分と判断
- **Residual Risk（前回指摘）への対応**: 実 LINE payload の再配信、Claude の遅延/タイムアウト、並行 webhook 負荷は引き続き未検証。ngrok + 実機テストのフェーズで確認予定

---

## 参考コミット

```
319a236 initial commit: minimal LINE bot with Claude Opus 4.7
 - FastAPI webhook (/callback, /health) with signature verification
 - Claude Opus 4.7 integration via Anthropic SDK
 - pydantic-settings for env vars, pytest suite
 - Codex review fixes:
   - run_in_threadpool for Claude/LINE sync calls (High)
   - in-memory idempotency via webhook_event_id + is_redelivery (Medium)
   - wrap UTF-8 body decode in try/except (Low)
```
