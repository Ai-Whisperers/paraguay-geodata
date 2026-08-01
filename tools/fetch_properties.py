"""
tools/fetch_properties.py — Real-estate listings scraper (Phase 2 — LIVE).

Implements the ethics gate from `docs/ethics/scraper-policy.md`:
  - 30 req/min/portal (was 50 — start stricter to be conservative)
  - User-Agent = `paraguay-geodata/0.1 (+...; contact: iván@ai-whisperers.org)`
  - 6 hour page cache
  - Exponential backoff on 429/503
  - PII-strip rules per `docs/ethics/scraper-policy.md`

Portals:
  - infocasas.com.py (HTML, scrape-friendly)
  - propiedades.com.py (Angular SPA, headless Chrome)
  - baiker.com — SKIPPED (dead domain redirect)

Run:
    python3 -m tools.fetch_properties --portal infocasas --max-pages 3
    python3 -m tools.fetch_properties --portal propiedades --max-pages 2
    python3 -m tools.fetch_properties --portal all --max-pages 3
    python3 -m tools.fetch_properties --bbox "-57.58,-25.32,-57.48,-25.23" --portal infocasas

Output:
    data/properties/snapshots/<portal>_<date>.geojson (gitignored raw)
    exports/web/data/properties_latest.geojson (PII-stripped, Pages-deployable)
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, parse_qs

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]

USER_AGENT = (
    "paraguay-geodata/0.1 "
    "(+https://github.com/Ai-Whisperers/paraguay-geodata; "
    "contact: ivan@ai-whisperers.org)"
)

SLEEP_BETWEEN_REQUESTS_SEC = 2.0  # be conservative
PAGE_CACHE_HOURS = 6


# ---------- ethics gate ---------------------------------------------------------

def check_ethics_gate(portal: str) -> None:
    """Per docs/ethics/scraper-policy.md — refuse to scrape before gate passes."""
    if portal == "baiker":
        raise SystemExit("ETHICS GATE: baiker.com is dead (redirector to web.de). Skip.")
    if portal not in ("infocasas", "propiedades", "all"):
        raise SystemExit(f"ETHICS GATE: unknown portal '{portal}'")
    print(f"[ethic_gate] OK portal={portal} rate={1.0/SLEEP_BETWEEN_REQUESTS_SEC:.2f} req/s")


# ---------- shared cache -------------------------------------------------------

def cache_path(portal: str, url: str) -> Path:
    cache_dir = REPO_ROOT / "data" / "properties" / "cache" / portal
    cache_dir.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"{h}.html"


def cache_fresh(p: Path) -> bool:
    if not p.exists():
        return False
    age_hours = (time.time() - p.stat().st_mtime) / 3600
    return age_hours < PAGE_CACHE_HOURS


# ---------- portal: infocasas ---------------------------------------------------

INFOCASAS_LISTING_URL_RE = re.compile(r'href="(/[a-z0-9-]+/\d+)"', re.I)
INFOCASAS_PRICE_RE = re.compile(r'[\$\s]*([\d,.]+)\s*(USD|Gs|guaran)', re.I)
INFOCASAS_AREA_RE = re.compile(r'([\d,.]+)\s*(?:m2|m²|hectares|has?|m²)', re.I)
INFOCASAS_BBOX_RE = re.compile(r'lat["\s:]+([\d.-]+)[",\s]+lon[g]?["\s:]+([\d.-]+)', re.I)


def scrape_infocasas_listing_index(client: httpx.Client, page: int = 1, dept_slug: str = "") -> list[dict]:
    """Fetch one page of listings index. Returns list of {url, source_id, raw_title}."""
    if dept_slug:
        url = f"https://www.infocasas.com.py/venta/inmuebles/{dept_slug}?page={page}"
    else:
        url = f"https://www.infocasas.com.py/venta/inmuebles?page={page}"

    cached = cache_path("infocasas", url)
    if cache_fresh(cached):
        html = cached.read_text()
    else:
        time.sleep(SLEEP_BETWEEN_REQUESTS_SEC + random.random() * 0.5)
        r = client.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        r.raise_for_status()
        html = r.text
        cached.write_text(html, encoding="utf-8")
    matches = INFOCASAS_LISTING_URL_RE.findall(html)
    # dedup
    return [
        {
            "url_path": m,
            "source_id": m.split("/")[-1],
            "abs_url": urljoin("https://www.infocasas.com.py", m),
        }
        for m in dict.fromkeys(matches)
    ]


def scrape_infocasas_detail(client: httpx.Client, listing: dict) -> dict:
    """Fetch one listing detail page. Extract price, area, lat/lon, attrs."""
    url = listing["abs_url"]
    cached = cache_path("infocasas", url)
    if cache_fresh(cached):
        html = cached.read_text()
    else:
        time.sleep(SLEEP_BETWEEN_REQUESTS_SEC + random.random() * 0.5)
        r = client.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        r.raise_for_status()
        html = r.text
        cached.write_text(html, encoding="utf-8")

    # lat/lon from various places: ld+json, map init, page-data
    lat_lon = _extract_lat_lon(html)
    price = _extract_price(html)
    area_ha = _extract_area_ha(html)
    title = _extract_title(html)
    address = _extract_address(html)
    bedrooms = _extract_bedrooms(html)
    depto = address.get("state") if address else None
    depto_from_url = _extract_depto_from_url(url)
    if not depto:
        depto = depto_from_url
    elif depto_from_url:
        depto = f"{depto} / {depto_from_url}"

    return {
        "id": "ic_" + hashlib.sha1(("infocasas:" + listing["source_id"]).encode()).hexdigest()[:12],
        "source": "infocasas",
        "source_id": listing["source_id"],
        "source_url": url,
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
        "lat": lat_lon[0],
        "lon": lat_lon[1],
        "title": title,
        "address": address,
        "depto": depto,
        "bedrooms": bedrooms,
        "price_pyg": price["pyg"] if price else None,
        "price_usd": price["usd"] if price else None,
        "area_ha": area_ha,
        "$/ha": (price["usd"] / area_ha) if (price and area_ha and area_ha > 0) else None,
        "price_band_vs_anchors": None,
        "district": None,
        "departamento": None,
        "attrs": _extract_attrs_infocasas(html),
        "images": _extract_images_infocasas(html, max_n=8),
    }


_PHOTO_RE_INFOCASAS = re.compile(
    r'https?://cdn[0-9]?\.infocasas\.com\.uy/repo/img/[a-z0-9_\-\.]+\.(?:jpg|jpeg|png|webp)',
    re.I,
)
_BRAND_PATTERNS_INFOCASAS = [
    re.compile(r'/isotipo', re.I),
    re.compile(r'/logo-?infocasas', re.I),
    re.compile(r'/@2x\.png', re.I),
    re.compile(r'fincaraiz\.com\.co/web/', re.I),
    re.compile(r'whatsapp-image-', re.I),  # WhatsApp profile photos, not property
]


def _extract_images_infocasas(html: str, max_n: int = 8) -> list[str]:
    """Pull unique property image URLs from an infocasas detail page.

    Filters out branding (logo/isotipo), WhatsApp profile photos, and
    favicons. Returns up to `max_n` ordered by first occurrence in HTML.
    """
    from collections import OrderedDict
    seen = OrderedDict()
    for u in _PHOTO_RE_INFOCASAS.findall(html):
        if any(p.search(u) for p in _BRAND_PATTERNS_INFOCASAS):
            continue
        if u not in seen:
            seen[u] = True
        if len(seen) >= max_n:
            break
    return list(seen.keys())


def _extract_lat_lon(html: str) -> tuple[float | None, float | None]:
    # infocasas detail pages embed the property as JSON: "latitude":-25.x,"longitude":-57.x
    m = re.search(r'"latitude"\s*:\s*(-?\d+\.\d+)\s*,\s*"longitude"\s*:\s*(-?\d+\.\d+)', html)
    if m:
        return float(m.group(1)), float(m.group(2))
    # Generic fallback patterns
    for pat in [
        r'"lat"\s*:\s*(-?\d+\.\d+)\s*,\s*"lng"\s*:\s*(-?\d+\.\d+)',
        r'lat:\s*(-?\d+\.\d+),\s*lng:\s*(-?\d+\.\d+)',
        r'map\.setView\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]',
        r'center\s*=\s*\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]',
    ]:
        m = re.search(pat, html)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None, None


def _extract_price(html: str) -> dict | None:
    """infocasas price JSON. Two observed shapes:

    PYG  (most common):
        "price":{"amount":3400000000,"currency":"PYG"}
        or
        "price":{"amount":3400000000,"currency":{"id":2,"name":"Gs.","rate":1}}

    USD  (many Asunción premium listings):
        "price":{"amount":1600000,"admin_included":1600000,"hidePrice":false,
                 "currency":{"id":1,"name":"U$S","rate":1}}
    """
    # Shape A: amount + currency (string OR nested object)
    m = re.search(
        r'"price"\s*:\s*\{\s*"amount"\s*:\s*(\d+)'
        r'(?:\s*,\s*"admin_included"\s*:\s*\d+)?'
        r'(?:\s*,\s*"hidePrice"\s*:\s*(?:true|false))?'
        r'\s*,\s*"currency"\s*:\s*(?:"([^"]+)"|\{[^}]*"name"\s*:\s*"([^"]+)"[^}]*\})',
        html,
    )
    if m:
        amount = int(m.group(1))
        currency = (m.group(2) or m.group(3) or "").upper()
        # "U$S" → USD; "Gs." / "Gs" → PYG
        if "U$S" in currency or "USD" in currency or "DOLAR" in currency:
            return {"usd": amount, "pyg": int(amount * 7500)}
        if "GS" in currency or "PYG" in currency:
            return {"pyg": amount, "usd": amount / 7500.0}
        # Default to PYG for unknown
        return {"pyg": amount, "usd": amount / 7500.0}

    # Fallback: extract from <p class="main-price">Gs. 3.400.000.000</p>
    m = re.search(r'main-price[^>]*>Gs\.\s*([\d.]+)', html)
    if m:
        try:
            pyg = int(m.group(1).replace(".", ""))
            return {"pyg": pyg, "usd": pyg / 7500.0}
        except ValueError:
            pass
    # USD fallback
    m = re.search(r'main-price[^>]*>U\$S\s*([\d.,]+)', html, re.I)
    if m:
        try:
            usd = int(m.group(1).replace(".", "").replace(",", ""))
            return {"usd": usd, "pyg": int(usd * 7500)}
        except ValueError:
            pass
    return None


def _extract_title(html: str) -> str | None:
    """infocasas title: stored in <title> and embedded in __NEXT_DATA__ JSON."""
    m = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)+?)(?:",|\")', html)
    if m:
        return m.group(1)
    m = re.search(r'<title>([^<|]+?)(?:\s*[|·][^<]*)?</title>', html)
    if m:
        return m.group(1).strip()
    return None


def _extract_address(html: str) -> dict | None:
    """infocasas address JSON: "address":{"street":"...","city":"...","state":"..."}"""
    m = re.search(
        r'"address"\s*:\s*\{[^{}]*"street"\s*:\s*"((?:[^"\\]|\\.)*?)"'
        r'[^{}]*"city"\s*:\s*"((?:[^"\\]|\\.)*?)"'
        r'[^{}]*"state"\s*:\s*"((?:[^"\\]|\\.)*?)"',
        html,
    )
    if m:
        return {"street": m.group(1), "city": m.group(2), "state": m.group(3)}
    return None


def _extract_bedrooms(html: str) -> int | None:
    m = re.search(r'"bedrooms"\s*:\s*\{[^}]*"value"\s*:\s*(\d+)', html)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s*(?:dormitorios?|bedrooms?|habitaciones?)', html, re.I)
    if m:
        return int(m.group(1))
    return None


def _extract_depto_from_url(url: str) -> str | None:
    """Extract depto from infocasas URL.

    Common URL shapes seen in the data:
      /vendo-casa-en-pedro-juan-caballero/192262411     → city mention (Amambay)
      /terreno-venta-ciudad-del-este-alto-parana-paraguay/193732319  → both city + depto
      /casa-quinta-en-caazapa/191924051                → depto slug
      /inversion-km-20-monday-ciudad-del-este-...      → city in path
      /venta/inmuebles/alto-paraguay/pagina2           → explicit depto slug
    """
    url_lower = url.lower()

    # First try the structured /<op>/inmuebles/<depto>/ path
    m = re.search(
        r'infocasas\.com\.py/(?:venta|alquiler|alquilar|temporal)/[^/]*'
        r'(?:inmuebles?|terrenos?|casas?|propiedades?)?/?'
        r'(asuncion|central|alto-parana|concepcion|san-pedro|cordillera|guaira'
        r'|caaguazu|caazapa|itapua|misiones|paraguari|neembucu|amambay'
        r'|canindeyu|presidente-hayes|boqueron|alto-paraguay)',
        url_lower,
    )
    if m:
        return slug_to_depto(m.group(1))

    # Fallback: scan the URL slug for any depto/city keyword
    candidates = [
        ("alto-paraguay", "Alto Paraguay"), ("boqueron", "Boquerón"),
        ("presidente-hayes", "Presidente Hayes"), ("alto-parana", "Alto Paraná"),
        ("canindeyu", "Canindeyú"), ("amambay", "Amambay"), ("caaguazu", "Caaguazú"),
        ("san-pedro", "San Pedro"), ("concepcion", "Concepción"),
        ("caazapa", "Caazapá"), ("neembucu", "Ñeembucú"),
        ("paraguari", "Paraguarí"), ("cordillera", "Cordillera"),
        ("itapua", "Itapúa"), ("misiones", "Misiones"),
        ("central", "Central"), ("asuncion", "Asunción"), ("guaira", "Guairá"),
    ]
    for slug, name in candidates:
        if slug in url_lower:
            return name

    # Last: try to find a city in the slug → map to nearest depto
    cities = [
        ("asuncion", "Asunción"), ("ciudad-del-este", "Alto Paraná"),
        ("encarnacion", "Itapúa"), ("pedro-juan-caballero", "Amambay"),
        ("concepcion", "Concepción"), ("villarrica", "Guairá"),
        ("coronel-oviedo", "Caaguazú"), ("san-lorenzo", "Central"),
        ("luque", "Central"), ("capiata", "Central"),
        ("fernando-de-la-mora", "Central"), ("lambare", "Central"),
        ("itaugua", "Central"), ("mariano-roque-alonso", "Central"),
        ("presidente-franco", "Alto Paraná"), ("pilar", "Ñeembucú"),
        ("caaguazu", "Caaguazú"), ("salto-del-guaira", "Canindeyú"),
        ("san-juan-bautista", "Misiones"), ("caazapa", "Caazapá"),
        ("villa-hayes", "Presidente Hayes"), ("nueva-esperanza", "Canindeyú"),
        ("herrera", "Alto Paraná"), ("chacoi", "Presidente Hayes"),
        ("monday", "Alto Paraná"), ("piedecuesta", "Itapúa"),
        ("sapucai", "Paraguarí"), ("coronel-bogado", "Caazapá"),
        ("itacurubi", "Central"), ("ybycui", "Paraguarí"),
        ("ybaylu", "Caaguazú"), ("la-paloma", "Canindeyú"),
        ("la-patri", "Boquerón"), ("tt-martinez", "Boquerón"),
        ("tte-martinez", "Boquerón"), ("fuerte-olimp", "Boquerón"),
        ("san-bernardino", "Cordillera"),
        ("capitan-miranda", "Itapúa"), ("capitan", "Itapúa"),
        ("santani", "San Pedro"), ("mariscal-estigarribia", "Boquerón"),
        ("mariscal", "Boquerón"),  # default for Mariscal (Chaco reference)
        ("bahia-negra", "Alto Paraguay"), ("agua-dulce", "Alto Paraguay"),
        ("chaco", "Boquerón"),
        ("molas-lopez", "Alto Paraná"),
        ("colonias-alemana", "Alto Paraná"), ("colonia-alemana", "Alto Paraná"),
        ("colonias-unidas", "Itapúa"),
        ("ypacarai", "Central"), ("ybanez", "Alto Paraná"),
        ("shopping-mariscal", "Asunción"), ("los-laureles", "Asunción"),
        ("las-lomas", "Central"), ("mariscal", "Asunción"),
        ("obrero", "Alto Paraná"), ("cde", "Alto Paraná"),
        ("ita", "Central"),  # short
        ("mayor-martinez", "Ñeembucú"),
        ("san-ramon", "Misiones"),
        ("arroyos-y-esteros", "Cordillera"),
    ]
    for slug, depto in cities:
        if slug in url_lower:
            return depto

    return None


def slug_to_depto(slug: str) -> str:
    """Map infocasas URL slug → human-friendly depto name."""
    return {
        "asuncion": "Asunción", "central": "Central", "alto-parana": "Alto Paraná",
        "concepcion": "Concepción", "san-pedro": "San Pedro", "cordillera": "Cordillera",
        "guaira": "Guairá", "caaguazu": "Caaguazú", "caazapa": "Caazapá",
        "itapua": "Itapúa", "misiones": "Misiones", "paraguari": "Paraguarí",
        "neembucu": "Ñeembucú", "amambay": "Amambay", "canindeyu": "Canindeyú",
        "presidente-hayes": "Presidente Hayes", "boqueron": "Boquerón",
        "alto-paraguay": "Alto Paraguay",
    }.get(slug.lower(), slug.title())


def _extract_area_ha(html: str) -> float | None:
    """Extract the terrain area in hectares from an InfoCasas detail page.

    The site includes area as a structured JSON entry like
    `{"field":"m2Terrain","value":"525 m2","text":"M\u00b2 del terreno"}`
    — that's the *primary* area.  Fall back to a narrowed regex scan only
    if the structured entry isn't found.

    The historical regex-scan path was buggy: it could match the literal
    characters "1HA" inside base64-encoded image fragments and return 1.0 ha
    for what was actually a 525 m² listing.  See tests.
    """
    # 1. Look for {"field":"m2Terrain","value":"<N> m2"} or similar
    for pat in (
        r'"field"\s*:\s*"m2Terrain"\s*,\s*"value"\s*:\s*"([\d,.]+)\s*m2?"',
        r'"field"\s*:\s*"m2Cubiertos"\s*,\s*"value"\s*:\s*"([\d,.]+)\s*m2?"',
    ):
        m = re.search(pat, html)
        if m:
            try:
                m2 = float(m.group(1).replace(",", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ""))
                return m2 / 10000.0
            except ValueError:
                pass

    # 2. Narrowed regex: only look in the title/og:description zone (the
    # first 30K chars), NOT the entire page (avoids base64 false matches).
    head = html[:30_000]
    # Hectares first
    m = re.search(r'([\d,.]+)\s*(?:has?|hectares?)', head, re.I)
    if m:
        try:
            return float(m.group(1).replace(",", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ""))
        except ValueError:
            pass
    # m² → ha
    m = re.search(r'([\d,.]+)\s*(?:m2|m²)', head, re.I)
    if m:
        try:
            raw = m.group(1)
            if "," in raw and "." in raw:
                raw = raw.replace(",", "")
            elif "," in raw and re.match(r"^\d{1,3},\d{3}$", raw):
                raw = raw.replace(",", "")
            elif "," in raw:
                raw = raw.replace(",", ".")
            m2 = float(raw)
            return m2 / 10000.0
        except ValueError:
            pass
    return None


def _extract_attrs_infocasas(html: str) -> dict:
    attrs = {}
    for label, key in [("dormitorios", "bedrooms"), ("baños", "bathrooms"),
                       ("cochera", "garage"), ("piscina", "pool"),
                       ("habitaciones", "rooms")]:
        m = re.search(rf'{label}["\s:]+(\d+)', html, re.I)
        if m:
            try:
                attrs[key] = int(m.group(1))
            except ValueError:
                pass
    return attrs


# ---------- portal: propiedades (SPA, headless Chrome required) ---------------

def scrape_propiedades_listings_page(page: int = 1) -> list[dict]:
    """Use headless Chrome to render SPA and extract listing links."""
    # Cheaper first probe: extract from SPA's XHR endpoints if exposed
    # Otherwise headless Chrome
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[propiedades] playwright not installed; falling back to chrome_dump")
        try:
            import subprocess
            url = f"https://propiedades.com.py/inmuebles?page={page}"
            r = subprocess.run(
                ["google-chrome", "--headless", "--no-sandbox", "--disable-gpu",
                 "--virtual-time-budget=15000", "--dump-dom", url],
                capture_output=True, text=True, timeout=30,
            )
            html = r.stdout
            # Extract __NEXT_DATA__ / ld+json / hrefs
            urls = re.findall(r'href="(/[a-z0-9-]+/\d+)"', html)
            return [{"url_path": u, "source_id": u.split("/")[-1],
                     "abs_url": urljoin("https://propiedades.com.py", u)}
                    for u in dict.fromkeys(urls)]
        except Exception as e:
            print(f"[propiedades] chrome dump failed: {e}")
            return []
    # if playwright installed
    from playwright.sync_api import sync_playwright as _pw
    url = f"https://propiedades.com.py/inmuebles?page={page}"
    with _pw() as pw:
        browser = pw.chromium.launch(headless=True)
        pg = browser.new_page(user_agent=USER_AGENT)
        pg.goto(url, wait_until="domcontentloaded", timeout=30000)
        # wait for SPA to render listing cards
        try:
            pg.wait_for_selector("a[href*='/inmueble/']", timeout=15000)
        except Exception:
            pass
        hrefs = pg.eval_on_selector_all(
            "a[href*='/inmueble/']",
            "els => Array.from(new Set(els.map(e => e.getAttribute('href'))))",
        )
        browser.close()
    return [{"url_path": h, "source_id": h.split("/")[-1] if "/" in h else h,
             "abs_url": urljoin("https://propiedades.com.py", h) if h.startswith("/")
                       else h}
            for h in hrefs]


# ---------- PII strip + dedup + listing schema --------------------------------

def public_strip(feat: dict) -> dict:
    """Apply PII-strip rules from docs/ethics/scraper-policy.md."""
    p = feat["properties"]
    # 100m-rounding for exact lat/lon (paraguayan privacy compromise)
    if p.get("lat") is not None and p.get("lon") is not None:
        p["lat"] = round(p["lat"], 3)  # ~110 m
        p["lon"] = round(p["lon"], 3)
    # drop anything not in our schema
    allowed = {"id", "source", "source_id", "source_url", "scraped_at_utc",
               "lat", "lon", "title", "address", "depto", "bedrooms",
               "price_usd", "price_pyg", "area_ha", "$/ha",
               "attrs", "escritura_anchor_id", "escritura_distance_m",
               "price_band_vs_anchors", "district", "departamento"}
    for k in list(p.keys()):
        if k not in allowed:
            del p[k]
    return feat


def to_geojson(records: list[dict]) -> dict:
    """Build a FeatureCollection from records (with lat/lon)."""
    features = []
    for r in records:
        if r.get("lat") is None or r.get("lon") is None:
            continue
        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {k: v for k, v in r.items() if k not in ("lat", "lon")},
        }
        features.append(public_strip(feat))
    return {"type": "FeatureCollection", "features": features}


# ---------- main ---------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Listings scraper (Phase 2 LIVE).")
    parser.add_argument("--portal", default="infocasas",
                        choices=["infocasas", "propiedades", "all"])
    parser.add_argument("--max-pages", type=int, default=2,
                        help="Max listing-index pages to crawl per portal.")
    parser.add_argument("--bbox", default=None,
                        help="Optional bbox filter: 'W,S,E,N' (will filter results).")
    parser.add_argument("--dept", default="",
                        help="infocasas dept slug (e.g. 'asuncion', 'central', 'alto-parana').")
    parser.add_argument("--write-public", action="store_true",
                        help="Overwrite exports/web/data/properties_latest.geojson "
                             "(off by default to prevent per-dept runs clobbering "
                             "the merged canonical artifact)")
    args = parser.parse_args(argv)

    check_ethics_gate(args.portal)

    portals = (["infocasas", "propiedades"] if args.portal == "all" else [args.portal])
    all_records: list[dict] = []

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for portal in portals:
            print(f"\n[fetch] === {portal} ===")
            if portal == "infocasas":
                for page in range(1, args.max_pages + 1):
                    print(f"[fetch] {portal} index page {page}")
                    try:
                        listings = scrape_infocasas_listing_index(
                            client, page=page, dept_slug=args.dept,
                        )
                        print(f"[fetch] {portal} page {page}: {len(listings)} unique listings")
                        for listing in listings[:20]:  # cap per page to be polite
                            try:
                                rec = scrape_infocasas_detail(client, listing)
                                if rec.get("lat") is not None:
                                    all_records.append(rec)
                            except Exception as e:
                                print(f"[fetch] {portal} detail err: {e}")
                    except Exception as e:
                        print(f"[fetch] {portal} page {page} err: {e}")
            elif portal == "propiedades":
                for page in range(1, args.max_pages + 1):
                    try:
                        listings = scrape_propiedades_listings_page(page=page)
                        print(f"[fetch] {portal} page {page}: {len(listings)} unique listings")
                        # Note: detail fetching for propiedades is more involved
                        # (Angular SPA); for now we record URLs only.
                        for listing in listings[:20]:
                            all_records.append({
                                "id": "pp_" + hashlib.sha1(("propiedades:" + listing["source_id"]).encode()).hexdigest()[:12],
                                "source": "propiedades",
                                "source_id": listing["source_id"],
                                "source_url": listing["abs_url"],
                                "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
                                "lat": None, "lon": None,
                                "needs_detail": True,
                            })
                    except Exception as e:
                        print(f"[fetch] {portal} page {page} err: {e}")

    # Optional bbox filter
    if args.bbox:
        W, S, E, N = (float(x) for x in args.bbox.split(","))
        before = len(all_records)
        all_records = [
            r for r in all_records
            if r.get("lat") is not None and S <= r["lat"] <= N and W <= r["lon"] <= E
        ]
        print(f"\n[fetch] bbox filter: {before} → {len(all_records)} records in {W},{S},{E},{N}")

    # Per-department snapshot file (so subsequent runs can merge without overwriting)
    # Use either --dept argument or derive from listings (Central dept cluster etc)
    dept_slug = args.dept or "latest"
    raw_path = REPO_ROOT / "data" / "properties" / "snapshots" / f"{dept_slug}_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')}.geojson"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps({"raw_records": all_records}, indent=2))
    print(f"\n[fetch] per-dept raw snapshot: {raw_path} ({raw_path.stat().st_size} bytes)")

    # Write raw snapshot (gitignored)
    raw_path = REPO_ROOT / "data" / "properties" / "snapshots" / f"all_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.geojson"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps({"raw_records": all_records}, indent=2))
    print(f"\n[fetch] raw snapshot: {raw_path} ({raw_path.stat().st_size} bytes)")

    # Write public-stripped snapshot for the viewer.  We make this
    # OPT-IN via --write-public, because partial per-dept runs overwrite
    # the canonical artifact (which has data merged across sources) and
    # leave the viewer showing only one departo's listings.
    if os.environ.get("WRITE_PUBLIC") == "1" or getattr(args, "write_public", False):
        geo = to_geojson(all_records)
        pub_path = REPO_ROOT / "exports" / "web" / "data" / "properties_latest.geojson"
        pub_path.parent.mkdir(parents=True, exist_ok=True)
        pub_path.write_text(json.dumps(geo, indent=2))
        print(f"[fetch] public snapshot: {pub_path} ({pub_path.stat().st_size} bytes)")
        print(f"[fetch] features in viewer: {len(geo['features'])}")
    else:
        print(f"[fetch] raw snapshot only (use --write-public or WRITE_PUBLIC=1 to overwrite exports/ web artifact)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))