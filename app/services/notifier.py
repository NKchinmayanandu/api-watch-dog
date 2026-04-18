import requests
import os

def send_alert(message: str, chat_id: int | None):
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        print("Telegram bot token missing ⚠️")
        return

    if not chat_id:
        print("No chat_id for this user → skipping alert")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            print("Telegram failed:", response.text)

    except Exception as e:
        print("telegram error:", e)