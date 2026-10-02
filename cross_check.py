# -*- coding: utf-8 -*-
"""Ищет NANO, похожие на 80%+ на кадры из других готовых сценариев (work/<prefix>.json).
python cross_check.py work/<prefix>.json
"""
import glob
import os
import re
import sys
from promptlib import load, similar

me = os.path.abspath(sys.argv[1])
mine = load(me)
others = [p for p in glob.glob("work/*.json")
          if re.fullmatch(r"[a-z]+\.json", os.path.basename(p)) and os.path.abspath(p) != me]
hits = 0
for p in others:
    for j, o in enumerate(load(p), 1):
        for i, r in enumerate(mine, 1):
            s = similar(r["nano"], o["nano"])
            if s >= 0.8:
                hits += 1
                print(f"ERR #{i} похож на {os.path.basename(p)}#{j} ({s:.0%})")
print("OK: пересечений с другими сценариями нет" if not hits else f"НАЙДЕНО {hits} пересечений")
sys.exit(1 if hits else 0)
