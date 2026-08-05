/* exports/web/pwa-install.js — PWA install prompt + service worker registration.

Loads lazily so it doesn't block first paint. Adds:
  1. Service worker registration (if /sw.js exists)
  2. beforeinstallprompt event handler that shows a banner
  3. iOS Safari fallback hint for "Add to Home Screen"

Trigger:
  The browser fires beforeinstallprompt when the user has visited enough
  times. We cache the event and show a banner after a 30s idle delay so
  we don't interrupt the user on first visit.

Banner:
  A small toast at the bottom-right says "Instalar Paraguay Geodata"
  with a single button. Click → user gets the native install prompt.
"""
 */
(function () {
  'use strict';

  // Service worker registration
  if ('serviceWorker' in navigator) {
    // Register relative to the page so it works on any subpath
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function (err) {
        // Silent fail — CSP may block workers; we don't want to spam the console
        console.warn('[pwa] service worker registration failed:', err.message);
      });
    });
  }

  // Install prompt
  var installEvent = null;
  var banner = null;
  var dismissed = false;

  window.addEventListener('beforeinstallprompt', function (e) {
    // Prevent the default browser prompt
    e.preventDefault();
    installEvent = e;
    // Show our banner after 30s idle (don't pester on first visit)
    setTimeout(showBanner, 30000);
  });

  // iOS Safari: show "Add to Home Screen" hint instead
  var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  var isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;

  if (isIOS && !isStandalone) {
    setTimeout(function () {
      if (!banner && !dismissed) showIOSHint();
    }, 45000);
  }

  function showBanner() {
    if (banner || dismissed || !installEvent) return;
    banner = document.createElement('div');
    banner.setAttribute('role', 'status');
    banner.style.cssText = 'position:fixed; bottom:20px; right:20px; padding:12px 16px; background:var(--bg-elev, #1f2937); color:var(--fg, #f9fafb); border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.3); font-family:system-ui,sans-serif; font-size:13px; z-index:9999; display:flex; align-items:center; gap:12px; max-width:340px;';
    banner.innerHTML = ''
      + '<span>' + (window.PY_I18N && window.PY_I18N.i18n[window.PY_I18N.getLang()]
          ? window.PY_I18N.i18n[window.PY_I18N.getLang()]['pwa.installPrompt'] || 'Instalar Paraguay Geodata'
          : 'Instalar Paraguay Geodata') + '</span>'
      + '<button type="button" id="pwaInstallBtn" style="background:var(--accent, #0f766e); color:white; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; font-size:12px;">'
        + (window.PY_I18N && window.PY_I18N.i18n[window.PY_I18N.getLang()]
            ? window.PY_I18N.i18n[window.PY_I18N.getLang()]['pwa.install'] || 'Instalar'
            : 'Instalar')
      + '</button>'
      + '<button type="button" id="pwaDismissBtn" aria-label="Dismiss" style="background:transparent; color:var(--fg-dim, #9ca3af); border:none; cursor:pointer; font-size:16px; padding:0 4px;">×</button>';
    document.body.appendChild(banner);
    document.getElementById('pwaInstallBtn').addEventListener('click', triggerInstall);
    document.getElementById('pwaDismissBtn').addEventListener('click', dismissBanner);
  }

  function showIOSHint() {
    if (banner || dismissed) return;
    banner = document.createElement('div');
    banner.setAttribute('role', 'status');
    banner.style.cssText = 'position:fixed; bottom:20px; right:20px; padding:12px 16px; background:var(--bg-elev, #1f2937); color:var(--fg, #f9fafb); border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.3); font-family:system-ui,sans-serif; font-size:12px; z-index:9999; max-width:340px; line-height:1.5;';
    banner.innerHTML = '<strong>Instalar Paraguay Geodata</strong><br>Toque <span style="font-size:16px;">⎋</span> → "Añadir a pantalla de inicio"'
      + '<button type="button" aria-label="Dismiss" id="pwaDismissBtn" style="position:absolute; top:4px; right:8px; background:transparent; color:var(--fg-dim, #9ca3af); border:none; cursor:pointer; font-size:14px;">×</button>';
    document.body.appendChild(banner);
    document.getElementById('pwaDismissBtn').addEventListener('click', dismissBanner);
  }

  function triggerInstall() {
    if (!installEvent) return;
    installEvent.prompt();
    installEvent.userChoice.then(function (choice) {
      // Whether the user installed or not, hide the banner
      dismissBanner();
      installEvent = null;
    });
  }

  function dismissBanner() {
    if (banner) banner.remove();
    banner = null;
    dismissed = true;
    // Don't re-show this session
    try { sessionStorage.setItem('pwa-dismissed', '1'); } catch (e) {}
  }

  // Honor prior dismissal
  try {
    if (sessionStorage.getItem('pwa-dismissed') === '1') dismissed = true;
  } catch (e) {}

  // App installed → dismiss banner
  window.addEventListener('appinstalled', dismissBanner);
})();