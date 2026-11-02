"""生成一份示例 PPT，方便新用户零门槛体验完整流程。"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Pt

SAMPLE_SLIDES: list[tuple[str, list[str]]] = [
    ("AI 时代，我们该如何学习", ["从“记住知识”到“调用工具”", "效率被重新定义", "每个人都在同一起跑线"]),
    ("三个正在发生的变化", ["信息获取成本趋近于零", "稀缺的不再是答案，而是好问题", "评价标准从“完成”转向“判断”"]),
    ("被低估的三种能力", ["提问：把模糊需求拆成可执行的问题", "验证：对 AI 的答案保持怀疑", "整合：把碎片产出拼成完整方案"]),
    ("一个真实案例", ["用 AI 三天做完两周的调研", "关键不是快，而是敢于先做一版", "人的价值在取舍，而非堆砌"]),
    ("接下来怎么做", ["每周留两小时做“工具实验”", "建立自己的提示词库", "把重复劳动全部交给机器"]),
    ("总结", ["工具会变，判断力不会过时", "先行动，再优化", "把时间还给真正重要的事"]),
]


def build_sample_pptx(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Pt(960)
    prs.slide_height = Pt(540)

    layout_title = prs.slide_layouts[0]
    layout_content = prs.slide_layouts[1]

    cover = prs.slides.add_slide(layout_title)
    cover.shapes.title.text = SAMPLE_SLIDES[0][0]
    cover.placeholders[1].text = "一次关于学习方式的分享"

    for title, bullets in SAMPLE_SLIDES[1:]:
        slide = prs.slides.add_slide(layout_content)
        slide.shapes.title.text = title
        body = slide.placeholders[1].text_frame
        body.text = bullets[0]
        for line in bullets[1:]:
            body.add_paragraph().text = line

    prs.save(path)
    return path
