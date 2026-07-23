import httpx
from app.core.config import settings


async def send_message(chat_id: str | int, text: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        print("⚠️  TELEGRAM_BOT_TOKEN not set — skipping message")
        return

    if not chat_id:
        print("⚠️  No chat_id provided — skipping message")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with httpx.AsyncClient(timeout=5) as Client:
        response = await Client.post(
            url=url,
            json={
            "chat_id": chat_id,
            "text": text
            }
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram rejected message: {data}"
            )
        

