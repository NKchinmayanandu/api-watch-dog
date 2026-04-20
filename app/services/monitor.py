import requests
import time
from datetime import datetime, timedelta

from app.services.notifier import send_alert
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.user import User


def check_endpoint(url: str):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return "UP", response.status_code
        else:
            return "DOWN", response.status_code
    except requests.exceptions.RequestException:
        return "DOWN", None


def has_status_changed(old_status: str, new_status: str):
    return old_status != new_status


def run_monitor():
    last_cleanup = 0   

    while True:
        now = time.time()
        db = SessionLocal()

        try:
            print("Monitor loop running...")

            # 🔥 CLEANUP (every 1 hour)
            if now - last_cleanup > 3600:
                db.query(CheckLog).filter(
                    CheckLog.checked_at < datetime.utcnow() - timedelta(days=1)
                ).delete()
                db.commit()
                last_cleanup = now
                print("🧹 Old logs cleaned")

            endpoints = db.query(Endpoint).all()

            for endpoint in endpoints:
                url = endpoint.url

                current_status, code = check_endpoint(url)
                
                # Double check if DOWN
                if current_status == "DOWN":
                    time.sleep(2)
                    current_status, code = check_endpoint(url)

                last_status = endpoint.last_status
  
                user = db.query(User).filter(User.id == endpoint.user_id).first()
                chat_id = user.chat_id if user else None

                if last_status is None or has_status_changed(last_status, current_status):

                    log = CheckLog(
                        endpoint_id=endpoint.id,
                        status=current_status,
                        status_code=code
                    )
                    db.add(log)
                    
                    endpoint.last_changed = datetime.utcnow()
                
                    if last_status is None:
                        if current_status == "DOWN":
                            send_alert(f"🚨 {url} is DOWN (first check)", chat_id)

                    else:
                        if current_status == "DOWN":
                            send_alert(f"🚨 {url} went DOWN", chat_id)
                        else:
                            send_alert(f"✅ {url} is back UP", chat_id)

                endpoint.last_status = current_status
                endpoint.last_checked = datetime.utcnow()
                db.commit()

        except Exception as e:
            print("❌ ERROR:", e)

        finally:
            db.close()

        time.sleep(30)