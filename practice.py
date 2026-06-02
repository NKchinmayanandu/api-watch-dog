from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.telegram_service import send_message as send_telegram_message
router = APIRouter()


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

                # already linked condn
                if user.chat_id:
                    await send_telegram_message(
                        chat_id,
                        "✅ Your Telegram account is already linked."
                        )
                    return {"ok": True}

                user.chat_id = chat_id
                db.commit()

                await send_telegram_message(
                    chat_id,
                    "✅ Telegram linked successfully!"
                    )

            else:
                print("❌ TOKEN NOT FOUND:", token)
                # for now we are not genrating new tokens so this is not neccessary 
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