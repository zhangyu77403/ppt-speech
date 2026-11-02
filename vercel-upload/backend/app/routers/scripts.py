"""讲稿生成、查询、编辑、导出。"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..models import Presentation, Script, User
from ..schemas import GenerateIn, ScriptContent, ScriptOut, ScriptUpdateIn
from ..services.exporter import to_docx, to_markdown
from ..services.generator import count_words, generate_script
from ..services.styles import get_style

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


def _out(row: Script) -> ScriptOut:
    content = ScriptContent.model_validate(row.content or {})
    return ScriptOut(
        id=row.id,
        title=row.title,
        presentation_id=row.presentation_id,
        style_key=row.style_key,
        style_name=row.style_name,
        duration_min=row.duration_min,
        audience=row.audience,
        language=row.language,
        engine=row.engine,
        word_count=row.word_count,
        content=content,
        created_at=row.created_at,
    )


def _owned(db: Session, script_id: int, user: User) -> Script:
    row = db.get(Script, script_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="讲稿不存在")
    return row


@router.post("/generate", response_model=ScriptOut)
async def generate(
    payload: GenerateIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ScriptOut:
    presentation = db.get(Presentation, payload.presentation_id)
    if not presentation or presentation.user_id != user.id:
        raise HTTPException(status_code=404, detail="演示文稿不存在")
    if not presentation.slides:
        raise HTTPException(status_code=400, detail="该演示文稿没有可用的页面内容")

    style = get_style(payload.style_key)
    slides = [
        {"title": s.title, "body": s.body or [], "notes": s.notes or ""}
        for s in sorted(presentation.slides, key=lambda x: x.slide_index)
    ]

    result = await generate_script(
        title=presentation.title,
        slides=slides,
        style_key=style["key"],
        duration_min=payload.duration_min,
        audience=payload.audience,
        language=payload.language,
        extra=payload.extra,
    )

    content = {
        "opening": result.get("opening", ""),
        "slides": result.get("slides", []),
        "closing": result.get("closing", ""),
        "tips": result.get("tips", []),
    }
    text = content["opening"] + "".join(s.get("script", "") for s in content["slides"]) + content["closing"]
    row = Script(
        user_id=user.id,
        presentation_id=presentation.id,
        title=presentation.title,
        style_key=style["key"],
        style_name=style["name"],
        duration_min=payload.duration_min,
        audience=payload.audience,
        language=payload.language,
        engine=result.get("engine", "template"),
        word_count=count_words(text),
        content=content,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(row)


@router.get("", response_model=list[ScriptOut])
def list_scripts(
    presentation_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    stmt = select(Script).where(Script.user_id == user.id)
    if presentation_id:
        stmt = stmt.where(Script.presentation_id == presentation_id)
    rows = db.scalars(stmt.order_by(Script.created_at.desc(), Script.id.desc())).all()
    return [_out(r) for r in rows]


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(script_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> ScriptOut:
    return _out(_owned(db, script_id, user))


@router.patch("/{script_id}", response_model=ScriptOut)
def update_script(
    script_id: int,
    payload: ScriptUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ScriptOut:
    row = _owned(db, script_id, user)
    if payload.title is not None:
        row.title = payload.title[:255]
    if payload.content is not None:
        content = ScriptContent.model_validate(payload.content)
        row.content = content.model_dump()
        text = content.opening + "".join(s.script for s in content.slides) + content.closing
        row.word_count = count_words(text)
    db.commit()
    db.refresh(row)
    return _out(row)


@router.delete("/{script_id}")
def delete_script(script_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = _owned(db, script_id, user)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/{script_id}/export")
def export_script(
    script_id: int,
    fmt: str = Query(default="md", pattern="^(md|docx)$"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = _owned(db, script_id, user)
    safe_name = "".join(c for c in (row.title or "演讲稿") if c not in '\\/:*?"<>|')[:60] or "演讲稿"

    if fmt == "docx":
        payload = to_docx(row)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{safe_name}.docx"
    else:
        payload = to_markdown(row).encode("utf-8")
        media = "text/markdown; charset=utf-8"
        filename = f"{safe_name}.md"

    return Response(
        content=payload,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
