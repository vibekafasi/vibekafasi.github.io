#!/usr/bin/env python3
"""Sitenin bütün bakım adımlarını sırayla çalıştırır. Yeni sayfa ekledikten / sayfaları yeniden ürettikten sonra:

    python3 bakim/hepsi.py

1) gorseller.py     eksik AVIF/WebP kopyaları üretir (Pillow gerekir; yoksa atlanır)
2) duzelt.py        <head> bloğunu, hreflang/canonical'ı, eksik SEO etiketlerini tek tip yapar
3) arama_dizini.py  site araması dizinini (assets/arama/*.json) yeniler
4) site_haritasi.py sitemap.xml'i hreflang karşılıklarıyla yeniler
Hepsi tekrar çalıştırılabilir: değişmesi gerekmeyen dosyaya dokunmaz."""
import importlib, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
for ad in ('gorseller', 'duzelt', 'arama_dizini', 'site_haritasi'):
    try:
        importlib.import_module(ad).main()
    except ImportError as e:
        print(f'{ad}: atlandı ({e})')
