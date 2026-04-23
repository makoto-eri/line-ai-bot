import os

os.environ.setdefault("LINE_CHANNEL_SECRET", "test-secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


class StubMessage:
    def __init__(self, text: str) -> None:
        self.text = text


class StubDeliveryContext:
    def __init__(self, is_redelivery: bool = False) -> None:
        self.is_redelivery = is_redelivery


class StubEvent:
    def __init__(
        self,
        reply_token: str,
        text: str,
        webhook_event_id: str = "evt-1",
        is_redelivery: bool = False,
    ) -> None:
        self.reply_token = reply_token
        self.message = StubMessage(text)
        self.webhook_event_id = webhook_event_id
        self.delivery_context = StubDeliveryContext(is_redelivery=is_redelivery)


class StubLineClient:
    def __init__(self, events: list | None = None) -> None:
        self.reply_calls: list[tuple[str, str]] = []
        self._events = events

    def parse_events(self, body: str, signature: str):
        if signature == "bad-signature":
            raise ValueError("invalid line signature")
        if self._events is not None:
            return self._events
        return [StubEvent("reply-token", "相談です")]

    def reply_text(self, reply_token: str, text: str) -> None:
        self.reply_calls.append((reply_token, text))


class StubClaudeClient:
    def generate_reply(self, user_message: str) -> str:
        return f"echo:{user_message}"


@pytest.fixture(autouse=True)
def _reset_idempotency_cache():
    from app.main import _seen_event_expiry

    _seen_event_expiry.clear()
    yield
    _seen_event_expiry.clear()


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_callback_returns_400_when_signature_missing():
    response = client.post("/callback", content="{}")
    assert response.status_code == 400
    assert response.json()["detail"] == "missing signature"


def test_callback_returns_400_when_signature_invalid(monkeypatch):
    monkeypatch.setattr("app.main.line_client", StubLineClient())
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())

    response = client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "bad-signature"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid signature"


def test_callback_returns_400_when_body_not_utf8():
    response = client.post(
        "/callback",
        content=b"\xff\xfe",
        headers={"X-Line-Signature": "valid-signature"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid webhook body"


def test_callback_replies_to_text_event(monkeypatch):
    stub_line_client = StubLineClient()
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert stub_line_client.reply_calls == [("reply-token", "echo:相談です")]


def test_callback_skips_duplicate_event(monkeypatch):
    stub_line_client = StubLineClient(
        events=[StubEvent("reply-token", "相談です", webhook_event_id="dup-1")]
    )
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    first = client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "valid-signature"},
    )
    second = client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "valid-signature"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert stub_line_client.reply_calls == [("reply-token", "echo:相談です")]


def test_callback_skips_redelivered_event(monkeypatch):
    stub_line_client = StubLineClient(
        events=[
            StubEvent(
                "reply-token",
                "相談です",
                webhook_event_id="redeliver-1",
                is_redelivery=True,
            )
        ]
    )
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert stub_line_client.reply_calls == []
