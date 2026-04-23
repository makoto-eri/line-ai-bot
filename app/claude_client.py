from anthropic import Anthropic

from app.config import Settings

SYSTEM_PROMPT = (
    "あなたは業務相談に答えるアシスタントです。"
    "LINEで返信するため、結論を先に述べ、必要なら短い補足を加えてください。"
    "冗長な前置きや定型の挨拶は省き、実務的に答えてください。"
    "回答は4000文字以内に収めてください。"
)

# LINE の reply_token は 1 分制限。ネットワーク往復・LINE API 送信時間を
# 差し引くと Claude 生成に割けるのは 30 秒程度が上限。
_REQUEST_TIMEOUT_SECONDS = 30.0

# Anthropic SDK のデフォルト max_retries=2 では、timeout 発生時に retry が走って
# 総経過時間が reply_token 1 分制限を超える可能性があるため 0 に固定する。
# アプリ側で即フォールバック返信する方針を貫く。
_MAX_RETRIES = 0


class ClaudeClient:
    def __init__(self, settings: Settings) -> None:
        self._client = Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=_REQUEST_TIMEOUT_SECONDS,
            max_retries=_MAX_RETRIES,
        )
        self._model = settings.claude_model
        self._max_tokens = settings.claude_max_tokens

    def generate_reply(self, user_message: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            system=SYSTEM_PROMPT,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": user_message}],
        )

        text_blocks = [block.text for block in response.content if block.type == "text"]
        reply = "".join(text_blocks).strip()
        return reply or "すみません、うまく回答を生成できませんでした。"
