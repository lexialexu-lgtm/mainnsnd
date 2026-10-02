# -*- coding: utf-8 -*-
"""Общие правила и проверки для NANO / VEO / KARTA."""
import json
import re
from difflib import SequenceMatcher

TAIL = "no illustration, no cartoon, no CGI glow, no neon, no fantasy."
NO_KIDS = "no kids."

NANO_BANNED = [
    "illustration", "diagram", "cutaway", "cross-section", "cross section", "infographic",
    "schematic", "render", "rendered", "rendering", "concept art",
    "glow", "glowing", "sheen", "neon", "luminous", "sparkle", "sparkling", "hologram",
    "holographic", "wireframe", "ethereal", "magical", "mystical",
    # стиль съёмки не задаём
    "documentary", "photojournalism", "photojournalistic", "film stock", "film grain",
    "kodak", "fujifilm", "portra", "cinestill",
    # дети
    "child", "children", "kid", "kids", "boy", "girl", "baby", "babies", "toddler",
    "teen", "teenager", "schoolchild", "infant",
    # жесть
    "blood", "bloody", "corpse", "dead body", "gore", "severed",
    # буквы, цифры, схемы в кадре
    "formula", "equation", "chart", "graph", "arrow", "arrows",
    # бренды
    "tesla", "spacex", "nasa logo", "snoopy", "falcon 9",
]
VEO_BANNED = ["blur", "blurry", "dust", "debris", "dirt", "grit"]

# Слова, означающие людей в кадре -> нужен "no kids."
PEOPLE_WORDS = [
    "man", "men", "woman", "women", "person", "people", "adult", "adults", "astronaut",
    "astronauts", "engineer", "engineers", "scientist", "scientists", "astronomer",
    "astronomers", "physicist", "physicists", "mathematician", "researcher", "researchers",
    "technician", "technicians", "worker", "workers", "crew", "pilot", "teacher", "figure",
    "figures", "family", "couple", "hand", "hands", "fingers", "palm", "silhouette",
    "operator", "controller", "controllers", "colleagues", "audience", "listeners",
    "students", "student", "tightrope walker", "cyclist", "driver", "programmer",
]

VEO_RE = re.compile(r"^(?:(\d+) )?([A-Z][A-Za-z\- ,]*?\.) no music$")

SPACE_WORDS_RU = ["Вселенн", "галактик", "Галактик", "звёзд", "звезд", "звезда", "звезды",
                  "планет", "расширен", "реликт", "сингул", "Луна", "Луны", "Луне", "Луну",
                  "Солнц", "орбит", "комет", "астероид", "чёрн", "космос", "космическ"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


def source_lines(path):
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def words(text):
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text.lower())


def has_term(text, term):
    t = text.lower()
    return re.search(r"(?<![a-z0-9-])" + re.escape(term) + r"(?![a-z0-9-])", t) is not None


def veo_base(veo):
    m = VEO_RE.match(veo.strip())
    return m.group(2) if m else None


def _tokens(text):
    return tuple(words(text.replace(TAIL, "").replace(NO_KIDS, "")))


def similar(a, b):
    """Похожесть двух промтов по словам, без общего хвоста (0..1)."""
    a, b = _tokens(a), _tokens(b)
    sm = SequenceMatcher(None, a, b, autojunk=False)
    if sm.real_quick_ratio() < 0.8 or sm.quick_ratio() < 0.8:
        return 0.0
    return sm.ratio()


def check_rows(rows, src):
    """Возвращает (errors, warnings)."""
    errs, warns = [], []
    if len(rows) != len(src):
        errs.append(f"строк в JSON {len(rows)}, в исходнике {len(src)}")
    prev_part = 1
    for i, r in enumerate(rows, 1):
        p = f"#{i}"
        for k in ("part", "space", "nano", "veo", "karta"):
            if k not in r:
                errs.append(f"{p}: нет поля {k}")
        if any(k not in r for k in ("part", "space", "nano", "veo", "karta")):
            continue
        if r["part"] not in (1, 2, 3, 4, 5):
            errs.append(f"{p}: part={r['part']}")
        elif r["part"] < prev_part:
            errs.append(f"{p}: part идёт назад ({prev_part}->{r['part']})")
        else:
            prev_part = r["part"]
        if not isinstance(r["space"], bool):
            errs.append(f"{p}: space не bool")
        if i <= len(src) and r["karta"] != src[i - 1]:
            errs.append(f"{p}: КАРТА не совпадает с исходником")
        nano = r["nano"].strip()
        if not (nano.endswith(TAIL) or nano.endswith(TAIL + " " + NO_KIDS)):
            errs.append(f"{p}: NANO не заканчивается хвостом")
        body = nano.replace(TAIL, "").replace(NO_KIDS, "")
        for t in NANO_BANNED:
            if has_term(body, t):
                errs.append(f"{p}: NANO запрещённое слово '{t}'")
        if re.search(r"[А-Яа-яЁё]", nano):
            errs.append(f"{p}: в NANO кириллица")
        if any(has_term(body, w) for w in PEOPLE_WORDS) and not nano.endswith(NO_KIDS):
            errs.append(f"{p}: в NANO есть люди, но нет 'no kids.'")
        n_words = len(words(body))
        if n_words < 25:
            warns.append(f"{p}: NANO короткий ({n_words} слов)")
        veo = r["veo"].strip()
        base = veo_base(veo)
        if base is None:
            errs.append(f"{p}: VEO не по формату 'N Движение. no music': {veo!r}")
        else:
            if not (1 <= len(base.split()) <= 6):
                errs.append(f"{p}: VEO длиннее 6 слов")
        for t in VEO_BANNED:
            if has_term(veo, t):
                errs.append(f"{p}: VEO запрещённое слово '{t}'")
    # VEO: уникальность и чередование
    seen = {}
    for i, r in enumerate(rows, 1):
        v = r.get("veo", "").strip()
        if v in seen:
            errs.append(f"#{i}: VEO повторяет #{seen[v]}: {v!r}")
        seen.setdefault(v, i)
    for i in range(1, len(rows)):
        a, b = veo_base(rows[i - 1].get("veo", "")), veo_base(rows[i].get("veo", ""))
        if a and a == b:
            errs.append(f"#{i + 1}: VEO то же движение, что в предыдущем кадре ({a})")
    # NANO: дубли и похожие
    nanos = [r.get("nano", "").strip() for r in rows]
    for i in range(len(nanos)):
        for j in range(i + 1, len(nanos)):
            s = similar(nanos[i], nanos[j])
            if s >= 0.8:
                errs.append(f"#{i + 1} и #{j + 1}: NANO похожи на {s:.0%}")
    return errs, warns


def space_share(rows):
    return sum(1 for r in rows if r.get("space")) / max(1, len(rows))


def duration(src, cps=15.0):
    """Оценка хронометража по символам (≈15 символов речи в секунду)."""
    sec = int(round(sum(len(s) for s in src) / cps))
    return f"{sec // 60}:{sec % 60:02d}"
