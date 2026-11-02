"""FastAPI 应用入口。"""
from __future__ import annotations

import logging
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import UPLOAD_DIR, settings
from .database import DB_BACKEND, SessionLocal, init_db
from .models import Presentation, Slide, User
from .routers import auth, meta, presentations, scripts
from .security import hash_password
from .services.ppt_parser import parse_pptx
from .services.sample_ppt import build_sample_pptx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ppt-speech")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def seed_demo() -> None:
    """创建体验账号，并附带一份示例 PPT。"""
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == "demo"))
        if not user:
            user = User(username="demo", display_name="体验用户", password_hash=hash_password("demo123"))
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info("已创建体验账号 demo / demo123")

        has_deck = db.scalar(select(Presentation).where(Presentation.user_id == user.id))
        if not has_deck:
            target = UPLOAD_DIR / "sample-ai-learning.pptx"
            if not target.exists():
                build_sample_pptx(target)
            parsed = parse_pptx(target)
            deck = Presentation(
                user_id=user.id,
                title=parsed["title"],
                original_filename="示例-AI时代的学习.pptx",
                stored_path=str(target),
                file_size=target.stat().st_size,
                slide_count=parsed["slide_count"],
            )
            db.add(deck)
            db.flush()
            for item in parsed["slides"]:
                db.add(
                    Slide(
                        presentation_id=deck.id,
                        slide_index=item["slide_index"],
                        title=item["title"],
                        body=item["body"],
                        notes=item["notes"],
                    )
                )
            db.commit()
            log.info("已生成示例演示文稿：%s", parsed["title"])
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_demo()
    log.info("服务已启动：%s（DB=%s，LLM=%s）", settings.app_name, DB_BACKEND, "on" if settings.llm_enabled else "off")
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(presentations.router)
app.include_router(scripts.router)
app.include_router(meta.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "db": DB_BACKEND, "llm": settings.llm_enabled}


if FRONTEND_DIST.exists():  # 生产构建后，前后端同源部署
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        """静态文件优先，其余路径交给前端路由（history 模式回退 index.html）。"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="接口不存在")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

else:  # 开发阶段：Vite 单独启动，这里给个提示页
    @app.get("/")
    def index() -> dict:
        return {
            "message": "前端未构建。开发模式请运行 cd frontend && pnpm dev（默认 http://localhost:5173）",
            "docs": "/api/docs",
        }
