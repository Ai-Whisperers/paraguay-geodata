"""tools/cross_source_dedupe.py — find and merge cross-source duplicates.

The canonical pipeline clusters by `source + url_hash`, so a property
listed by InfoCasas AND TuLugar gets TWO clusters — even when they
refer to the same physical finca. This tool:

  1. Builds a spatial grid index (S2-like cells ~150m) for fast lookup.
  2. For each listing, finds candidates in neighboring cells.
  3. Applies a similarity score:
     - geo proximity (<200m = strong, <500m = weak)
     - price match (<25% diff = strong, <50% = weak)
     - title tokens overlap (Jaccard ≥ 0.5 = strong, ≥ 0.3 = weak)
     - area match (<20% diff = strong)
     - property_type match
  4. Groups listings into clusters via union-find.
  5. For each cluster, picks a "canonical" listing (highest-quality source)
     and a list of `also_listed_by` source URLs.

Writes:
  data/properties/canonical_properties.geojson  (updated cluster_id, also_listed_by)
  data/properties/duplicate_clusters.json        (audit trail of merges)

Usage:
  python3 -m tools.cross_source_dedupe
  python3 -m tools.cross_source_dedupe --max-distance 200 --max-price-diff 0.30
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_PATH = REPO_ROOT / "data" / "properties" / "canonical_properties.geojson"
AUDIT_PATH = REPO_ROOT / "data" / "properties" / "duplicate_clusters.json"

# A "good" listing is one we'd prefer to keep as the canonical for a cluster.
# Higher = better.  Used to break ties when picking the cluster representative.
SOURCE_QUALITY = {
    "infocasas":      100,  # largest brand, clean titles
    "tucasa":          95,
    "asuncion_estate": 80,  # many synthetic titles
    "tulugar":         85,  # detailed descriptions
    "inmueblespy":     70,
    "propiedades":     90,
    "argenprop":       60,
    "clasipar":        50,
    "bienesonline":    40,
    "ml_inmuebles":    30,
    "century21":       45,
    "unknown":         10,
}

# Tokens we strip from titles before computing similarity.
# Spanish stopwords + listing-template boilerplate.
_TITLE_STRIP = re.compile(
    r"\b(en venta|venta de|alquiler|alquilo|se vende|vendo|se alquila|"
    r"departamento en|casa en|terreno en|propiedad en|inmueble en|"
    r"depto\.?|apartamento|house|casa|country|barrio|ciudad de|"
    r"excelente|hermoso|hermosa|lindo|linda|amplio|amplia|premium|"
    r"\d+\s*dormitorios?|\d+\s*ambientes?|\d+\s*habitaciones?)\b",
    re.IGNORECASE,
)
_NON_WORD = re.compile(r"[^a-záéíóúñü0-9 ]")
_MULTI_SPACE = re.compile(r"\s+")


def _normalize_title(title: str | None) -> str:
    if not title:
        return ""
    t = title.lower()
    t = _TITLE_STRIP.sub(" ", t)
    t = _NON_WORD.sub(" ", t)
    t = _MULTI_SPACE.sub(" ", t).strip()
    return t


def _title_tokens(title: str | None) -> set[str]:
    return set(_normalize_title(title).split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))


def _price_ratio(a: float | None, b: float | None) -> float:
    """Return the larger / smaller price ratio. 1.0 = identical. ∞ if one is missing."""
    if not a or not b or a <= 0 or b <= 0:
        return float("inf")
    return max(a, b) / min(a, b)


def _area_ratio(a: float | None, b: float | None) -> float:
    if not a or not b or a <= 0 or b <= 0:
        return float("inf")
    return max(a, b) / min(a, b)


class UnionFind:
    """Tiny union-find for clustering."""

    def __init__(self):
        self.parent: dict[int, int] = {}

    def add(self, x: int):
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def build_spatial_grid(features: list[dict], cell_deg: float = 0.002,
                        skip_centroids: bool = True) -> dict[tuple[int, int], list[int]]:
    """Group feature indices by (cell_x, cell_y). cell_deg=0.002 ≈ 200m at PY latitudes.

    skip_centroids=True excludes listings whose coords came from a city-centroid
    fallback (geometry_set_by='enrich_missing_only'). Those are 4,793 asuncion_estate
    listings that all stack at the same point — without excluding them, the dedupe
    would falsely merge hundreds of unrelated properties into one cluster per city.
    """
    grid: dict[tuple[int, int], list[int]] = {}
    n_skipped = 0
    for idx, f in enumerate(features):
        c = f.get("geometry", {}).get("coordinates")
        if not c or len(c) < 2:
            continue
        lon, lat = c[0], c[1]
        if abs(lat) > 90 or abs(lon) > 180:
            continue
        if skip_centroids:
            setter = f.get("properties", {}).get("geometry_set_by", "")
            if setter == "enrich_missing_only":
                n_skipped += 1
                continue
        cx = int(lon / cell_deg)
        cy = int(lat / cell_deg)
        grid.setdefault((cx, cy), []).append(idx)
    if n_skipped:
        print(f"  skipped {n_skipped:,} centroid-fallback listings (no real coords)", flush=True)
    return grid


def neighbors(grid: dict, cx: int, cy: int, radius: int = 1) -> list[int]:
    """Return all indices in cells within ±radius of (cx, cy)."""
    out: list[int] = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (cx + dx, cy + dy)
            if key in grid:
                out.extend(grid[key])
    return out


def similarity_score(
    a: dict, b: dict,
    *,
    max_distance_m: float,
    max_price_ratio: float,
    max_area_ratio: float,
) -> tuple[float, dict]:
    """Return (score, breakdown).  Higher = more likely the same property."""
    breakdown: dict = {"geo_m": None, "price_ratio": None, "area_ratio": None,
                        "jaccard": None, "same_type": None, "score": 0.0}

    ca = a.get("geometry", {}).get("coordinates")
    cb = b.get("geometry", {}).get("coordinates")
    if not ca or len(ca) < 2 or not cb or len(cb) < 2:
        return 0.0, breakdown
    lon1, lat1 = ca[0], ca[1]
    lon2, lat2 = cb[0], cb[1]
    d_m = _haversine_m(lon1, lat1, lon2, lat2)
    breakdown["geo_m"] = d_m
    if d_m > max_distance_m:
        return 0.0, breakdown

    pa = a["properties"]
    pb = b["properties"]
    price_ratio = _price_ratio(pa.get("price_usd"), pb.get("price_usd"))
    breakdown["price_ratio"] = price_ratio
    if price_ratio > max_price_ratio:
        return 0.0, breakdown

    area_ratio = _area_ratio(pa.get("area_ha"), pb.get("area_ha"))
    breakdown["area_ratio"] = area_ratio

    ta = _normalize_title(pa.get("title") or "")
    tb = _normalize_title(pb.get("title") or "")
    if ta and tb:
        j = _jaccard(set(ta.split()), set(tb.split()))
        breakdown["jaccard"] = j
    else:
        j = 0.0
        breakdown["jaccard"] = None  # no signal

    same_type = pa.get("property_type") == pb.get("property_type") and pa.get("property_type") not in (None, "unknown", "")
    breakdown["same_type"] = same_type

    # Score: weighted sum
    # geo (closest is best): 40 pts if d_m ≤ 50, 20 pts if d_m ≤ 150, 5 pts if d_m ≤ max
    geo_pts = 40 * max(0, 1 - d_m / max_distance_m)
    # price (closest is best): 30 pts if ratio ≤ 1.05, 20 if ≤ 1.15, 10 if ≤ max
    if price_ratio == 1.0:
        price_pts = 30
    elif price_ratio <= 1.05:
        price_pts = 28
    elif price_ratio <= 1.15:
        price_pts = 22
    elif price_ratio <= 1.30:
        price_pts = 15
    else:
        price_pts = 5
    # title jaccard: 20 pts if ≥ 0.7, 12 if ≥ 0.5, 5 if ≥ 0.3
    if j is None:
        title_pts = 0
    elif j >= 0.7:
        title_pts = 20
    elif j >= 0.5:
        title_pts = 12
    elif j >= 0.3:
        title_pts = 5
    else:
        title_pts = 0
    # area: 5 pts if ≤ 1.10, 2 if ≤ 1.20
    if area_ratio <= 1.10:
        area_pts = 5
    elif area_ratio <= 1.20:
        area_pts = 3
    elif area_ratio <= 1.50:
        area_pts = 1
    else:
        area_pts = 0
    # same type: 5 pts
    type_pts = 5 if same_type else 0

    breakdown["score"] = round(geo_pts + price_pts + title_pts + area_pts + type_pts, 2)
    return breakdown["score"], breakdown


def is_duplicate(score: float, same_source: bool = False, has_title_match: bool = False) -> bool:
    """Threshold for declaring two listings duplicates of each other.

    Cross-source pairs need STRONG evidence — different portals often list
    hundreds of units in the same tower, so a strong title (or street address)
    match is required to merge across sources. Same-source pairs may share a
    building but rarely share the exact same unit, so we still require a
    meaningful score.

    Rules:
      - Different sources: require score ≥ 75 AND title jaccard ≥ 0.40
        (so we don't merge "Casa en Asunción" with "Casa en Asunción" — too vague)
      - Same source: NEVER merge. The merger already dedupes by source_url
        (which is unique per portal per listing). Same-source clusters
        detected by this tool are always false positives: a portal mapping
        N distinct properties to the same city center (e.g. asuncion.estate's
        map fallback) produces a high score for unrelated listings.
    """
    if same_source:
        return False
    return score >= 75.0 and has_title_match


def find_clusters(features: list[dict], *, max_distance_m: float, max_price_ratio: float,
                   max_area_ratio: float = 1.5, cell_deg: float = 0.002) -> tuple[UnionFind, list[dict]]:
    """Find duplicate clusters among features. Returns (UnionFind, per-pair similarity list)."""
    grid = build_spatial_grid(features, cell_deg=cell_deg, skip_centroids=True)
    cell_radius = max(1, int(math.ceil(max_distance_m / (cell_deg * 111000))))
    print(f"  grid: {len(grid)} cells with features, radius={cell_radius} cells")

    uf = UnionFind()
    for idx in range(len(features)):
        uf.add(idx)

    pairs: list[dict] = []
    seen_pairs: set[tuple[int, int]] = set()

    # For each feature, look at neighbors within cell_radius cells
    for idx, f in enumerate(features):
        c = f.get("geometry", {}).get("coordinates")
        if not c or len(c) < 2:
            continue
        # Skip centroid-fallback listings as the source side too — only merge
        # them if they match a real-coord listing from another source.
        setter_a = f.get("properties", {}).get("geometry_set_by", "")
        is_centroid_a = setter_a == "enrich_missing_only"
        lon, lat = c[0], c[1]
        cx, cy = int(lon / cell_deg), int(lat / cell_deg)

        # Only check forward (idx < j) to avoid double work
        for jdx in neighbors(grid, cx, cy, radius=cell_radius):
            if jdx <= idx:
                continue
            pair_key = (idx, jdx)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Don't bother if BOTH are centroids (already filtered from grid, but defensive)
            setter_b = features[jdx].get("properties", {}).get("geometry_set_by", "")
            if is_centroid_a and setter_b == "enrich_missing_only":
                continue

            score, breakdown = similarity_score(
                features[idx], features[jdx],
                max_distance_m=max_distance_m,
                max_price_ratio=max_price_ratio,
                max_area_ratio=max_area_ratio,
            )
            src_a = features[idx]["properties"].get("source")
            src_b = features[jdx]["properties"].get("source")
            same_source = src_a == src_b
            # Many portals (notably asuncion.estate) return the same map-center
            # coord for every listing in a city when the address isn't geocoded.
            # When N>5 listings share the EXACT same coord, the coord is almost
            # certainly the city center, not a per-property location. In that
            # case, geo is meaningless for dedupe — fall back to title only.
            ca = features[idx].get("geometry", {}).get("coordinates", [])
            cb = features[jdx].get("geometry", {}).get("coordinates", [])
            # We need access to the per-cell listing count. Cheap check: if
            # the 4-decimal grid cell has many features, the coord is
            # probably a city center. The grid is built globally below; for
            # now, use a heuristic — count neighbors in our grid.
            coord_a = (round(ca[0], 4), round(ca[1], 4)) if ca else None
            coord_b = (round(cb[0], 4), round(cb[1], 4)) if cb else None
            grid[coord_a].count(idx) if False else None  # placeholder
            # Actually compute from grid directly:
            cell_count = None
            if coord_a is not None and coord_a in grid:
                cell_count = len(grid[coord_a])

            # Cross-source requires title similarity OR address match (we don't have
            # addresses extracted, so use title jaccard). Same-source matches at
            # the same physical address can also have generic titles.
            ta = _normalize_title(features[idx]["properties"].get("title") or "")
            tb = _normalize_title(features[jdx]["properties"].get("title") or "")
            if ta and tb:
                j = _jaccard(set(ta.split()), set(tb.split()))
                has_title_match = j >= 0.40
            else:
                j = None
                # No title on at least one — require very close geo (≤30m) and
                # IDENTICAL price. And only if the coord is rare (not a city
                # center shared by many listings).
                geo_m = breakdown.get("geo_m", 9999)
                price_ratio = breakdown.get("price_ratio", 9999)
                precise_a = ca and round(ca[0], 4) != round(ca[0], 2)
                precise_b = cb and round(cb[0], 4) != round(cb[0], 2)
                is_rare_cell = cell_count is None or cell_count <= 3
                has_title_match = (geo_m <= 30 and price_ratio <= 1.02
                                    and precise_a and precise_b
                                    and is_rare_cell)
            # Don't bother with same-source pairs — they always false-positive
            # when the portal maps N distinct listings to the same city center.
            # The merger already dedupes by source_url.
            if same_source:
                continue
            if is_duplicate(score, same_source=same_source, has_title_match=has_title_match):
                uf.union(idx, jdx)
                pairs.append({
                    "a": features[idx]["properties"].get("id"),
                    "b": features[jdx]["properties"].get("id"),
                    "a_source": src_a,
                    "b_source": src_b,
                    "same_source": same_source,
                    "title_jaccard": j if ta and tb else None,
                    **breakdown,
                })
    return uf, pairs


def cluster_canonical(features: list[dict], uf: UnionFind) -> dict[int, list[int]]:
    """Group indices by their cluster root and return {root: [indices]}."""
    groups: dict[int, list[int]] = collections.defaultdict(list)
    for idx in range(len(features)):
        groups[uf.find(idx)].append(idx)
    return dict(groups)


def pick_canonical(indices: list[int], features: list[dict]) -> int:
    """Pick the best feature index to be the canonical representative."""
    def quality(idx: int) -> tuple:
        p = features[idx]["properties"]
        return (
            SOURCE_QUALITY.get(p.get("source", "unknown"), 10),  # source reputation
            1 if (p.get("title") or "").strip() else 0,           # has title
            1 if (p.get("description") or "").strip() else 0,     # has description
            1 if p.get("lat") is not None else 0,                # has coords
            1 if (p.get("images") or []) else 0,                 # has images
            -idx,                                                 # prefer earlier in original
        )
    return max(indices, key=quality)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Find and merge cross-source duplicates.")
    ap.add_argument("--max-distance", type=float, default=200.0,
                    help="Max distance in meters for geo match (default: 200)")
    ap.add_argument("--max-price-diff", type=float, default=0.30,
                    help="Max price ratio as fraction (1.30 = within 30 percent, default: 0.30)")
    ap.add_argument("--max-area-diff", type=float, default=0.50,
                    help="Max area ratio (default: 0.50)")
    ap.add_argument("--score-threshold", type=float, default=55.0,
                    help="Min similarity score to merge (default: 55)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute clusters but don't write output")
    args = ap.parse_args(argv)

    if not CANON_PATH.exists():
        print(f"  ERR: {CANON_PATH} not found — run canonicalize_properties first")
        return 1

    print(f"=== cross-source dedupe ===", flush=True)
    print(f"  max-distance: {args.max_distance}m, max-price-diff: {args.max_price_diff*100:.0f}%, "
          f"max-area-diff: {args.max_area_diff*100:.0f}%, threshold: {args.score_threshold}", flush=True)

    data = json.loads(CANON_PATH.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features", flush=True)

    # Track original cluster_id so we can preserve the per-source prefix
    original_clusters = {f["properties"].get("id"): f["properties"].get("cluster_id") for f in features}

    uf, pairs = find_clusters(
        features,
        max_distance_m=args.max_distance,
        max_price_ratio=1 + args.max_price_diff,
        max_area_ratio=1 + args.max_area_diff,
    )

    groups = cluster_canonical(features, uf)
    n_clusters = len(groups)
    n_multi = sum(1 for v in groups.values() if len(v) > 1)
    print(f"  cluster groups: {n_clusters:,} (multi-listing: {n_multi})", flush=True)
    print(f"  duplicate pairs found: {len(pairs):,}", flush=True)

    # Pick canonical for each cluster and assign new cluster_id
    new_cluster_ids: dict[int, str] = {}
    also_listed_by: dict[int, list[str]] = {}
    cluster_members: dict[str, list[dict]] = {}

    for root, indices in groups.items():
        canon_idx = pick_canonical(indices, features)
        canon_props = features[canon_idx]["properties"]
        canon_source = canon_props.get("source", "unknown")
        # cluster_id: "{root}-{hash}" for stability
        new_id = f"cls-{root:08d}"
        new_cluster_ids[root] = new_id

        # Also-listed-by list: every OTHER member's source + url
        members: list[dict] = []
        for i in indices:
            p = features[i]["properties"]
            members.append({
                "source": p.get("source"),
                "source_id": p.get("source_id"),
                "source_url": p.get("source_url"),
                "id": p.get("id"),
            })
        also_listed_by[root] = [
            {"source": m["source"], "source_url": m["source_url"]}
            for m in members if m["id"] != canon_props.get("id")
        ]
        cluster_members[new_id] = members

    # Assign new cluster_id + also_listed_by to each feature
    for idx, f in enumerate(features):
        root = uf.find(idx)
        f["properties"]["cluster_id"] = new_cluster_ids[root]
        f["properties"]["also_listed_by"] = also_listed_by[root]
        f["properties"]["cluster_size"] = len(groups[root])

    # Audit trail
    audit = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "params": {
            "max_distance_m": args.max_distance,
            "max_price_diff": args.max_price_diff,
            "max_area_diff": args.max_area_diff,
            "score_threshold": args.score_threshold,
        },
        "totals": {
            "features": n,
            "clusters": n_clusters,
            "multi_listing_clusters": n_multi,
            "duplicate_pairs": len(pairs),
            "merged": sum(len(v) - 1 for v in groups.values()),
        },
        "clusters": [
            {
                "cluster_id": cid,
                "size": len(members),
                "canonical_id": members[0]["id"] if members else None,
                "members": members,
            }
            for cid, members in cluster_members.items()
            if len(members) > 1
        ],
        "pair_samples": pairs[:50],  # first 50 for inspection
    }

    if args.dry_run:
        print(f"\n=== DRY RUN — would write ===")
        print(f"  clusters: {n_clusters:,} (was 1 per source-url)")
        print(f"  multi-listing clusters: {n_multi}")
        print(f"  total listings merged into clusters: {sum(len(v) - 1 for v in groups.values()):,}")
        return 0

    # Write back
    data["features"] = features
    data["generated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    CANON_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  wrote {CANON_PATH}", flush=True)
    print(f"  wrote {AUDIT_PATH} ({AUDIT_PATH.stat().st_size:,}b)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
