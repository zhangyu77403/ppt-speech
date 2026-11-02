"""路由依赖：从 Authorization 头解析当前用户。"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

AUTH_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="请先登录",
    headers={"WWW-Authenticate": "Bearer"},
)


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AUTH_ERROR
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        raise AUTH_ERROR
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise AUTH_ERROR
    return user
