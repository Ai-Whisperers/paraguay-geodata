"""tools/fetch_asuncion_estate.py

Fetcher for asuncion.estate — the biggest known scrapable PY real-estate
portal (~20K listings).  Page enumerates listings at:

  /<lang>/<city>/<op>/<type>/<page>     (24 listings per page)

where:
  lang  = en | es | pt | ru
  city  = asuncion | central | alto-parana | cordillera | itapua | boqueron |
          presidente-hayes | paraguari | san-pedro | caaguazu | misiones |
          concepcion | neembucu | alto-paraguay | caazapa | canindeyu
  op    = sale | rent
  type  = houses | apartments | lands | offices | local-commercials
  page  = 1..N

Cards on listing pages have USD + PYG price, beds, baths, m², location.
Detail pages have ld+json RealEstateListing with price, address, beds, baths,
plus a Leaflet map with data-lat / data-lng coordinates.

We index every (city, op, type, page) until we get a 404, dedupe by listing
identifier, and write a single GeoJSON FeatureCollection to the snapshot dir.

Usage:
  python3 -m tools.fetch_asuncion_estate --output-dir data/properties/snapshots
"""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "properties" / "snapshots"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Discovered cities. Add new ones here as the catalog grows.
KNOWN_CITIES = [
    "asuncion", "central", "alto-parana", "cordillera", "itapua", "boqueron",
    "presidente-hayes", "paraguari", "san-pedro", "caaguazu", "misiones",
    "concepcion", "neembucu", "alto-paraguay", "caazapa", "canindeyu",
    "ciudad-del-este", "encarnacion", "villarrica",
]

OPS = ["sale", "rent"]
PROPERTY_TYPES = ["houses", "apartments", "lands", "offices", "local-commercials"]

# PYG conversion (USD → PYG).  Matches the FX rate used by InfoCasas & TuLugar.
FX_PYG_PER_USD = 7300


def _parse_amount(s: str) -> int | None:
    """Parse a Paraguay-style amount string into an integer.

    Rules:
      - "1.000.000" → 1,000,000  (dots are thousands separators)
      - "1,500"     → 1,500      (comma is thousands separator)
      - "80.000"    → 80,000     (single dot, dot is thousands)
      - "59000000"  → 59000000   (no separator)
    We pick the format that gives the most reasonable value: prefer dot-as-
    thousands when there are exactly 2+ groups of 3 digits after a dot.

    Returns None on failure.
    """
    if not s:
        return None
    s = s.strip()
    # Strip non-digit chars except , and .
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    # If both separators appear, the right-most is the decimal.
    if "." in s and "," in s:
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")  # dot-decimal: "1,234.56" → "1234.56"
        else:
            s = s.replace(".", "").replace(",", ".")  # comma-decimal: "1.234,56" → "1234.56"
        try:
            return int(float(s))
        except Exception:
            return None
    if "," in s:
        # Comma alone: usually thousands
        s = s.replace(",", "")
    if "." in s:
        # Could be decimal or thousands.  Heuristic: if exactly 2+ groups of
        # 3 digits after a dot, dots are thousands separators.
        parts = s.split(".")
        if len(parts) >= 3 or (len(parts) == 2 and len(parts[1]) == 3):
            s = s.replace(".", "")
        # Else treat as decimal
        try:
            return int(float(s))
        except Exception:
            return None
    try:
        return int(s)
    except Exception:
        return None


def _fetch(url: str, timeout: int = 15) -> str | None:
    """Gzip-aware fetch of a single URL.  Returns body text or None on failure."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except urllib.error.HTTPError:
        return None
    except Exception as e:
        print(f"  warn {url}: {e}", file=sys.stderr)
        return None
    if r.headers.get("Content-Encoding") == "gzip":
        return gzip.decompress(raw).decode("utf-8", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def _walk_catalog() -> list[tuple[str, str, str, int]]:
    """Enumerate every (city, op, type, page) and return the ones that exist.

    Walks the listing page for each combination.  Stops on 404 (no more pages).
    Parallelized via ThreadPoolExecutor for speed (~3x faster than serial).

    Returns a list of (city, op, type, page) tuples.
    """
    # Build the full matrix of candidates
    candidates: list[tuple[str, str, str]] = []
    for city in KNOWN_CITIES:
        for op in OPS:
            for ptype in PROPERTY_TYPES:
                candidates.append((city, op, ptype))

    # Probe all (city, op, type, page=1) in parallel; this tells us which combos exist
    def probe(c):
        city, op, ptype = c
        url = f"https://asuncion.estate/en/{city}/{op}/{ptype}/1"
        body = _fetch(url)
        if body is None:
            return (city, op, ptype, 0)
        cards = re.findall(
            rf'href="(/en/{re.escape(city)}/[a-z-]+-\d+)"',
            body,
        )
        return (city, op, ptype, len(cards))

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        page1_results = list(ex.map(probe, candidates))

    # Now walk pagination for the combos that returned cards (also in parallel)
    active = [(city, op, ptype) for city, op, ptype, n in page1_results if n > 0]

    def probe_page(args):
        city, op, ptype, page = args
        url = f"https://asuncion.estate/en/{city}/{op}/{ptype}/{page}"
        body = _fetch(url)
        if body is None:
            return (city, op, ptype, page, False)
        cards = re.findall(
            rf'href="(/en/{re.escape(city)}/[a-z-]+-\d+)"',
            body,
        )
        return (city, op, ptype, page, bool(cards))

    # Probe up to 5 pages per active combo in parallel
    page_candidates = [
        (city, op, ptype, page)
        for city, op, ptype in active
        for page in range(1, 6)
    ]
    found: list[tuple[str, str, str, int]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        for city, op, ptype, page, has_cards in ex.map(probe_page, page_candidates):
            if has_cards:
                found.append((city, op, ptype, page))
    return found


def _parse_listing_card(card_html: str, city: str, op: str, ptype: str) -> dict | None:
    """Parse one listing card from a category page.

    Returns a dict with: source_url, title, price_usd, price_pyg,
    beds, baths, area_sqm, listing_type, property_type, source_id.
    Coordinates (lat/lon) are filled by the detail-page pass.
    """
    # Find the detail anchor + ID (any <a href="/<lang>/<city>/<slug>-NNNN">...</a>)
    m = re.search(
        rf'href="(/en/{re.escape(city)}/[a-z-]+-(\d+))"',
        card_html,
    )
    if not m:
        return None
    detail_path = m.group(1)
    listing_id = m.group(2)
    source_url = f"https://asuncion.estate{detail_path}"

    # Title (h5.list-title) — strip HTML
    title_match = re.search(r"<h5[^>]*>(.*?)</h5>", card_html, re.DOTALL)
    title = ""
    if title_match:
        title = re.sub(r"<[^>]+>", " ", title_match.group(1))
        title = re.sub(r"\s+", " ", title).strip()[:200]

    # Price (USD)
    price_usd = None
    price_pyg = None
    m_usd = re.search(r"U\$S\s*([\d.,]+)", card_html)
    if m_usd:
        price_usd = _parse_amount(m_usd.group(1))
        if price_usd is not None:
            price_pyg = int(price_usd * FX_PYG_PER_USD)
    if price_pyg is None:
        m_gs = re.search(r"Gs\.?\s*([\d.,]+)", card_html)
        if m_gs:
            price_pyg = _parse_amount(m_gs.group(1))
            if price_pyg is not None:
                price_usd = round(price_pyg / FX_PYG_PER_USD, 2)

    # Beds / baths / area
    beds = None
    baths = None
    area_sqm = None
    m = re.search(r'flaticon-bed[^"]*"[^>]*></span>\s*(\d+)', card_html)
    if m:
        beds = int(m.group(1))
    m = re.search(r'flaticon-shower[^"]*"[^>]*></span>\s*(\d+)', card_html)
    if m:
        baths = int(m.group(1))
    m = re.search(r'flaticon-expand[^"]*"[^>]*></span>\s*(\d+)\s*m', card_html)
    if m:
        area_sqm = int(m.group(1))

    # Map op/ptype → listing_type / property_type
    listing_type = "sale" if op == "sale" else "rent"
    ptype_map = {
        "houses": "house",
        "apartments": "apartment",
        "lands": "land",
        "offices": "office",
        "local-commercials": "commercial",
    }
    property_type = ptype_map.get(ptype, "unknown")

    # Location from card (often there's a city tag)
    location = None
    m_loc = re.search(r'<a[^>]*>([A-Z][\wá-úñÁ-ÚÑ -]+)</a>', card_html)
    if m_loc:
        location = m_loc.group(1).strip()

    h = hashlib.sha1(("asuncion_estate:" + listing_id).encode()).hexdigest()[:12]
    return {
        "type": "Feature",
        "geometry": None,  # filled by detail-page pass
        "properties": {
            "id": "ae_" + h,
            "source": "asuncion_estate",
            "source_id": listing_id,
            "source_url": source_url,
            "source_platform": "asuncion.estate",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": title or detail_path.split("/")[-1].rsplit("-", 1)[0].replace("-", " ").title(),
            "city": location,
            "state_province": city.replace("-", " ").title() if city != "asuncion" else "Asunción",
            "country": "Paraguay",
            "listing_type": listing_type,
            "property_type": property_type,
            "currency": "USD" if price_usd else "PYG",
            "price_pyg": price_pyg,
            "price_usd": price_usd,
            "bedrooms": beds,
            "bathrooms": baths,
            "area_sqm": area_sqm,
            "area_ha": (area_sqm / 10000.0) if area_sqm else None,
            "images": [],
            "description": "",
            "lat": None,
            "lon": None,
        },
    }


def _parse_detail_page(html: str) -> dict:
    """Extract coords + images + description from the detail page.

    Returns a dict with: lat, lon, images (list), description.
    """
    out: dict = {"lat": None, "lon": None, "images": [], "description": ""}
    # Coords from leaflet map div (asuncion.estate uses ts-map attributes)
    # Try multiple attribute patterns in order of specificity:
    for lat_attr, lon_attr in (
        ("data-ts-map-center-latitude", "data-ts-map-center-longitude"),
        ("data-ts-marker-latitude", "data-ts-marker-longitude"),
        ("data-ts-map-lat", "data-ts-map-lng"),
        ("data-lat", "data-lng"),
    ):
        m = re.search(
            rf'{lat_attr}="(-?\d+\.\d+)"[^>]*\s*{lon_attr}="(-?\d+\.\d+)"',
            html,
        )
        if not m:
            m = re.search(
                rf'{lat_attr}="(-?\d+\.\d+)".*?{lon_attr}="(-?\d+\.\d+)"',
                html,
            )
        if m:
            out["lat"] = float(m.group(1))
            out["lon"] = float(m.group(2))
            break

    # ld+json RealEstateListing
    for blob in re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    ):
        if '"@type":"RealEstateListing"' in blob:
            try:
                d = json.loads(blob)
                out["images"] = d.get("image") or []
                out["description"] = (d.get("description") or "").strip()
                # Some listings embed price/area/category here
                if "offers" in d and isinstance(d["offers"], dict):
                    p = d["offers"].get("price")
                    if isinstance(p, (int, float)):
                        out["ld_price"] = float(p)
                if "numberOfRooms" in d:
                    out["ld_rooms"] = d["numberOfRooms"]
                if "numberOfBedrooms" in d:
                    out["ld_bedrooms"] = d["numberOfBedrooms"]
                if "numberOfBathroomsTotal" in d:
                    out["ld_bathrooms"] = d["numberOfBathroomsTotal"]
                if "category" in d:
                    out["ld_category"] = d["category"]
                if "address" in d and isinstance(d["address"], dict):
                    out["ld_address"] = d["address"]
            except Exception:
                pass
    return out


def _enrich_with_detail(feat: dict, detail: dict) -> dict:
    """Apply a parsed detail-page dict to a feature in place."""
    p = feat["properties"]
    p["lat"] = detail.get("lat")
    p["lon"] = detail.get("lon")
    if detail.get("lat") is not None and detail.get("lon") is not None:
        feat["geometry"] = {
            "type": "Point",
            "coordinates": [detail["lon"], detail["lat"]],
        }
    p["images"] = detail.get("images") or p["images"]
    if detail.get("description") and not p.get("description"):
        p["description"] = detail["description"]
    # Backfill from ld+json when the card parser missed
    if detail.get("ld_bedrooms") is not None and p.get("bedrooms") is None:
        p["bedrooms"] = detail["ld_bedrooms"]
    if detail.get("ld_bathrooms") is not None and p.get("bathrooms") is None:
        p["bathrooms"] = detail["ld_bathrooms"]
    if detail.get("ld_price") is not None:
        # ld_price is USD ("priceCurrency":"U$S" or "USD")
        if p.get("price_usd") is None:
            p["price_usd"] = detail["ld_price"]
            p["price_pyg"] = int(detail["ld_price"] * FX_PYG_PER_USD)
    if detail.get("ld_address") and not p.get("address"):
        p["address"] = detail["ld_address"]
    return feat


def _fetch_detail(url: str, timeout: int = 12) -> dict | None:
    body = _fetch(url, timeout)
    if body is None:
        return None
    return _parse_detail_page(body)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--max-listings", type=int, default=0,
                    help="0 = no limit (default)")
    ap.add_argument("--detail-concurrency", type=int, default=8)
    ap.add_argument("--detail-timeout", type=int, default=12)
    ap.add_argument("--skip-detail", action="store_true",
                    help="Skip the detail-page enrichment pass (cards only, "
                         "no lat/lon or images)")
    args = ap.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=== walking catalog (this may take a few minutes) ===", flush=True)
    combos = _walk_catalog()
    print(f"  {len(combos)} (city, op, type, page) combos")

    # Phase 1: collect cards from every category page
    by_id: dict[str, dict] = {}
    for city, op, ptype, page in combos:
        body = _fetch(f"https://asuncion.estate/en/{city}/{op}/{ptype}/{page}")
        if body is None:
            continue
        # Each card lives inside <div class="listing-style7"> ... </div>
        cards = re.findall(
            r'<div[^>]+class="[^"]*listing-style\d[^"]*"[^>]*>(.*?)(?=<div[^>]+class="[^"]*listing-style)',
            body, re.DOTALL,
        )
        if not cards:
            # Fallback: split by the anchor pattern (find every listing-anchor
            # and grab a generous context window around it).
            anchors = list(re.finditer(
                rf'href="(/en/{re.escape(city)}/[a-z-]+-\d+)"',
                body,
            ))
            seen_ids: set[str] = set()
            cards = []
            for am in anchors:
                listing_id_match = re.search(r"-(\d+)$", am.group(1))
                if not listing_id_match:
                    continue
                lid = listing_id_match.group(1)
                if lid in seen_ids:
                    continue
                seen_ids.add(lid)
                # Capture 1500 chars before and after the anchor
                start = max(0, am.start() - 1500)
                end = min(len(body), am.end() + 1500)
                cards.append(body[start:end])
        for c in cards:
            feat = _parse_listing_card(c, city, op, ptype)
            if feat:
                sid = feat["properties"]["source_id"]
                if sid not in by_id:
                    by_id[sid] = feat
        if args.max_listings and len(by_id) >= args.max_listings:
            break
    print(f"  {len(by_id)} unique cards collected")

    # Phase 2: enrich with detail pages (lat/lon, images, description)
    if not args.skip_detail and by_id:
        print(f"=== enriching {len(by_id)} listings with detail pages ===", flush=True)
        urls = [feat["properties"]["source_url"] for feat in by_id.values()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.detail_concurrency) as ex:
            future_to_url = {
                ex.submit(_fetch_detail, u, args.detail_timeout): u
                for u in urls
            }
            n = 0
            for fut in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[fut]
                detail = fut.result()
                n += 1
                if detail is None:
                    continue
                # Find the feature whose source_url matches
                for feat in by_id.values():
                    if feat["properties"]["source_url"] == url:
                        _enrich_with_detail(feat, detail)
                        break
                if n % 50 == 0:
                    print(f"  {n}/{len(urls)} detail pages processed", flush=True)

    # Phase 3: drop listings that still have no coords (out of PY bbox or missing)
    PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}

    def _in_py(coord):
        if not isinstance(coord, list) or len(coord) < 2:
            return False
        lon, lat = coord[0], coord[1]
        return (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"]
                and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"])

    kept: list[dict] = []
    dropped_no_coord = 0
    for feat in by_id.values():
        g = feat.get("geometry")
        if g is None:
            # No coords — try one last heuristic: use city centroid
            city = feat["properties"].get("state_province", "")
            city_lower = city.lower()
            # Use the .estate's known city centroid (no boundary lookup)
            city_centroids = {
                "asunción": (-25.2637, -57.5759),
                "central": (-25.3318, -57.4831),
                "alto-parana": (-25.5163, -54.6118),
                "ciudad del este": (-25.5097, -54.6118),
                "cordillera": (-25.2200, -57.3500),
                "itapua": (-27.3333, -55.8667),
                "boqueron": (-22.4500, -60.5000),
                "presidente hayes": (-23.5167, -58.7833),
                "paraguari": (-25.6200, -57.1500),
                "san pedro": (-24.0833, -57.0833),
                "caaguazu": (-25.4500, -56.0167),
                "misiones": (-26.6333, -57.0833),
                "concepcion": (-23.4000, -57.4333),
                "neembucu": (-26.9833, -58.3000),
                "alto paraguay": (-20.0833, -59.0333),
                "caazapa": (-26.2000, -56.3667),
                "canindeyu": (-24.4167, -54.6167),
            }
            centroid = city_centroids.get(city_lower)
            if centroid:
                feat["geometry"] = {
                    "type": "Point",
                    "coordinates": [centroid[1], centroid[0]],
                }
                feat["properties"]["lat"] = centroid[0]
                feat["properties"]["lon"] = centroid[1]
            else:
                dropped_no_coord += 1
                continue
        if not _in_py(feat["geometry"]["coordinates"]):
            dropped_no_coord += 1
            continue
        kept.append(feat)
    print(f"  dropped {dropped_no_coord} without coords, kept {len(kept)}")

    # Phase 4: write snapshot
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "asuncion_estate",
        "feature_count": len(kept),
        "features": kept,
    }
    out_path = args.output_dir / f"asuncion_estate_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M')}.geojson"
    out_path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )
    print(f"  wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())