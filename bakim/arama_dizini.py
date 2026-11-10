#!/usr/bin/env python3
"""Site araması için küçük dizin dosyaları üretir: assets/arama/tr.json, ru.json, en.json.
Tek komut:  python3 bakim/arama_dizini.py
Yalnızca herkese görünen bilgiler girer (başlık, kısa açıklama, adres). Kilitli derslerin şifreli içeriği asla girmez.
Biçim: {"v":1,"o":[[başlık, açıklama, adres, tür, ek], ...]}  tür: d=ders, t=terim, s=sayfa, b=bölüm"""
import re, json, html, pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent
SON_EK = re.compile(r'\s*[|·—–-]\s*Vibe Kafası.*$|\s*\|\s*.*Akademi.*$')


def temiz(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x or ''))).strip()


def bul(desen, h):
    m = re.search(desen, h, re.S)
    return temiz(m.group(1)) if m else ''


def main():
    dizin = {'tr': [], 'ru': [], 'en': []}
    for dosya in sorted(KOK.rglob('index.html')):
        if any(p in dosya.parts for p in ('.git', 'node_modules', 'bakim')):
            continue
        rel = '/' + dosya.relative_to(KOK).as_posix()[:-len('index.html')]
        h = dosya.read_text(encoding='utf-8')
        if 'name="robots" content="noindex' in h:
            continue
        dil = (re.search(r'<html lang="([a-z]+)"', h) or [None, 'tr'])[1]
        if dil not in dizin:
            continue
        baslik = bul(r'<h1[^>]*>(.*?)</h1>', h) or SON_EK.sub('', bul(r'<title>(.*?)</title>', h))
        aciklama = html.unescape(bul(r'<meta name="description" content="([^"]*)"', h))
        tr_rel = re.sub(r'^/(ru|en)/', '/', rel)
        if re.fullmatch(r'/akademi/sozluk/[^/]+/', tr_rel):
            tur, ek = 't', ''
        elif 'class="ders' in h and 'data-ders=' in h:
            tur = 'd'
            ek = bul(r'<div class="ym"><span>(.*?)</span>(.*?)</div>', h)
            m = re.search(r'<div class="ym"><span>(.*?)</span>(.*?)</div>', h, re.S)
            ek = f'{temiz(m.group(1))} · {temiz(m.group(2))}' if m else ''
        else:
            tur, ek = 's', ''
            baslik = SON_EK.sub('', bul(r'<title>(.*?)</title>', h)) or baslik
        dizin[dil].append([baslik, aciklama, rel, tur, ek])
        # Kılavuz bölümleri (herkese açık başlıklar) ayrı sonuç olarak
        if tr_rel == '/kilavuz/':
            for kid, bb in re.findall(r'<section[^>]* id="([a-z0-9-]+)"[^>]*>.*?<h2[^>]*>(.*?)</h2>', h, re.S):
                dizin[dil].append([temiz(bb), baslik, f'{rel}#{kid}', 'b', ''])
    cikti = KOK / 'assets' / 'arama'
    cikti.mkdir(parents=True, exist_ok=True)
    for dil, o in dizin.items():
        sira = {'s': 0, 'd': 1, 'b': 2, 't': 3}
        o.sort(key=lambda x: (sira[x[3]], x[2]))
        (cikti / f'{dil}.json').write_text(json.dumps({'v': 1, 'o': o}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print('arama_dizini:', {k: len(v) for k, v in dizin.items()})


if __name__ == '__main__':
    main()
