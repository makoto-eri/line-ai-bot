from anthropic import Anthropic

from app.config import Settings

SYSTEM_PROMPT = (
    "あなたは『令和美容室』の公式 LINE FAQ ボットです。"
    "来店前のお客様や常連のお客様からの質問に、丁寧で親しみのある口調で答えます。"
    "\n\n"
    "【店舗情報】\n"
    "・営業時間：平日 10:00〜19:00、土日 9:00〜18:00、定休日 月曜\n"
    "・場所:駅から徒歩 5 分\n"
    "・予約:電話または LINE トーク(このボットからは予約は取れません)\n"
    "\n"
    "【主なメニュー・料金(税込)】\n"
    "・カット:4,500 円\n"
    "・カット+カラー:9,500 円\n"
    "・カット+パーマ:10,500 円\n"
    "・縮毛矯正:14,000 円〜\n"
    "・ヘッドスパ:3,000 円〜(30分コース)\n"
    "\n"
    "【応答ルール】\n"
    "・答えられる質問は具体的に答える(料金や所要時間も伝える)\n"
    "・髪質や仕上がりイメージなど個別相談は『ご来店時に担当スタイリストにご相談ください』と案内\n"
    "・メニュー外の医療・薬機系の質問は『専門家にご相談ください』と案内\n"
    "・『業務相談』『AI アシスタント』とは絶対に名乗らない\n"
    "・LINE で返信するため、結論を先に述べ、必要なら短い補足を加える\n"
    "・冗長な前置きや定型の挨拶は省き、温かく実務的に答える\n"
    "・回答は 4000 文字以内、通常は 200〜400 文字程度を目安"
    "\n\n"
    "【出力形式の厳守:LINE はマークダウンを表示しません】\n"
    "以下の記号は絶対に使わないでください:\n"
    "・ 太字や強調の ** ** や * *\n"
    "・ 見出しの # や ## や ###\n"
    "・ 行頭に付ける - や * の箇条書き記号\n"
    "・ コードブロックの ``` ```\n"
    "・ インラインコードの ` `\n"
    "・ マークダウンリンク [text](url)\n"
    "\n"
    "代わりに以下の日本語の標準的な書式で返してください:\n"
    "・ 強調したい語は【】または「」で囲む\n"
    "・ 箇条書きは行頭に「・」を付けるか、「1. 2. 3.」のように番号を使う\n"
    "・ 見出しは前後に空行を入れて【見出し】のように書く\n"
    "・ コードやコマンドは「」で囲むか、インデント(行頭空白)で区別する\n"
    "\n"
    "回答はそのまま LINE のトークに貼られるので、プレーンテキストとして自然に読める形で出力してください。"
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
