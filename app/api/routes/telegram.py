from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        print("DATA:", data)  # keep this for debugging

        message = data.get("message")
        if not message:
            return {"ok": True}

        chat = message.get("chat")
        if not chat:
            return {"ok": True}

        chat_id = str(chat.get("id"))
        text = message.get("text", "")

        async with httpx.AsyncClient() as client:

            if text.startswith("/start"):
                parts = text.split()

                if len(parts) > 1:
                    token = parts[1]

                    user = db.query(User).filter(User.link_token == token).first()

                    if user:
                        user.chat_id = chat_id
                        db.commit()

                        print(f"✅ Linked Telegram for user {user.id}")

                        # 🔥 SEND RESPONSE
                        await client.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "✅ Telegram linked successfully!"
                            }
                        )

                    else:
                        if not user:
                            print("❌ TOKEN NOT FOUND:", token) 

                        await client.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "❌ Invalid or expired link."
                            }
                        )

                else:
                    # 🔥 HANDLE PLAIN /start
                    await client.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": "Use the link from dashboard to connect."
                        }
                    )

    except Exception as e:
        print("Webhook error:", e)

    return {"ok": True}