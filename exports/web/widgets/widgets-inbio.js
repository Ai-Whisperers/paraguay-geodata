/* widgets/widgets-inbio.js — INBIO zafra crops + climate widget.
 *
 * Source: extracted from the legacy widgets.v3.js. Loaded on demand
 * by widgets.js when the INBIO / Climate tabs are opened.
 */
(() => {
  "use strict";

  const WIDGETS = (window.__WIDGETS = window.__WIDGETS || {});

  async function loadINBIOWidget() {
    try {
      const r = await fetch("./data/inbio_zafra_strip.json");
      if (!r.ok) throw new Error("HTTP " + r.status);
      const d = await r.json();
      const el = document.getElementById("inbioWidget");
      if (!el) return;
      const crop = d.dominant_crop || "?";
      const ha = (d.total_ha || 0).toLocaleString();
      el.innerHTML = `
        <div>Dominant crop: <strong>${crop}</strong></div>
        <div>Total area: <strong>${ha} ha</strong></div>
        <div style="color:var(--fg-dim); font-size:10px; margin-top:4px;">
          Fuente: INBIO · ${d.as_of || ""}
        </div>`;
    } catch (e) {
      const el = document.getElementById("inbioWidget");
      if (el) el.innerHTML = '<div style="color:var(--err)">⚠ INBIO unavailable</div>';
    }
  }

  async function loadClimate() {
    try {
      const r = await fetch("./data/data_freshness.json");
      if (!r.ok) throw new Error("HTTP " + r.status);
      const d = await r.json();
      const el = document.getElementById("climateWidget");
      if (!el) return;
      el.innerHTML = `
        <div>Stale: <strong>${d.stale_pct || 0}%</strong></div>
        <div style="color:var(--fg-dim); font-size:10px; margin-top:4px;">
          Listings >14 days old · ${d.as_of || ""}
        </div>`;
    } catch (e) {
      const el = document.getElementById("climateWidget");
      if (el) el.innerHTML = '<div style="color:var(--err)">⚠ Climate unavailable</div>';
    }
  }

  function loadInsights() {
    // Stub: insights loader is owned by tabs.js. This is a no-op wrapper.
    if (typeof window.__loadInsightsImpl === "function") {
      window.__loadInsightsImpl();
    }
  }

  WIDGETS.inbio = { loadINBIOWidget, loadClimate, loadInsights };
})();
