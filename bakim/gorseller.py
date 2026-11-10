#!/usr/bin/env python3
"""Görsellerin modern ve küçük kopyalarını üretir (AVIF + WebP, birkaç genişlikte). Orijinal JPG'lere dokunmaz.
Tek komut:  python3 bakim/gorseller.py      (gerekli: pip install pillow  — Pillow 11+ AVIF destekler)
Yalnızca eksik ya da kaynağından eski kopyaları üretir; tekrar çalıştırmak güvenlidir."""
import pathlib, re
from PIL import Image

KOK = pathlib.Path(__file__).resolve().parent.parent
ISLER = [  # (klasör, desen, genişlikler)
    ('kilavuz/img', r'[a-z_]+\.jpg', (480, 960)),
    ('assets/video', r'[a-z-]+\.jpg', (360,)),
]


def kaydet(im, hedef, tur):
    if tur == 'avif':
        im.save(hedef, quality=55, speed=4)
    else:
        im.save(hedef, quality=78, method=6)


def main():
    n = 0
    for klasor, desen, genislikler in ISLER:
        for kaynak in sorted((KOK / klasor).glob('*.jpg')):
            if not re.fullmatch(desen, kaynak.name):
                continue
            im = Image.open(kaynak).convert('RGB')
            g, y = im.size
            hedefler = [(kaynak.with_suffix('.' + t), None, t) for t in ('avif', 'webp')]
            hedefler += [(kaynak.with_name(f'{kaynak.stem}-{w}.{t}'), w, t) for w in genislikler if w < g for t in ('avif', 'webp')]
            for hedef, w, tur in hedefler:
                if hedef.exists() and hedef.stat().st_mtime >= kaynak.stat().st_mtime:
                    continue
                kopya = im if w is None else im.resize((w, round(y * w / g)), Image.LANCZOS)
                kaydet(kopya, hedef, tur)
                n += 1
    # Menü logosu (40 px gösterilir, 2x ekran için 80 px)
    logo = KOK / 'assets' / 'ikon' / 'logo-80.webp'
    if not logo.exists():
        Image.open(KOK / 'assets' / 'logo.webp').convert('RGB').resize((80, 80), Image.LANCZOS).save(logo, quality=82, method=6)
        n += 1
    print(f'gorseller: {n} dosya üretildi')


if __name__ == '__main__':
    main()
