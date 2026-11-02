"""ORM 模型：users / presentations / slides / scripts。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    presentations: Mapped[list["Presentation"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    scripts: Mapped[list["Script"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="未命名演示文稿", nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    slide_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    owner: Mapped[User] = relationship(back_populates="presentations")
    slides: Mapped[list["Slide"]] = relationship(
        back_populates="presentation",
        cascade="all, delete-orphan",
        order_by="Slide.slide_index",
    )
    scripts: Mapped[list["Script"]] = relationship(back_populates="presentation", cascade="all, delete-orphan")


class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    presentation_id: Mapped[int] = mapped_column(
        ForeignKey("presentations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slide_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    body: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    presentation: Mapped[Presentation] = relationship(back_populates="slides")


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    presentation_id: Mapped[int] = mapped_column(
        ForeignKey("presentations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    style_key: Mapped[str] = mapped_column(String(32), default="formal", nullable=False)
    style_name: Mapped[str] = mapped_column(String(32), default="正式严谨", nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    audience: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="zh", nullable=False)
    engine: Mapped[str] = mapped_column(String(32), default="template", nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    owner: Mapped[User] = relationship(back_populates="scripts")
    presentation: Mapped[Presentation] = relationship(back_populates="scripts")
