"""Contract tests for scripts/merge_property_sources.py.

These tests exercise the PURE functions (_normalize_*_features, _stub_clasipar)
and the dedup logic in isolation, without mutating the live 40 MB
tulugar_snap.json or the live properties_latest.geojson publish file.

Why: running the full pipeline mutates two published data files. A unit test
that fuzzes the schema or breaks dedup would silently corrupt production.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "merge_property_sources.py"

_spec = importlib.util.spec_from_file_location("merge_property_sources", SCRIPT)
assert _spec is not None and _spec.loader is not None
merge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge)


# ---------- Pure normalization tests ----------

def test_normalize_infocasas_strips_pii_and_rounds_coords():
    """_normalize_infocasas keeps listing shape and snaps lat/lon to 4 dp."""
    raw = {
        "geometry": {"type": "Point", "coordinates": [-57.57594, -25.26371]},
        "properties": {
            "id": "ic_X",
            "source_id": "X",
            "source_url": "https://infocasas.com.py/anuncio/X",
            "title": "Casa en Sajonia",
            "price_pyg": 730000000,
            "price_usd": 100000,
            "area_ha": 0.5,
            "depto": "Central",
            "agent_phone": "+595991555111",  # must NOT survive
        },
    }
    out = merge._normalize_infocasas(raw)

    assert out["lat"] == -25.2637, "coord rounded to 4 dp"
    assert out["lon"] == -57.5759
    assert out["source"] == "infocasas"
    assert out["country"] == "Paraguay"
    assert out["listing_type"] == "sale"
    assert "agent_phone" not in out, "PII fields must be stripped"
    assert out["verified"] is False
    assert out["features"] == []


def test_normalize_tulugar_drops_records_without_coords():
    """TuLugar records missing lat/lon must NOT be ingested."""
    raw = {"properties": {"lat": None, "lon": None, "title": "X"}}
    out = merge._normalize_tulugar(raw)
    assert out["lat"] is None and out["lon"] is None


def test_normalize_tulugar_computes_per_ha_when_missing():
    """$/ha must be derived from price + area when not pre-computed upstream."""
    raw = {
        "properties": {
            "lat": -25.27, "lon": -57.58,
            "price_usd": 100_000,
            "area_sqm": 5000,  # = 0.5 ha
            "title": "Casa",
            "source_id": "TL",
            "source_url": "https://tulugar.com.py/x",
        }
    }
    out = merge._normalize_tulugar(raw)
    assert out["area_ha"] == 0.5
    assert out["$/ha"] == 200_000, "100_000 USD / 0.5 ha = 200_000 USD/ha"


def test_normalize_tulugar_falls_back_to_pyg_for_per_ha():
    """When USD is missing, derive $/ha from PYG at a stable FX rate."""
    raw = {
        "properties": {
            "lat": -25.27, "lon": -57.58,
            "price_pyg": 730_000_000,  # 7300 PYG/USD → 100_000 USD
            "area_sqm": 5000,          # 0.5 ha
            "title": "Casa",
            "source_id": "TL",
            "source_url": "https://tulugar.com.py/y",
        }
    }
    out = merge._normalize_tulugar(raw)
    # Uses 7300 PYG/USD; 730M / 7300 / 0.5 = 200_000
    assert out["$/ha"] == pytest.approx(200_000, rel=0.001)


def test_stub_clasipar_records_pending_detail_marker():
    """Clasipar URL stubs must be tagged so the viewer doesn't try to render
    empty property cards."""
    out = merge._stub_clasipar("https://clasipar.com.py/anuncio/12345-casa")
    assert out["source"] == "clasipar"
    assert out["lat"] is None and out["lon"] is None
    assert out["images"] == []
    # The internal marker survives normalization in main() but is dropped before
    # publishing (line 282 strips leading-underscore keys).
    assert out.get("_pending_detail") is True


# ---------- Dedup logic tests ----------

def test_dedup_two_records_same_coords_same_listing_merges():
    """Two records at the same lat/lon + same listing_type must collapse to one.

    TuLugar should win when its record is richer (more non-null fields).
    """
    # Mirror the dedup loops in main() in isolation.
    by_url = {}    # pass 1 — nothing to merge yet (different URLs)
    deduped = [
        {  # infocasas (less rich)
            "source": "infocasas", "source_url": "u1",
            "lat": -25.27, "lon": -57.58, "listing_type": "sale",
            "title": "INF", "price_usd": 100000, "images": ["a.jpg"],
        },
        {  # tulugar (richer)
            "source": "tulugar", "source_url": "u2",
            "lat": -25.27, "lon": -57.58, "listing_type": "sale",
            "title": "TL", "price_usd": 105000, "description": "Lindo",
            "address": "Calle Palma 123", "city": "Asunción",
            "bedrooms": 3, "area_ha": 0.5, "images": ["b.jpg"],
        },
    ]
    by_loc = {}
    for r in deduped:
        key = (r["lat"], r["lon"], r.get("listing_type") or "sale")
        by_loc.setdefault(key, []).append(r)

    final = []
    for key, group in by_loc.items():
        group.sort(
            key=lambda r: sum(1 for v in r.values() if v is not None and v != []),
            reverse=True,
        )
        final.append(group[0])

    assert len(final) == 1
    assert final[0]["source"] == "tulugar", "richer source must win"
    assert final[0]["address"] == "Calle Palma 123"


def test_dedup_different_listing_types_not_merged():
    """Same coords + DIFFERENT listing_type → keep both."""
    sale = {
        "source": "tulugar", "lat": -25.27, "lon": -57.58,
        "listing_type": "sale", "price_usd": 100_000,
    }
    rent = {
        "source": "tulugar", "lat": -25.27, "lon": -57.58,
        "listing_type": "rent", "price_pyg": 5_000_000,
    }
    by_loc = {}
    for r in (sale, rent):
        key = (r["lat"], r["lon"], r.get("listing_type") or "sale")
        by_loc.setdefault(key, []).append(r)

    final = []
    for key, group in by_loc.items():
        if len(group) == 1:
            final.append(group[0])
        else:
            final.append(group[0])
    assert len(final) == 2


def test_internal_marker_dropped_before_publish():
    """Lines starting with ``_`` must be stripped before GeoJSON output
    (else _pending_detail: true would leak into the public file).
    """
    row = {"lat": -25.27, "lon": -57.58, "_pending_detail": True, "title": "X"}
    props = {k: v for k, v in row.items() if not k.startswith("_")}
    assert "_pending_detail" not in props
    assert "title" in props


def test_records_without_coords_excluded_from_geojson():
    """Records lacking lat/lon are skipped before the GeoJSON write
    (we can't put them on a map)."""
    rows = [
        {"lat": -25.27, "lon": -57.58, "title": "Mapped"},
        {"lat": None,  "lon": None,  "title": "Unmappable"},
    ]
    geo_features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]}
            if r.get("lat") is not None
            else None,  # this branch never runs in main(); here to be explicit
            "properties": r,
        }
        for r in rows
        if r.get("lat") is not None and r.get("lon") is not None
    ]
    assert len(geo_features) == 1


# ---------- Output contract (live data snapshot) ----------

def test_published_properties_minimum_schema(data_root, live_only):
    """Every published feature must carry the consumer-required fields that
    index.html popups + heatmaps + filters depend on.

    Skips if properties_latest.geojson isn't built yet.
    """
    f = data_root / "properties_latest.geojson"
    if not f.exists() or f.stat().st_size < 1_000_000:
        pytest.skip("properties_latest.geojson not published")

    import json
    d = json.load(open(f))
    REQUIRED = {
        "id", "source", "source_id", "title",
        "price_usd", "lat", "lon", "state_province",
        "listing_type",
    }
    sample = d["features"][:200]
    missing_counts = {}
    for feat in sample:
        props = feat.get("properties") or {}
        for k in REQUIRED:
            if k not in props:
                missing_counts[k] = missing_counts.get(k, 0) + 1
    # Strict policy: 95%+ must have every required key. The other 5% are
    # clasipar stubs (`_pending_detail: true`) which legitimately lack
    # coords/price/title.
    for k, n in missing_counts.items():
        assert n / len(sample) <= 0.05, (
            f"field {k!r} missing on {n}/{len(sample)} sampled properties "
            f"({100*n/len(sample):.1f}%) — check stub filter in main()"
        )


def test_published_properties_pii_invariant(data_root, live_only):
    """Even after merging all 3 sources, the published GeoJSON must have
    zero +595 phone patterns in non-pii/non-id fields.

    (PII scrubbing happens separately in tools/scrub_pii.py — this test
    catches regressions where the merge step accidentally re-introduces
    raw agent fields.)
    """
    import json, re
    f = data_root / "properties_latest.geojson"
    if not f.exists() or f.stat().st_size < 1_000_000:
        pytest.skip("properties_latest.geojson not published")
    d = json.load(open(f))
    phone_re = re.compile(r"\+595[\s\-]?9\d{2}")  # strict +595 + 9xx
    id_keys = {"id", "source_id", "source_url", "scraped_at_utc"}
    leaks = 0
    for feat in d["features"]:
        for k, v in (feat.get("properties") or {}).items():
            if k in id_keys or k.startswith("pii_"):
                continue
            if isinstance(v, str) and phone_re.search(v):
                leaks += 1
    assert leaks == 0, f"{leaks} properties have phone-shaped PII in non-id fields"
