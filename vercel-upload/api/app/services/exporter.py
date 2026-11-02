"""讲稿导出：Markdown / Word。"""
from __future__ import annotations

from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def _fmt_seconds(seconds: int) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m}分{s:02d}秒"


def to_markdown(script) -> str:
    content = script.content or {}
    lines: list[str] = [
        f"# {script.title}",
        "",
        f"> 风格：{script.style_name} ｜ 目标时长：{script.duration_min} 分钟 ｜ 听众：{script.audience or '—'} ｜ 字数：{script.word_count}",
        "",
        "## 开场白",
        "",
        content.get("opening", ""),
        "",
    ]
    for item in content.get("slides", []):
        lines += [
            f"## 第 {item.get('index')} 页 · {item.get('title', '')}",
            "",
            f"*建议用时：{_fmt_seconds(item.get('seconds', 60))}*",
            "",
            item.get("script", ""),
            "",
        ]
    lines += ["## 结束语", "", content.get("closing", ""), ""]
    tips = content.get("tips") or []
    if tips:
        lines += ["## 现场提示", ""] + [f"- {t}" for t in tips] + [""]
    return "\n".join(lines)


def _set_cn_font(run, name: str = "微软雅黑") -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def to_docx(script) -> bytes:
    content = script.content or {}
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(script.title or "演讲稿")
    run.bold = True
    run.font.size = Pt(20)
    _set_cn_font(run)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta.add_run(
        f"风格：{script.style_name}　｜　目标时长：{script.duration_min} 分钟　｜　听众：{script.audience or '—'}"
    )
    meta_run.font.size = Pt(10)
    meta_run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    _set_cn_font(meta_run)

    def heading(text: str) -> None:
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(0x2B, 0x2B, 0x2B)
        _set_cn_font(r)

    def body(text: str) -> None:
        for para in (text or "").split("\n"):
            if not para.strip():
                continue
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Pt(24)
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run(para.strip())
            _set_cn_font(r)

    if content.get("opening"):
        heading("开场白")
        body(content["opening"])

    for item in content.get("slides", []):
        doc.add_paragraph()
        heading(f"第 {item.get('index')} 页 · {item.get('title', '')}　（{_fmt_seconds(item.get('seconds', 60))}）")
        body(item.get("script", ""))

    if content.get("closing"):
        doc.add_paragraph()
        heading("结束语")
        body(content["closing"])

    tips = content.get("tips") or []
    if tips:
        doc.add_paragraph()
        heading("现场提示")
        for tip in tips:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(tip)
            _set_cn_font(r)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
