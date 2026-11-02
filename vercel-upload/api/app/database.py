"""数据库连接：MySQL 优先，检测不可用时自动回退 SQLite（方便本地演示）。"""
from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

log = logging.getLogger("ppt-speech.db")


def _mysql_alive(url: str) -> bool:
    """用短超时探测 MySQL 是否可连接，避免启动时长时间卡住。"""
    try:
        probe = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
        probe.dispose()
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("MySQL 不可用，回退 SQLite：%s", str(exc).splitlines()[0][:200])
        return False


def _resolve_url() -> tuple[str, str]:
    if settings.database_url:
        return settings.database_url, "env"
    # Vercel 上没有本地 MySQL，探测只会白白拖慢冷启动
    if not settings.is_vercel and _mysql_alive(settings.mysql_url):
        return settings.mysql_url, "mysql"
    return f"sqlite:///{settings.sqlite_path}", "sqlite"


DB_URL, DB_BACKEND = _resolve_url()

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=connect_args,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  确保模型已注册

    Base.metadata.create_all(bind=engine)
    log.info("数据库已就绪：%s (%s)", DB_URL.split("@")[-1], DB_BACKEND)
