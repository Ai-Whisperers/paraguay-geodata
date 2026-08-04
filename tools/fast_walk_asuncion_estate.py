"""tools/fast_walk_asuncion_estate.py — fast bulk walk of asuncion.estate.

Replaces the slow detail-enriching fetch_asuncion_estate.py for cases
where you just want a complete count + listing URLs.

The original fetch_asuncion_estate.py walks the catalog then enriches
with detail pages (~2s each × thousands = hours). This walker just
gets cards from every (city, op, type, page) combination, dedupes, and
writes a single geojson. No detail enrichment.

For detail-enriched output, run fetch_asuncion_estate.py in --max-listings=N
mode and skip detail pages that are already in canonical.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

KNOWN_CITIES = [
    "asuncion", "central", "alto-parana", "cordillera", "itapua", "boqueron",
    "presidente-hayes", "paraguari", "san-pedro", "caaguazu", "misiones",
    "concepcion", "neembucu", "alto-paraguay", "caazapa", "canindeyu",
    "ciudad-del-este", "encarnacion", "villarrica",
]
OPS = ["sale", "rent"]
PROPERTY_TYPES = ["houses", "apartments", "lands", "offices", "local-commercials"]


def _fetch(url: str, timeout: int = 12) -> str | None:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": UA}),
            timeout=timeout,
        ) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _cards_in(html: str, city: str) -> list[str]:
    """Extract /en/<city>/<slug>-NNNN links from a listing page."""
    return re.findall(rf'href="(/en/{re.escape(city)}/[a-z-]+-\d+)"', html)


def walk(max_pages: int = 20, concurrency: int = 30) -> list[dict]:
    """Walk every (city, op, type, page) and collect unique cards."""
    combos = [(c, o, t) for c in KNOWN_CITIES for o in OPS for t in PROPERTY_TYPES]

    # Probe page=1 in parallel to find active combos
    def probe_p1(c, o, t):
        url = f"https://asuncion.estate/en/{c}/{o}/{t}/1"
        body = _fetch(url)
        n = len(_cards_in(body, c)) if body else 0
        return (c, o, t, n > 0, n)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        p1_results = list(ex.map(lambda c: probe_p1(*c), combos))
    active = [(c, o, t) for c, o, t, active, n in p1_results if active]
    print(f"  active combos: {len(active)}/{len(combos)}")

    # Walk pages 1..max_pages for each active combo
    pages = [(c, o, t, p) for c, o, t in active for p in range(1, max_pages + 1)]

    def fetch_page(args):
        c, o, t, p = args
        url = f"https://asuncion.estate/en/{c}/{o}/{t}/{p}"
        body = _fetch(url)
        return (c, o, t, p, _cards_in(body, c) if body else [])

    by_id: dict[str, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        for i, (c, o, t, p, links) in enumerate(ex.map(fetch_page, pages)):
            for link in links:
                # link is /en/city/slug-NNNN
                m = re.search(r"-(\d+)$", link)
                if not m:
                    continue
                listing_id = m.group(1)
                if listing_id in by_id:
                    continue
                by_id[listing_id] = {
                    "url": f"https://asuncion.estate{link}",
                    "city": c,
                    "op": o,
                    "type": t,
                    "page": p,
                }
            if (i + 1) % 50 == 0:
                print(f"  {(i + 1)}/{len(pages)} pages scanned, {len(by_id)} unique IDs", flush=True)
    print(f"  total unique listings: {len(by_id)}")
    return list(by_id.values())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "properties" / "snapshots" / "asuncion_estate_fast_walk.geojson")
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=30)
    args = ap.parse_args(argv)

    print(f"=== fast walk asuncion.estate ===", flush=True)
    listings = walk(max_pages=args.max_pages, concurrency=args.concurrency)

    # Convert to features with stable IDs
    import hashlib
    features = []
    for listing in listings:
        h = hashlib.sha1(("asuncion_estate:" + listing["url"].split("-")[-1]).encode()).hexdigest()[:12]
        features.append({
            "type": "Feature",
            "geometry": None,
            "properties": {
                "id": "ae_" + h,
                "source": "asuncion_estate",
                "source_id": listing["url"].split("-")[-1],
                "source_url": listing["url"],
                "source_platform": "asuncion.estate",
                "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
                "title": "",
                "city": listing["city"].replace("-", " ").title() if listing["city"] != "asuncion" else "Asunción",
                "state_province": listing["city"].replace("-", " ").title() if listing["city"] != "asuncion" else "Asunción",
                "country": "Paraguay",
                "listing_type": "sale" if listing["op"] == "sale" else "rent",
                "property_type": {"houses": "house", "apartments": "apartment", "lands": "land",
                                   "offices": "office", "local-commercials": "commercial"}.get(listing["type"], "unknown"),
                "currency": None,
                "price_pyg": None,
                "price_usd": None,
                "area_sqm": None,
                "area_ha": None,
                "bedrooms": None,
                "bathrooms": None,
                "parking_spaces": None,
                "images": [],
                "lat": None,
                "lon": None,
                "area_source": "unknown",
                "canonical_features": [],
                "features_raw": [],
                "last_seen_at": datetime.now(timezone.utc).isoformat(),
                "freshness_days": 0,
                "cluster_id": None,
                "usd_per_ha": None,
                "quality_flags": ["no_detail_enrichment"],
                "pii_scrubbed": False,
                "pii_scrub_utc": None,
                "pii_scrub_version": None,
            },
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": "asuncion_estate_fast_walk",
        "feature_count": len(features),
        "features": features,
    }
    args.output.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK: wrote {len(features)} features → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
