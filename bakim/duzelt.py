#!/usr/bin/env python3
"""Vibe Kafası site bakımı: bütün HTML sayfalarının <head> kısmını tek tip ve güncel tutar.

Tek komut (depo kökünden):   python3 bakim/hepsi.py      (bu dosya onun ilk adımıdır)

Ne yapar? (her çalıştırmada aynı sonucu verir; zaten doğru olan sayfaya dokunmaz)
  * Google Fonts bağlantısını kaldırır, yerine <!--vk:bas--> ... <!--/vk:bas--> bloğunu koyar:
    güvenlik politikası (CSP), yazı tipleri (assets/yazi), ikonlar, manifest, vk-ek.css/js,
    sayfa geçiş hızlandırma (speculation rules) ve eksik SEO etiketleri / yapılandırılmış veri.
  * hreflang (TR/RU/EN) ve canonical bağlantılarını gerçek dosyalara göre düzeltir.
  * Menüdeki logoyu küçük dosyaya çevirir, kilavuz ve video görsellerini <picture> (AVIF/WebP) yapar.
  * Boş başlık kimliklerini (id="") doldurur.
Sayfa içeriğine, metinlere, Akademi kilidine, GoatCounter ayarlarına ve assets/sayilar.json'a dokunmaz.
"""
import os, re, json, html, pathlib, sys

KOK = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://vibekafasi.github.io'
DILLER = ('tr', 'ru', 'en')
LOCALE = {'tr': 'tr_TR', 'ru': 'ru_RU', 'en': 'en_US'}
ATLA = {'404.html', 'offline.html'}  # kendi başlıkları elle yazılı sayfalar

CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://gc.zgo.at; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob: https://vibekafasi.goatcounter.com; font-src 'self'; "
       "connect-src 'self' https://vibekafasi.goatcounter.com; media-src 'self' blob:; worker-src 'self'; "
       "manifest-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'")
# KAFA paneli kamera/el hareketi için MediaPipe'ı jsDelivr'dan, modelleri Google Storage'dan yükler.
CSP_KAFA = ("default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' https://cdn.jsdelivr.net https://gc.zgo.at blob:; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; "
            "connect-src 'self' https://cdn.jsdelivr.net https://storage.googleapis.com https://vibekafasi.goatcounter.com data: blob:; "
            "media-src 'self' blob: mediastream:; worker-src 'self' blob:; manifest-src 'self'; frame-src 'none'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'")
SPEKULASYON = json.dumps({"prerender": [{"source": "document", "where": {"and": [
    {"href_matches": "/*"},
    {"not": {"href_matches": "/kafa/*"}}, {"not": {"href_matches": "/ru/kafa/*"}}, {"not": {"href_matches": "/en/kafa/*"}},
    {"not": {"href_matches": "/*.pdf"}}, {"not": {"href_matches": "/*.mp4"}},
    {"not": {"selector_matches": "[target=_blank], [download], [data-vk-yok-on]"}}]}, "eagerness": "moderate"}]},
    separators=(',', ':'))
ON_YUKLE = {  # ilk boyamada gereken yazı tipleri (dil başına)
    'tr': ['inter-latin', 'inter-latin-ext', 'unbounded-latin', 'unbounded-latin-ext'],
    'ru': ['inter-cyrillic', 'inter-latin', 'unbounded-cyrillic', 'unbounded-latin'],
    'en': ['inter-latin', 'unbounded-latin'],
}
OG_RESIM = {'': 'ana', 'kilavuz/': 'kilavuz', 'kafa/': 'kafa'}
KAFA_ACIKLAMA = {
    'tr': 'KAFA ASİSTAN örnek paneli: günün, görevlerin, notların ve hedeflerin tek ekranda. Kamerayla elinle, mikrofonla sesinle yönet.',
    'ru': 'Пример панели KAFA ASİSTAN: твой день, задачи, заметки и цели на одном экране. Управляй руками через камеру и голосом через микрофон.',
    'en': 'KAFA ASİSTAN sample panel: your day, tasks, notes and goals on one screen. Control it with hand gestures via camera and with your voice.',
}
SITE_ADI = {'tr': 'Vibe Kafası', 'ru': 'Vibe Kafası', 'en': 'Vibe Kafası'}
SLOGAN = {'tr': 'Kodla, Üret, Öğren, Eğlen!', 'ru': 'Кодируй, создавай, учись, веселись!', 'en': 'Code, Create, Learn, Have fun!'}
AKADEMI_AD = {'tr': 'Akademi', 'ru': 'Академия', 'en': 'Academy'}
ANA_AD = {'tr': 'Ana sayfa', 'ru': 'Главная', 'en': 'Home'}
SOSYAL = ['https://www.instagram.com/vibe.kafasi/', 'https://www.youtube.com/@vibe.kafasi', 'https://www.tiktok.com/@vibe.kafasi', 'https://t.me/vibekafasi']

TR_HARF = str.maketrans({'ı': 'i', 'İ': 'i', 'ş': 's', 'Ş': 's', 'ğ': 'g', 'Ğ': 'g', 'ç': 'c', 'Ç': 'c', 'ö': 'o', 'Ö': 'o', 'ü': 'u', 'Ü': 'u', 'â': 'a', 'î': 'i', 'û': 'u'})
KIRIL = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя', ['a', 'b', 'v', 'g', 'd', 'e', 'e', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch', 'sh', 'sch', '', 'y', '', 'e', 'yu', 'ya']))


def slug(metin):
    m = re.sub(r'<[^>]+>', '', html.unescape(metin)).translate(TR_HARF).lower()
    m = ''.join(KIRIL.get(c, c) for c in m)
    return re.sub(r'[^a-z0-9]+', '-', m).strip('-')[:60] or 'bolum'


def sayfa_yolu(dosya):
    rel = '/' + dosya.relative_to(KOK).as_posix()
    return rel[:-len('index.html')] if rel.endswith('/index.html') else rel


def tr_yolu(yol):
    return re.sub(r'^/(ru|en)/', '/', yol)


def dil_yolu(yol, dil):
    t = tr_yolu(yol)
    return t if dil == 'tr' else '/' + dil + t


def var_mi(yol):
    p = KOK / yol.lstrip('/')
    return (p / 'index.html').is_file() if yol.endswith('/') else p.is_file()


def meta(h, ad):
    m = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % re.escape(ad), h)
    return html.unescape(m.group(1)) if m else None


def esc(s):
    return html.escape(s, quote=True)


def ld(veri):
    return '<script type="application/ld+json">' + json.dumps(veri, ensure_ascii=False, separators=(',', ':')) + '</script>'


def kirinti(h, yol, dil):
    """Sayfadaki görünür 'yol' kırıntısından BreadcrumbList üretir (zaten yoksa)."""
    if '"BreadcrumbList"' in h:
        return None
    m = re.search(r'<p class="yol">(.*?)</p>', h, re.S)
    ogeler = [(ANA_AD[dil], SITE + ('/' if dil == 'tr' else f'/{dil}/'))]
    if m:
        for href, ad in re.findall(r'<a href="([^"]+)">(.*?)</a>', m.group(1)):
            from urllib.parse import urljoin
            u = urljoin(SITE + yol, href)
            if '#' in u:
                continue
            ogeler.append((html.unescape(re.sub(r'<[^>]+>', '', ad)).strip(), u))
    elif '/akademi/' not in yol:
        return None
    else:
        ogeler.append((AKADEMI_AD[dil], SITE + dil_yolu('/akademi/', dil)))
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    if h1:
        son = html.unescape(re.sub(r'<[^>]+>', ' ', h1.group(1)))
        son = re.sub(r'\s+', ' ', son).strip()
        if SITE + yol not in [u for _, u in ogeler]:
            ogeler.append((son, SITE + yol))
    if len(ogeler) < 2:
        return None
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": a, "item": u} for i, (a, u) in enumerate(ogeler)]}


def sss(h, dil):
    """Kılavuzdaki 'Çalışmıyorsa ne yaparım?' bölümündeki gerçek soru-cevaplardan FAQPage üretir."""
    if '"FAQPage"' in h:
        return None
    sorular = []
    for s, c in re.findall(r'<details[^>]*><summary>(.*?)</summary><div>(.*?)</div></details>', h, re.S):
        temiz = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', x))).strip()
        sorular.append({"@type": "Question", "name": temiz(s), "acceptedAnswer": {"@type": "Answer", "text": temiz(c)}})
    if not sorular:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": dil, "mainEntity": sorular}


def ana_ld(dil, yol):
    url = SITE + yol
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": SITE + "/#org", "name": "Vibe Kafası", "url": SITE + "/",
         "logo": {"@type": "ImageObject", "url": SITE + "/assets/ikon/ikon-512.png", "width": 512, "height": 512},
         "slogan": SLOGAN[dil], "sameAs": SOSYAL},
        {"@type": "WebSite", "@id": url + "#site", "name": "Vibe Kafası", "url": url, "inLanguage": dil,
         "publisher": {"@id": SITE + "/#org"}}]}


def blok(h, yol, dil, dosya):
    kafa = tr_yolu(yol) == '/kafa/'
    s = ['<!--vk:bas: bakim/duzelt.py yönetir, elle değiştirme-->']
    s.append(f'<meta http-equiv="Content-Security-Policy" content="{CSP_KAFA if kafa else CSP}">')
    s.append('<meta name="referrer" content="strict-origin-when-cross-origin">')
    s.append('<meta name="color-scheme" content="dark">')
    yazilar = ['orbitron-latin', 'inter-latin'] if kafa else ON_YUKLE[dil]
    for y in yazilar:
        s.append(f'<link rel="preload" href="/assets/yazi/{y}.woff2" as="font" type="font/woff2" crossorigin>')
    s.append('<link rel="stylesheet" href="/assets/yazi/yazi.css">')
    s.append('<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/assets/ikon/favicon-32.png" type="image/png" sizes="32x32">')
    s.append('<link rel="apple-touch-icon" href="/assets/ikon/apple-touch-icon.png">')
    s.append(f'<link rel="manifest" href="{"/" if dil == "tr" else "/" + dil + "/"}manifest.webmanifest">')
    s.append('<meta name="apple-mobile-web-app-title" content="Vibe Kafası"><meta name="mobile-web-app-capable" content="yes">')
    # --- eksik SEO etiketleri (sayfada zaten varsa eklenmez) ---
    url = SITE + yol
    if not re.search(r'<link rel="canonical"', h):
        s.append(f'<link rel="canonical" href="{url}">')
    if not re.search(r'<link rel="alternate" hreflang=', h):
        for d in DILLER:
            if var_mi(dil_yolu(yol, d)):
                s.append(f'<link rel="alternate" hreflang="{d}" href="{SITE + dil_yolu(yol, d)}">')
        s.append(f'<link rel="alternate" hreflang="x-default" href="{SITE + dil_yolu(yol, "tr")}">')
    baslik = html.unescape(re.search(r'<title>(.*?)</title>', h, re.S).group(1)).strip()
    aciklama = meta(h, 'description')
    if not aciklama and kafa:
        aciklama = KAFA_ACIKLAMA[dil]
        s.append(f'<meta name="description" content="{esc(aciklama)}">')
    og_ac = meta(h, 'og:description') or aciklama or ''
    anah = tr_yolu(yol).lstrip('/')
    eksik = {
        'og:title': baslik, 'og:description': og_ac, 'og:url': url, 'og:type': 'website' if anah in OG_RESIM else 'article',
        'og:site_name': SITE_ADI[dil], 'og:locale': LOCALE[dil],
        'twitter:card': 'summary_large_image', 'twitter:title': meta(h, 'og:title') or baslik, 'twitter:description': og_ac,
    }
    if anah in OG_RESIM:
        eksik['og:image'] = f'{SITE}/assets/og/{OG_RESIM[anah]}-{dil}.jpg'
        eksik['og:image:width'] = '1200'; eksik['og:image:height'] = '630'
        eksik['og:image:alt'] = baslik
        eksik['twitter:image'] = eksik['og:image']
    for k, v in eksik.items():
        if meta(h, k) is None and v:
            nitelik = 'name' if k.startswith('twitter:') else 'property'
            s.append(f'<meta {nitelik}="{k}" content="{esc(v)}">')
    if yol == '/':
        try:
            kodlar = json.loads((KOK / 'bakim' / 'dogrulama.json').read_text(encoding='utf-8'))
        except Exception:
            kodlar = {}
        for ad, kod in kodlar.items():
            if not ad.startswith('_') and kod and re.fullmatch(r'[A-Za-z0-9_\-]{6,120}', kod):
                s.append(f'<meta name="{ad}" content="{kod}">')
    if anah == '' and '"Organization"' not in h:
        s.append(ld(ana_ld(dil, yol)))
    if '/akademi/' in yol:
        k = kirinti(h, yol, dil)
        if k:
            s.append(ld(k))
    if anah == 'kilavuz/':
        f = sss(h, dil)
        if f:
            s.append(ld(f))
    if not kafa:
        s.append('<link rel="stylesheet" href="/assets/vk-ek.css">')
        s.append('<script src="/assets/vk-ek.js" defer></script>')
    s.append(f'<script type="speculationrules">{SPEKULASYON}</script>')
    s.append('<!--/vk:bas-->')
    return '\n'.join(s)


def gorsel_picture(h):
    """Kılavuz ve video kapak görsellerini AVIF/WebP + JPG yedekli <picture> yapar."""
    def kilavuz(m):
        img = m.group(0)
        if 'decoding="async"' in img:
            return img
        ad = re.search(r'src="(?:/kilavuz/)?img/([a-z_]+)\.jpg"', img).group(1)
        boy = BOYUT.get(f'kilavuz/img/{ad}.jpg')
        if not boy:
            return img
        g, y = boy
        yeni = img.replace(' loading="lazy"', '')
        yeni = yeni[:-1] + f' width="{g}" height="{y}" loading="lazy" decoding="async">' if 'width=' not in yeni else yeni
        kaynak = lambda t: ', '.join(f'/kilavuz/img/{ad}-{w}.{t} {w}w' for w in GENISLIK['kilavuz'] if w < g) + f', /kilavuz/img/{ad}.{t} {g}w'
        boyutlar = '(max-width: 760px) calc(100vw - 40px), 720px'
        return (f'<picture><source type="image/avif" srcset="{kaynak("avif")}" sizes="{boyutlar}">'
                f'<source type="image/webp" srcset="{kaynak("webp")}" sizes="{boyutlar}">{yeni}</picture>')
    h = re.sub(r'(?<!</source>)<img src="(?:/kilavuz/)?img/[a-z_]+\.jpg"[^>]*>', kilavuz, h)

    def video(m):
        img = m.group(0)
        ad = re.search(r'/assets/video/([a-z-]+)\.jpg', img).group(1)
        kaynak = lambda t: ', '.join(f'/assets/video/{ad}-{w}.{t} {w}w' for w in GENISLIK['video']) + f', /assets/video/{ad}.{t} 720w'
        boyutlar = '(max-width: 640px) 50vw, 260px'
        return (f'<picture><source type="image/avif" srcset="{kaynak("avif")}" sizes="{boyutlar}">'
                f'<source type="image/webp" srcset="{kaynak("webp")}" sizes="{boyutlar}">{img[:-1]} decoding="async">'
                f'</picture>') if 'decoding=' not in img else img
    h = re.sub(r'(?<!</source>)<img src="/assets/video/[a-z-]+\.jpg"[^>]*>', video, h)
    # ana sayfa büyük logo: AVIF (yarı boyut) + öncelikli yükleme
    h = re.sub(r'<img class="logo" src="(?:/|\.\./)?assets/logo\.webp" alt="" width="512" height="512">',
               '<picture><source type="image/avif" srcset="/assets/logo.avif"><img class="logo" src="/assets/logo.webp" alt="" width="512" height="512" fetchpriority="high" decoding="async"></picture>', h)
    return h


GENISLIK = {'kilavuz': (480, 960), 'video': (360,)}
BOYUT = {}


def bos_kimlik(h):
    """Boş id="" başlıklarına başlık metninden okunur bir kimlik verir (içindekiler ve çapa bağlantıları için)."""
    var = set(re.findall(r' id="([^"]+)"', h))
    def f(m):
        etiket, once, sonra, ic = m.group(1), m.group(2), m.group(3), m.group(4)
        k = taban = slug(ic); i = 2
        while k in var:
            k = f'{taban}-{i}'; i += 1
        var.add(k)
        return f'<{etiket}{once} id="{k}"{sonra}>{ic}</{etiket}>'
    return re.sub(r'<(h[2-4])([^>]*?) id=""([^>]*)>(.*?)</\1>', f, h, flags=re.S)


def tekrar_kimlik(h):
    """Aynı sayfada iki kez kullanılmış başlık kimliklerinden sonrakini benzersiz yapar."""
    gorulen = set()
    def f(m):
        k = m.group(3)
        if k not in gorulen:
            gorulen.add(k); return m.group(0)
        yeni = taban = slug(m.group(5)); i = 2
        while yeni in gorulen or f' id="{yeni}"' in h:
            yeni = f'{taban}-{i}'; i += 1
        gorulen.add(yeni)
        return f'<{m.group(1)}{m.group(2)} id="{yeni}"{m.group(4)}>{m.group(5)}</{m.group(1)}>'
    return re.sub(r'<(h[2-4])([^>]*?) id="([^"]+)"([^>]*)>(.*?)</\1>', f, h, flags=re.S)


def hreflang_duzelt(h, yol):
    def f(m):
        d = m.group(1)
        hedef = SITE + (dil_yolu(yol, 'tr') if d == 'x-default' else dil_yolu(yol, d))
        return f'<link rel="alternate" hreflang="{d}" href="{hedef}">'
    return re.sub(r'<link rel="alternate" hreflang="([a-z-]+)" href="[^"]*">', f, h)


VIDEO_H2 = {'tr': 'Bütün videolar', 'ru': 'Все видео', 'en': 'All videos'}


ARA_ETIKET = {'tr': 'Ara', 'ru': 'Поиск', 'en': 'Search'}
PAYLAS = {'tr': 'Paylaş', 'ru': 'Поделиться', 'en': 'Share'}
ICINDEKILER = {'tr': 'İçindekiler', 'ru': 'Содержание', 'en': 'Contents'}
SVG_ARA = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
SVG_PAYLAS = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>'


def sabit_ogeler(h, yol, dil):
    """Arama düğmesi, ders paylaş düğmesi ve içindekiler kutusunu sayfaya baştan yazar
    (JavaScript sonradan eklerse sayfa kayar; baştan yazılınca kayma olmaz)."""
    if '<div class="vk-sag">' in h and 'class="vk-ara-dug"' not in h:
        h = h.replace('<div class="vk-sag">', f'<div class="vk-sag"><button type="button" class="vk-ara-dug" aria-label="{ARA_ETIKET[dil]} (/)" aria-haspopup="dialog" title="{ARA_ETIKET[dil]}">{SVG_ARA}</button>', 1)
    if 'class="ders' not in h or '<div class="meta">' not in h:
        return h
    m = re.search(r'(<div class="meta">.*?)(</div>)', h, re.S)
    if m and 'vk-paylas' not in m.group(1):
        h = h[:m.end(1)] + f'<button type="button" class="vk-paylas">{SVG_PAYLAS}{PAYLAS[dil]}</button>' + h[m.end(1):]
    if 'class="vk-icindekiler"' in h:
        return h
    bas = h.find('<div class="meta">'); son = h.find('<section class="anlasildi"', bas)
    govde = h[bas:son if son > 0 else len(h)]
    govde = re.sub(r'<section class="kilit".*?</section>', '', govde, flags=re.S)
    bas_lar = [(i, re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip()) for i, t in re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', govde, re.S)]
    if len(bas_lar) < 3:
        return h
    ol = ''.join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in bas_lar)
    kutu = (f'<details class="vk-icindekiler"><summary><span>{ICINDEKILER[dil]}</span><small>{len(bas_lar)}</small></summary>'
            f'<nav aria-label="{ICINDEKILER[dil]}"><ol>{ol}</ol></nav></details>')
    m = re.search(r'<div class="meta">.*?</div>', h, re.S)
    return h[:m.end()] + kutu + h[m.end():]


def kurs_ld(h):
    """Akademi 'Course' verisine Google'ın istediği ücretsiz teklif (offers) bilgisini ekler (yoksa)."""
    def f(m):
        try:
            v = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        if v.get('@type') != 'Course' or 'offers' in v:
            return m.group(0)
        v['offers'] = {"@type": "Offer", "price": 0, "priceCurrency": "USD", "category": "Free", "availability": "https://schema.org/InStock"}
        inst = v.get('hasCourseInstance')
        if isinstance(inst, dict) and 'courseSchedule' not in inst and 'courseWorkload' not in inst:
            inst['courseWorkload'] = 'PT5H'
        return '<script type="application/ld+json">' + json.dumps(v, ensure_ascii=False) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "Course".*?)</script>', f, h, flags=re.S)


def erisim(h, yol, dil):
    """Erişilebilirlik (WCAG) için küçük işaretleme düzeltmeleri; görünüm değişmez."""
    t = tr_yolu(yol)
    if t == '/akademi/':
        h = re.sub(r'<aside class="harita"><h3>(.*?)</h3>', r'<aside class="harita"><h2>\1</h2>', h)
    if t == '/akademi/videolar/' and 'class="vk-gizli"' not in h:
        h = h.replace('<div class="vv-izgara"', f'<h2 class="vk-gizli">{VIDEO_H2[dil]}</h2><div class="vv-izgara"', 1)
    if t == '/kilavuz/':
        h = h.replace('.kk h4{', '.kk h3,.kk h4{').replace('.kk h3,.kk h3,.kk h4{', '.kk h3,.kk h4{')
        h = re.sub(r'(<div class="kk">\s*)<h4>(.*?)</h4>', r'\1<h3>\2</h3>', h, flags=re.S)
        h = h.replace('<tr><th></th>', '<tr><td></td>')
    if t == '/kafa/':
        h = h.replace('<canvas id="bg">', '<canvas id="bg" aria-hidden="true">').replace('<canvas id="holo">', '<canvas id="holo" aria-hidden="true">')
        h = h.replace('<div id="havaImlec"></div>', '<div id="havaImlec" aria-hidden="true"></div>').replace('<div id="sahne">', '<div id="sahne" role="main">')
    return h


def isle(dosya):
    yol = sayfa_yolu(dosya)
    eski = dosya.read_text(encoding='utf-8')
    h = eski
    m = re.search(r'<html lang="([a-z]+)"', h)
    dil = m.group(1) if m and m.group(1) in DILLER else 'tr'
    # 1) eski yazı tipi / ikon bağlantıları
    h = re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"(?: crossorigin)?>', '', h)
    h = re.sub(r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">', '<!--vk:yer-->', h, count=1)
    h = re.sub(r'<link rel="icon" href="(?:\.\./|/)?assets/logo-256\.webp">\n?', '', h)
    # 2) yönetilen blok: varsa yenile, yoksa yazı tipi bağlantısının yerine (o da yoksa </head> önüne) koy
    h = re.sub(r'\n?<!--vk:bas.*?<!--/vk:bas-->\n?', '\n<!--vk:yer-->\n', h, count=1, flags=re.S)
    if '<!--vk:yer-->' not in h:
        h = h.replace('</head>', '<!--vk:yer-->\n</head>', 1)
    h = re.sub(r'\n*<!--vk:yer-->\n*', '\n<!--vk:yer-->\n', h, count=1)
    h = h.replace('<!--vk:yer-->', blok(h.replace('<!--vk:yer-->', ''), yol, dil, dosya), 1)
    # 3) küçük düzeltmeler
    h = hreflang_duzelt(h, yol)
    h = re.sub(r'(<meta property="og:image" content=")https://vibekafasi\.github\.io/assets/og\.jpg(">)',
               lambda m: m.group(1) + f'{SITE}/assets/og/{OG_RESIM.get(tr_yolu(yol).lstrip("/"), "ana")}-{dil}.jpg' + m.group(2), h)
    h = re.sub(r'<a class="vk-marka" href="([^"]*)" aria-label="[^"]*">', r'<a class="vk-marka" href="\1">', h)
    h = h.replace('<img src="/assets/logo-256.webp" alt="" width="40" height="40">', '<img src="/assets/ikon/logo-80.webp" alt="" width="40" height="40">')
    h = h.replace('async src="//gc.zgo.at/count.js"', 'async src="https://gc.zgo.at/count.js"')
    h = bos_kimlik(h)
    h = tekrar_kimlik(h)
    h = gorsel_picture(h)
    h = erisim(h, yol, dil)
    h = kurs_ld(h)
    h = sabit_ogeler(h, yol, dil)
    if h != eski:
        dosya.write_text(h, encoding='utf-8')
        return True
    return False


def main():
    from PIL import Image
    for p in (KOK / 'kilavuz' / 'img').glob('*.jpg'):
        if re.fullmatch(r'[a-z_]+\.jpg', p.name):
            BOYUT[f'kilavuz/img/{p.name}'] = Image.open(p).size
    degisen = 0
    for dosya in sorted(KOK.rglob('*.html')):
        if any(x in dosya.parts for x in ('.git', 'node_modules', 'bakim')) or dosya.name in ATLA:
            continue
        degisen += isle(dosya)
    print(f'duzelt: {degisen} sayfa güncellendi')


if __name__ == '__main__':
    main()
