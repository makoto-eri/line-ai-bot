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


class StubNonTextEvent:
    """MessageEvent だが message が TextMessageContent ではないケース"""

    def __init__(self, reply_token: str = "reply-token") -> None:
        self.reply_token = reply_token
        self.message = object()
        self.webhook_event_id = "non-text-evt"
        self.delivery_context = StubDeliveryContext()


class StubLineClient:
    def __init__(self, events: list | None = None, reply_raises: bool = False) -> None:
        self.reply_calls: list[tuple[str, str]] = []
        self._events = events
        self._reply_raises = reply_raises

    def parse_events(self, body: str, signature: str):
        if signature == "bad-signature":
            raise ValueError("invalid line signature")
        if self._events is not None:
            return self._events
        return [StubEvent("reply-token", "相談です")]

    def reply_text(self, reply_token: str, text: str) -> None:
        if self._reply_raises:
            raise RuntimeError("line api unavailable")
        self.reply_calls.append((reply_token, text))


class StubClaudeClient:
    def __init__(self, raises: bool = False) -> None:
        self._raises = raises

    def generate_reply(self, user_message: str) -> str:
        if self._raises:
            raise RuntimeError("claude api unavailable")
        return f"echo:{user_message}"


@pytest.fixture(autouse=True)
def _reset_idempotency_cache():
    from app.main import _seen_event_expiry

    _seen_event_expiry.clear()
    yield
    _seen_event_expiry.clear()


def _post_callback():
    return client.post(
        "/callback",
        content="{}",
        headers={"X-Line-Signature": "valid-signature"},
    )


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

    response = _post_callback()

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

    first = _post_callback()
    second = _post_callback()

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

    response = _post_callback()

    assert response.status_code == 200
    assert stub_line_client.reply_calls == []


def test_callback_returns_200_when_events_empty(monkeypatch):
    stub_line_client = StubLineClient(events=[])
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())

    response = _post_callback()

    assert response.status_code == 200
    assert stub_line_client.reply_calls == []


def test_callback_skips_empty_text(monkeypatch):
    stub_line_client = StubLineClient(
        events=[StubEvent("reply-token", "   ", webhook_event_id="blank-1")]
    )
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = _post_callback()

    assert response.status_code == 200
    assert stub_line_client.reply_calls == []


def test_callback_ignores_non_text_message(monkeypatch):
    stub_line_client = StubLineClient(events=[StubNonTextEvent()])
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubNonTextEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = _post_callback()

    assert response.status_code == 200
    assert stub_line_client.reply_calls == []


def test_callback_sends_fallback_when_claude_raises(monkeypatch):
    stub_line_client = StubLineClient()
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient(raises=True))
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = _post_callback()

    assert response.status_code == 200
    assert len(stub_line_client.reply_calls) == 1
    reply_token, text = stub_line_client.reply_calls[0]
    assert reply_token == "reply-token"
    assert "応答できません" in text


def test_callback_returns_200_when_line_reply_raises(monkeypatch):
    stub_line_client = StubLineClient(reply_raises=True)
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = _post_callback()

    # LINE 返信 API が落ちても Webhook には 200 を返し、再送を促さない
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_callback_handles_only_first_text_event_in_batch(monkeypatch):
    stub_line_client = StubLineClient(
        events=[
            StubEvent("reply-token-1", "一つ目", webhook_event_id="batch-1"),
            StubEvent("reply-token-2", "二つ目", webhook_event_id="batch-2"),
            StubEvent("reply-token-3", "三つ目", webhook_event_id="batch-3"),
        ]
    )
    monkeypatch.setattr("app.main.line_client", stub_line_client)
    monkeypatch.setattr("app.main.claude_client", StubClaudeClient())
    monkeypatch.setattr("app.main.MessageEvent", StubEvent)
    monkeypatch.setattr("app.main.TextMessageContent", StubMessage)

    response = _post_callback()

    assert response.status_code == 200
    # Day 1 方針: 先頭 1 件のみ処理
    assert stub_line_client.reply_calls == [("reply-token-1", "echo:一つ目")]


def test_line_client_truncates_long_text(monkeypatch):
    from app.line_client import _LINE_TEXT_MAX_CHARS, _truncate_for_line

    long_text = "あ" * (_LINE_TEXT_MAX_CHARS + 100)
    truncated = _truncate_for_line(long_text)

    assert len(truncated) <= _LINE_TEXT_MAX_CHARS
    assert truncated.endswith("…（以下省略）")


def test_line_client_does_not_truncate_short_text():
    from app.line_client import _truncate_for_line

    text = "短い返答"
    assert _truncate_for_line(text) == text


def test_sanitize_strips_bold_asterisks():
    from app.line_client import _sanitize_for_line

    assert _sanitize_for_line("これは**重要**です") == "これは重要です"
    assert _sanitize_for_line("**件名:** 【お詫び】") == "件名: 【お詫び】"


def test_sanitize_converts_headers():
    from app.line_client import _sanitize_for_line

    assert _sanitize_for_line("## 主な違い\n内容") == "【主な違い】\n内容"
    assert _sanitize_for_line("# タイトル") == "【タイトル】"


def test_sanitize_converts_leading_bullets():
    from app.line_client import _sanitize_for_line

    src = "手順:\n- ステップ1\n- ステップ2\n  - 補足"
    expected = "手順:\n・ステップ1\n・ステップ2\n  ・補足"
    assert _sanitize_for_line(src) == expected


def test_sanitize_removes_inline_code_and_fences():
    from app.line_client import _sanitize_for_line

    src = "コマンドは `curl ...` です\n\n```bash\nuvicorn app:main\n```"
    result = _sanitize_for_line(src)
    assert "`" not in result
    assert "```" not in result
    assert "curl ..." in result
    assert "uvicorn app:main" in result


def test_sanitize_flattens_markdown_links():
    from app.line_client import _sanitize_for_line

    src = "詳細は [公式サイト](https://example.com) を参照"
    assert _sanitize_for_line(src) == "詳細は 公式サイト (https://example.com) を参照"


def test_format_for_line_chains_sanitize_and_truncate():
    from app.line_client import _LINE_TEXT_MAX_CHARS, format_for_line

    body = "**" + ("長" * _LINE_TEXT_MAX_CHARS) + "**"
    result = format_for_line(body)
    assert "**" not in result
    assert len(result) <= _LINE_TEXT_MAX_CHARS


def test_claude_client_sets_short_timeout_and_disables_retry():
    """LINE reply_token の 1 分制限を守るため timeout=30s / max_retries=0 を固定する"""
    from app.claude_client import (
        _MAX_RETRIES,
        _REQUEST_TIMEOUT_SECONDS,
        ClaudeClient,
    )
    from app.config import Settings

    settings = Settings(
        LINE_CHANNEL_SECRET="test-secret",
        LINE_CHANNEL_ACCESS_TOKEN="test-token",
        ANTHROPIC_API_KEY="test-anthropic-key",
    )

    client_instance = ClaudeClient(settings)

    assert _REQUEST_TIMEOUT_SECONDS == 30.0
    assert _MAX_RETRIES == 0
    assert client_instance._client.max_retries == _MAX_RETRIES
    # SDK 側の timeout は httpx.Timeout でラップされるため read 属性で確認
    actual_timeout = client_instance._client.timeout
    timeout_value = getattr(actual_timeout, "read", actual_timeout)
    assert timeout_value == _REQUEST_TIMEOUT_SECONDS
