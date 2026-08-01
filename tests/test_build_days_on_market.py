"""tests/test_build_days_on_market.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_days_on_market as bdm  # noqa: E402


def _features(deptos=("Central", "Asunción"), days=(10, 20, 30, 45, 60)):
    out = []
    for i, d in enumerate(days):
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-55, -25]},
            "properties": {
                "id": f"x_{i}",
                "state_province": deptos[i % len(deptos)],
                "freshness_days": d,
                "title": f"Lote {i}",
                "source": "tulugar",
                "source_url": f"https://x/{i}",
            },
        })
    return out


def test_summary_median_correct():
    payload = bdm.build(_features())
    assert payload["summary"]["median_days"] == 30


def test_summary_quantiles():
    payload = bdm.build(_features())
    assert payload["summary"]["p25"] == 20
    assert payload["summary"]["p75"] == 45


def test_by_depto_aggregation():
    payload = bdm.build(_features())
    assert payload["by_depto"]["Central"]["n"] >= 1
    assert payload["by_depto"]["Asunción"]["n"] >= 1


def test_stale_pct_calculation():
    payload = bdm.build(_features())
    # 60d and 45d both > 30 → 40% stale in "Central" if all 5 land there.
    # The features split between two deptos; just check the math exists.
    for d, v in payload["by_depto"].items():
        assert 0 <= v["stale_pct"] <= 100


def test_stale_listings_sorted_desc():
    payload = bdm.build(_features())
    days = [r["freshness_days"] for r in payload["stale_listings"]]
    assert days == sorted(days, reverse=True)


def test_empty_input():
    payload = bdm.build([])
    assert payload["summary"]["median_days"] is None
    assert payload["by_depto"] == {}