/* monitoring.js — env-gated monitoring bootstrapper.
 *
 * Drop a <meta name="sentry-dsn" content="..." /> OR
 * <meta name="plausible-domain" content="..."/> in <head> to enable.
 * Empty/absent meta = monitoring stays OFF (default).
 *
 * Keeps public site clean of any hardcoded tracking; nothing ships
 * unless the operator opts in.
 *
 * Self-contained: no bundler.  ~1KB minified.
 */
(function () {
  if (typeof window === 'undefined' || self !== top) return;
  if (window.__MONITORING_INITIALIZED__) return;
  window.__MONITORING_INITIALIZED__ = true;

  function meta(name) {
    var el = document.querySelector('meta[name="' + name + '"]');
    return el ? el.getAttribute('content') : null;
  }

  // ─── Sentry ───────────────────────────────────────────────────────────
  var sentryDsn = meta('sentry-dsn');
  if (sentryDsn) {
    var s = document.createElement('script');
    s.src = 'https://browser.sentry-cdn.com/7.119.0/bundle.tracing.replay.min.js';
    s.crossOrigin = 'anonymous';
    s.onload = function () {
      if (!window.Sentry) return;
      window.Sentry.init({
        dsn: sentryDsn,
        tracesSampleRate: 0.1,
        replaysSessionSampleRate: 0.0,   // off by default — enable for screen replay
        replaysOnErrorSampleRate: 0.0,
        environment: meta('sentry-environment') || location.hostname,
        release: meta('app-version') || 'unknown',
      });
      console.log('[monitoring] Sentry initialized');
    };
    document.head.appendChild(s);
  }

  // ─── Plausible (privacy-friendly analytics) ──────────────────────────
  var plausibleDomain = meta('plausible-domain');
  if (plausibleDomain) {
    var p = document.createElement('script');
    p.src = 'https://plausible.io/js/script.js';
    p.defer = true;
    p.dataset.domain = plausibleDomain;
    document.head.appendChild(p);
    console.log('[monitoring] Plausible enabled for ' + plausibleDomain);
  }

  // ─── Heartbeat: report JS errors to /api/v1/vitals ──────────────────
  // Always on (lightweight, ~1 line).  Falls back to console if beacon fails.
  window.addEventListener('error', function (e) {
    var body = JSON.stringify({
      type: 'js_error',
      msg: String(e.message || ''),
      src: e.filename || '',
      line: e.lineno || 0,
      col: e.colno || 0,
      ts: Date.now(),
    });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/v1/vitals', body);
      } else {
        console.warn('[js_error]', body);
      }
    } catch (_) { /* swallow */ }
  });
})();
