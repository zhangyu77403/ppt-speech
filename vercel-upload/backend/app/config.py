"""应用配置：环境变量 + .env 文件。

运行环境差异：
- 本地 / Docker：数据与上传文件放在 backend/data/
- Vercel：函数文件系统只读，唯一可写目录是 /tmp（且实例重启即清空）
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

# Vercel 会在运行时注入 VERCEL=1，此时改用 /tmp（唯一可写目录）
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("NOW_REGION"))

# PPT_SPEECH_DATA_DIR 可用于本地模拟 / 自托管时指定数据目录
_DATA_DIR_OVERRIDE = os.environ.get("PPT_SPEECH_DATA_DIR")

if _DATA_DIR_OVERRIDE:
    DATA_DIR = Path(_DATA_DIR_OVERRIDE)
elif IS_VERCEL:
    DATA_DIR = Path("/tmp/ppt-speech")
else:
    DATA_DIR = BASE_DIR / "data"

MAX_UPLOAD_MB = 4 if IS_VERCEL else 30  # Vercel 函数请求体上限约 4.5MB

UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "讲稿工坊 SlideScript"
    app_env: str = "prod" if IS_VERCEL else "dev"

    # 数据库：优先 DATABASE_URL；否则尝试 MySQL；不可用时回退 SQLite（仅本地演示）
    database_url: str = ""
    mysql_url: str = "mysql+pymysql://root:123456@127.0.0.1:3306/ppt_speech?charset=utf8mb4"
    sqlite_path: str = str(DATA_DIR / "app.db")

    # 鉴权
    secret_key: str = "slide-script-dev-secret-change-me"
    token_expire_hours: int = 72

    # 大模型（任意 OpenAI 兼容接口：DeepSeek / 通义 / Moonshot / OpenAI）
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_timeout: int = 50  # 必须小于 Vercel 函数 maxDuration

    max_upload_mb: int = MAX_UPLOAD_MB
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())

    @property
    def is_vercel(self) -> bool:
        return IS_VERCEL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
