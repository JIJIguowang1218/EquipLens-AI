/* EquipLens 高保真 · 共享脚本
   - 顶部进度：走过的灰、当前黑、未到不显示（文字居中于所属线段）
   - 底部动作坞：聚焦展开、预判行、提交
   - 通用：toast、图片兜底、分段揭示 */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  window.$ = $; window.$$ = $$;
  window.sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  /* ---------- progress ---------- */
  window.paintSteps = function (cur) {
    $$('.steps .step').forEach((el, i) => {
      el.classList.toggle('done', i < cur);
      el.classList.toggle('now', i === cur);
    });
  };

  /* ---------- toast ---------- */
  let tEl = null;
  window.toast = function (msg) {
    if (!tEl) { tEl = document.createElement('div'); tEl.className = 'toast'; document.body.appendChild(tEl); }
    tEl.textContent = msg; tEl.classList.add('on');
    clearTimeout(tEl._t); tEl._t = setTimeout(() => tEl.classList.remove('on'), 1900);
  };

  /* ---------- 图片兜底：缺图时退化为渐变块 ---------- */
  window.bindImg = function (img) {
    img.addEventListener('error', () => {
      const box = img.parentElement;
      img.remove();
      if (box && !box.querySelector('.ph')) {
        box.insertAdjacentHTML('beforeend',
          '<div class="ph"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
          'stroke-width="1.4"><path d="M3 17h18M5 17V9l4-3h6l4 3v8"/><circle cx="8.5" cy="18.5" r="1.6"/>' +
          '<circle cx="15.5" cy="18.5" r="1.6"/></svg></div>');
      }
    });
  };

  /* ---------- dock ---------- */
  window.initDock = function (opt) {
    const dock = $('#dock'), ta = $('#ask'), send = $('#send'), back = $('#back');
    if (!dock) return;
    const collapse = () => { if (!ta.value.trim()) dock.classList.remove('focus'); };
    ta.addEventListener('focus', () => dock.classList.add('focus'));
    ta.addEventListener('blur', () => setTimeout(collapse, 120));
    ta.addEventListener('input', () => {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 96) + 'px';
    });
    const submit = () => {
      const v = ta.value.trim();
      if (!v) { ta.focus(); return; }
      if (opt && opt.onSubmit) opt.onSubmit(v);
      ta.value = ''; ta.style.height = ''; dock.classList.remove('focus');
    };
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
    });
    send && send.addEventListener('click', submit);
    back && back.addEventListener('click', () => {
      if (opt && opt.onBack) opt.onBack();
      else if (history.length > 1) history.back();
    });
  };

  /* ---------- 进入下一页（带一点淡出） ---------- */
  window.go = function (url) {
    document.body.style.transition = 'opacity .28s ease';
    document.body.style.opacity = '0';
    setTimeout(() => { location.href = url; }, 240);
  };

  /* 页面进入淡入 */
  document.addEventListener('DOMContentLoaded', () => {
    document.body.style.opacity = '0';
    requestAnimationFrame(() => {
      document.body.style.transition = 'opacity .34s ease';
      document.body.style.opacity = '1';
    });
  });
})();
