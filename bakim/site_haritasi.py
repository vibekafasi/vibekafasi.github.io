#!/usr/bin/env python3
"""sitemap.xml üretir: bütün sayfalar + her sayfanın TR/RU/EN karşılıkları (hreflang) + son değişiklik tarihi (git'ten).
Tek komut:  python3 bakim/site_haritasi.py"""
import re, subprocess, pathlib, datetime
from xml.sax.saxutils import escape

KOK = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://vibekafasi.github.io'
DILLER = ('tr', 'ru', 'en')


def git_tarihleri():
    """Her dosyanın son commit tarihi (tek git çağrısıyla). Git yoksa boş döner."""
    try:
        cikti = subprocess.run(['git', '-C', str(KOK), 'log', '--format=@%cs', '--name-only', '--', '*.html'],
                               capture_output=True, text=True, check=True).stdout
    except Exception:
        return {}
    t, son = None, {}
    for satir in cikti.splitlines():
        if satir.startswith('@'):
            t = satir[1:]
        elif satir and satir not in son:
            son[satir] = t
    return son


def main():
    tarih = git_tarihleri()
    bugun = datetime.date.today().isoformat()
    sayfalar = {}
    for dosya in sorted(KOK.rglob('index.html')):
        if any(p in dosya.parts for p in ('.git', 'node_modules', 'bakim')):
            continue
        h = dosya.read_text(encoding='utf-8')
        if 'name="robots" content="noindex' in h:
            continue
        rel = dosya.relative_to(KOK).as_posix()
        sayfalar['/' + rel[:-len('index.html')]] = tarih.get(rel, bugun)
    def tr_yolu(y): return re.sub(r'^/(ru|en)/', '/', y)
    def dil_yolu(y, d): return tr_yolu(y) if d == 'tr' else f'/{d}' + tr_yolu(y)
    def oncelik(y):
        t = tr_yolu(y)
        if t == '/': return '1.0'
        if t in ('/akademi/', '/kilavuz/'): return '0.9'
        if t.startswith('/akademi/sozluk/') and t != '/akademi/sozluk/': return '0.6'
        return '0.8'
    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for y in sorted(sayfalar, key=lambda y: (tr_yolu(y), y)):
        s.append(f'<url><loc>{escape(SITE + y)}</loc><lastmod>{sayfalar[y]}</lastmod><priority>{oncelik(y)}</priority>')
        es = [d for d in DILLER if dil_yolu(y, d) in sayfalar]
        if len(es) > 1:
            for d in es:
                s.append(f' <xhtml:link rel="alternate" hreflang="{d}" href="{escape(SITE + dil_yolu(y, d))}"/>')
            s.append(f' <xhtml:link rel="alternate" hreflang="x-default" href="{escape(SITE + dil_yolu(y, "tr"))}"/>')
        s.append('</url>')
    s.append('</urlset>')
    (KOK / 'sitemap.xml').write_text('\n'.join(s) + '\n', encoding='utf-8')
    print(f'site_haritasi: {len(sayfalar)} sayfa')


if __name__ == '__main__':
    main()
