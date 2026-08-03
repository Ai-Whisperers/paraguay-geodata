/* utils.js — pure utility helpers extracted from the home page's
 * 257 KB inline script.  Nothing here depends on the map or the
 * lazy-loaded widget bundles.  Load with <script src="utils.js"></script>
 * before the inline script.
 */
(function () {
  "use strict";

  /* coordToDMS — convert a decimal lon/lat to degrees/minutes/seconds.
   * Returns a string like "25° 20' 24.0\" S".
   */
  function coordToDMS(coord, isLat) {
    const abs = Math.abs(coord);
    const d = Math.floor(abs);
    const minFloat = (abs - d) * 60;
    const m = Math.floor(minFloat);
    const s = ((minFloat - m) * 60).toFixed(1);
    const suffix = isLat ? (coord >= 0 ? "N" : "S") : (coord >= 0 ? "E" : "W");
    return `${d}° ${m}' ${s}" ${suffix}`;
  }

  /* formatDistance — convert meters to a human-readable string.
   * 750m → "750 m", 1500m → "1.5 km", 12345m → "12.3 km".
   */
  function formatDistance(m) {
    if (m < 1000) return `${Math.round(m)} m`;
    return `${(m / 1000).toFixed(1)} km`;
  }

  /* showToast — display a temporary notification at the bottom of the
   * viewport. Plain text + optional type ("success" | "error" | "info").
   */
  function showToast(text, type = "info", duration = 3000) {
    let el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      Object.assign(el.style, {
        position: "fixed",
        bottom: "20px",
        left: "50%",
        transform: "translateX(-50%)",
        background: "var(--card, #161b22)",
        color: "var(--fg, #e6edf3)",
        padding: "10px 16px",
        borderRadius: "6px",
        border: "1px solid var(--line, #30363d)",
        zIndex: "9999",
        fontSize: "13px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
        opacity: "0",
        transition: "opacity 0.2s",
      });
      document.body.appendChild(el);
    }
    el.textContent = text;
    el.style.opacity = "1";
    if (type === "error") el.style.borderColor = "var(--err, #f85149)";
    else if (type === "success") el.style.borderColor = "var(--ok, #3fb950)";
    else el.style.borderColor = "var(--line, #30363d)";
    clearTimeout(el._hideTimeout);
    el._hideTimeout = setTimeout(() => { el.style.opacity = "0"; }, duration);
  }

  /* loaderComplete — hide the boot overlay once the tiles + properties
   * are loaded.
   */
  function loaderComplete() {
    const overlay = document.getElementById("boot-overlay");
    if (overlay) {
      overlay.style.opacity = "0";
      setTimeout(() => overlay.remove(), 400);
    }
    document.body.classList.add("loaded");
  }

  /* fetchDataFreshness — GET /data/data_freshness.json and return the
   * parsed object. Returns null on failure.
   */
  async function fetchDataFreshness() {
    try {
      const r = await fetch("./data/data_freshness.json");
      if (!r.ok) throw new Error("HTTP " + r.status);
      return await r.json();
    } catch (e) {
      console.warn("fetchDataFreshness failed:", e);
      return null;
    }
  }

  // Export to global so the inline script can call them.
  window.coordToDMS = coordToDMS;
  window.formatDistance = formatDistance;
  window.showToast = showToast;
  window.loaderComplete = loaderComplete;
  window.fetchDataFreshness = fetchDataFreshness;

  console.log("utils.js loaded");
})();
