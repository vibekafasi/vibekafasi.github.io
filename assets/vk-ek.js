/* Vibe Kafası: ek özellikler (hepsi "olursa güzel" katmanı; desteklemeyen tarayıcıda sessizce atlanır).
   Site araması, dil önerisi, ders içindekiler + paylaş + yukarı çık, çevrimdışı okuma (service worker),
   araç kartlarında paylaş, erişilebilirlik ekleri. Hiçbir çerez yok; yalnızca tarayıcı hafızası (localStorage). */
(function () {
  'use strict';
  if (window.__vkEk) return; window.__vkEk = 1;
  var d = document, kok = d.documentElement;
  var DIL = (kok.lang || 'tr').slice(0, 2); if (DIL !== 'ru' && DIL !== 'en') DIL = 'tr';
  var ON = DIL === 'tr' ? '' : '/' + DIL;
  var T = {
    tr: { ara: 'Ara', araYer: 'Ders, terim ya da sayfa ara…', araBos: 'Sonuç yok. Başka bir kelime dene.', araIpucu: 'Yazmaya başla: “git”, “api”, “deploy”…', kapat: 'Kapat', ders: 'Ders', terim: 'Terim', sayfa: 'Sayfa', bolum: 'Bölüm', atla: 'İçeriğe geç', icindekiler: 'İçindekiler', paylas: 'Paylaş', kopyalandi: 'Bağlantı kopyalandı', yukari: 'Yukarı çık', dilMetin: 'Bu sayfanın Türkçesi var.', dilDug: 'Türkçe aç', cevrim: 'Çevrimdışı okumak için dersleri indir', cevrimNot: 'İnternet yokken de dersleri açabilirsin. Yaklaşık 2 MB.', cevrimIn: 'İndiriliyor…', cevrimTamam: 'Hazır! Dersler bu cihazda çevrimdışı açılır.', cevrimHata: 'İndirme yarıda kaldı. Bağlantını kontrol edip tekrar dene.', sonuc: 'sonuç', aracPaylas: 'Bu aracı paylaş', kisayol: 'Kısayol: /' },
    ru: { ara: 'Поиск', araYer: 'Урок, термин или страница…', araBos: 'Ничего не найдено. Попробуй другое слово.', araIpucu: 'Начни печатать: «git», «api», «deploy»…', kapat: 'Закрыть', ders: 'Урок', terim: 'Термин', sayfa: 'Страница', bolum: 'Раздел', atla: 'Перейти к содержимому', icindekiler: 'Содержание', paylas: 'Поделиться', kopyalandi: 'Ссылка скопирована', yukari: 'Наверх', dilMetin: 'Эта страница есть на русском языке.', dilDug: 'Открыть на русском', cevrim: 'Скачать уроки для чтения без интернета', cevrimNot: 'Уроки откроются даже без интернета. Около 2 МБ.', cevrimIn: 'Скачиваем…', cevrimTamam: 'Готово! Уроки откроются на этом устройстве без интернета.', cevrimHata: 'Загрузка прервалась. Проверь интернет и попробуй ещё раз.', sonuc: 'результатов', aracPaylas: 'Поделиться инструментом', kisayol: 'Горячая клавиша: /' },
    en: { ara: 'Search', araYer: 'Search lessons, terms or pages…', araBos: 'No results. Try another word.', araIpucu: 'Start typing: “git”, “api”, “deploy”…', kapat: 'Close', ders: 'Lesson', terim: 'Term', sayfa: 'Page', bolum: 'Section', atla: 'Skip to content', icindekiler: 'Contents', paylas: 'Share', kopyalandi: 'Link copied', yukari: 'Back to top', dilMetin: 'This page is available in English.', dilDug: 'Open in English', cevrim: 'Download lessons for offline reading', cevrimNot: 'Open the lessons even without internet. About 2 MB.', cevrimIn: 'Downloading…', cevrimTamam: 'Done! Lessons now open offline on this device.', cevrimHata: 'Download stopped. Check your connection and try again.', sonuc: 'results', aracPaylas: 'Share this tool', kisayol: 'Shortcut: /' }
  };
  var t = T[DIL];
  var azHareket = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function hafiza(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } }
  function el(etiket, ozellik, cocuk) {
    var e = d.createElement(etiket);
    if (ozellik) Object.keys(ozellik).forEach(function (k) { if (k === 'text') e.textContent = ozellik[k]; else if (k === 'html') e.innerHTML = ozellik[k]; else e.setAttribute(k, ozellik[k]); });
    (cocuk || []).forEach(function (c) { if (c) e.appendChild(c); });
    return e;
  }
  function ikon(yol) { return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + yol + '</svg>'; }
  var IK = {
    ara: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    paylas: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
    yukari: '<path d="m6 15 6-6 6 6"/>',
    kapat: '<path d="M18 6 6 18M6 6l12 12"/>',
    indir: '<path d="M12 3v12m0 0-5-5m5 5 5-5M5 21h14"/>'
  };
  function guvenli(f) { try { f(); } catch (e) { if (window.console) console.warn('vk-ek:', e); } }

  /* ---------- kısa bildirim ---------- */
  var tost;
  function bildir(m) {
    if (!tost) { tost = el('div', { class: 'vk-tost', role: 'status', 'aria-live': 'polite' }); d.body.appendChild(tost); }
    tost.textContent = m; tost.classList.add('acik');
    clearTimeout(bildir.z); bildir.z = setTimeout(function () { tost.classList.remove('acik'); }, 2200);
  }

  /* ---------- paylaş (Web Share API, yoksa bağlantıyı kopyala) ---------- */
  function paylas(veri) {
    if (navigator.share) { navigator.share(veri).catch(function () {}); return; }
    var metin = veri.url;
    function tamam() { bildir(t.kopyalandi); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(metin).then(tamam, function () { window.prompt(t.paylas, metin); });
    else window.prompt(t.paylas, metin);
  }
  function paylasDugmesi(sinif, etiket, veri) {
    var b = el('button', { type: 'button', class: sinif, 'aria-label': etiket, html: ikon(IK.paylas) });
    if (etiket === t.paylas) b.appendChild(d.createTextNode(t.paylas));
    b.addEventListener('click', function () { paylas(typeof veri === 'function' ? veri() : veri); });
    return b;
  }

  /* ---------- içeriğe geç bağlantısı ---------- */
  guvenli(function () {
    var ana = d.querySelector('main') || d.getElementById('sahne');
    if (!ana || d.querySelector('.vk-atla')) return;
    if (!ana.id) ana.id = 'icerik';
    if (!ana.hasAttribute('tabindex')) ana.setAttribute('tabindex', '-1');
    var a = el('a', { class: 'vk-atla', href: '#' + ana.id, text: t.atla });
    a.addEventListener('click', function (e) { e.preventDefault(); ana.focus({ preventScroll: false }); ana.scrollIntoView(); });
    d.body.insertBefore(a, d.body.firstChild);
  });

  /* ---------- dil seçimini hatırla + nazik dil önerisi ---------- */
  guvenli(function () {
    d.querySelectorAll('.vk-dil a[hreflang]').forEach(function (a) {
      a.addEventListener('click', function () { hafiza('vk-dil', a.getAttribute('hreflang')); });
    });
    if (hafiza('vk-dil-oneri') === 'kapali') return;
    var secim = hafiza('vk-dil');
    if (secim === DIL) return;
    var tercih = null, diller = navigator.languages || [navigator.language || ''];
    for (var i = 0; i < diller.length; i++) { var k = (diller[i] || '').slice(0, 2).toLowerCase(); if (k === 'tr' || k === 'ru' || k === 'en') { tercih = k; break; } }
    if (secim) tercih = secim;
    if (!tercih || tercih === DIL) return;
    var hedef = d.querySelector('link[rel="alternate"][hreflang="' + tercih + '"]');
    if (!hedef) return;
    var href = hedef.getAttribute('href').replace(/^https:\/\/vibekafasi\.github\.io/, '');
    var tt = T[tercih];
    var bant = el('div', { class: 'vk-dil-oneri', role: 'region', 'aria-label': tt.dilMetin, lang: tercih });
    var git = el('a', { class: 'vk-do-git', href: href, hreflang: tercih, text: tt.dilDug });
    git.addEventListener('click', function () { hafiza('vk-dil', tercih); });
    var kapat = el('button', { type: 'button', class: 'vk-do-kapat', 'aria-label': tt.kapat, html: ikon(IK.kapat) });
    kapat.addEventListener('click', function () { hafiza('vk-dil-oneri', 'kapali'); bant.remove(); });
    bant.appendChild(el('span', { text: tt.dilMetin })); bant.appendChild(git); bant.appendChild(kapat);
    d.body.appendChild(bant);
    requestAnimationFrame(function () { bant.classList.add('acik'); });
  });

  /* ---------- site araması ---------- */
  guvenli(function () {
    var sag = d.querySelector('[data-vk-nav] .vk-sag');
    if (!sag || !('fetch' in window)) return;
    var dug = sag.querySelector('.vk-ara-dug');
    if (!dug) { dug = el('button', { type: 'button', class: 'vk-ara-dug', 'aria-label': t.ara + ' (/)', 'aria-haspopup': 'dialog', html: ikon(IK.ara) }); sag.insertBefore(dug, sag.firstChild); }
    dug.title = t.ara + ' — ' + t.kisayol;
    var dlg, giris, liste, durum, veri = null, sonuclar = [], aktif = -1;
    function norm(s) {
      return (s || '').toLocaleLowerCase(DIL === 'tr' ? 'tr' : DIL).replace(/ı/g, 'i').replace(/ё/g, 'е').normalize('NFD').replace(/[̀-ͯ]/g, '');
    }
    function yukle() {
      if (veri) return Promise.resolve(veri);
      return fetch('/assets/arama/' + DIL + '.json').then(function (r) { return r.json(); }).then(function (j) {
        veri = j.o.map(function (x) { return { b: x[0], a: x[1], u: x[2], t: x[3], e: x[4] || '', nb: norm(x[0]), na: norm(x[1] + ' ' + (x[4] || '')) }; });
        return veri;
      });
    }
    var TUR = { d: t.ders, t: t.terim, s: t.sayfa, b: t.bolum };
    function ara(q) {
      var n = norm(q).trim(); if (!n) return [];
      var parca = n.split(/\s+/);
      var s = [];
      veri.forEach(function (x) {
        var puan = 0;
        for (var i = 0; i < parca.length; i++) {
          var p = parca[i], ib = x.nb.indexOf(p), ia = x.na.indexOf(p);
          if (ib < 0 && ia < 0) return;
          if (ib === 0) puan += 40; else if (ib > 0) puan += (/[\s(«“"-]/.test(x.nb.charAt(ib - 1)) ? 25 : 12); else puan += 4;
        }
        if (x.nb === n) puan += 100; else if (x.nb.indexOf(n) === 0) puan += 30;
        if (x.t === 'd') puan += 3; if (x.t === 's') puan += 2;
        s.push([puan, x]);
      });
      s.sort(function (a, b) { return b[0] - a[0] || a[1].b.length - b[1].b.length; });
      return s.slice(0, 30).map(function (y) { return y[1]; });
    }
    function isaretle(metin, q) {
      var kutu = d.createDocumentFragment(), n = norm(metin), parcalar = norm(q).trim().split(/\s+/).filter(Boolean), isa = new Array(metin.length + 1).join('0').split('');
      parcalar.forEach(function (p) { var i = n.indexOf(p); if (i >= 0 && n.length === metin.length) for (var k = i; k < i + p.length; k++) isa[k] = '1'; });
      var bas = 0;
      for (var i = 1; i <= metin.length; i++) {
        if (i === metin.length || isa[i] !== isa[bas]) {
          var parca = metin.slice(bas, i);
          kutu.appendChild(isa[bas] === '1' ? el('mark', { text: parca }) : d.createTextNode(parca));
          bas = i;
        }
      }
      return kutu;
    }
    function ciz(q) {
      liste.innerHTML = ''; aktif = -1;
      if (!q.trim()) { durum.textContent = t.araIpucu; return; }
      sonuclar = ara(q);
      durum.textContent = sonuclar.length ? sonuclar.length + ' ' + t.sonuc : t.araBos;
      sonuclar.forEach(function (x, i) {
        var a = el('a', { href: x.u, id: 'vk-ara-' + i, role: 'option', 'aria-selected': 'false' });
        var bas = el('span', { class: 'vk-as-b' }); bas.appendChild(isaretle(x.b, q));
        a.appendChild(el('span', { class: 'vk-as-t vk-as-' + x.t, text: TUR[x.t] || '' }));
        a.appendChild(bas);
        if (x.a) a.appendChild(el('span', { class: 'vk-as-a', text: x.a }));
        if (x.e) a.appendChild(el('span', { class: 'vk-as-e', text: x.e }));
        a.addEventListener('mousemove', function () { sec(i, true); });
        liste.appendChild(el('li', { role: 'presentation' }, [a]));
      });
      if (sonuclar.length) sec(0, true);
    }
    function sec(i, sessiz) {
      var ogeler = liste.querySelectorAll('a');
      if (!ogeler.length) return;
      aktif = (i + ogeler.length) % ogeler.length;
      ogeler.forEach(function (a, k) { a.setAttribute('aria-selected', k === aktif ? 'true' : 'false'); });
      giris.setAttribute('aria-activedescendant', 'vk-ara-' + aktif);
      if (!sessiz) ogeler[aktif].scrollIntoView({ block: 'nearest' });
    }
    function kur() {
      if (dlg) return;
      dlg = el('dialog', { class: 'vk-ara', 'aria-label': t.ara });
      giris = el('input', { type: 'search', placeholder: t.araYer, 'aria-label': t.araYer, autocomplete: 'off', spellcheck: 'false', role: 'combobox', 'aria-expanded': 'true', 'aria-controls': 'vk-ara-liste', 'aria-autocomplete': 'list', enterkeyhint: 'search' });
      var kapat = el('button', { type: 'button', class: 'vk-ara-kapat', 'aria-label': t.kapat, html: ikon(IK.kapat) });
      liste = el('ul', { id: 'vk-ara-liste', role: 'listbox', 'aria-label': t.ara });
      durum = el('p', { class: 'vk-ara-durum', role: 'status', 'aria-live': 'polite', text: t.araIpucu });
      var ust = el('div', { class: 'vk-ara-ust', html: ikon(IK.ara) }, [giris, kapat]);
      dlg.appendChild(el('div', { class: 'vk-ara-kutu' }, [ust, durum, liste]));
      d.body.appendChild(dlg);
      kapat.addEventListener('click', function () { dlg.close(); });
      dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
      dlg.addEventListener('close', function () { kok.classList.remove('vk-ara-acik'); dug.focus(); });
      var bekle;
      giris.addEventListener('input', function () { clearTimeout(bekle); bekle = setTimeout(function () { yukle().then(function () { ciz(giris.value); }); }, 60); });
      giris.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); sec(aktif + 1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); sec(aktif - 1); }
        else if (e.key === 'Enter') { var a = liste.querySelectorAll('a')[aktif]; if (a) { e.preventDefault(); location.href = a.href; } }
        else if (e.key === 'Escape') { e.preventDefault(); dlg.close(); }
      });
    }
    function ac() {
      kur();
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
      kok.classList.add('vk-ara-acik');
      giris.focus(); giris.select();
      yukle().then(function () { if (giris.value) ciz(giris.value); }).catch(function () { durum.textContent = t.araBos; });
    }
    dug.addEventListener('click', ac);
    d.addEventListener('keydown', function (e) {
      var yaziyor = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || '') || (e.target && e.target.isContentEditable);
      if ((e.key === '/' && !yaziyor && !e.ctrlKey && !e.metaKey && !e.altKey) || ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K'))) {
        if (dlg && dlg.open) return; e.preventDefault(); ac();
      }
    });
    var q = new URLSearchParams(location.search).get('ara');
    if (q) { ac(); giris.value = q; yukle().then(function () { ciz(q); }); }
  });

  /* ---------- ders sayfası: içindekiler, paylaş, kaydırılabilir tablolar ---------- */
  function basliklar(icerik) {
    return Array.prototype.filter.call(icerik.querySelectorAll('h2'), function (h) {
      return !h.closest('.kilit, .anlasildi, .akilda, .test, .kaynak, [hidden], .vk-icindekiler') && h.textContent.trim();
    });
  }
  function kimlikVer(h, i) {
    if (h.id) return h.id;
    var s = h.textContent.toLocaleLowerCase(DIL).replace(/ı/g, 'i').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9Ѐ-ӿ]+/g, '-').replace(/^-|-$/g, '') || 'bolum-' + (i + 1);
    while (d.getElementById(s)) s += '-' + (i + 1);
    h.id = s; return s;
  }
  function icindekilerKur(icerik, yeniden) {
    var eski = icerik.querySelector('.vk-icindekiler');
    var hs = basliklar(icerik); if (hs.length < 3) return;
    var meta = icerik.querySelector('.meta'); if (!meta) return;
    var det = eski, ol;
    if (!eski || yeniden) {
      /* sayfada hazır yoksa (ör. kilidi yeni açılan ders) burada kurulur */
      ol = el('ol');
      hs.forEach(function (h, i) { ol.appendChild(el('li', null, [el('a', { href: '#' + kimlikVer(h, i), text: h.textContent.trim() })])); });
      det = el('details', { class: 'vk-icindekiler' }, [el('summary', { html: '<span>' + t.icindekiler + '</span><small>' + hs.length + '</small>' }), el('nav', { 'aria-label': t.icindekiler }, [ol])]);
      if (eski) eski.replaceWith(det); else meta.parentNode.insertBefore(det, meta.nextSibling);
    } else ol = eski.querySelector('ol');
    if ('IntersectionObserver' in window) {
      var linkler = ol.querySelectorAll('a'), gor = {};
      var io = new IntersectionObserver(function (g) {
        g.forEach(function (x) { gor[x.target.id] = x.isIntersecting; });
        var ilk = null; hs.forEach(function (h) { if (!ilk && gor[h.id]) ilk = h.id; });
        if (ilk) linkler.forEach(function (a) { a.classList.toggle('aktif', a.getAttribute('href') === '#' + ilk); });
      }, { rootMargin: '-80px 0px -55% 0px' });
      hs.forEach(function (h) { io.observe(h); });
    }
  }
  guvenli(function () {
    var icerik = d.querySelector('main.ders article.icerik');
    if (!icerik) return;
    var meta = icerik.querySelector('.meta');
    var h1 = icerik.querySelector('h1');
    var dersVeri = function () { return { title: (h1 ? h1.textContent.trim() : d.title), text: (icerik.querySelector('.ozet') || {}).textContent || '', url: location.origin + location.pathname }; };
    var hazir = meta && meta.querySelector('.vk-paylas');
    if (hazir) hazir.addEventListener('click', function () { paylas(dersVeri()); });
    else if (meta) meta.appendChild(paylasDugmesi('vk-paylas', t.paylas, dersVeri));
    icindekilerKur(icerik);
    var kilitli = d.getElementById('kilitIcerik');
    if (kilitli && 'MutationObserver' in window) new MutationObserver(function () { if (!kilitli.hidden) { icindekilerKur(icerik, true); tablolar(); } }).observe(kilitli, { attributes: true, attributeFilter: ['hidden'] });
  });
  function tablolar() {
    d.querySelectorAll('.tablo, .sar').forEach(function (x) {
      if (x.scrollWidth > x.clientWidth + 2 && !x.hasAttribute('tabindex')) { x.setAttribute('tabindex', '0'); if (!x.getAttribute('role')) x.setAttribute('role', 'region'); if (!x.getAttribute('aria-label')) { var c = x.querySelector('caption, th'); x.setAttribute('aria-label', c ? c.textContent.trim() : t.icindekiler); } }
    });
  }
  guvenli(tablolar);

  /* ---------- ana sayfa araç kartları: paylaş ---------- */
  guvenli(function () {
    d.querySelectorAll('#araclar .kart .alt-sira').forEach(function (s) {
      var kart = s.closest('.kart'), h3 = kart && kart.querySelector('h3');
      if (!h3 || s.querySelector('.vk-kart-paylas')) return;
      var ad = h3.textContent.trim();
      var b = paylasDugmesi('vk-kart-paylas dug cam kucuk', t.aracPaylas + ': ' + ad, function () { return { title: ad + ' — Vibe Kafası', text: (kart.querySelector('p') || {}).textContent || '', url: location.origin + ON + '/#araclar' }; });
      b.setAttribute('title', t.aracPaylas);
      s.appendChild(b);
    });
  });

  /* ---------- yukarı çık ---------- */
  guvenli(function () {
    if (!d.querySelector('main')) return;
    var b = el('button', { type: 'button', class: 'vk-yukari', 'aria-label': t.yukari, title: t.yukari, html: ikon(IK.yukari) });
    b.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: azHareket ? 'auto' : 'smooth' });
      var ilk = d.querySelector('.vk-atla'); if (ilk) ilk.focus({ preventScroll: true });
    });
    d.body.appendChild(b);
    var acik = false, bekle = false;
    function kontrol() { bekle = false; var a = scrollY > innerHeight * 2 && d.body.scrollHeight > innerHeight * 3; if (a !== acik) { acik = a; b.classList.toggle('acik', a); } }
    addEventListener('scroll', function () { if (!bekle) { bekle = true; requestAnimationFrame(kontrol); } }, { passive: true });
  });

  /* ---------- sessiz döngü videoları yalnızca ekrandayken oynasın (pil ve işlemci tasarrufu) ---------- */
  guvenli(function () {
    if (azHareket || (navigator.connection && navigator.connection.saveData) || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (g) {
      g.forEach(function (x) {
        var v = x.target;
        if (x.isIntersecting) { if (v.paused && v.dataset.vkDurdu) { delete v.dataset.vkDurdu; var p = v.play(); if (p && p.catch) p.catch(function () {}); } }
        else if (!v.paused) { v.dataset.vkDurdu = '1'; v.pause(); }
      });
    }, { rootMargin: '120px 0px' });
    d.querySelectorAll('video[autoplay][muted][loop]').forEach(function (v) { io.observe(v); });
  });

  /* ---------- hareketi azalt / veri tasarrufu: kendiliğinden oynayan videoları durdur ---------- */
  guvenli(function () {
    var tasarruf = navigator.connection && navigator.connection.saveData;
    if (!azHareket && !tasarruf) return;
    d.querySelectorAll('video[autoplay]').forEach(function (v) {
      v.removeAttribute('autoplay'); v.autoplay = false; v.preload = 'none';
      try { v.pause(); } catch (e) {}
      if (!v.hasAttribute('controls') && !v.closest('a, button')) v.setAttribute('controls', '');
    });
  });

  /* ---------- sayfa geçişlerini hızlandır (Chrome: speculation rules; diğerleri: yok sayar) ---------- */
  guvenli(function () {
    if (d.querySelector('script[type="speculationrules"]')) return;
    if (!(HTMLScriptElement.supports && HTMLScriptElement.supports('speculationrules'))) return;
    var s = el('script', { type: 'speculationrules' });
    s.textContent = JSON.stringify({ prerender: [{ source: 'document', where: { and: [{ href_matches: '/*' }, { not: { href_matches: '/*kafa/*' } }, { not: { selector_matches: '[target=_blank], [download]' } }] }, eagerness: 'moderate' }] });
    d.head.appendChild(s);
  });

  /* ---------- çevrimdışı: service worker + Akademi derslerini indir ---------- */
  guvenli(function () {
    if (!('serviceWorker' in navigator)) return;
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') return;
    function kaydet() { navigator.serviceWorker.register('/sw.js').catch(function () {}); }
    if (d.readyState === 'complete') kaydet(); else addEventListener('load', kaydet);
    var akd = d.querySelector('main.anasayfa');
    if (!akd || !('caches' in window)) return;
    var kutu = el('div', { class: 'vk-cevrim' });
    var b = el('button', { type: 'button', class: 'dug cam kucuk vk-cevrim-dug', html: ikon(IK.indir) + '<span>' + t.cevrim + '</span>' });
    var not = el('p', { class: 'vk-cevrim-not', text: t.cevrimNot });
    kutu.appendChild(b); kutu.appendChild(not);
    var hedef = akd.querySelector('.kap') || akd;
    hedef.appendChild(kutu);
    if (hafiza('vk-cevrim-' + DIL)) { not.textContent = t.cevrimTamam; }
    b.addEventListener('click', function () {
      var adresler = [];
      akd.querySelectorAll('a[href]').forEach(function (a) {
        var u = new URL(a.getAttribute('href'), location.href);
        if (u.origin === location.origin && /\/akademi\/[a-z0-9-]+\/$/.test(u.pathname) && adresler.indexOf(u.pathname) < 0) adresler.push(u.pathname);
      });
      [ON + '/akademi/', ON + '/akademi/sozluk/', '/akademi/anahtar.json', '/assets/arama/' + DIL + '.json'].forEach(function (x) { if (adresler.indexOf(x) < 0) adresler.push(x); });
      b.disabled = true; not.textContent = t.cevrimIn;
      navigator.serviceWorker.ready.then(function (k) {
        var kanal = new MessageChannel();
        kanal.port1.onmessage = function (e) {
          var m = e.data || {};
          if (m.tur === 'ilerleme') not.textContent = t.cevrimIn + ' ' + m.bitti + '/' + m.toplam;
          if (m.tur === 'bitti') { b.disabled = false; if (m.hata) not.textContent = t.cevrimHata; else { not.textContent = t.cevrimTamam; hafiza('vk-cevrim-' + DIL, String(Date.now())); } }
        };
        k.active.postMessage({ tur: 'indir', adresler: adresler }, [kanal.port2]);
      }).catch(function () { b.disabled = false; not.textContent = t.cevrimHata; });
    });
  });
})();
