import requests
import time 
from app.services.notifier import send_alert
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.user import User
def check_endpoint(url:str):
    try:
        response = requests.get(url,timeout=5)

        if response.status_code == 200: 
            return "UP",response.status_code
        else:
            return "DOWN",response.status_code
    except requests.exceptions.RequestException:
        return "DOWN", None

def has_status_changed(old_status: str, new_status: str):
    return old_status != new_status

def run_monitor():
    last_status_map = {}

    while True:
        print("Monitor loop running...")

        db = SessionLocal()

        try:
            endpoints = db.query(Endpoint).all()

            for endpoint in endpoints:
                url = endpoint.url

                current_status, code = check_endpoint(url)

                log = CheckLog(
                        endpoint_id=endpoint.id,
                        status=current_status,
                        status_code=code
                                        )

                db.add(log)
                db.commit()

                # 🔥 FETCH USER
                user = db.query(User).filter(User.id == endpoint.user_id).first()
                chat_id = user.chat_id if user else None

                last_status = last_status_map.get(url)

                if last_status is None:
                    if current_status == "DOWN":
                        send_alert(f"🚨 {url} is DOWN (first check)", chat_id)

                elif has_status_changed(last_status, current_status):
                    if current_status == "DOWN":
                        send_alert(f"🚨 {url} went DOWN", chat_id)
                    else:
                        send_alert(f"✅ {url} is back UP", chat_id)

                last_status_map[url] = current_status

        except Exception as e:
            print("❌ ERROR:", e)

        finally:
            db.close()

        time.sleep(30)

               