from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.services.monitor import run_monitor
from app.api.routes.endpoints import router as endpoint_router
import os
from app.api.routes.auth import router as auth_router 
from app.api.routes.telegram import router as telegram_router
from app.api.routes.test import router as test_router
from app.api.routes.user import router as user_router
from app.workers.telegram_worker import telegram_worker
from app.workers.check_url_worker import check_url_worker
from app.workers.check_url_worker import check_url_worker

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
app.include_router(user_router)

@app.get("/")
def home():
    return FileResponse(
        "static/index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
    )

@app.on_event("startup")
async def start_monitor():
    print("🚀 STARTING TELEGRAM WORKER")
    asyncio.create_task(telegram_worker())

    print("🚀 STARTING URL CHECK WORKER")
    asyncio.create_task(check_url_worker())

    print("🚀 STARTING MONITOR ENQUEUER TASK")
    asyncio.create_task(run_monitor())

@app.get("/health")
def health():
    return {"status": "ok"}

