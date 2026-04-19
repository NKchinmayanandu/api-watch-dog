from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()

        message = data.get("message")
        if not message:
            return {"ok": True}

        chat = message.get("chat")
        if not chat:
            return {"ok": True}

        chat_id = str(chat.get("id"))
        text = message.get("text", "")

        if text.startswith("/start"):
            parts = text.split(" ")

            if len(parts) > 1:
                token = parts[1]

                user = db.query(User).filter(User.link_token == token).first()

                if user:
                    user.chat_id = chat_id
                    db.commit()

                    print(f"✅ Linked Telegram for user {user.id}")

    except Exception as e:
        print("Webhook error:", e)

    return {"ok": True}