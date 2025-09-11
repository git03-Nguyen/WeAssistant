from fastapi import APIRouter

from app.config.settings import SETTINGS

router = APIRouter()


@router.post("/")
async def root():
    return {"status": "healthy", "service": SETTINGS.app_name}
