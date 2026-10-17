/* Рідна Школа · Detroit — small progressive enhancements. No frameworks. */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');

  /* ---------- Language toggle (uk default, en optional) ---------- */
  function setLang(lang, persist) {
    if (lang === 'en') { root.setAttribute('data-lang', 'en'); root.setAttribute('lang', 'en'); }
    else { root.removeAttribute('data-lang'); root.setAttribute('lang', 'uk'); lang = 'uk'; }
    document.querySelectorAll('.lang-switch button').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true' : 'false');
    });
    if (persist) { try { localStorage.setItem('rs-lang', lang); } catch (e) { /* storage may be unavailable */ } }
  }
  var saved = null;
  try { saved = localStorage.getItem('rs-lang'); } catch (e) { saved = null; }
  setLang(saved === 'en' ? 'en' : 'uk', false);
  document.querySelectorAll('.lang-switch button').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.getAttribute('data-lang'), true); });
  });

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
      }
    });
  }

  /* ---------- Header shadow on scroll ---------- */
  var header = document.getElementById('site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Current page highlight ---------- */
  var here = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.site-nav a').forEach(function (a) {
    var target = a.getAttribute('href');
    if (target === here) a.setAttribute('aria-current', 'page');
  });

  /* ---------- Homework week tabs ---------- */
  var tabs = document.querySelectorAll('.week-tabs button');
  var panels = document.querySelectorAll('.week-panel');
  function showWeek(id) {
    panels.forEach(function (p) { p.hidden = p.id !== id; });
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('aria-controls') === id ? 'true' : 'false'); });
  }
  if (tabs.length && panels.length) {
    var initial = (location.hash && document.getElementById(location.hash.slice(1))) ? location.hash.slice(1) : tabs[0].getAttribute('aria-controls');
    showWeek(initial);
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        var id = t.getAttribute('aria-controls');
        showWeek(id);
        if (history.replaceState) history.replaceState(null, '', '#' + id);
      });
    });
  }

  /* ---------- Copy buttons ---------- */
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';
      var done = function () { var old = btn.textContent; btn.textContent = btn.getAttribute('data-done') || '✓'; setTimeout(function () { btn.textContent = old; }, 1500); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(); });
      } else { fallback(); }
      function fallback() {
        var el = document.getElementById(btn.getAttribute('aria-controls') || '');
        if (el && window.getSelection) {
          var r = document.createRange(); r.selectNodeContents(el);
          var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        }
      }
    });
  });
})();
