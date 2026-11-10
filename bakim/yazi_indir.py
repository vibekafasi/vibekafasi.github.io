#!/usr/bin/env python3
"""Yazı tiplerini Google Fonts'tan indirip assets/yazi/ altına koyar (kendi sunucumuzdan yüklenir: daha hızlı, gizlilik dostu).
Tek komut:  python3 bakim/yazi_indir.py      (gerekli: curl ve fonttools -> pip install fonttools brotli)
latin-ext dosyaları Türkçe ve yakın harflere (U+0100-017F vb.) inceltilir; Rusça için cyrillic alt kümesi tutulur."""
import re, subprocess, pathlib, tempfile
KOK = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'yazi'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
URL = 'https://fonts.googleapis.com/css2?family=Unbounded:wght@500..900&family=Inter:wght@400..800&family=JetBrains+Mono:wght@500&family=Orbitron:wght@500..900&display=swap'
EXT = 'U+0100-017F, U+0218-021B, U+20A0-20C0'
KOK.mkdir(parents=True, exist_ok=True)
css = subprocess.run(['curl', '-sS', '-A', UA, URL], capture_output=True, text=True, check=True).stdout
out = ["/* Vibe Kafası: kendi sunucumuzdaki yazı tipleri (Google Fonts, SIL Open Font License). Yeniden üretmek: python3 bakim/yazi_indir.py */"]
for alt, b in re.findall(r'/\* ([a-z-]+) \*/\s*(@font-face \{.*?\})', css, re.S):
    if alt not in ('latin', 'latin-ext', 'cyrillic'):
        continue
    aile = re.search(r"font-family: '([^']+)'", b).group(1)
    ad = f"{aile.lower().replace(' ', '-')}-{alt}.woff2"
    hedef = KOK / ad
    subprocess.run(['curl', '-sS', '-o', str(hedef), re.search(r'url\((\S+?)\)', b).group(1)], check=True)
    ur = re.search(r'unicode-range: ([^;]+);', b).group(1)
    if alt == 'latin-ext':
        with tempfile.TemporaryDirectory() as t:
            gecici = pathlib.Path(t) / ad
            subprocess.run(['pyftsubset', str(hedef), '--unicodes=' + EXT.replace(' ', ''), '--flavor=woff2',
                            '--layout-features=*', '--output-file=' + str(gecici)], check=True)
            hedef.write_bytes(gecici.read_bytes())
        ur = EXT
    w = re.search(r'font-weight: ([^;]+);', b).group(1)
    out.append(f"@font-face{{font-family:'{aile}';font-style:normal;font-weight:{w};font-display:swap;src:url({ad}) format('woff2');unicode-range:{ur}}}")
(KOK / 'yazi.css').write_text('\n'.join(out) + '\n')
print('tamam:', len(out) - 1, 'yazı tipi dosyası')
