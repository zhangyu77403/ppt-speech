"""PPTX 解析：抽取每页标题、要点、备注。"""
from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation as PptxPresentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

MAX_BULLET_CHARS = 160
MAX_BULLETS = 8


def _clean(text: object, limit: int = MAX_BULLET_CHARS) -> str:
    if text is None:
        return ""
    value = re.sub(r"\s+", " ", str(text)).strip()
    value = value.replace("\u000b", " ").strip()
    return value[:limit]


def _iter_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_shapes(shape.shapes)
        else:
            yield shape


def _text_of(shape) -> list[str]:
    lines: list[str] = []
    if not shape.has_text_frame:
        return lines
    for paragraph in shape.text_frame.paragraphs:
        text = _clean(paragraph.text)
        if text:
            lines.append(text)
    return lines


def _table_lines(shape) -> list[str]:
    rows: list[str] = []
    if not getattr(shape, "has_table", False):
        return rows
    for row in shape.table.rows:
        cells = [_clean(cell.text, 60) for cell in row.cells]
        cells = [c for c in cells if c]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def parse_pptx(path: str | Path) -> dict:
    prs = PptxPresentation(str(path))
    slides: list[dict] = []

    for index, slide in enumerate(prs.slides, start=1):
        title_shape = slide.shapes.title
        title = _clean(title_shape.text, 120) if title_shape is not None else ""

        body: list[str] = []
        for shape in _iter_shapes(slide.shapes):
            if title_shape is not None and shape.shape_id == title_shape.shape_id:
                continue
            if getattr(shape, "has_table", False):
                body.extend(_table_lines(shape))
                continue
            body.extend(_text_of(shape))

        # 去重并保持顺序
        seen: set[str] = set()
        bullets: list[str] = []
        for line in body:
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            bullets.append(line)
        bullets = bullets[:MAX_BULLETS]

        if not title:
            title = bullets[0] if bullets else f"第 {index} 页"
            bullets = bullets[1:] if bullets else bullets

        notes = ""
        if slide.has_notes_slide:
            notes = _clean(slide.notes_slide.notes_text_frame.text, 1200)

        slides.append(
            {
                "slide_index": index,
                "title": title or f"第 {index} 页",
                "body": bullets,
                "notes": notes,
            }
        )

    first_title = next((s["title"] for s in slides if s["title"]), "")
    return {
        "title": first_title or Path(path).stem,
        "slide_count": len(slides),
        "slides": slides,
    }
