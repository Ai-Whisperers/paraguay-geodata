/* widgets.js — Lazy-loads the widget bundles on demand.
 *
 * The legacy widgets.v3.js (29 KB) is a bundle of 13 functions
 * (BCP, INBIO, Climate, Fair-price, Yield, Mortgage, ...). This
 * module replaces the monolithic bundle with 3 lazy-loaded bundles:
 *
 *   widgets/widgets-bcp.js    (BCP + fair-price)
 *   widgets/widgets-inbio.js (INBIO + Climate)
 *   widgets/widgets-calc.js  (Calculators + markets)
 *
 * Each module loads only when its feature is invoked. The legacy
 * widgets.v3.js is kept as a fallback for the inline triggers in
 * index.html; we re-export the same names so the page still works.
 *
 * Trigger: window.__WIDGETS.bcp.loadBCP etc.  (auto-routes to whichever
 * bundle is loaded).
 */
(function () {
  "use strict";

  // ---------- Module loader ----------
  const loaded = new Set();
  const loading = new Map();  // name -> Promise
  const cache = (window.__WIDGETS = window.__WIDGETS || {});

  function loadModule(name, scriptPath) {
    if (loaded.has(name)) return Promise.resolve(cache[name]);
    if (loading.has(name)) return loading.get(name);
    const p = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = scriptPath;
      s.async = true;
      s.onload = () => {
        loaded.add(name);
        loading.delete(name);
        resolve(cache[name]);
      };
      s.onerror = () => {
        loading.delete(name);
        reject(new Error("failed to load " + scriptPath));
      };
      document.head.appendChild(s);
    });
    loading.set(name, p);
    return p;
  }

  // ---------- Public API ----------
  async function loadBCP() {
    const m = await loadModule("bcp", "widgets/widgets-bcp.js");
    return m.loadBCP();
  }
  async function loadINBIOWidget() {
    const m = await loadModule("inbio", "widgets/widgets-inbio.js");
    return m.loadINBIOWidget();
  }
  async function loadClimate() {
    const m = await loadModule("inbio", "widgets/widgets-inbio.js");
    return m.loadClimate();
  }
  async function loadInsights() {
    const m = await loadModule("inbio", "widgets/widgets-inbio.js");
    return m.loadInsights();
  }
  async function loadFairPriceModel() {
    const m = await loadModule("bcp", "widgets/widgets-bcp.js");
    return m.loadFairPriceModel();
  }
  function fairPricePredict(p, lon, lat) {
    if (cache.bcp) return cache.bcp.fairPricePredict(p, lon, lat);
    // Fallback: trigger lazy load and return null this turn.
    loadModule("bcp", "widgets/widgets-bcp.js");
    return null;
  }
  function fairPriceScore(p, lat, lon) {
    if (cache.bcp) return cache.bcp.fairPriceScore(p, lat, lon);
    loadModule("bcp", "widgets/widgets-bcp.js");
    return null;
  }
  function calcYield(p, monthly_rent_usd) {
    if (cache.calc) return cache.calc.calcYield(p, monthly_rent_usd);
    loadModule("calc", "widgets/widgets-calc.js");
    return null;
  }
  function computeMortgage(...args) {
    if (cache.calc) return cache.calc.computeMortgage(...args);
    loadModule("calc", "widgets/widgets-calc.js");
    return null;
  }
  function computeAffordability(...args) {
    if (cache.calc) return cache.calc.computeAffordability(...args);
    loadModule("calc", "widgets/widgets-calc.js");
    return null;
  }
  function renderMarketSignals(p) {
    if (cache.calc) return cache.calc.renderMarketSignals(p);
    loadModule("calc", "widgets/widgets-calc.js");
    return "";
  }
  function renderPropertyCharts(canvas, p) {
    if (cache.calc) return cache.calc.renderPropertyCharts(canvas, p);
    loadModule("calc", "widgets/widgets-calc.js");
  }
  function wireCalculators() {
    if (cache.calc) return cache.calc.wireCalculators();
    loadModule("calc", "widgets/widgets-calc.js");
  }

  // ---------- Export to global ----------
  window.loadBCP = loadBCP;
  window.loadINBIOWidget = loadINBIOWidget;
  window.loadClimate = loadClimate;
  window.loadInsights = loadInsights;
  window.loadFairPriceModel = loadFairPriceModel;
  window.fairPricePredict = fairPricePredict;
  window.fairPriceScore = fairPriceScore;
  window.calcYield = calcYield;
  window.computeMortgage = computeMortgage;
  window.computeAffordability = computeAffordability;
  window.renderMarketSignals = renderMarketSignals;
  window.renderPropertyCharts = renderPropertyCharts;
  window.wireCalculators = wireCalculators;

  console.log("widgets.js (lazy) loaded — bundles load on demand");
})();
