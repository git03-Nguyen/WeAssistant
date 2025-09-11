from fastapi import APIRouter

from .base import router as root_router
from .v1 import router as v1_router

router = APIRouter()
router.include_router(root_router)
router.include_router(v1_router, prefix="/api/v1")
