#!/usr/bin/env python3
"""Günlük çalışır (GitHub Actions): süresi dolan ayların kodlarını akademi/anahtar.json'dan siler.
Bir ayın kodu, sonraki ayın 5'ine kadar geçerli kalır (geçiş payı). Gizli anahtar gerekmez."""
import json, datetime, pathlib
yol = pathlib.Path(__file__).with_name('anahtar.json')
d = json.loads(yol.read_text())
t = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
y, m = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
onceki = f'{y:04d}-{m:02d}'; simdi = f'{t.year:04d}-{t.month:02d}'
sil = [a for a in d['aylar'] if a < simdi and not (a == onceki and t.day <= 5)]
for a in sil: del d['aylar'][a]
if sil:
    yol.write_text(json.dumps(d, separators=(',', ':'))); print('silindi:', sil)
else:
    print('değişiklik yok')
