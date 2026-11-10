/* Vibe Kafası service worker: siteyi hızlandırır ve Akademi derslerini internetsiz okunur yapar.
   Kural özeti (güvenli güncelleme için):
   - Sayfalar (HTML), CSS, JS, JSON: önce internet (her zaman en yeni sürüm), internet yoksa kayıtlı kopya.
   - Yazı tipleri ve ikonlar: önce kayıtlı kopya (değişmezler). Diğer görseller: kayıtlı kopyayı göster, arkada tazele.
   - assets/sayilar.json: önce internet; internetsizken en fazla 1 günlük kopya kullanılır.
   - Videolar ve başka sitelerden gelenler (GoatCounter, Telegram vb.): hiç dokunulmaz.
   SURUM değişince eski kayıtlar silinir. */
'use strict';
const SURUM = 'vk-2026-11-11a';
const KABUK = SURUM + '-kabuk', SAYFA = 'vk-sayfa', VARLIK = 'vk-varlik';
const GUN = 24 * 60 * 60 * 1000;
const KABUK_DOSYALAR = [
  '/offline.html', '/favicon.ico',
  '/assets/vk-nav.css', '/assets/vk-nav.js', '/assets/vk-ek.css', '/assets/vk-ek.js',
  '/assets/yazi/yazi.css', '/assets/yazi/inter-latin.woff2', '/assets/yazi/inter-latin-ext.woff2', '/assets/yazi/inter-cyrillic.woff2',
  '/assets/yazi/unbounded-latin.woff2', '/assets/yazi/unbounded-latin-ext.woff2', '/assets/yazi/unbounded-cyrillic.woff2',
  '/assets/yazi/jetbrains-mono-latin.woff2', '/assets/ikon/logo-80.webp', '/assets/ikon/ikon-192.png',
  '/akademi/akademi.css', '/akademi/akademi.js', '/ru/akademi/akademi.css', '/ru/akademi/akademi.js', '/en/akademi/akademi.css', '/en/akademi/akademi.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(KABUK).then((c) => Promise.all(KABUK_DOSYALAR.map((u) => c.add(new Request(u, { cache: 'reload' })).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const adlar = await caches.keys();
    await Promise.all(adlar.filter((a) => a.endsWith('-kabuk') && a !== KABUK).map((a) => caches.delete(a)));
    if (self.registration.navigationPreload) await self.registration.navigationPreload.enable().catch(() => {});
    await self.clients.claim();
  })());
});

function anahtar(istek) {
  const u = new URL(istek.url);
  u.search = ''; u.hash = '';
  return u.href;
}

async function kaydet(onbellek, istek, yanit) {
  if (!yanit || !yanit.ok || yanit.type !== 'basic' || yanit.status !== 200) return;
  const kopya = yanit.clone();
  const basliklar = new Headers(kopya.headers);
  basliklar.set('sw-zaman', String(Date.now()));
  const govde = await kopya.blob();
  const c = await caches.open(onbellek);
  await c.put(anahtar(istek), new Response(govde, { status: 200, statusText: 'OK', headers: basliklar }));
}

async function bul(istek) {
  const k = anahtar(istek);
  return (await caches.match(k, { ignoreVary: true })) || (await caches.match(istek, { ignoreVary: true }));
}

async function onceInternet(e, onbellek, enFazlaYas) {
  try {
    const on = e.preloadResponse ? await e.preloadResponse : null;
    const yanit = on || await fetch(e.request);
    if (yanit.ok) e.waitUntil(kaydet(onbellek, e.request, yanit.clone()));
    return yanit;
  } catch (hata) {
    const eski = await bul(e.request);
    if (eski) {
      const zaman = +(eski.headers.get('sw-zaman') || 0);
      if (!enFazlaYas || (zaman && Date.now() - zaman < enFazlaYas)) return eski;
    }
    if (e.request.mode === 'navigate') {
      const yedek = await caches.match('/offline.html');
      if (yedek) return yedek;
    }
    throw hata;
  }
}

async function onceKayit(e) {
  const eski = await bul(e.request);
  if (eski) return eski;
  const yanit = await fetch(e.request);
  e.waitUntil(kaydet(VARLIK, e.request, yanit.clone()));
  return yanit;
}

async function eskiyiGosterTazele(e) {
  const eski = await bul(e.request);
  const taze = fetch(e.request).then((y) => { e.waitUntil(kaydet(VARLIK, e.request, y.clone())); return y; }).catch(() => eski);
  return eski || taze;
}

self.addEventListener('fetch', (e) => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== self.location.origin) return;              // GoatCounter, Telegram, CDN: dokunma
  if (r.headers.has('range') || /\.(mp4|webm|pdf)$/i.test(u.pathname)) return; // video ve büyük dosya
  if (u.pathname === '/sw.js') return;
  if (u.pathname === '/assets/sayilar.json') { e.respondWith(onceInternet(e, VARLIK, GUN)); return; }
  if (r.mode === 'navigate' || /\.(html|css|js|json|webmanifest)$/i.test(u.pathname) || u.pathname.endsWith('/')) {
    e.respondWith(onceInternet(e, r.mode === 'navigate' ? SAYFA : VARLIK, 0)); return;
  }
  if (/^\/assets\/(yazi|ikon)\//.test(u.pathname) || /\.(woff2|ico)$/i.test(u.pathname)) { e.respondWith(onceKayit(e)); return; }
  if (/\.(avif|webp|png|jpe?g|svg|gif)$/i.test(u.pathname)) { e.respondWith(eskiyiGosterTazele(e)); }
});

/* Akademi sayfasındaki "çevrimdışı için indir" düğmesi: verilen adresleri sırayla kaydeder ve ilerlemeyi bildirir. */
self.addEventListener('message', (e) => {
  const m = e.data || {};
  if (m.tur !== 'indir' || !Array.isArray(m.adresler)) return;
  const port = e.ports && e.ports[0];
  const adresler = m.adresler.filter((a) => typeof a === 'string' && a.startsWith('/') && !a.startsWith('//')).slice(0, 600);
  e.waitUntil((async () => {
    let bitti = 0, hata = 0;
    const kuyruk = adresler.slice();
    async function isci() {
      while (kuyruk.length) {
        const a = kuyruk.shift();
        try {
          const y = await fetch(a, { cache: 'no-cache' });
          if (!y.ok) throw new Error(String(y.status));
          await kaydet(/\.json$/.test(a) ? VARLIK : SAYFA, new Request(new URL(a, self.location.origin).href), y);
        } catch (x) { hata++; }
        bitti++;
        if (port) port.postMessage({ tur: 'ilerleme', bitti, toplam: adresler.length });
      }
    }
    await Promise.all([isci(), isci(), isci(), isci()]);
    if (port) port.postMessage({ tur: 'bitti', hata });
  })());
});
