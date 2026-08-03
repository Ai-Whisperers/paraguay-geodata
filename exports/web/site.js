/* Paraguay Geodata — site behavior
   - i18n init
   - cookie banner
   - saved/compare/feedback widgets (cookie-backed)
   - onboarding overlay
   - map controls (scale, north, legend)
   - shared helpers (saved-listings store, compare store, property rendering)
*/
(function () {
    'use strict';

    // ===== Local storage helpers =====
    function getStore(key, defaultValue) {
        try {
            var v = localStorage.getItem('py.' + key);
            return v === null ? defaultValue : JSON.parse(v);
        } catch (e) { return defaultValue; }
    }
    function setStore(key, value) {
        try { localStorage.setItem('py.' + key, JSON.stringify(value)); } catch (e) {}
    }

    window.PY = window.PY || {};
    window.PY.getStore = getStore;
    window.PY.setStore = setStore;

    // ===== Saved listings =====
    window.PY.saved = {
        get: function () { return getStore('saved', []); },
        add: function (id) {
            var list = getStore('saved', []);
            if (list.indexOf(id) === -1) list.push(id);
            setStore('saved', list);
        },
        remove: function (id) {
            var list = getStore('saved', []).filter(function (i) { return i !== id; });
            setStore('saved', list);
        },
        toggle: function (id) {
            var list = getStore('saved', []);
            if (list.indexOf(id) >= 0) {
                list = list.filter(function (i) { return i !== id; });
                setStore('saved', list);
                return false;
            }
            list.push(id);
            setStore('saved', list);
            return true;
        },
        has: function (id) { return getStore('saved', []).indexOf(id) >= 0; },
        clear: function () { setStore('saved', []); }
    };

    // ===== Compare (max 4) =====
    window.PY.compare = {
        get: function () { return getStore('compare', []); },
        add: function (id) {
            var list = getStore('compare', []);
            if (list.indexOf(id) >= 0) return;
            if (list.length >= 4) {
                window.PY.notify && window.PY.notify(
                    (window.PY_I18N ? window.PY_I18N.getLang() : 'es') === 'es'
                        ? 'Máximo 4 propiedades para comparar' : 'Max 4 properties to compare',
                    'warn'
                );
                return;
            }
            list.push(id);
            setStore('compare', list);
        },
        remove: function (id) {
            var list = getStore('compare', []).filter(function (i) { return i !== id; });
            setStore('compare', list);
        },
        toggle: function (id) {
            var list = getStore('compare', []);
            if (list.indexOf(id) >= 0) {
                list = list.filter(function (i) { return i !== id; });
                setStore('compare', list);
                return false;
            }
            if (list.length >= 4) return false;
            list.push(id);
            setStore('compare', list);
            return true;
        },
        clear: function () { setStore('compare', []); }
    };

    // ===== Notifications (toast) =====
    window.PY.notify = function (text, kind) {
        kind = kind || 'info';
        var n = document.createElement('div');
        n.textContent = text;
        n.style.cssText = 'position:fixed;top:80px;right:16px;z-index:99999;'
            + 'background:var(--bg-elev);color:var(--fg);padding:10px 16px;'
            + 'border-radius:6px;border:1px solid var(--line);'
            + (kind === 'warn' ? 'border-color:var(--warn);' : '')
            + (kind === 'good' ? 'border-color:var(--good);' : '');
        document.body.appendChild(n);
        setTimeout(function () { n.remove(); }, 3000);
    };

    // ===== Cookie banner =====
    function initCookieBanner() {
        if (getStore('cookieChoice', null) !== null) return;
        var lang = window.PY_I18N ? window.PY_I18N.getLang() : 'es';
        var i18n = (window.PY_I18N && window.PY_I18N.i18n) || {};
        var text = (i18n[lang] && i18n[lang]['cookieBanner.text']) ||
                   (i18n.es && i18n.es['cookieBanner.text']) ||
                   'We use cookies to remember language and saved properties.';
        var accept = (i18n[lang] && i18n[lang]['cookieBanner.accept']) || 'Accept';
        var decline = (i18n[lang] && i18n[lang]['cookieBanner.decline']) || 'Necessary only';

        var banner = document.createElement('div');
        banner.className = 'cookie-banner';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-label', 'Cookie consent');
        banner.innerHTML = '<p></p><button class="accept"></button><button class="decline"></button>';
        banner.querySelector('p').textContent = text;
        var btnA = banner.querySelector('button.accept');
        btnA.textContent = accept;
        var btnD = banner.querySelector('button.decline');
        btnD.textContent = decline;
        btnA.addEventListener('click', function () {
            setStore('cookieChoice', 'accept');
            banner.remove();
        });
        btnD.addEventListener('click', function () {
            setStore('cookieChoice', 'necessary');
            banner.remove();
        });
        document.body.appendChild(banner);
    }

    // ===== Feedback widget =====
    function initFeedback() {
        var btn = document.createElement('button');
        btn.className = 'feedback-btn';
        btn.setAttribute('aria-label', 'Feedback');
        btn.textContent = '💬';
        btn.title = 'Feedback';
        document.body.appendChild(btn);

        var modal = document.createElement('div');
        modal.className = 'feedback-modal';
        modal.innerHTML = '<h3 style="margin:0 0 8px;font-size:14px;">Feedback</h3>' +
            '<textarea placeholder="¿Qué cambiarías?"></textarea>' +
            '<div style="display:flex;gap:8px;margin-top:8px;justify-content:flex-end;">' +
            '<button class="btn btn-secondary btn-sm cancel">Cancelar</button>' +
            '<button class="btn btn-sm send">Enviar</button>' +
            '</div>';
        document.body.appendChild(modal);

        var textarea = modal.querySelector('textarea');
        btn.addEventListener('click', function () {
            modal.classList.toggle('open');
            if (modal.classList.contains('open')) textarea.focus();
        });
        modal.querySelector('.cancel').addEventListener('click', function () {
            modal.classList.remove('open');
            textarea.value = '';
        });
        modal.querySelector('.send').addEventListener('click', function () {
            var text = textarea.value.trim();
            if (!text) return;
            // Send to mailto — fallback until we have a backend
            var subject = encodeURIComponent('PY Geodata feedback');
            var body = encodeURIComponent(text + '\n\n— sent from geodata.paragu-ai.com on ' + new Date().toISOString());
            window.location.href = 'mailto:erebus@ai-whisperers.org?subject=' + subject + '&body=' + body;
            modal.classList.remove('open');
            textarea.value = '';
            window.PY.notify('¡Gracias!', 'good');
        });
    }

    // ===== Onboarding overlay =====
    function initOnboarding() {
        if (getStore('onboarded', false)) return;
        var lang = window.PY_I18N ? window.PY_I18N.getLang() : 'es';
        var i18n = (window.PY_I18N && window.PY_I18N.i18n) || {};
        function t(k) {
            return (i18n[lang] && i18n[lang][k]) || (i18n.es && i18n.es[k]) || k;
        }
        var steps = [
            { title: t('onboarding.step1.title'), body: t('onboarding.step1.body') },
            { title: t('onboarding.step2.title'), body: t('onboarding.step2.body') },
            { title: t('onboarding.step3.title'), body: t('onboarding.step3.body') },
            { title: t('onboarding.step4.title'), body: t('onboarding.step4.body') },
            { title: t('onboarding.step5.title'), body: t('onboarding.step5.body') },
        ];
        var idx = 0;

        var overlay = document.createElement('div');
        overlay.className = 'onboarding-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-label', 'Onboarding');

        function render() {
            var s = steps[idx];
            overlay.innerHTML = '<div class="onboarding-card">' +
                '<h2></h2><p></p>' +
                '<div class="nav-row">' +
                '<span class="progress"></span>' +
                (idx < steps.length - 1
                    ? '<div><button class="skip">' + t('onboarding.skip') + '</button> ' +
                      '<button class="next">' + t('onboarding.next') + '</button></div>'
                    : '<button class="next">' + t('onboarding.done') + '</button>') +
                '</div></div>';
            overlay.querySelector('h2').textContent = s.title;
            overlay.querySelector('p').textContent = s.body;
            overlay.querySelector('.progress').textContent =
                (idx + 1) + ' / ' + steps.length;
            var nextBtn = overlay.querySelector('.next');
            var skipBtn = overlay.querySelector('.skip');
            if (nextBtn) nextBtn.addEventListener('click', function () {
                if (idx < steps.length - 1) { idx++; render(); }
                else { setStore('onboarded', true); overlay.remove(); }
            });
            if (skipBtn) skipBtn.addEventListener('click', function () {
                setStore('onboarded', true); overlay.remove();
            });
        }
        render();
        document.body.appendChild(overlay);
        overlay.classList.add('open');
    }

    // ===== Mobile menu toggle =====
    function initMobileMenu() {
        var h = document.querySelector('header.site-header');
        if (!h) return;
        var nav = h.querySelector('nav.primary');
        if (!nav) return;
        // Build a hamburger
        var btn = document.createElement('button');
        btn.className = 'menu-toggle';
        btn.setAttribute('aria-label', (window.PY_I18N && window.PY_I18N.i18n &&
            window.PY_I18N.i18n[(window.PY_I18N.getLang() || 'es')]['common.menu']) || 'Menu');
        btn.textContent = '☰';
        h.insertBefore(btn, nav);
        btn.addEventListener('click', function () { nav.classList.toggle('open'); });
    }

    // ===== Saved-listings counter badge =====
    function updateSavedCount() {
        var badges = document.querySelectorAll('[data-saved-count]');
        var n = window.PY.saved.get().length;
        badges.forEach(function (b) { b.textContent = n; });
    }

    // ===== Wire on load =====
    function boot() {
        initCookieBanner();
        initFeedback();
        initMobileMenu();
        updateSavedCount();
        // Onboarding only on the home page (if there's a #map element or path)
        if (location.pathname === '/' || location.pathname === '/index.html' ||
            location.pathname.endsWith('/index.html')) {
            setTimeout(initOnboarding, 800);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // Re-render saved-count on storage change
    window.addEventListener('storage', updateSavedCount);

})();

// === Web Vitals observer (anonymized) ===
// Pulls in web-vitals from CDN, observes LCP/CLS/INP/FCP/TTFB, and
// surfaces them via console.log or Sentry breadcrumb (if Sentry is loaded).
// Self-contained: no bundler.
(function () {
  if (typeof window === "undefined") return;
  if (window.self !== window.top) return;
  if (window.__WV_INITIALIZED__) return;
  window.__WV_INITIALIZED__ = true;

  const ready = (cb) => {
    if (document.readyState !== "loading") cb();
    else document.addEventListener("DOMContentLoaded", cb);
  };

  ready(() => {
    const s = document.createElement("script");
    s.src = "https://unpkg.com/web-vitals@4/dist/web-vitals.attribution.iife.js";
    s.crossOrigin = "anonymous";
    s.onload = () => {
      if (typeof webVitals === "undefined") return;
      const reporter = (metric) => {
        const data = {
          name: metric.name,
          id: metric.id,
          value: metric.value,
          rating: metric.rating,
          delta: metric.delta,
          navigationType: metric.navigationType,
          url: location.href,
        };
        if (window.Sentry && window.Sentry.addBreadcrumb) {
          window.Sentry.addBreadcrumb({ category: "vitals", data: data });
        } else {
          console.log("[vitals]", data);
        }
      };
      webVitals.onLCP(reporter);
      webVitals.onCLS(reporter);
      webVitals.onINP(reporter);
      webVitals.onFCP(reporter);
      webVitals.onTTFB(reporter);
    };
    document.head.appendChild(s);
  });
})();
