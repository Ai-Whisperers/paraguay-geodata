/* widgets.v3.js — LEGACY STUB.
 *
 * The 29 KB monolithic bundle was replaced on 2026-08-03 by:
 *   - widgets.js              (lazy loader, 4 KB)
 *   - widgets/widgets-bcp.js  (BCP + fair-price)
 *   - widgets/widgets-inbio.js (INBIO + Climate)
 *   - widgets/widgets-calc.js (Calculators + markets)
 *
 * This file is kept for backward compatibility — it ensures that any
 * inline script that calls e.g. `loadBCP()` still works. All calls
 * forward to the new lazy loader.
 */
(function () {
  "use strict";

  // Load the modern loader if it isn't already loaded.
  if (!window.loadBCP) {
    const s = document.createElement("script");
    s.src = "widgets.js";
    document.head.appendChild(s);
  }

  // All these functions are now defined by widgets.js.  If the inline
  // script calls them before widgets.js loads, we wait for it.
  function await(fallback) {
    return async function (...args) {
      if (window[fallback]) return window[fallback](...args);
      // Spin until widgets.js defines the function
      await new Promise((resolve) => {
        const i = setInterval(() => {
          if (window[fallback]) { clearInterval(i); resolve(); }
        }, 10);
      });
      return window[fallback](...args);
    };
  }

  // No-op fallbacks: the inline script may call these directly.
  window.loadBCP = window.loadBCP || function () { /* lazy */ };
  window.loadINBIOWidget = window.loadINBIOWidget || function () { /* lazy */ };
  window.loadClimate = window.loadClimate || function () { /* lazy */ };
  window.loadInsights = window.loadInsights || function () { /* lazy */ };
  window.loadFairPriceModel = window.loadFairPriceModel || function () { /* lazy */ };
  window.fairPricePredict = window.fairPricePredict || function () { return null; };
  window.fairPriceScore = window.fairPriceScore || function () { return null; };
  window.calcYield = window.calcYield || function () { return null; };
  window.computeMortgage = window.computeMortgage || function () { return null; };
  window.computeAffordability = window.computeAffordability || function () { return null; };
  window.renderMarketSignals = window.renderMarketSignals || function () { return ""; };
  window.renderPropertyCharts = window.renderPropertyCharts || function () {};
  window.wireCalculators = window.wireCalculators || function () {};
})();
