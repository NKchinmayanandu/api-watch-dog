from fastapi import APIRouter, Response

router = APIRouter()

FAIL_MODE = False

@router.get("/toggle-fail")
def toggle_fail():
    global FAIL_MODE
    FAIL_MODE = not FAIL_MODE
    return {"fail_mode": FAIL_MODE}

@router.get("/health")
def health(response: Response):
    if FAIL_MODE:
        response.status_code = 500
        return {"status": "down"}
    return {"status": "ok"}