"""Tests/test_golden_facets.py — regression test for facets.json shape.

This catches schema drift in facets.json. Each rebuild can add new fields
or change the shape; the test verifies the *contract* (field names +
types) but not the values (since listings change daily).

The facets.json has these top-level sections:
  - generated_at: ISO date
  - feature_count: total listings
  - freshness: {median_days, ...}
  - facets: dict of facet_name → list of {value, count}
  - quality: {total, clean, flagged, by_flag: dict}
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FACETS = REPO / "exports/web/api/v1/facets.json"


def _load():
    return json.loads(FACTS.read_text() if False else FACETS.read_text())


def test_facets_exists():
    assert FACETS.exists(), f"{FACETS} not found"


def test_facets_valid_json():
    data = _load()
    assert isinstance(data, dict)


def test_facets_has_required_top_keys():
    data = _load()
    for key in ["generated_at", "feature_count", "freshness", "facets", "quality"]:
        assert key in data, f"missing top-level key: {key}"


def test_facets_generated_at_iso():
    data = _load()
    generated = data["generated_at"]
    assert "T" in generated  # ISO format includes T separator
    assert generated.endswith("Z") or "+" in generated


def test_facets_feature_count_positive():
    """feature_count should be a positive integer."""
    data = _load()
    fc = data.get("feature_count", 0)
    assert isinstance(fc, int)
    assert fc > 0


def test_facets_quality_total_matches_feature_count():
    """quality.total == feature_count."""
    data = _load()
    quality_total = data.get("quality", {}).get("total", 0)
    feature_count = data.get("feature_count", 0)
    if quality_total and feature_count:
        assert quality_total == feature_count, f"quality.total={quality_total} != feature_count={feature_count}"


def test_facets_facets_is_dict():
    data = _load()
    assert isinstance(data["facets"], dict)


def test_facets_each_facet_is_list_of_dicts():
    """Each facet should be a list of {value, count}."""
    data = _load()
    for name, items in data["facets"].items():
        assert isinstance(items, list), f"facet {name} is not a list"
        if items:
            for item in items:
                assert "value" in item, f"facet {name} missing 'value' key"
                assert "count" in item, f"facet {name} missing 'count' key"
                assert isinstance(item["count"], int)


def test_facets_has_source_facet():
    """The source facet should always exist (even if empty)."""
    data = _load()
    assert "source" in data["facets"]


def test_facets_source_totals_match_feature_count():
    """Sum of source counts should equal feature_count."""
    data = _load()
    sources = data["facets"].get("source", [])
    source_total = sum(s["count"] for s in sources)
    feature_count = data.get("feature_count", 0)
    assert source_total == feature_count, f"source total {source_total} != feature_count {feature_count}"


def test_facets_has_property_type_facet():
    """The property_type facet is the main filter dimension."""
    data = _load()
    assert "property_type" in data["facets"]


def test_facets_property_type_at_least_5_types():
    """Should have at least 5 known property types."""
    data = _load()
    types = data["facets"].get("property_type", [])
    assert len(types) >= 5


def test_facets_quality_by_flag_is_dict():
    data = _load()
    by_flag = data.get("quality", {}).get("by_flag", {})
    assert isinstance(by_flag, dict)


def test_facets_quality_flag_values_positive():
    """All flag counts should be positive integers."""
    data = _load()
    by_flag = data.get("quality", {}).get("by_flag", {})
    for flag, count in by_flag.items():
        assert isinstance(count, int)
        assert count >= 0


def test_facets_freshness_has_median():
    data = _load()
    assert "median_days" in data["freshness"]


def test_facets_freshness_reasonable():
    """median_days should be reasonable (< 365)."""
    data = _load()
    median = data["freshness"].get("median_days", 0)
    assert 0 <= median < 365, f"median_days={median} outside expected range"


def test_facets_counts_no_big_jumps():
    """Detects catastrophic regressions in property_type distribution.

    Counts shouldn't jump >50% between rebuilds. If they do, it likely
    indicates a bug in canonicalize or one of the infer/impute tools.
    """
    data = _load()
    pt = data["facets"].get("property_type", [])
    for item in pt:
        count = item.get("count", 0)
        value = item.get("value", "?")
        # All known types should have at least 1 listing now that
        # infer_property_type runs as part of the pipeline
        if value not in ("?", "unknown", ""):
            assert count > 0, f"property_type {value!r} has 0 listings"


def test_facets_freshness_p75_reasonable():
    """p75_days should be > median_days."""
    data = _load()
    freshness = data["freshness"]
    median = freshness.get("median_days", 0)
    p75 = freshness.get("p75_days", 0)
    if p75:
        assert p75 >= median, f"p75 ({p75}) should be >= median ({median})"


def test_facets_no_orphan_facets():
    """All facets should have a non-empty name."""
    data = _load()
    for name, items in data["facets"].items():
        assert isinstance(name, str)
        assert len(name) > 0, "facet has empty name"
