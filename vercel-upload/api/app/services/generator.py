"""讲稿生成：优先调用大模型（OpenAI 兼容接口），无 Key 时使用本地模板引擎。"""
from __future__ import annotations

import json
import logging
import random
import re
from collections.abc import Iterable
from typing import Any

import httpx

from ..config import settings
from .styles import get_style

log = logging.getLogger("ppt-speech.gen")

CHARS_PER_MINUTE = 240  # 中文演讲平均语速（字/分钟）


# --------------------------------------------------------------------------- #
# 本地模板引擎（无大模型 Key 时的兜底，保证功能随时可用）
# --------------------------------------------------------------------------- #
FLAVOR: dict[str, dict[str, list[str]]] = {
    "formal": {
        "open": [
            "各位领导、各位{audience}，大家好。今天我汇报的主题是《{title}》，预计用时 {minutes} 分钟。",
            "尊敬的各位{audience}，上午好。下面由我就《{title}》作专题汇报，大约需要 {minutes} 分钟。",
            "大家好，感谢各位的时间。接下来我围绕《{title}》作简要说明。",
        ],
        "intro": ["首先，我们来看第 {i} 部分：{topic}。", "接下来进入第 {i} 部分，{topic}。", "第 {i} 部分，重点关注的是{topic}。"],
        "comment": [
            "这几项内容相互支撑，构成了本页的完整逻辑。",
            "需要说明的是，上述判断基于当前已掌握的情况。",
            "这一点，也是后续所有工作的前提。",
        ],
        "trans": ["以上是这一部分的主要内容，我们继续。", "接下来，把视线移到下一部分。", "这部分讲完，我们进入下一页。"],
        "tail": ["这一页的结论就落在这里。", "相关数据已在材料中列明。", ""],
        "close": [
            "以上就是我的汇报，恳请各位批评指正，谢谢大家。",
            "汇报完毕，感谢各位{audience}的聆听，欢迎提问。",
        ],
        "tips": ["语速控制在每分钟 240 字左右", "每页停留 45–90 秒，结论先行", "汇报结束后预留提问时间"],
    },
    "humorous": {
        "open": [
            "大家好，很高兴今天能站在这里，跟{audience}聊聊《{title}》。先说好，接下来 {minutes} 分钟，保证不睡着。",
            "各位{audience}好！为了这 {minutes} 分钟，我改了十七版稿子，最后决定还是说人话。",
        ],
        "intro": ["先看这个：{topic}。", "然后是这个有点意思的部分，{topic}。", "好，翻到第 {i} 页，{topic}。"],
        "comment": [
            "听起来像常识，但真做起来全是坑。",
            "这条我踩过，所以你们不用踩了。",
            "别急着点头，回去试试就知道有多难。",
        ],
        "trans": ["好，这一页先放过它，下一页更精彩。", "说到这儿，我们换个话题。", "铺垫完了，进入正题。"],
        "tail": ["对，就这么简单。", "道理都懂，做到的人不多。", ""],
        "close": [
            "以上就是今天的全部内容，希望各位{audience}带走一点点东西，哪怕只是一个笑点。谢谢大家！",
            "讲完了。如果只记住一句话，那就是——别把它想得太难。谢谢！",
        ],
        "tips": ["笑点是调味料，不是主菜，别超过 1/5 篇幅", "自嘲可以，别自贬", "重要信息前后各停一秒"],
    },
    "passionate": {
        "open": [
            "各位{audience}，今天我只讲一件事——《{title}》。给我 {minutes} 分钟，也给你们自己一次被打动的机会。",
            "站到这里之前，我问自己：这件事，值得讲吗？答案是值得。因为它是《{title}》。",
        ],
        "intro": ["第一，{topic}。", "看清楚这件事：{topic}。", "再看这里——{topic}！"],
        "comment": ["这不是选择，这是必须。", "我们没有退路，也不需要退路。", "这就是差距，也是机会。"],
        "trans": ["往前一步。", "继续。", "下一页，是更硬的骨头。"],
        "tail": ["记住这一点。", "把它刻在心里。", ""],
        "close": [
            "所以，不要再等了。从今天开始，从这一页开始。谢谢大家！",
            "我把话放在这里：做到的人，才有资格谈未来。谢谢！",
        ],
        "tips": ["短句为主，每个停顿都在推情绪", "结尾要有明确的行动号召", "音量与节奏做两到三次起伏"],
    },
    "story": {
        "open": [
            "我想先讲一个画面。关于《{title}》，关于我们为什么走到今天。",
            "去年的这个时候，我还不确定这件事能不能成。今天，我站在这里，讲《{title}》。",
        ],
        "intro": ["故事走到这一幕：{topic}。", "然后，转折出现了——{topic}。", "接下来发生的，和{topic}有关。"],
        "comment": [
            "那一刻我才明白，原来问题出在这里。",
            "这个细节，后来成了整件事的关键。",
            "很多年后回头看，那其实是一个分水岭。",
        ],
        "trans": ["故事还没讲完，我们往下走。", "再往后，事情开始变得不一样。", "接着，画面切到下一页。"],
        "tail": ["这就是当时的真实处境。", "没有人预料到后面会发生什么。", ""],
        "close": [
            "故事讲到这里，还没有结束。因为接下来的那一页，要由在座的各位一起写完。谢谢。",
            "这就是我想讲的全部。谢谢你们听完。",
        ],
        "tips": ["开场三秒内给出画面，而不是背景", "一次只讲一个人、一件事", "细节比形容词更有说服力"],
    },
    "academic": {
        "open": [
            "各位老师、各位同学，大家好。我汇报的题目是《{title}》，汇报时长约 {minutes} 分钟。",
            "尊敬的答辩委员会，下面我就《{title}》的研究工作做汇报。",
        ],
        "intro": ["第 {i} 部分，{topic}。", "接下来说明{topic}。", "关于第 {i} 部分，我们聚焦{topic}。"],
        "comment": ["该结果在 95% 置信水平下显著。", "这一处理保证了结论的稳健性。", "相关局限将在结论部分一并说明。"],
        "trans": ["以上是这一部分的汇报，我们进入下一部分。", "接下来汇报下一组结果。", "下面说明方法与数据。"],
        "tail": ["这一结论与已有文献基本一致。", "相关参数已附在附录中。", ""],
        "close": ["以上是我的汇报，恳请各位老师批评指正，谢谢。", "汇报完毕，请各位老师提问。"],
        "tips": ["先讲问题与贡献，再讲细节", "术语首次出现给全称", "主动交代局限，减少被追问"],
    },
    "roadshow": {
        "open": [
            "各位投资人好。今天 {minutes} 分钟，我讲清楚一件事：为什么现在是《{title}》最好的时机。",
            "感谢各位的时间。我们是{title}，我直接进入正题。",
        ],
        "intro": ["先看痛点：{topic}。", "第二块，{topic}。", "市场层面，{topic}。"],
        "comment": ["这是一个每年还在增长的市场。", "我们的获客成本只有行业均值的六成。", "这是别人短期内抄不走的部分。"],
        "trans": ["我们把镜头拉到下一页。", "说完市场，说方案。", "接下来是各位最关心的部分。"],
        "tail": ["这三个数字，是我们最硬的底牌。", "数据不会说谎。", ""],
        "close": [
            "以上就是我们的全部内容。现在，我们开放本轮融资，期待与各位同行。谢谢。",
            "一句话总结：需求真实、增长确定、团队在手。谢谢各位。",
        ],
        "tips": ["前 60 秒讲清痛点与规模", "用三个数字支撑一个结论", "留出 30% 时间给问答"],
    },
    "warm": {
        "open": [
            "今天站在这里，我其实准备了很多话，最后只想说一句：谢谢在座的每一位{audience}。",
            "关于《{title}》，我想从一个人说起。",
        ],
        "intro": ["我想先说{topic}。", "再往后，是{topic}。", "还有一件事，我一直记得：{topic}。"],
        "comment": ["这份心意，我一直记着。", "有些话当时没说出口，今天补上。", "日子过得真快，但那种感觉还在。"],
        "trans": ["说到这里，我想起了下一页的那件事。", "这些话，慢慢说。", "我们接着往下。"],
        "tail": ["愿我们都平安，愿我们都还在。", "我们都不擅长表达，可心里都清楚。", ""],
        "close": ["最后，把最好的祝福送给在座的每一位。谢谢大家。", "话不多说，都在心里。谢谢你们。"],
        "tips": ["语速放慢，留白比修辞重要", "说具体的人名和事", "结尾不要突然拔高"],
    },
    "concise": {
        "open": ["三件事：进展、问题、要什么支持。{minutes} 分钟讲完。", "直接说结论。今天讲《{title}》。"],
        "intro": ["第一，{topic}。", "第二，{topic}。", "第三，{topic}。"],
        "comment": ["细节在文档里。", "这一项目前卡在审批。", "需要两位同事支持。"],
        "trans": ["下一页。", "继续。", "最后一点。"],
        "tail": ["结论如上。", "已闭环。", ""],
        "close": ["讲完了，有问题现在提。", "就这些，散会。"],
        "tips": ["每页不超过三句话", "先说结论，理由一句带过", "需要决策的事项单独列出"],
    },
}

ORDINALS = ["第一", "第二", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"]

# 用于把某一页“讲够时长”的扩展句，{topic} 会被替换成当页标题
EXPAND = [
    "换句话说，{topic}不是一个抽象的说法，它落在每个人每天的具体选择里。",
    "很多人第一次听到{topic}，会觉得离自己很远，其实它就在手边。",
    "如果把时间拉长三年来看，{topic}带来的差别会非常明显。",
    "这一点，在{topic}上体现得尤其清楚。",
    "我举个例子：同样一件事，懂{topic}的人，处理方式完全不同。",
    "所以{topic}不是一个可选项，而是一个前提条件。",
    "这里的关键，不是知道{topic}，而是愿不愿意在真实场景里用它。",
    "回到{topic}本身，它真正解决的其实是效率问题。",
    "再说直白一点，{topic}决定了你在这件事上的上限。",
    "在座的各位如果只能带走一句话，那就是关于{topic}的这一句。",
    "最后补充一句：{topic}不是一次性动作，而是需要长期坚持的习惯。",
    "这也是为什么，我更愿意把{topic}叫作一种能力，而不是一个知识点。",
]


def _pick(pool: list[str], rng: random.Random) -> str:
    return pool[rng.randrange(len(pool))] if pool else ""


def _take(pool: list[str], used: dict[str, int], limit: int = 2) -> str:
    """优先取未使用过的句子；全部用过则允许重复，但同一句最多出现 limit 次。"""
    for item in pool:
        if item and used.get(item, 0) == 0:
            used[item] = 1
            return item
    for item in pool:
        if item and used.get(item, 0) < limit:
            used[item] = used.get(item, 0) + 1
            return item
    return ""


def count_words(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def estimate_seconds(text: str, language: str = "zh") -> int:
    words = count_words(text)
    if language == "en":
        return max(5, round(words / 2.5))
    return max(5, round(words / (CHARS_PER_MINUTE / 60)))


def _strip_end(text: str) -> str:
    return (text or "").strip().rstrip("。；;，,、 ")


def _enumerate(bullets: list[str], style_key: str, language: str) -> str:
    """把要点串成一句口语化的长句，而不是逐条罗列。"""
    bullets = [_strip_end(b) for b in bullets if _strip_end(b)]
    if not bullets:
        return ""
    if language == "en":
        return " ".join(f"{b}." for b in bullets)

    if style_key == "concise":
        return "；".join(bullets[:3]) + "。"

    if len(bullets) == 1:
        return f"{bullets[0]}。"

    clauses = [f"{ORDINALS[idx]}，{bullet}" for idx, bullet in enumerate(bullets[:5])]
    joined = "；".join(clauses)
    return joined + ("！" if style_key == "passionate" else "。")


def _filler(pool: list[str], used: dict[str, int], rng: random.Random) -> str:
    return _take(pool, used) or _pick(pool, rng)


def template_generate(
    *,
    title: str,
    slides: Iterable[dict],
    style_key: str,
    duration_min: int,
    audience: str,
    language: str = "zh",
) -> dict:
    """无大模型时，用风格化模板拼装讲稿，长度按目标时长控制。"""
    flavor = FLAVOR.get(style_key, FLAVOR["formal"])
    rng = random.Random(f"{title}|{style_key}|{duration_min}")
    slides = list(slides)
    used: dict[str, int] = {}

    budget_chars = max(300, int(duration_min * CHARS_PER_MINUTE * 0.95))
    opening = _pick(flavor["open"], rng).format(title=title, audience=audience or "朋友", minutes=duration_min)
    closing = _pick(flavor["close"], rng).format(title=title, audience=audience or "朋友", minutes=duration_min)

    n = max(1, len(slides))
    body_budget = max(240, budget_chars - count_words(opening) - count_words(closing))
    # 封面页与结束语不占用等分预算，正文各页平摊剩下的字数
    per_slide = max(60, body_budget // max(1, n - 1)) if n > 1 else body_budget

    expand_bag = EXPAND[:]
    rng.shuffle(expand_bag)

    def next_expand(topic: str) -> str:
        nonlocal expand_bag
        if not expand_bag:
            expand_bag = EXPAND[:]
            rng.shuffle(expand_bag)
        return expand_bag.pop().format(topic=topic)
    hooks = {
        "story": "我想先从一个具体的场景说起，那个场景，和今天这个题目有关。",
        "passionate": "我先问在座各位一个问题：这件事，和我们有没有关系？",
        "humorous": "先声明一下，今天这一页不是广告，是真心话。",
        "academic": "本汇报围绕一个核心问题展开，下面先交代研究背景。",
        "roadshow": "先说结论：这件事值得做，而且现在就该做。",
        "warm": "今天不打算讲大道理，只想讲几件小事。",
        "concise": "背景一句话带过，直接看结论。",
        "formal": "在进入正文之前，我先交代一下本次汇报的背景。",
    }

    out_slides: list[dict] = []
    for i, slide in enumerate(slides, start=1):
        topic = (slide.get("title") or f"第 {i} 页").strip()
        bullets = [b for b in (slide.get("body") or []) if b and b.strip()]
        parts: list[str] = []

        if i == 1:
            # 封面页：不重复标题，先给一句“为什么讲这个”
            parts.append(hooks.get(style_key, hooks["formal"]))
            if bullets:
                parts.append(_enumerate(bullets, style_key, language))
            if style_key != "concise":
                parts.append(next_expand(topic))
        else:
            parts.append(_pick(flavor["intro"], rng).format(i=i, topic=topic))
            if bullets:
                parts.append(_enumerate(bullets, style_key, language))
            # 交替补充点评句与扩展句，把这一页讲到目标字数
            guard = 0
            while count_words("".join(parts)) < per_slide and guard < 10:
                if guard % 2 == 0:
                    extra = _filler(flavor["comment"], used, rng)
                elif style_key == "concise":
                    extra = _filler(flavor["trans"], used, rng)
                else:
                    extra = next_expand(topic)
                if not extra:
                    extra = _filler(flavor["trans"], used, rng)
                if not extra:
                    break
                guard += 1
                if extra not in parts:
                    parts.append(extra)
            tail = _pick(flavor["tail"], rng)
            if tail:
                parts.append(tail)

        script = "".join(p for p in parts if p)
        out_slides.append(
            {
                "index": i,
                "title": topic,
                "script": script,
                "seconds": estimate_seconds(script, language),
            }
        )

    return {
        "opening": opening,
        "slides": out_slides,
        "closing": closing,
        "tips": flavor["tips"],
        "engine": "template",
    }


# --------------------------------------------------------------------------- #
# 大模型生成
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """你是一位资深的演讲教练与中文演讲稿作者，擅长把 PPT 大纲改写成可以直接照着念的口语化讲稿。

写作要求：
1. 以第一人称、口语化表达，句子短，避免书面腔和堆砌形容词。
2. 严格按页输出：每一页对应一段讲稿，长度与该页信息量匹配，页与页之间用自然的口语过渡衔接。
3. 不要复述版面文字，要把要点"讲"出来：补充解释、举例、给出结论。
4. 必须包含开场白（自我介绍 + 主题 + 钩子）和结束语（总结 + 号召/致谢）。
5. 全文中文（若 language=en 则用英文），总字数按目标时长控制（中文约 240 字/分钟）。
6. 只输出 JSON，不要输出 Markdown 代码块或任何解释。"""

USER_TEMPLATE = """请为下面这份 PPT 写一份演讲稿。

【演讲风格】{style_name}
风格要求：{style_prompt}

【基本信息】
- 演示文稿标题：{title}
- 目标时长：{duration} 分钟（约 {chars} 字）
- 听众：{audience}
- 语言：{language}
{extra}

【PPT 内容】
{slides_text}

【输出 JSON 结构】
{{
  "opening": "开场白全文",
  "slides": [{{"index": 1, "title": "该页标题", "script": "这一页要讲的话"}}],
  "closing": "结束语全文",
  "tips": ["给演讲者的 2-3 条现场提示"]
}}"""


def _slides_text(slides: list[dict]) -> str:
    lines = []
    for i, s in enumerate(slides, start=1):
        lines.append(f"第 {i} 页 | 标题：{s.get('title') or '（无标题）'}")
        for b in s.get("body") or []:
            lines.append(f"  - {b}")
        if s.get("notes"):
            lines.append(f"  备注：{s['notes']}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


async def llm_generate(
    *,
    title: str,
    slides: list[dict],
    style_key: str,
    duration_min: int,
    audience: str,
    language: str,
    extra: str = "",
) -> dict | None:
    style = get_style(style_key)
    chars = duration_min * CHARS_PER_MINUTE
    prompt = USER_TEMPLATE.format(
        style_name=style["name"],
        style_prompt=style["prompt"],
        title=title,
        duration=duration_min,
        chars=chars,
        audience=audience or "普通听众",
        language="英文" if language == "en" else "中文",
        extra=f"- 额外要求：{extra}" if extra else "",
        slides_text=_slides_text(slides),
    )

    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 400:  # 部分服务不支持 response_format
                payload.pop("response_format", None)
                resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            log.warning("大模型调用失败，改用模板引擎：%s", exc)
            return None

    parsed = _extract_json(content)
    if not parsed or not isinstance(parsed.get("slides"), list):
        log.warning("大模型返回内容无法解析为 JSON")
        return None

    out_slides = []
    for i, item in enumerate(parsed["slides"], start=1):
        script = str(item.get("script", "")).strip()
        if not script:
            continue
        fallback_title = slides[i - 1].get("title") if i <= len(slides) else ""
        out_slides.append(
            {
                "index": int(item.get("index") or i),
                "title": str(item.get("title") or fallback_title or f"第 {i} 页"),
                "script": script,
                "seconds": estimate_seconds(script, language),
            }
        )
    if not out_slides:
        return None

    return {
        "opening": str(parsed.get("opening", "")).strip(),
        "slides": out_slides,
        "closing": str(parsed.get("closing", "")).strip(),
        "tips": [str(t) for t in (parsed.get("tips") or [])][:4],
        "engine": "llm",
    }


async def generate_script(
    *,
    title: str,
    slides: list[dict],
    style_key: str,
    duration_min: int,
    audience: str,
    language: str = "zh",
    extra: str = "",
) -> dict:
    if settings.llm_enabled:
        result = await llm_generate(
            title=title,
            slides=slides,
            style_key=style_key,
            duration_min=duration_min,
            audience=audience,
            language=language,
            extra=extra,
        )
        if result:
            return result

    return template_generate(
        title=title,
        slides=slides,
        style_key=style_key,
        duration_min=duration_min,
        audience=audience,
        language=language,
    )
