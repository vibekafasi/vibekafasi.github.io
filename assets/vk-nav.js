/* Vibe Kafası: ortak üst menü davranışı (kayan ışık, kaydırınca küçülme, mobil menü). Hata verse bile sayfayı bozmaz. */
(function () {
  try {
    var nav = document.querySelector('[data-vk-nav]'); if (!nav) return;
    var linkler = nav.querySelector('.vk-linkler'), isik = nav.querySelector('.vk-isik');
    // aktif sayfa
    var yol = location.pathname.replace(/index\.html$/, '');
    nav.querySelectorAll('a[data-yol]').forEach(function (a) {
      var y = a.getAttribute('data-yol');
      var akt = y === '/akademi/' ? (yol === '/akademi/' || (yol.indexOf('/akademi/') === 0 && !/\/akademi\/(sozluk|mezuniyet)\//.test(yol))) : yol.indexOf(y) === 0 && y !== '/';
      if (akt) a.setAttribute('aria-current', 'page');
    });
    // kayan ışık
    function git(a) {
      if (!isik || !linkler) return;
      if (!a) { isik.style.opacity = 0; return; }
      var r = a.getBoundingClientRect(), k = linkler.getBoundingClientRect();
      isik.style.left = (r.left - k.left) + 'px'; isik.style.width = r.width + 'px'; isik.style.opacity = 1;
    }
    var aktif = linkler && linkler.querySelector('a[aria-current="page"]');
    if (linkler) {
      linkler.querySelectorAll('a').forEach(function (a) { a.addEventListener('mouseenter', function () { git(a); }); a.addEventListener('focus', function () { git(a); }); });
      linkler.addEventListener('mouseleave', function () { git(aktif); });
      requestAnimationFrame(function () { git(aktif); });
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { git(aktif); });
      addEventListener('resize', function () { git(aktif); });
    }
    // kaydırınca küçül
    var son = false;
    function kay() { var k = scrollY > 24; if (k !== son) { son = k; nav.classList.toggle('kucuk', k); requestAnimationFrame(function () { git(aktif); }); } }
    addEventListener('scroll', kay, { passive: true }); kay();
    // mobil menü
    var dug = nav.querySelector('.vk-menu-dug'), mob = nav.querySelector('.vk-mobil');
    function ac(a) {
      nav.classList.toggle('vk-acik', a); document.documentElement.classList.toggle('vk-kilit', a);
      if (dug) { dug.setAttribute('aria-expanded', a ? 'true' : 'false'); dug.setAttribute('aria-label', a ? 'Menüyü kapat' : 'Menüyü aç'); }
      if (mob) { mob.setAttribute('aria-hidden', a ? 'false' : 'true'); if (a) { var ilk = mob.querySelector('a'); if (ilk) setTimeout(function () { ilk.focus(); }, 250); } }
    }
    if (dug) dug.addEventListener('click', function () { ac(!nav.classList.contains('vk-acik')); });
    if (mob) mob.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { ac(false); }); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && nav.classList.contains('vk-acik')) { ac(false); if (dug) dug.focus(); } });
    addEventListener('resize', function () { if (innerWidth > 860 && nav.classList.contains('vk-acik')) ac(false); });
  } catch (e) {}
})();
