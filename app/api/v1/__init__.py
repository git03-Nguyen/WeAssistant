from fastapi import APIRouter

from . import chat, documents, threads, users

router = APIRouter()
router.include_router(chat.router, tags=["chat"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(threads.router, prefix="/threads", tags=["threads"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
