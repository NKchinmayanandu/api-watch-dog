import asyncio
import httpx
from datetime import datetime, timedelta

from app.services.telegram_service import send_message
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.user import User


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def check_endpoint(url: str) -> tuple[str, int | None]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                return "UP", response.status_code
            else:
                return "DOWN", response.status_code
    except httpx.RequestError:
        return "DOWN", None


def has_status_changed(old_status: str, new_status: str) -> bool:
    return old_status != new_status


async def run_monitor():
    last_cleanup = 0.0

    while True:
        now = asyncio.get_event_loop().time()
        db = SessionLocal()

        try:
            print("🚀 Monitor loop running...")

            # 🔥 CLEANUP (every 1 hour)
            if now - last_cleanup > 3600:
                db.query(CheckLog).filter(
                    CheckLog.checked_at < datetime.utcnow() - timedelta(days=1)
                ).delete()

                db.commit()

                last_cleanup = now
                print("🧹 Old logs cleaned")

            endpoints = db.query(Endpoint).all()

            # 🔥 Run all endpoint checks concurrently
            tasks = [
                check_endpoint(endpoint.url)
                for endpoint in endpoints
            ]

            results = await asyncio.gather(*tasks)

            # Process results in same order as endpoints
            for endpoint, (current_status, code) in zip(endpoints, results):

                try:
                    url = endpoint.url

                    # Double-check DOWN before alerting
                    if current_status == "DOWN":
                        await asyncio.sleep(2)
                        current_status, code = await check_endpoint(url)

                    last_status = endpoint.last_status

                    user = db.query(User).filter(
                        User.id == endpoint.user_id
                    ).first()

                    chat_id = user.chat_id if user else None

                    # Status changed
                    if (
                        last_status is None
                        or has_status_changed(last_status, current_status)
                    ):

                        log = CheckLog(
                            endpoint_id=endpoint.id,
                            status=current_status,
                            status_code=code,
                        )

                        db.add(log)

                        endpoint.last_changed = datetime.utcnow()

                        # First check
                        if last_status is None:

                            if current_status == "DOWN":
                                await send_message(
                                    chat_id,
                                    f"🚨 {url} is DOWN (first check)"
                                )

                        # Status transition
                        else:

                            if current_status == "DOWN":
                                await send_message(
                                    chat_id,
                                    f"🚨 {url} went DOWN"
                                )

                            else:
                                await send_message(
                                    chat_id,
                                    f"✅ {url} is back UP"
                                )

                    endpoint.last_status = current_status
                    endpoint.last_checked = datetime.utcnow()

                    db.commit()

                except Exception as e:
                    print(f"❌ ERROR checking {endpoint.url}: {e}")
                    db.rollback()

        except Exception as e:
            print(f"❌ MONITOR ERROR: {e}")

        finally:
            db.close()

        await asyncio.sleep(30)