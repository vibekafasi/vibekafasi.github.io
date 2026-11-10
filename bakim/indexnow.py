#!/usr/bin/env python3
"""Arama motorlarına (Bing, Yandex, Seznam, Naver... IndexNow ortaklığı) "bu sayfalar değişti" haberini yollar.
Google IndexNow kullanmaz; Google için sitemap.xml yeterli (Search Console'a bir kez eklenir).

Kullanım:
  python3 bakim/indexnow.py                 -> son commit'te değişen sayfaları bildirir
  python3 bakim/indexnow.py --hepsi         -> sitemap.xml'deki bütün sayfaları bildirir (ilk kurulumda bir kez)
  python3 bakim/indexnow.py /akademi/git-nedir/ /ru/   -> yalnız verilen adresleri bildirir
  python3 bakim/indexnow.py --fark ESKI YENI          -> iki commit arasında değişen sayfalar (otomatik bakım kullanır)
Anahtar dosyası sitenin kökünde durur (ANAHTAR.txt); gizli değildir, IndexNow böyle ister."""
import json, re, subprocess, sys, pathlib, urllib.request

KOK = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://vibekafasi.github.io'
ANAHTAR = next((p.stem for p in KOK.glob('*.txt') if re.fullmatch(r'[0-9a-f]{32}', p.stem)), None)


def degisenler(once='HEAD~1', sonra='HEAD'):
    if not once or set(once) == {'0'}:
        once = 'HEAD~1'
    try:
        c = subprocess.run(['git', '-C', str(KOK), 'diff', '--name-only', once, sonra, '--', '*.html'], capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    out = []
    for f in c.split():
        if f.endswith('index.html') and (KOK / f).exists():
            out.append('/' + f[:-len('index.html')])
    return out


def main():
    if not ANAHTAR:
        sys.exit('IndexNow anahtar dosyası bulunamadı')
    arg = sys.argv[1:]
    if '--fark' in arg:
        i = arg.index('--fark')
        adresler = [SITE + a for a in degisenler(*arg[i + 1:i + 3])]
    elif '--hepsi' in arg:
        adresler = re.findall(r'<loc>([^<]+)</loc>', (KOK / 'sitemap.xml').read_text())
    else:
        adresler = [SITE + a for a in (arg or degisenler())]
    if not adresler:
        print('indexnow: bildirilecek sayfa yok'); return
    veri = json.dumps({'host': 'vibekafasi.github.io', 'key': ANAHTAR, 'keyLocation': f'{SITE}/{ANAHTAR}.txt', 'urlList': adresler[:10000]}).encode()
    istek = urllib.request.Request('https://api.indexnow.org/indexnow', data=veri, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(istek, timeout=30) as y:
            print('indexnow:', y.status, len(adresler), 'adres bildirildi')
    except Exception as e:
        print('indexnow: gönderilemedi ->', e)


if __name__ == '__main__':
    main()
