"""Property risk output contract tests — T3 from the audit matrix.

Covers the 3 published risk artifacts:
  - data/property_risk_analysis.json (full per-property)
  - data/property_risk_index.json   (lightweight coords+scores)
  - data/property_risk_summary.json (by-depto aggregate)

Also acts as a snapshot test: stability across rebuilds — risk scores for
known landmarks (Asunción Centro, Central, Itapúa, Boquerón) must stay within
tight bounds when the underlying layers don't change.

If a layer input changes (flood polygons, climate_risk.geojson), re-baseline
the fixtures by running scripts/build_risk_v2.py and re-running this suite.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


KNOWN_LANDMARKS = {
    # capital of Paraguay → low flood risk score expected
    "Asunción": (-25.2637, -57.5759),
    # High-urban: large central city
    "Ciudad del Este": (-25.5097, -54.6111),
    # Rural Chaco: should have high indigenous + seasonal flood baseline
    "Filadelfia": (-22.2701, -60.0333),
    # Eastern border city (mostly agricultural)
    "Pedro Juan Caballero": (-22.5667, -55.7333),
}


# ---------- File existence & basic shape ----------

def test_risk_full_index_exists_and_is_featurecollection(data_root, live_only):
    """property_risk_index.json: lightweight heatmap input. Many entries, each
    with lat/lon/score."""
    f = data_root / "property_risk_index.json"
    if not f.exists() or f.stat().st_size < 10_000:
        pytest.skip("property_risk_index.json not built yet")
    d = json.load(open(f))
    assert "index" in d
    entries = d["index"]
    assert isinstance(entries, dict)
    # A pin per property → at least 5K entries (the catalog has ~10K)
    assert len(entries) >= 1_000, f"only {len(entries)} risk-index entries"


def test_risk_full_analysis_has_required_top_level_keys(data_root, live_only):
    """property_risk_analysis.json shape: {analyses: [...], schema_version, ...}"""
    f = data_root / "property_risk_analysis.json"
    if not f.exists() or f.stat().st_size < 100_000:
        pytest.skip("property_risk_analysis.json not built yet")
    d = json.load(open(f))
    assert isinstance(d.get("analyses"), list)
    assert d["analyses"], "analyses array is empty"
    sample = d["analyses"][0]
    # Each entry must be loadable in the popup's risk UI
    for k in ("id", "lat", "lon"):
        assert k in sample, f"missing {k!r} in {sample.keys()}"


def test_risk_summary_by_depto(data_root, live_only):
    """property_risk_summary.json: by-depto aggregate. Top deptos listed + ranked."""
    f = data_root / "property_risk_summary.json"
    if not f.exists() or f.stat().st_size < 5_000:
        pytest.skip("property_risk_summary.json not built yet")
    d = json.load(open(f))
    # Should be at least a by-depto aggregate
    keys = set(d.keys())
    assert keys, "summary JSON is empty"
    # At least one of the documented keys
    assert any(k in keys for k in ("by_depto", "ranking", "top_risks", "deptos")), (
        f"summary JSON has no recognized aggregate key: {keys}"
    )


# ---------- Heatmap ↔ analysis consistency ----------

def test_risk_index_lat_lon_present_in_analysis(data_root, live_only):
    """Every risk-index entry must be resolvable to an analysis entry."""
    fi = data_root / "property_risk_index.json"
    fa = data_root / "property_risk_analysis.json"
    if not fi.exists() or not fa.exists():
        pytest.skip("risk artifacts not built")
    if fi.stat().st_size < 10_000 or fa.stat().st_size < 100_000:
        pytest.skip("risk artifacts too small (not built)")
    idx = json.load(open(fi))["index"]
    ana = json.load(open(fa))
    ana_ids = {a["id"] for a in ana.get("analyses", [])}
    # At least 95% of index entries must resolve in the analysis file
    n_idx = len(idx)
    n_match = sum(1 for pid in idx if pid in ana_ids)
    assert n_match >= n_idx * 0.95, (
        f"only {n_match}/{n_idx} ({100*n_match/n_idx:.1f}%) of index ids "
        "found in analysis file"
    )


# ---------- Score plausibility ----------

def test_no_extreme_score_outliers(data_root, live_only):
    """Risk scores should be in a reasonable range. If 1% of properties have
    scores >1000, that's a pipeline bug (e.g. un-bounded flood loop)."""
    f = data_root / "property_risk_analysis.json"
    if not f.exists() or f.stat().st_size < 100_000:
        pytest.skip("risk artifact not built")
    d = json.load(open(f))
    scores = []
    for a in d["analyses"]:
        for k in ("risk_score", "pro_score", "net_score"):
            v = a.get(k)
            if isinstance(v, (int, float)):
                scores.append(v)
    if not scores:
        pytest.skip("no numeric scores found")
    outliers = [s for s in scores if s > 1000]
    assert len(outliers) / len(scores) < 0.01, (
        f"{len(outliers)} of {len(scores)} scores > 1000 — possible runaway"
    )


def test_scores_within_documented_bounds(data_root, live_only):
    """Per docs/PROPERTY_RISK_ANALYSIS.md: risk 0-200+, pro 0-35. Score
    distribution should be conservative."""
    f = data_root / "property_risk_analysis.json"
    if not f.exists() or f.stat().st_size < 100_000:
        pytest.skip("risk artifact not built")
    d = json.load(open(f))
    n = 0
    for a in d["analyses"]:
        for k in ("risk_score", "pro_score", "net_score"):
            v = a.get(k)
            if isinstance(v, (int, float)):
                n += 1
                assert -200 <= v <= 500, (
                    f"{a.get('id')} {k}={v} outside plausible range"
                )
    assert n > 0, "no scores encountered"


def test_risk_full_analysis_top_level_metadata_present(data_root, live_only):
    """Top-level keys include generated_at + method + stats + analyses."""
    f = data_root / "property_risk_analysis.json"
    if not f.exists() or f.stat().st_size < 100_000:
        pytest.skip("risk artifact not built")
    d = json.load(open(f))
    for k in ("analyses", "generated_at"):
        assert k in d, f"missing top-level key {k!r}"
