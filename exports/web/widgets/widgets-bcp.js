/* widgets/widgets-bcp.js — BCP macro widget + fair-price model.
 *
 * Source: extracted from the legacy widgets.v3.js (29 KB monolith).
 * Loaded on demand by widgets.js when the BCP / Insights / Property
 * tabs are opened. Bundles loadBCP + loadFairPriceModel + fairPricePredict
 * + fairPriceScore.
 *
 * IMPORTANT: this file exists for the refactor; the legacy widgets.v3.js
 * still ships the full bundle to keep the page working. See plan item D.
 */
(() => {
  "use strict";

  const WIDGETS = (window.__WIDGETS = window.__WIDGETS || {});

  /* loadBCP — fetch the BCP macro indicator block + render it. */
  async function loadBCP() {
    try {
      const r = await fetch("./data/bcp_latest.json");
      if (!r.ok) throw new Error("HTTP " + r.status);
      const d = await r.json();
      const el = document.getElementById("bcpWidget");
      if (!el) return;
      const fmt = (v) => v == null ? "—" : String(v);
      el.innerHTML = `
        <div><strong>TPM</strong>: ${fmt(d.tpm)}%</div>
        <div><strong>Reservas</strong>: $${fmt(d.reservas)} M</div>
        <div><strong>USD/PYG</strong>: ${fmt(d.fx_usd_pyg)}</div>
        <div><strong>IPC</strong>: ${fmt(d.ipc)}%</div>
        <div style="margin-top:4px; color:var(--fg-dim); font-size:10px;">
          BCP · ${d.as_of || ""}
        </div>`;
    } catch (e) {
      const el = document.getElementById("bcpWidget");
      if (el) el.innerHTML = '<div style="color:var(--err)">⚠ BCP unavailable</div>';
    }
  }

  /* loadFairPriceModel — load the experimental model + render its
   * metadata. Note: the model is R² ≈ 0.017 and is labeled as such in
   * the JSON; it is NOT a real valuation tool. USE FOR DEMO ONLY.
   */
  async function loadFairPriceModel() {
    try {
      const r = await fetch("./data/ml/fair_price_model_v2.json");
      if (!r.ok) throw new Error("HTTP " + r.status);
      const m = await r.json();
      const w = document.getElementById("fairPriceWidget");
      if (!w) return;
      const disc = m.disclosure || {};
      const n = (m.depto_models || m.per_depto || {}).length || 0;
      w.innerHTML = `
        <div>Trained on <strong>${(m.training_samples || m.input_rows || 0).toLocaleString()}</strong> properties</div>
        <div style="color:var(--warn); margin-top:4px; font-size:10px;">
          ⚠ ${disc.warning || "EXPERIMENTAL"} · R² ${disc.r_squared || "?"}
        </div>
        <div style="color:var(--fg-dim); font-size:10px; margin-top:4px;">
          ${disc.note || ""}
        </div>`;
    } catch (e) {
      const el = document.getElementById("fairPriceWidget");
      if (el) el.innerHTML = '<div style="color:var(--err)">⚠ Model unavailable</div>';
    }
  }

  /* fairPricePredict — applies the model coefficients to a property.
   * Returns null if the model is missing or the property has no area.
   */
  function fairPricePredict(p, lon, lat) {
    if (!window.fairPriceModel) return null;
    const depto = p.state_province || "Unknown";
    const model = window.fairPriceModel.depto_models?.[depto] || window.fairPriceModel.global_fallback;
    if (!model || !p.area_ha) return null;
    const log_area = Math.log10(Math.max(0.01, p.area_ha));
    const log_pred = (model.intercept || 0)
      + (model.coefs?.log_area || 0) * log_area
      + (model.coefs?.lat || 0) * lat
      + (model.coefs?.lon || 0) * lon;
    return Math.pow(10, log_pred);
  }

  /* fairPriceScore — converts a predicted price into a 0-100 score
   * + an emoji for the popup. 0 = cheap, 100 = overpriced.
   * NOTE: This is a UI decoration; the underlying model has R²≈0.02.
   */
  function fairPriceScore(p, lat, lon) {
    const pred = fairPricePredict(p, lon, lat);
    if (pred == null || !p.price_usd) return null;
    const ratio = p.price_usd / pred;
    if (ratio < 0.7) return { score: 20, label: "💰 deal" };
    if (ratio > 1.3) return { score: 80, label: "🔥 overpriced" };
    return { score: 50, label: "≈ fair" };
  }

  WIDGETS.bcp = { loadBCP, loadFairPriceModel, fairPricePredict, fairPriceScore };
})();
