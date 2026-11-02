"""风格列表与运行配置。"""
from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..database import DB_BACKEND
from ..schemas import StyleOut
from ..services.styles import STYLES

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/styles", response_model=list[StyleOut])
def list_styles() -> list[StyleOut]:
    return [StyleOut(**s) for s in STYLES]


@router.get("/meta/config")
def config() -> dict:
    return {
        "app_name": settings.app_name,
        "llm_enabled": settings.llm_enabled,
        "llm_model": settings.llm_model if settings.llm_enabled else "",
        "db_backend": DB_BACKEND,
        "max_upload_mb": settings.max_upload_mb,
        "demo_user": "demo",
    }
