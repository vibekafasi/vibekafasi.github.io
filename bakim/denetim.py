#!/usr/bin/env python3
"""Sitenin statik denetimi (CI'da her PR'da çalışır). Tek komut:  python3 bakim/denetim.py
Hata sayılanlar (çıkış kodu 1): kırık iç bağlantı/çapa, hreflang karşılıksız, tekrar eden kimlik, bozuk JSON-LD,
alt metni olmayan görsel, eksik başlık/açıklama/canonical. Diğerleri yalnız uyarıdır."""
import sys, os, re, json, html
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote
from collections import defaultdict, Counter
KOK = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SITE = 'https://vibekafasi.github.io'
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.a=[]; s.ids=Counter(); s.meta={}; s.links=[]; s.title=None; s._t=False; s.ld=[]; s._ld=None; s.imgs=[]; s.lang=None; s.blank=[]; s.h1=0; s.srcs=[]
    def handle_starttag(s, t, at):
        d=dict(at)
        if 'id' in d: s.ids[d['id']]+=1
        if t=='html': s.lang=d.get('lang')
        if t=='a' and 'href' in d:
            s.a.append(d['href'])
            if d.get('target')=='_blank' and 'noopener' not in (d.get('rel') or '') and 'noreferrer' not in (d.get('rel') or ''): s.blank.append(d['href'])
        if t=='a' and 'name' in d: s.ids[d['name']]+=1
        if t=='meta': s.meta[d.get('name') or d.get('property') or d.get('http-equiv') or '?']=d.get('content')
        if t=='link': s.links.append(d)
        if t=='title': s._t=True; s.title=''
        if t=='script' and d.get('type')=='application/ld+json': s._ld=''
        if t in ('img','source','video','script','link','iframe'):
            for k in ('src','href','poster','srcset'):
                if d.get(k) and not (t=='link' and d.get('rel') in ('canonical','alternate')): s.srcs.append(d[k].split()[0] if k!='srcset' else d[k].split(',')[0].split()[0])
        if t=='img': s.imgs.append(d)
        if t=='h1': s.h1+=1
    def handle_endtag(s,t):
        if t=='title': s._t=False
        if t=='script' and s._ld is not None: s.ld.append(s._ld); s._ld=None
    def handle_data(s,d):
        if s._t: s.title+=d
        if s._ld is not None: s._ld+=d
sayfalar={}
for dp,dn,fn in os.walk(KOK):
    if any(x in dp.split(os.sep) for x in ('.git', 'node_modules', 'bakim')): continue
    for f in fn:
        if f.endswith('.html'):
            yol=os.path.join(dp,f); rel='/'+os.path.relpath(yol,KOK).replace(os.sep,'/')
            url=rel[:-10] if rel.endswith('/index.html') else rel
            p=P(); p.feed(open(yol,encoding='utf-8').read()); sayfalar[url]=p
sorun=defaultdict(list)
def hedef_var(u):
    u=unquote(u)
    if u in sayfalar: return True
    if u.endswith('/') and (u+'index.html') in sayfalar: return True
    fs=os.path.join(KOK,u.lstrip('/'))
    return os.path.isfile(fs) or os.path.isfile(os.path.join(fs,'index.html'))
for url,p in sorted(sayfalar.items()):
    taban=SITE+url
    for h in p.a+p.srcs:
        if h.startswith(('mailto:','tel:','javascript:','data:','blob:')): continue
        tam=urljoin(taban,h); pu=urlparse(tam)
        if pu.netloc not in ('vibekafasi.github.io',''): continue
        yol=pu.path or '/'
        if not hedef_var(yol): sorun['kirik_ic_baglanti'].append(f'{url} -> {h}'); continue
        if pu.fragment:
            hp=sayfalar.get(yol) or sayfalar.get(yol.rstrip('/')+'/')
            if hp and pu.fragment not in hp.ids and pu.fragment not in ('top',''): sorun['kirik_capa'].append(f'{url} -> {h}')
    for i,c in p.ids.items():
        if c>1: sorun['tekrar_id'].append(f'{url} #{i} x{c}')
    if url in ('/404.html', '/offline.html'): continue
    if not p.title: sorun['baslik_yok'].append(url)
    elif len(p.title)>70: sorun['baslik_uzun(>70)'].append(f'{url} {len(p.title)}')
    if not p.meta.get('description'): sorun['aciklama_yok'].append(url)
    elif not (50<=len(p.meta['description'])<=170): sorun['aciklama_boyu'].append(f"{url} {len(p.meta['description'])}")
    can=[l for l in p.links if l.get('rel')=='canonical']
    if not can: sorun['canonical_yok'].append(url)
    elif can[0]['href']!=SITE+url: sorun['canonical_farkli'].append(f"{url} {can[0]['href']}")
    alt={l.get('hreflang'):l.get('href') for l in p.links if l.get('rel')=='alternate' and l.get('hreflang')}
    if not alt: sorun['hreflang_yok'].append(url)
    else:
        if 'x-default' not in alt: sorun['hreflang_xdefault_yok'].append(url)
        for dl,h in alt.items():
            if dl=='x-default': continue
            hu=urlparse(h).path; hp=sayfalar.get(hu)
            if not hp: sorun['hreflang_hedef_yok'].append(f'{url} {dl}->{hu}'); continue
            geri={l.get('hreflang'):l.get('href') for l in hp.links if l.get('rel')=='alternate'}
            if geri.get(p.lang)!=SITE+url: sorun['hreflang_karsiliksiz'].append(f'{url} {dl}->{hu}')
    for k in ('og:title','og:description','og:image','og:url','twitter:card'):
        if not p.meta.get(k): sorun[f'{k}_yok'].append(url)
    if p.h1!=1: sorun['h1_sayisi'].append(f'{url} {p.h1}')
    for ld in p.ld:
        try: json.loads(ld)
        except Exception as e: sorun['jsonld_bozuk'].append(f'{url} {e}')
    for im in p.imgs:
        if 'alt' not in im: sorun['img_alt_yok'].append(f"{url} {im.get('src')}")
        if not (im.get('width') and im.get('height')): sorun['img_boyut_yok'].append(f"{url} {im.get('src')}")
    for b in p.blank: sorun['blank_noopener_yok'].append(f'{url} {b}')
    if not any(l.get('rel')=='manifest' for l in p.links): sorun['manifest_yok'].append(url)
    if not any(l.get('rel')=='apple-touch-icon' for l in p.links): sorun['apple_icon_yok'].append(url)
    if 'Content-Security-Policy' not in p.meta: sorun['csp_yok'].append(url)
HATA = {'kirik_ic_baglanti', 'kirik_capa', 'tekrar_id', 'baslik_yok', 'aciklama_yok', 'canonical_yok', 'canonical_farkli',
        'hreflang_yok', 'hreflang_hedef_yok', 'hreflang_karsiliksiz', 'jsonld_bozuk', 'img_alt_yok', 'blank_noopener_yok', 'h1_sayisi'}
print('Sayfa sayısı:', len(sayfalar))
hata = 0
for k,v in sorted(sorun.items()):
    tur = 'HATA' if k in HATA else 'uyarı'
    hata += len(v) if tur == 'HATA' else 0
    print(f'\n## [{tur}] {k}: {len(v)}'); [print('  ',x) for x in v[:int(os.environ.get('N','8'))]]
print(f'\nSonuç: {hata} hata')
sys.exit(1 if hata else 0)
