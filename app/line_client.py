import re
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

# LINE TextMessage の上限は 5000 文字。末尾省略分を差し引いた実効上限。
_LINE_TEXT_MAX_CHARS = 5000
_TRUNCATE_SUFFIX = "…（以下省略）"


_RE_BOLD = re.compile(r"\*\*([^*\n]+?)\*\*")
_RE_ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+?)\*(?![*\w])")
_RE_HEADER = re.compile(r"^#{1,6}[ \t]+(.+?)\s*$", flags=re.MULTILINE)
_RE_FENCE_OPEN = re.compile(r"^```[^\n]*\n?", flags=re.MULTILINE)
_RE_FENCE_CLOSE = re.compile(r"\n?```\s*$", flags=re.MULTILINE)
_RE_INLINE_CODE = re.compile(r"`([^`\n]+?)`")
_RE_LIST_DASH = re.compile(r"^([ \t]*)[-*][ \t]+", flags=re.MULTILINE)
_RE_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")


def _sanitize_for_line(text: str) -> str:
    """LINE が表示できないマークダウン記号を自然な日本語表記に変換する。

    Claude に「マークダウンを使うな」と指示しているが、守られない場合の
    セーフティネット。送信直前に機械的に整形する。
    """
    # 太字 **text** → text
    text = _RE_BOLD.sub(r"\1", text)
    # 斜体 *text* → text （** 残りには当たらないよう境界条件を厳しくする）
    text = _RE_ITALIC.sub(r"\1", text)
    # 見出し ## 見出し → 【見出し】
    text = _RE_HEADER.sub(r"【\1】", text)
    # コードフェンス ``` ... ``` → 中身だけ残す
    text = _RE_FENCE_OPEN.sub("", text)
    text = _RE_FENCE_CLOSE.sub("", text)
    # インラインコード `text` → text
    text = _RE_INLINE_CODE.sub(r"\1", text)
    # リンク [text](url) → text (url)
    text = _RE_LINK.sub(r"\1 (\2)", text)
    # 行頭の - / * 箇条書き → ・
    text = _RE_LIST_DASH.sub(r"\1・", text)
    return text


def _truncate_for_line(text: str) -> str:
    if len(text) <= _LINE_TEXT_MAX_CHARS:
        return text
    head = text[: _LINE_TEXT_MAX_CHARS - len(_TRUNCATE_SUFFIX)]
    return head + _TRUNCATE_SUFFIX


def format_for_line(text: str) -> str:
    """LINE 送信用に整形する（マークダウン除去 → 長さ制限）。"""
    return _truncate_for_line(_sanitize_for_line(text))


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
        safe_text = format_for_line(text)
        with ApiClient(self._configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=safe_text)],
                )
            )
