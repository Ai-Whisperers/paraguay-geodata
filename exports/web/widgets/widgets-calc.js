/* widgets/widgets-calc.js — Calculators (yield, mortgage, affordability).
 *
 * Source: extracted from the legacy widgets.v3.js. Loaded on demand
 * by widgets.js when the User tab is opened or when a calculator is
 * shown.
 */
(() => {
  "use strict";

  const WIDGETS = (window.__WIDGETS = window.__WIDGETS || {});

  /* calcYield — annualized gross yield, assuming monthly rent × 12.
   * Returns a percentage (e.g., 7.5) or null if inputs are missing.
   */
  function calcYield(p, monthly_rent_usd) {
    if (!monthly_rent_usd || !p.price_usd) return null;
    return (monthly_rent_usd * 12 / p.price_usd) * 100;
  }

  /* computeMortgage — simple amortization given principal, rate, term.
   * Paraguayan mortgages are typically USD-indexed; the rate is the
   * BCP-published rate (~6-12% depending on the institution).
   */
  function computeMortgage(principal, rate_pct, term_years) {
    if (!principal || !term_years) return null;
    const r = (rate_pct / 100) / 12;
    const n = term_years * 12;
    const m = (principal * r) / (1 - Math.pow(1 + r, -n));
    return {
      monthly: m,
      total: m * n,
      interest: m * n - principal,
    };
  }

  /* computeAffordability — given a monthly budget, what can you afford?
   * Uses a 30/40 ratio (housing costs ≤ 30% of gross income, DTI ≤ 40%).
   */
  function computeAffordability(monthly_income_usd, rate_pct, term_years) {
    if (!monthly_income_usd) return null;
    const max_payment = monthly_income_usd * 0.30;
    const r = (rate_pct / 100) / 12;
    const n = term_years * 12;
    const loan = (max_payment * (1 - Math.pow(1 + r, -n))) / r;
    return loan;
  }

  /* renderMarketSignals — small summary line shown in the popup.
   * Returns a string of HTML.
   */
  function renderMarketSignals(p) {
    if (!p) return "";
    const yieldPct = p.monthly_rent_usd ? calcYield(p, p.monthly_rent_usd) : null;
    const pricePerM2 = p.price_usd && p.area_sqm ? p.price_usd / p.area_sqm : null;
    const out = [];
    if (yieldPct != null) {
      out.push(`<span>Yield: <strong>${yieldPct.toFixed(1)}%</strong></span>`);
    }
    if (pricePerM2) {
      out.push(`<span>$/m²: <strong>$${Math.round(pricePerM2).toLocaleString()}</strong></span>`);
    }
    return out.join(" ");
  }

  /* renderPropertyCharts — placeholder for chart rendering. The home
   * page uses Chart.js directly; this stub gives the same surface so
   * legacy callers don't break.
   */
  function renderPropertyCharts(canvas, p) {
    if (!canvas || !canvas.getContext) return;
    if (typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    const yieldPct = p.monthly_rent_usd ? calcYield(p, p.monthly_rent_usd) : 0;
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Yield", "Vacancy", "Cost"],
        datasets: [{
          data: [yieldPct, 5, 100 - yieldPct - 5],
          backgroundColor: ["#3fb950", "#7d8590", "#161b22"],
        }],
      },
    });
  }

  /* wireCalculators — bind the calculator inputs to the helpers above.
   * Called once after DOMContentLoaded.
   */
  function wireCalculators() {
    // The original DOM wiring is in tabs.js. This is a no-op stub.
  }

  WIDGETS.calc = {
    calcYield, computeMortgage, computeAffordability,
    renderMarketSignals, renderPropertyCharts, wireCalculators,
  };
})();
