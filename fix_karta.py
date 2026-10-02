# -*- coding: utf-8 -*-
"""Подставляет КАРТА дословно из исходника.
python fix_karta.py rows.json source.txt
"""
import sys
from promptlib import load, save, source_lines

rows_path, src_path = sys.argv[1], sys.argv[2]
rows = load(rows_path)
src = source_lines(src_path)
if len(rows) != len(src):
    sys.exit(f"ОШИБКА: строк в JSON {len(rows)}, в исходнике {len(src)} — сначала выровняй количество")
changed = 0
for r, s in zip(rows, src):
    if r.get("karta") != s:
        changed += 1
    r["karta"] = s
save(rows_path, rows)
print(f"OK: КАРТА подставлена, исправлено {changed} из {len(rows)}")
