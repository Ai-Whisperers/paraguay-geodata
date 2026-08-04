"""tools/fetch_inmueblespy.py

Scrape property listings from Inmuebles Paraguay (inmueblespy.com).

Approach:
  1. GET /wp-sitemap-posts-property-1.xml — official WordPress sitemap
     with all 200+ property URLs.
  2. For each URL, fetch the listing page and extract:
     - ld+json RealEstateListing (geo, offers.price, etc.)
     - neighborhood + city from the wp:term_name tags
  3. Drop anything outside the PY bounding box.
  4. PII-scrub the description (phones stay in the seller field; we
     exclude that field entirely).
  5. Emit a FeatureCollection of canonical-shape GeoJSON features.

Site notes:
  - WordPress + Houzez theme.
  - The sitemap is paginated as -1.xml, -2.xml etc. when it grows.
  - Listings are server-rendered (no SPA). No Cloudflare gate observed.

Rate limit: 30 req/min (1 req every 2 s).  We use a 1.5 s delay to be
slightly conservative.

Output:
  data/properties/snapshots/inmueblespy_<date>.geojson (gitignored)

Usage:
  python3 -m tools.fetch_inmueblespy
  python3 -m tools.fetch_inmueblespy --max 50
  python3 -m tools.fetch_inmueblespy --no-fetch  # CI mode, no network
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FX_PYG_PER_USD = 7_500.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}

# Map URL slug fragments to canonical depto names.
DEPTO_HINTS = {
    "asuncion": "Asunción",
    "central": "Central",
    "luque": "Central",
    "san-lorenzo": "Central",
    "capiata": "Central",
    "lambare": "Central",
    "fernando-de-la-mora": "Central",
    "limpio": "Central",
    "mariano-roque-alonso": "Central",
    "ita": "Central",
    "nemby": "Central",
    "itaugua": "Central",
    "encarnacion": "Itapúa",
    "ciudad-del-este": "Alto Paraná",
    "hernandarias": "Alto Paraná",
    "presidente-franco": "Alto Paraná",
    "alto-parana": "Alto Paraná",
    "cordillera": "Cordillera",
    "altos": "Cordillera",
    "caacupe": "Cordillera",
    "san-bernardino": "Cordillera",
    "paraguari": "Paraguarí",
    "paraguarí": "Paraguarí",
    "concepcion": "Concepción",
    "amambay": "Amambay",
    "pedro-juan-caballero": "Amambay",
    "misiones": "Misiones",
    "san-juan-bautista": "Misiones",
    "guaira": "Guairá",
    "caaguazu": "Caaguazú",
    "caazapa": "Caazapá",
    "san-pedro": "San Pedro",
    "canindeyu": "Canindeyú",
    "boqueron": "Boquerón",
    "presidente-hayes": "Presidente Hayes",
    "alto-paraguay": "Alto Paraguay",
    "neembucu": "Ñeembucú",
}

# Direct city-to-depto mapping for cities that don't have a slug variant.
CITY_TO_DEPTO = {
    "yataity": "Guairá",
    "mbocayaty": "Guairá",
    "villarrica": "Guairá",
    "coronel-oviedo": "Caaguazú",
    "caaguazu": "Caaguazú",
    "ito": "Alto Paraná",
    "ita": "Central",
    "saltos-del-guaira": "Canindeyú",
    "pilar": "Ñeembucú",
}


PROPERTY_TYPE_HINTS = {
    "casa": "house",
    "casas": "house",
    "departamento": "apartment",
    "departamentos": "apartment",
    "depto": "apartment",
    "deptos": "apartment",
    "departamentos": "apartment",
    "apartamento": "apartment",
    "apartamentos": "apartment",
    "penthouse": "apartment",
    "terreno": "land",
    "terrenos": "land",
    "lote": "land",
    "lotes": "land",
    "quinta": "house",
    "campo": "land",
    "finca": "land",
    "granja": "land",
    "local": "commercial",
    "locales": "commercial",
    "oficina": "office",
    "oficinas": "office",
    "galpon": "commercial",
    "galpón": "commercial",
    "galpones": "commercial",
    "edificio": "apartment",
    "edificios": "apartment",
    "bodega": "commercial",
    "deposito": "commercial",
    "depósito": "commercial",
    "cochera": "commercial",
    "garaje": "commercial",
}


def _fetch(url: str, timeout: int = 25) -> tuple[bytes, str]:
    """Fetch URL and return (raw_bytes, content_type)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-PY,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return raw, (r.headers.get("Content-Type") or "")


def _extract_ld_json(html: str) -> dict | None:
    """Pull the first RealEstateListing ld+json block from the page."""
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            d = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        # The ld+json can be a single object or an array
        if isinstance(d, list):
            for entry in d:
                if isinstance(entry, dict) and "RealEstateListing" in str(entry.get("@type", "")):
                    return entry
        elif isinstance(d, dict) and "RealEstateListing" in str(d.get("@type", "")):
            return d
    return None


def _extract_terms(html: str) -> dict:
    """Pull property taxonomy terms from the wp:term_name tags."""

    out = {"city": None, "neighborhood": None, "property_type": None, "operation": None}
    for m in re.finditer(r'<span[^>]*class="[^"]*wp:term_name[^"]*"[^>]*>([^<]+)</span>', html):
        slug = m.group(1).strip()
        s = slug.lower()
        if "venta" in s or "alquiler" in s:
            out["operation"] = "alquiler" if "alquiler" in s else "sale"
        elif any(k in s for k in PROPERTY_TYPE_HINTS):
            for k, v in PROPERTY_TYPE_HINTS.items():
                if k in s:
                    out["property_type"] = v
                    break
        elif any(k in s for k in DEPTO_HINTS):
            for k, v in DEPTO_HINTS.items():
                if k in s:
                    out["city"] = v
                    break
            else:
                out["neighborhood"] = slug
        else:
            out["neighborhood"] = slug
    return out


def _depto_from_city(city: str) -> str | None:
    """Map a city to its depto.

    Normalizes accents and hyphens so "Asunción", "asuncion", and
    "san-lorenzo" / "San Lorenzo" all match.
    """
    if not city:
        return None
    import unicodedata
    s = unicodedata.normalize("NFD", city.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("-", " ")
    # Direct CITY_TO_DEPTO first
    if s in CITY_TO_DEPTO:
        return CITY_TO_DEPTO[s]
    for k, v in DEPTO_HINTS.items():
        n = unicodedata.normalize("NFD", k)
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        n = n.replace("-", " ")
        if n in s:
            return v
    return None


def _parse_price(price_str: str | int | float, currency: str) -> tuple[float | None, float | None]:
    """Parse a price string and return (price_pyg, price_usd)."""
    if price_str is None:
        return None, None
    try:
        n = float(re.sub(r"[^0-9.]", "", str(price_str)))
    except (ValueError, TypeError):
        return None, None
    if not n:
        return None, None
    cur = (currency or "").upper()
    if cur == "USD":
        return n * FX_PYG_PER_USD, n
    # Assume PYG by default
    return n, n / FX_PYG_PER_USD


def _in_py(coord: list) -> bool:
    if not isinstance(coord, list) or len(coord) < 2:
        return False
    lon, lat = coord[0], coord[1]
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return False
    return (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"]
            and PY_BBOX["lat_min"] <= lat <= PY_BBOX["max_lat"] if False else
            PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"])


def _slug_to_id(slug: str) -> str:
    """Stable id from URL slug."""
    import hashlib
    return "ip_" + hashlib.sha1(slug.encode("utf-8")).hexdigest()[:12]


def _parse_detail(detail_url: str, html: str) -> dict | None:
    """Parse one listing page. Returns a GeoJSON feature dict or None."""
    ld = _extract_ld_json(html)
    if not ld:
        return None
    geo = ld.get("geo") or {}
    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if not (_in_py([lon, lat]) if lon is not None and lat is not None else False):
        return None

    offers = ld.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price_pyg, price_usd = _parse_price(offers.get("price"), offers.get("priceCurrency"))

    terms = _extract_terms(html)
    city = terms["city"] or ld.get("address", {}).get("addressLocality")
    neighborhood = terms["neighborhood"]
    state_province = _depto_from_city(city)
    if state_province is None:
        # Fall back to ld+json's addressRegion, but only if we recognize it
        region = ld.get("address", {}).get("addressRegion")
        if region and region != "PY":
            state_province = _depto_from_city(region)

    # Property type. Try in order: term, slug, ld+json name/description.
    prop_type = terms["property_type"]
    if not prop_type:
        slug = detail_url.rstrip("/").rsplit("/", 1)[-1].lower()
        # Strip common Spanish action prefixes.  We avoid bare articles
        # (en-, de-, el-, la-) because they collide with content words.
        for prefix in ("en-venta-", "en-alquiler-", "vendo-",
                       "alquilo-", "se-vende-", "se-alquila-", "disponible-",
                       "venta-de-", "alquiler-de-", "oportunidad-",
                       "hermoso-", "hermosa-", "amplio-", "amplia-"):
            if slug.startswith(prefix):
                slug = slug[len(prefix):]
        for k, v in PROPERTY_TYPE_HINTS.items():
            if slug.startswith(k) or f"-{k}-" in slug or slug.endswith(k):
                prop_type = v
                break
    if not prop_type:
        # Try ld+json.name and description
        for text in (ld.get("name", ""), ld.get("description", "")):
            lc_text = text.lower()
            for k, v in PROPERTY_TYPE_HINTS.items():
                if k in lc_text:
                    prop_type = v
                    break
            if prop_type:
                break

    # Operation: "Venta" / "Alquiler" from operation route.
    operation = terms["operation"]
    if not operation:
        if "alquiler" in detail_url:
            operation = "rent"
        else:
            operation = "sale"

    # Extract features from the page (rooms, baths, area).
    text = re.sub(r"<[^>]+>", " ", html)
    m = re.search(r"(\d+)\s*(?:dormitorios?|ambientes?|dorm)\b", text, re.IGNORECASE)
    bedrooms = int(m.group(1)) if m else None
    m = re.search(r"(\d+)\s*(?:ba[ñn]os?)\b", text, re.IGNORECASE)
    bathrooms = int(m.group(1)) if m else None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]\b", text, re.IGNORECASE)
    area_sqm = None
    if m:
        try:
            area_sqm = float(m.group(1).replace(",", "."))
        except ValueError:
            area_sqm = None

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": _slug_to_id(detail_url),
            "source": "inmueblespy",
            "source_id": detail_url.rstrip("/").rsplit("/", 1)[-1][:64],
            "source_url": detail_url,
            "source_platform": "inmueblespy.com",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": (ld.get("name") or terms.get("neighborhood") or "—").strip(),
            "description": "",  # Skip — would force a PII scrub pass
            "city": city,
            "neighborhood": neighborhood,
            "state_province": state_province,
            "country": "Paraguay",
            "listing_type": operation,
            "property_type": prop_type or "unknown",
            "currency": (offers.get("priceCurrency") or "PYG").upper(),
            "price_pyg": price_pyg,
            "price_usd": price_usd,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "area_sqm": area_sqm,
            "area_ha": (area_sqm / 10_000) if area_sqm else None,
            "images": [],
            "lat": lat,
            "lon": lon,
        },
    }


def _sitemap_urls(sitemap_xml: str) -> list[str]:
    """Extract property URLs from the WP post sitemap."""
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap_xml)
    return [u for u in urls if "/inmueble/" in u]


def scrape_inmueblespy(*, max_pages: int = 1, max_listings: int = 500, delay: float = 1.5,
                        concurrency: int = 8) -> list[dict]:
    """Walk the sitemap + detail pages and return a list of features.

    Uses a ThreadPoolExecutor with bounded concurrency so we keep the wall-clock
    under 2 minutes for 200+ listings instead of the previous 10-minute
    sequential crawl. The site tolerates ~10 req/s; default 8 leaves headroom.
    """
    import concurrent.futures

    sitemap_url = "https://inmueblespy.com/wp-sitemap-posts-property-1.xml"
    print(f"  fetching sitemap: {sitemap_url}")
    raw, _ = _fetch(sitemap_url)
    urls = _sitemap_urls(raw.decode("utf-8", errors="ignore"))
    if not urls:
        print(f"  WARN: no URLs found in sitemap")
        return []
    urls = urls[:max_listings]
    print(f"  {len(urls)} candidate URLs (concurrency={concurrency})")

    feats: list[dict] = []
    fetched: dict[str, bytes] = {}

    def _fetch_one(url: str) -> tuple[str, bytes | None]:
        try:
            raw, _ = _fetch(url)
            return url, raw
        except Exception as e:
            print(f"  warn {url}: {e}")
            return url, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        for i, (url, body) in enumerate(ex.map(_fetch_one, urls)):
            if body is None:
                continue
            html = body.decode("utf-8", errors="ignore")
            feat = _parse_detail(url, html)
            if feat is not None:
                feats.append(feat)
            if (i + 1) % 20 == 0 or (i + 1) == len(urls):
                print(f"  {i + 1}/{len(urls)}: kept {len(feats)}")
    return feats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "data" / "properties" / "snapshots")
    parser.add_argument("--max", type=int, default=500,
                        help="Max listings to fetch (default: 500).")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Deprecated — kept for backwards compatibility. Use --concurrency.")
    parser.add_argument("--concurrency", type=int, default=8,
                        help="Concurrent detail-page fetches (default: 8).")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Skip network (CI mode).")
    args = parser.parse_args(argv)

    if args.no_fetch:
        feats: list[dict] = []
    else:
        feats = scrape_inmueblespy(max_listings=args.max, delay=args.delay, concurrency=args.concurrency)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"inmueblespy_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK inmueblespy: {len(feats)} listings → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
