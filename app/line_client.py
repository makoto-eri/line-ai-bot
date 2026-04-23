from typing import Any

from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from app.config import Settings


class LineClient:
    def __init__(self, settings: Settings) -> None:
        self._parser = WebhookParser(settings.line_channel_secret)
        self._configuration = Configuration(
            access_token=settings.line_channel_access_token
        )

    def parse_events(self, body: str, signature: str) -> list[Any]:
        try:
            return self._parser.parse(body, signature)
        except InvalidSignatureError as exc:
            raise ValueError("invalid line signature") from exc

    def reply_text(self, reply_token: str, text: str) -> None:
        with ApiClient(self._configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)],
                )
            )
