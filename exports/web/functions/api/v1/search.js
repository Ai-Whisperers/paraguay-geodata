// /functions/api/v1/search.js
// Server-side filtered search over the slim per-depto indexes.
//
// GET /api/v1/search?depto=Asunción&type=apartment&min=50000&max=200000&k=2&limit=20
//
// Query params:
//   depto       filter by state_province (slug or full name)
//   type        filter by property_type (apartment/house/land/commercial/office)
//   min         min price_usd
//   max         max price_usd
//   k           min bedrooms
//   q           substring match against title (case-insensitive)
//   limit       max results (default 20, capped at 200)
//
// Each per-depto file is 50 KB to 1.4 MB. The endpoint loads only the
// requested depto (or all for empty depto). Free-tier CPU budget: ~50ms.
//
// Why per-depto: the full canonical geojson is 18 MB. Even a slim 5 MB
// unified index exceeds the 100ms CPU budget. Per-depto splits it into
// 19 small files, each fast to read + filter.
export async function onRequest(context) {
  if (context.request.method !== "GET") {
    return new Response("Method Not Allowed", { status: 405 });
  }
  const url = new URL(context.request.url);
  const depto = url.searchParams.get("depto") || "";
  const type = url.searchParams.get("type") || "";
  const min = parseFloat(url.searchParams.get("min") || "") || 0;
  const max = parseFloat(url.searchParams.get("max") || "") || 0;
  const minBeds = parseInt(url.searchParams.get("k") || "", 10) || 0;
  const q = (url.searchParams.get("q") || "").toLowerCase();
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "20", 10) || 20, 200);

  // Resolve which depto files to load
  const origin = url.origin;
  let filesToLoad = [];
  if (depto) {
    filesToLoad = [deptoSlug(depto)];
  } else {
    // No depto specified — load the manifest
    try {
      const resp = await fetch(`${origin}/data/search/_index.json`);
      if (!resp.ok) throw new Error(`manifest HTTP ${resp.status}`);
      const manifest = await resp.json();
      filesToLoad = manifest.deptos.map((d) => d.slug);
    } catch (e) {
      return jsonError(500, `manifest fetch failed: ${e.message}`);
    }
  }

  const all = [];
  for (const slug of filesToLoad) {
    try {
      const resp = await fetch(`${origin}/data/search/${slug}.json`);
      if (!resp.ok) {
        console.warn(`search: ${slug} HTTP ${resp.status}`);
        continue;
      }
      const body = await resp.json();
      const records = body.features || [];
      for (const r of records) {
        if (type && r.pt !== type) continue;
        if (min && r.p < min) continue;
        if (max && r.p > max) continue;
        if (minBeds && r.k < minBeds) continue;
        if (q && !r.t.toLowerCase().includes(q)) continue;
        all.push(r);
        if (all.length >= limit) break;
      }
    } catch (e) {
      console.warn(`search: failed to load ${slug}: ${e.message}`);
    }
    if (all.length >= limit) break;
  }

  return new Response(JSON.stringify({
    total: all.length,
    depto: depto || null,
    filters: { type, min, max, minBeds, q, limit },
    features: all.slice(0, limit),
  }), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=60",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

// Map "Asunción" or "asuncion" to the same slug.
function deptoSlug(s) {
  return s.toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "unknown";
}

function jsonError(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}