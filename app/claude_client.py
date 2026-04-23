from anthropic import Anthropic

from app.config import Settings

SYSTEM_PROMPT = (
    "あなたは業務相談に答えるアシスタントです。"
    "LINEで返信するため、結論を先に述べ、必要なら短い補足を加えてください。"
    "冗長な前置きや定型の挨拶は省き、実務的に答えてください。"
)


class ClaudeClient:
    def __init__(self, settings: Settings) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)
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
