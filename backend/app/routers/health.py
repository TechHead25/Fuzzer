from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Fuzz-Sentinel backend is running"}
