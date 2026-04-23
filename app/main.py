import logging
import threading
import time
from collections import OrderedDict

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.claude_client import ClaudeClient
from app.config import get_settings
from app.line_client import LineClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
line_client = LineClient(settings)
claude_client = ClaudeClient(settings)

_IDEMPOTENCY_TTL_SECONDS = 300.0
_IDEMPOTENCY_MAX_ENTRIES = 10000
_seen_event_expiry: "OrderedDict[str, float]" = OrderedDict()
_seen_event_lock = threading.Lock()

_CLAUDE_FAILURE_REPLY = (
    "すみません。今は応答できません。少し時間をおいて再度お試しください。"
)


def _already_seen(event_id: str) -> bool:
    now = time.monotonic()
    with _seen_event_lock:
        while _seen_event_expiry:
            oldest_id = next(iter(_seen_event_expiry))
            if _seen_event_expiry[oldest_id] > now:
                break
            _seen_event_expiry.popitem(last=False)
        if event_id in _seen_event_expiry:
            return True
        _seen_event_expiry[event_id] = now + _IDEMPOTENCY_TTL_SECONDS
        while len(_seen_event_expiry) > _IDEMPOTENCY_MAX_ENTRIES:
            _seen_event_expiry.popitem(last=False)
        return False


app = FastAPI()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str | None = Header(default=None),
) -> dict[str, str]:
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="missing signature")

    raw_body = await request.body()
    try:
        body = raw_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid webhook body") from exc

    try:
        events = line_client.parse_events(body, x_line_signature)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid signature") from exc
    except Exception as exc:
        logger.exception("failed to parse webhook body")
        raise HTTPException(status_code=400, detail="invalid webhook body") from exc

    # Day 1 方針: 1 Webhook に複数テキストイベントが入っていても
    # reply_token の 1 分制限を守るため先頭 1 件だけ処理する。
    # それ以降のイベントはログに残してスキップする。
    handled = False
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        delivery_context = getattr(event, "delivery_context", None)
        if delivery_context is not None and getattr(
            delivery_context, "is_redelivery", False
        ):
            logger.info("skipping redelivered webhook event")
            continue

        event_id = getattr(event, "webhook_event_id", None)
        if event_id and _already_seen(event_id):
            logger.info("skipping duplicate webhook event %s", event_id)
            continue

        user_text = event.message.text.strip()
        if not user_text:
            continue

        if handled:
            logger.info(
                "skipping additional text event in same webhook (event_id=%s)",
                event_id,
            )
            continue

        try:
            reply_text = await run_in_threadpool(
                claude_client.generate_reply, user_text
            )
        except Exception:
            logger.exception("failed to generate claude response")
            reply_text = _CLAUDE_FAILURE_REPLY

        try:
            await run_in_threadpool(
                line_client.reply_text, event.reply_token, reply_text
            )
        except Exception:
            logger.exception("failed to send line reply")

        handled = True

    return {"status": "ok"}
