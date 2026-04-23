1. High: `async def callback` の中で同期 I/O をそのまま実行しているため、Claude 呼び出しや LINE 返信が遅いとイベントループ全体を塞ぎます。単一 worker の `uvicorn` 構成では別 webhook まで巻き込んで待たせるので、LINE 側タイムアウトや再配信の原因になります。参照: [app/main.py](</C:/Users/えりっぺ/Documents/line-ai-bot/app/main.py:25>), [app/claude_client.py](</C:/Users/えりっぺ/Documents/line-ai-bot/app/claude_client.py:18>), [app/line_client.py](</C:/Users/えりっぺ/Documents/line-ai-bot/app/line_client.py:29>), [render.yaml](</C:/Users/えりっぺ/Documents/line-ai-bot/render.yaml:7>)。修正するなら、`callback` を同期 `def` にするか、`run_in_threadpool` で `generate_reply` / `reply_text` を逃がすか、非同期クライアントに揃えるべきです。

2. Medium: webhook の重複防止がなく、`webhook_event_id` も `delivery_context.is_redelivery` も見ていないので、LINE が同一イベントを再配信すると同じ内容を二重返信します。1 の遅延と組み合わさると実際に起きやすいです。参照: [app/main.py](</C:/Users/えりっぺ/Documents/line-ai-bot/app/main.py:43>)。少なくとも `event.webhook_event_id` をキーにした短TTLの idempotency を入れるべきです。

3. Low: リクエスト本文の UTF-8 デコードが例外処理の外にあるため、不正バイト列で `UnicodeDecodeError` がそのまま 500 になります。`b"\xff"` を投げると再現しました。参照: [app/main.py](</C:/Users/えりっぺ/Documents/line-ai-bot/app/main.py:33>)。ここは `400 invalid webhook body` に畳む方が安全です。

**Open Questions**

なし。

**Residual Risk**

`.git` が無かったので差分ではなく現行ファイル一式をレビューしました。テストは `.\\.venv\\Scripts\\python.exe -m pytest` で 4 件通過していますが、実 LINE payload の再配信、Claude の遅延/タイムアウト、並行 webhook 負荷は未検証です。`pytest` 実行時に `.pytest_cache` への書き込み警告も出ています。
