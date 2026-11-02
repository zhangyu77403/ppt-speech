"""PPT 上传、列表、详情、删除。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import UPLOAD_DIR, settings
from ..database import get_db
from ..deps import current_user
from ..models import Presentation, Slide, User
from ..schemas import PresentationDetail, PresentationOut, SlideOut
from ..services.ppt_parser import parse_pptx

router = APIRouter(prefix="/api/presentations", tags=["presentations"])

ALLOWED = {".pptx"}


@router.post("/upload", response_model=PresentationDetail)
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PresentationDetail:
    filename = file.filename or "presentation.pptx"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=400, detail="只支持 .pptx 文件（可先用 PowerPoint 另存为 pptx）")

    raw = await file.read()
    size = len(raw)
    if size == 0:
        raise HTTPException(status_code=400, detail="文件为空")
    if size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {settings.max_upload_mb}MB")

    stored = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    stored.write_bytes(raw)

    try:
        parsed = parse_pptx(stored)
    except Exception as exc:  # noqa: BLE001
        stored.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"解析失败：{exc}") from exc

    if not parsed["slides"]:
        stored.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="这份 PPT 里没有可识别的文字内容")

    presentation = Presentation(
        user_id=user.id,
        title=parsed["title"][:255],
        original_filename=filename[:255],
        stored_path=str(stored),
        file_size=size,
        slide_count=parsed["slide_count"],
    )
    db.add(presentation)
    db.flush()

    for item in parsed["slides"]:
        db.add(
            Slide(
                presentation_id=presentation.id,
                slide_index=item["slide_index"],
                title=item["title"],
                body=item["body"],
                notes=item["notes"],
            )
        )
    db.commit()
    db.refresh(presentation)
    return _detail(presentation)


@router.get("", response_model=list[PresentationOut])
def list_presentations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(Presentation)
        .where(Presentation.user_id == user.id)
        .order_by(Presentation.created_at.desc(), Presentation.id.desc())
    ).all()
    return [PresentationOut.model_validate(r) for r in rows]


@router.get("/{presentation_id}", response_model=PresentationDetail)
def get_presentation(
    presentation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PresentationDetail:
    row = db.scalar(
        select(Presentation)
        .options(selectinload(Presentation.slides))
        .where(Presentation.id == presentation_id, Presentation.user_id == user.id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="演示文稿不存在")
    return _detail(row)


@router.delete("/{presentation_id}")
def delete_presentation(
    presentation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = db.get(Presentation, presentation_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="演示文稿不存在")
    Path(row.stored_path).unlink(missing_ok=True) if row.stored_path else None
    db.delete(row)
    db.commit()
    return {"ok": True}


def _detail(row: Presentation) -> PresentationDetail:
    slides = sorted(row.slides, key=lambda s: s.slide_index)
    return PresentationDetail(
        id=row.id,
        title=row.title,
        original_filename=row.original_filename,
        slide_count=row.slide_count,
        file_size=row.file_size,
        created_at=row.created_at,
        slides=[SlideOut.model_validate(s) for s in slides],
    )
