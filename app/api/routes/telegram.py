from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    try:
        message = data.get("message", {})
        chat_id = str(message["chat"]["id"])
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