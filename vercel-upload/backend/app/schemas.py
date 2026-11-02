"""请求/响应模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- 鉴权 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    display_name: str = Field(default="", max_length=32)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ---------- PPT ----------
class SlideOut(BaseModel):
    slide_index: int
    title: str
    body: list[str]
    notes: str = ""

    model_config = {"from_attributes": True}


class PresentationOut(BaseModel):
    id: int
    title: str
    original_filename: str
    slide_count: int
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PresentationDetail(PresentationOut):
    slides: list[SlideOut]


# ---------- 风格 ----------
class StyleOut(BaseModel):
    key: str
    name: str
    emoji: str
    tagline: str
    description: str
    accent: str
    sample: str


# ---------- 讲稿 ----------
class GenerateIn(BaseModel):
    presentation_id: int
    style_key: str = "formal"
    duration_min: int = Field(default=8, ge=1, le=60)
    audience: str = Field(default="公司同事", max_length=64)
    language: str = Field(default="zh", pattern="^(zh|en)$")
    extra: str = Field(default="", max_length=500)


class ScriptSlide(BaseModel):
    index: int
    title: str
    script: str
    seconds: int = 60


class ScriptContent(BaseModel):
    opening: str = ""
    slides: list[ScriptSlide] = []
    closing: str = ""
    tips: list[str] = []


class ScriptOut(BaseModel):
    id: int
    title: str
    presentation_id: int
    style_key: str
    style_name: str
    duration_min: int
    audience: str
    language: str
    engine: str
    word_count: int
    content: ScriptContent
    created_at: datetime

    model_config = {"from_attributes": True}


class ScriptUpdateIn(BaseModel):
    title: str | None = None
    content: dict[str, Any] | None = None
