from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

router = APIRouter()


async def send_telegram_message(chat_id: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            }
        )


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        try:
            data = await request.json()
        except Exception:
            print("❌ Invalid JSON received")
            return {"ok": True}

        print("📩 DATA:", data)

        message = data.get("message")
        if not message:
            return {"ok": True}

        chat = message.get("chat")
        if not chat:
            return {"ok": True}

        chat_id = str(chat.get("id"))
        text = message.get("text", "")

        print("💬 TEXT:", text)

        if not text.startswith("/start"):
            return {"ok": True}

        parts = text.split()

        # 🔹 CASE 1: /start <token>
        if len(parts) > 1:
            token = parts[1]

            user = db.query(User).filter(User.link_token == token).first()

            if user:
                user.chat_id = chat_id
                db.commit()

                print(f"✅ Linked Telegram for user {user.id}")

                await send_telegram_message(
                    chat_id,
                    "✅ Telegram linked successfully!"
                )

            else:
                print("❌ TOKEN NOT FOUND:", token)

                await send_telegram_message(
                    chat_id,
                    "❌ Invalid or expired link."
                )

        # 🔹 CASE 2: plain /start
        else:
            await send_telegram_message(
                chat_id,
                "Use the link from dashboard to connect your account."
            )

    except Exception as e:
        print("❌ Webhook error:", e)

    return {"ok": True}