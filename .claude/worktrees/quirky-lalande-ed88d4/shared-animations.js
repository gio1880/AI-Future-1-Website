/* AI Future — Unearthed Website · Shared Animations
   Used by pages that do not have their own inline animation script. */
(function () {
  'use strict';

  // ── Scroll progress bar ──
  var bar = document.getElementById('progressBar');
  if (bar) {
    var tick = function () {
      var h   = document.documentElement;
      var top = h.scrollTop || document.body.scrollTop;
      var max = (h.scrollHeight || document.body.scrollHeight) - h.clientHeight;
      bar.style.width = (max > 0 ? (top / max) * 100 : 0).toFixed(2) + '%';
    };
    document.addEventListener('scroll', tick, { passive: true });
    tick();
  }

  // ── Reveal on scroll ──
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) e.target.classList.add('in');
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  // ── Auto-stagger: add .reveal + data-delay to children of .reveal-stagger ──
  document.querySelectorAll('.reveal-stagger').forEach(function (parent) {
    Array.from(parent.children).forEach(function (child, i) {
      child.classList.add('reveal');
      child.dataset.delay = String(Math.min(i + 1, 5));
      io.observe(child);
    });
  });
})();
