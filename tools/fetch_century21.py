#!/usr/bin/env python3
"""tools/fetch_century21.py

Scraper for century21.com.py real-estate listings in Paraguay.

The site uses Laravel server-rendered HTML with the full listing data
inlined as a JSON object (the page hydrates the React tree from `window
.__NEXT_DATA__`-equivalent: each detail page contains `window.filtrosArray`
+ a per-property records array with `lat`, `lon`, `m2T`, `precio`, etc.).

Strategy
--------
1.  Index pages: GET /busqueda/<operacion>_<depto_slug> (e.g.
    `/busqueda/operacion_venta/en-estado_central`) → server returns a
    listing card grid with `<a href="/propiedad/<id>_<slug>">` links.
2.  Detail pages: GET /propiedad/<id>_<slug> → HTML contains an
    inlined JSON blob with lat/lon, m2T, precio, municipio, estado, etc.
3.  Output: data/properties/snapshots/century21_<date>.geojson

Tests
-----
    tests/test_fetch_century21.py — synthetic detail-page parsing.

Rate limit: 0.7s between requests (1.4 req/s).  Headers: realistic UA.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FX_PYG_PER_USD = 7_500.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
DETAIL_RE = re.compile(r"/propiedad/(\d+)_([\w-]+)")

DEPTO_SLUG = {
    "Asunción": "asuncion",
    "Alto Paraguay": "alto-paraguay",
    "Alto Paraná": "alto-parana",
    "Amambay": "amambay",
    "Boquerón": "boqueron",
    "Caaguazú": "caaguazu",
    "Caazapá": "caazapa",
    "Canindeyú": "canindeyu",
    "Central": "central",
    "Concepción": "concepcion",
    "Cordillera": "cordillera",
    "Guairá": "guaira",
    "Itapúa": "itapua",
    "Misiones": "misiones",
    "Ñeembucú": "neembucu",
    "Paraguarí": "paraguari",
    "Presidente Hayes": "presidente-hayes",
    "San Pedro": "san-pedro",
}


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-PY,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def _extract_prop_urls(index_html: str) -> list[str]:
    """Pick /propiedad/<id>_<slug> links from an index page."""
    urls: set[str] = set()
    for m in re.finditer(r'href="(/propiedad/\d+_[a-z0-9-]+)"', index_html, re.I):
        urls.add("https://century21.com.py" + m.group(1))
    return sorted(urls)


def _parse_detail(html: str, source_url: str) -> dict | None:
    """Pull a single property record out of an inlined JSON blob."""
    sid_m = DETAIL_RE.search(source_url)
    if not sid_m:
        return None
    sid = sid_m.group(1)

    # Find the JSON object whose `"id":<sid>` or `"id": "<sid>"` token starts it.
    # Use a balanced-brace scan that handles JSON strings + escapes correctly.
    pat = re.compile(r'"id":\s*"?\b' + sid + r'\b"?')
    m = pat.search(html)
    if not m:
        return None
    # Walk backwards to the opening `{` of this object
    start = html.rfind('{', 0, m.start())
    if start < 0:
        return None
    # Walk forward to the matching `}`
    depth = 0
    in_str = False
    esc = False
    end = start
    for i in range(start, min(len(html), start + 200_000)):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    raw = html[start:end]
    try:
        rec = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # Pull the salient fields
    lat = rec.get("lat")
    lon = rec.get("lon")
    if lat is None or lon is None:
        return None
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        return None
    # Out-of-bounds filter (Argentina/Uruguay)
    if not (-63.5 <= lon <= -54.0 and -27.5 <= lat <= -19.0):
        return None

    precio = rec.get("precio")
    moneda = (rec.get("moneda") or "PYG").upper()
    if precio is None:
        return None
    try:
        precio = float(precio)
    except (TypeError, ValueError):
        return None
    if moneda == "USD":
        price_usd = precio
        price_pyg = precio * FX_PYG_PER_USD
    else:
        price_pyg = precio
        price_usd = precio / FX_PYG_PER_USD

    m2t = rec.get("m2T") or rec.get("m2C")
    try:
        m2t = float(m2t) if m2t else None
    except (TypeError, ValueError):
        m2t = None
    area_ha = (m2t / 10000) if m2t else None
    area_sqm = m2t

    listing_type = "rent" if (rec.get("tipoOperacion") or "").lower() in ("renta", "alquiler") else "sale"

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": f"c21_{sid}",
            "source": "century21",
            "source_id": sid,
            "source_url": source_url,
            "source_platform": "century21.com.py",
            "scraped_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "title": rec.get("encabezado") or "Propiedad",
            "city": rec.get("municipio"),
            "state_province": rec.get("estado"),
            "country": rec.get("pais") or "Paraguay",
            "address": rec.get("calle"),
            "listing_type": listing_type,
            "property_type": _map_property_type(rec.get("subTipoPropiedad") or rec.get("tipoPropiedad")),
            "currency": moneda,
            "price_pyg": price_pyg,
            "price_usd": round(price_usd, 2),
            "area_sqm": area_sqm,
            "area_ha": round(area_ha, 4) if area_ha else None,
            "bedrooms": _safe_int(rec.get("recamaras")),
            "bathrooms": _safe_int(rec.get("banios")),
            "parking_spaces": _safe_int(rec.get("estacionamientos")),
            "images": [f["large"] for f in (rec.get("fotosArray") or []) if f.get("large")][:8],
            "description": (rec.get("descripcion") or "")[:1500],
            "lat": lat,
            "lon": lon,
        },
    }


def _safe_int(v) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _map_property_type(raw: str | None) -> str:
    if not raw:
        return "unknown"
    r = raw.lower()
    if "casa-duplex" in r: return "house"
    if "casa-en-condominio" in r: return "house"
    if "casa" in r: return "house"
    if "departamento" in r: return "apartment"
    if "terreno" in r: return "land"
    if "estancia" in r or "hacienda" in r or "ganadera" in r: return "land"
    if "local" in r or "oficina" in r: return "commercial"
    if "bodega" in r or "nave" in r or "fabrica" in r: return "commercial"
    if "quinta" in r or "fraccionamiento" in r: return "land"
    if "edificio" in r: return "commercial"
    return "unknown"


def _extract_index_data(html: str) -> list[dict]:
    """Extract the per-property records from the Century21 React hydration
    blob `window.REP_LOG_APP_PROPS = {...}`.  Multiple shapes exist:

    * Per-state search pages: `propiedades: [{...}, {...}]`
    * Universal /v/resultados: `datas: { results: [{...}, {...}], ... }`
    * Universal with no envelope:    `datas: { id:..., calle:..., lat:..., lon:..., ... }`
    Returns the parsed records (list of dicts).
    """
    pat = re.compile(r'REP_LOG_APP_PROPS\s*=\s*\{')
    m = pat.search(html)
    if not m:
        return []
    blob_start = m.end() - 1
    # Walk forward to the matching closing brace
    depth = 0
    in_str = False
    esc = False
    blob_end = blob_start
    for i in range(blob_start, min(len(html), blob_start + 2_000_000)):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                blob_end = i + 1
                break
    raw = html[blob_start:blob_end]

    # Strategy 1: find array bracket opener after one of the candidate
    # keys.  Per-state pages use "propiedades: [...]"; the universal
    # /v/resultados uses "datas: { ... results: [ ... ] }".
    arr_open = -1
    # Try direct top-level array first
    for variant in ('propiedades:[', 'propiedades: [', 'propiedades:\n\t\t[', 'propiedades: ['):
        i = raw.find(variant)
        if i >= 0:
            j = i + len(variant)
            if raw[j-1] == '[':
                arr_open = j - 1
            else:
                arr_open = raw.find('[', i)
            break
    if arr_open < 0:
        # Fallback: find "results: [" by plain string search in the raw.
        # The datas block ends at the outer closing of REP_LOG_APP_PROPS,
        # so we just need the first literal "results:[" substring.
        res_m = re.search(r'"results"\s*:\s*\[', raw)
        if res_m:
            j = res_m.end() - 1
            arr_open = j
    if arr_open < 0:
        return []  # not found

    # Walk to matching ] with bracket counter
    depth = 0
    in_str = False
    esc = False
    arr_end = arr_open
    for i in range(arr_open, min(len(raw), arr_open + 5_000_000)):
        c = raw[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                arr_end = i
                break
    array_text = raw[arr_open:arr_end + 1]

    # Walk each record at depth 1 and parse as JSON
    records: list[dict] = []
    i = 1
    while i < len(array_text) - 1:
        c = array_text[i]
        if c in ' ,':
            i += 1; continue
        if c == '{':
            start = i
            depth = 0
            in_s, esc = False, False
            end = start
            for j in range(start, min(len(array_text), start + 200_000)):
                cc = array_text[j]
                if in_s:
                    if esc: esc = False
                    elif cc == '\\': esc = True
                    elif cc == '"': in_s = False
                    continue
                if cc == '"': in_s = True
                elif cc == '{': depth += 1
                elif cc == '}':
                    depth -= 1
                    if depth == 0:
                        end = j + 1; break
            rec_raw = array_text[start:end]
            try:
                rec = json.loads(rec_raw)
                records.append(rec)
            except json.JSONDecodeError:
                pass
            i = end
            continue
        i += 1
    return records


def _parse_record(rec: dict) -> dict | None:
    """Convert a Century21 record to our canonical feature shape."""
    lat = rec.get("lat")
    lon = rec.get("lon")
    if not lat or not lon:
        return None
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        return None
    if not (-63.5 <= lon <= -54.0 and -27.5 <= lat <= -19.0):
        return None

    sid = str(rec.get("id") or "")
    if not sid:
        return None
    url_path = rec.get("urlCorrecta") or f"/propiedad/{sid}"
    source_url = "https://century21.com.py" + url_path

    precio = rec.get("precio")
    moneda = (rec.get("moneda") or "PYG").upper()
    if precio is None:
        return None
    try:
        precio = float(precio)
    except (TypeError, ValueError):
        return None
    if moneda == "USD":
        price_usd = precio
        price_pyg = precio * FX_PYG_PER_USD
    else:
        price_pyg = precio
        price_usd = precio / FX_PYG_PER_USD

    m2t = rec.get("m2T") or rec.get("m2C")
    try:
        m2t = float(m2t) if m2t else None
    except (TypeError, ValueError):
        m2t = None
    area_ha = (m2t / 10000) if m2t else None
    area_sqm = m2t

    listing_type = "rent" if (rec.get("tipoOperacion") or "").lower() in ("renta", "alquiler") else "sale"

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": f"c21_{sid}",
            "source": "century21",
            "source_id": sid,
            "source_url": source_url,
            "source_platform": "century21.com.py",
            "scraped_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "title": rec.get("encabezado") or "Propiedad",
            "city": rec.get("municipio"),
            "state_province": rec.get("estado"),
            "country": rec.get("pais") or "Paraguay",
            "address": rec.get("calle"),
            "listing_type": listing_type,
            "property_type": _map_property_type(rec.get("subTipoPropiedad") or rec.get("tipoPropiedad")),
            "currency": moneda,
            "price_pyg": price_pyg,
            "price_usd": round(price_usd, 2),
            "area_sqm": area_sqm,
            "area_ha": round(area_ha, 4) if area_ha else None,
            "bedrooms": _safe_int(rec.get("recamaras")),
            "bathrooms": _safe_int(rec.get("banios")),
            "parking_spaces": _safe_int(rec.get("estacionamientos")),
            "images": [f["large"] for f in (rec.get("fotosArray") or []) if f.get("large")][:8],
            "description": (rec.get("descripcion") or "")[:1500],
            "lat": lat,
            "lon": lon,
        },
    }


def scrape(deptos: list[str], max_pages_per_depto: int, sleep_s: float) -> list[dict]:
    """Index-based scrape: each `REP_LOG_APP_PROPS` blob carries the
    current page's full listing set with lat/lon inlined.  No need for
    detail-page fetches."""
    feats: list[dict] = []
    seen_ids: set[str] = set()
    for depto in deptos:
        slug = DEPTO_SLUG.get(depto)
        if not slug:
            print(f"  skip unknown depto: {depto}", file=sys.stderr)
            continue
        for page in range(1, max_pages_per_depto + 1):
            url = f"https://century21.com.py/busqueda/operacion_venta/en-estado_{slug}"
            if page > 1:
                url += f"?page={page}"
            try:
                idx_html = _fetch(url)
            except Exception as exc:
                print(f"  warn {url}: {exc}", file=sys.stderr)
                break
            records = _extract_index_data(idx_html)
            if not records:
                print(f"  {depto} page {page}: no records (end of results?)", file=sys.stderr)
                break
            page_kept = 0
            for rec in records:
                feat = _parse_record(rec)
                if feat is None:
                    continue
                sid = feat["properties"]["source_id"]
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                feats.append(feat)
                page_kept += 1
            print(f"  {depto} page {page}: {len(records)} records → kept {page_kept}")
            time.sleep(sleep_s)
    return feats


def scrape_sitemap() -> list[dict]:
    """Scrape all 515 PY listings from the sitemap.  Each /propiedad/<id>_<slug>
    page inlines the record into REP_LOG_APP_PROPS.propiedades — same shape as
    the universal page, but it returns ONE high-fidelity record per page.

    Note: at 1.5s sleep per request, scraping 515 listings takes ~13 minutes.
    That's well within budget for a daily cron.
    """
    feats: list[dict] = []
    seen_ids: set[str] = set()
    try:
        sitemap = _fetch("https://century21.com.py/sitemap.xml")
    except Exception as exc:
        print(f"  warn sitemap: {exc}", file=sys.stderr)
        return feats
    if not sitemap:
        return feats
    urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    urls = [u for u in urls if '/propiedad/' in u]
    print(f"  sitemap: {len(urls)} property URLs")
    import time
    for i, url in enumerate(urls):
        try:
            html = _fetch(url, timeout=15)
        except Exception as exc:
            print(f"  warn {url}: {exc}", file=sys.stderr)
            continue
        if not html or len(html) < 5000:
            continue
        records = _extract_index_data(html)
        for rec in records:
            feat = _parse_record(rec)
            if feat is None:
                continue
            sid = feat["properties"]["source_id"]
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            feats.append(feat)
        if (i + 1) % 20 == 0:
            print(f"  progress: {i+1}/{len(urls)} → {len(feats)} unique listings")
        time.sleep(0.7)
    return feats


def scrape_universal() -> list[dict]:
    """Hit the country-scoped search pages for all listing operations.
    Century21.com.py is a global network's Latin-American portal — the
    *universal* /v/resultados page serves non-PY records (e.g. Costa Rica).
    Country-scoped URLs (`/busqueda/operacion_<op>/en-pais_paraguay`)
    constrain results to PY explicitly.
    """
    feats: list[dict] = []
    seen_ids: set[str] = set()
    for op in ("venta", "renta", "pozo", "condominio"):
        url = f"https://century21.com.py/busqueda/operacion_{op}/en-pais_paraguay"
        try:
            html = _fetch(url)
        except Exception as exc:
            print(f"  warn {url}: {exc}", file=sys.stderr)
            continue
        if not html or len(html) < 5000:
            continue
        records = _extract_index_data(html)
        kept = 0
        for rec in records:
            feat = _parse_record(rec)
            if feat is None:
                continue
            sid = feat["properties"]["source_id"]
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            feats.append(feat)
            kept += 1
        print(f"  /{op}: {len(records)} records → kept {kept}")
    return feats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["paginated", "universal", "sitemap"], default="paginated",
                    help="paginated = iterate estados; universal = single GET on /v/resultados; "
                         "sitemap = scrape every /propiedad/<id>_<slug> from the sitemap (slowest, most thorough)")
    ap.add_argument("--deptos", nargs="+",
                    default=list(DEPTO_SLUG.keys()),
                    help="PY deptos to scrape (paginated mode only)")
    ap.add_argument("--max-pages-per-depto", type=int, default=5)
    ap.add_argument("--sleep", type=float, default=0.7)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--no-fetch", action="store_true",
                    help="skip network and emit an empty envelope (CI)")
    args = ap.parse_args(argv)

    if args.no_fetch:
        feats = []
    else:
        if args.mode == "universal":
            feats = scrape_universal()
            print(f"  universal mode: {len(feats)} records")
        elif args.mode == "sitemap":
            feats = scrape_sitemap()
            print(f"  sitemap mode: {len(feats)} records")
        else:
            feats = scrape(args.deptos, args.max_pages_per_depto, args.sleep)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"century21_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK century21: {len(feats)} listings → {out}")


if __name__ == "__main__":
    main()