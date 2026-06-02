from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/telegram-link")
def get_telegram_link(
    current_user: User = Depends(get_current_user)
):
    bot_username = "Chinmayanandu_bot"

    return {
        "telegram_link":
        f"https://t.me/{bot_username}?start={current_user.link_token}",

        "is_linked": bool(current_user.chat_id)
    }
