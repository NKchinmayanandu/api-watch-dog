from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import threading
from app.services.monitor import run_monitor
from app.api.routes.endpoints import router as endpoint_router
from app.services.notifier import send_alert
import os
from app.db.base import Base
from app.db.session import engine
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.api.routes.auth import router as auth_router 
from app.api.routes.telegram import router as telegram_router
from app.api.routes.test import router as test_router


load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

app = FastAPI()

# CORS — allow the static Render frontend to call this OCI backend
# Set ALLOWED_ORIGINS in your OCI .env as a comma-separated list, e.g.:
# ALLOWED_ORIGINS=https://api-watchdog.onrender.com
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(endpoint_router, prefix="/endpoints")
app.include_router(auth_router)
app.include_router(telegram_router)
app.include_router(test_router)

@app.get("/")
def home():
    return FileResponse(
        "static/index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
    )

@app.on_event("startup")
def start_mointor():
    print("🚀 STARTING MONITOR THREAD")
    thread = threading.Thread(target=run_monitor)
    thread.daemon = True
    thread.start()

@app.get("/health")
def health():
    return {"status": "ok"}

