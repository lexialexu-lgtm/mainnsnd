# -*- coding: utf-8 -*-
"""Нумерует VEO, чтобы в файле не было одинаковых строк.
Счётчик свой для каждого движения: "1 Animate it. no music", "2 Animate it. no music", ...
python number_veo.py rows.json
"""
import re
import sys
from collections import Counter
from promptlib import load, save

path = sys.argv[1]
rows = load(path)
cnt = Counter()
for i, r in enumerate(rows, 1):
    v = re.sub(r"^\d+\s+", "", r["veo"].strip())
    v = re.sub(r"\s*no music\.?$", "", v, flags=re.I).strip()
    if not v.endswith("."):
        v += "."
    v = v[0].upper() + v[1:]
    cnt[v] += 1
    r["veo"] = f"{cnt[v]} {v} no music"
save(path, rows)
print("OK: VEO пронумерованы;", ", ".join(f"{k} ×{n}" for k, n in cnt.most_common()))
