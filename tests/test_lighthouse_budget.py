"""Tests for lighthouse-budget.json — the perf/a11y/SEO gate.

These tests verify the budget file is well-formed and the assertion
thresholds are sane. They don't run actual Lighthouse (that needs a
real browser and happens in CI), but they catch:
  - Invalid JSON
  - Missing required fields (path, timings, assertions)
  - minScore thresholds outside 0.5-1.0 range
  - Resource budget entries without a budget number
"""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BUDGET = REPO / "lighthouse-budget.json"


def _budget():
    return json.loads(BUDGET.read_text())


def test_valid_json():
    data = _budget()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_required_fields():
    """Every entry has path, timings, assertions, resourceSizes."""
    for entry in _budget():
        assert "path" in entry, f"entry missing path: {entry}"
        assert "resourceSizes" in entry
        assert "timings" in entry
        assert "assertions" in entry


def test_path_glob_present():
    """At least one entry matches all paths (the /* entry)."""
    paths = [e["path"] for e in _budget()]
    assert "/*" in paths, f"missing default /* path, got: {paths}"


def test_assertion_thresholds_sane():
    """Every minScore is in [0.5, 1.0]."""
    for entry in _budget():
        for assertion, rule in entry["assertions"].items():
            assert isinstance(rule, list), f"{assertion}: rule must be list"
            assert len(rule) >= 2, f"{assertion}: rule too short"
            assert rule[0] in ("error", "warn", "off"), f"{assertion}: invalid severity {rule[0]}"
            min_score = rule[1].get("minScore")
            assert min_score is not None, f"{assertion}: missing minScore"
            assert 0.5 <= min_score <= 1.0, f"{assertion}: {min_score} outside [0.5, 1.0]"


def test_resource_budgets_have_numbers():
    """Every resourceSizes entry has a positive budget."""
    for entry in _budget():
        for rs in entry["resourceSizes"]:
            assert "resourceType" in rs, f"missing resourceType: {rs}"
            assert "budget" in rs, f"missing budget: {rs}"
            assert rs["budget"] > 0, f"budget must be positive: {rs}"


def test_timing_budgets_have_metric():
    """Every timings entry has a metric name."""
    valid_metrics = {
        "first-contentful-paint", "largest-contentful-paint",
        "total-blocking-time", "cumulative-layout-shift",
        "interactive", "speed-index",
    }
    for entry in _budget():
        for tm in entry["timings"]:
            assert "metric" in tm, f"missing metric: {tm}"
            assert "budget" in tm, f"missing budget: {tm}"
            assert tm["budget"] > 0, f"timing budget must be positive: {tm}"
            assert tm["metric"] in valid_metrics, f"unknown metric: {tm['metric']}"


def test_perf_threshold_at_least_seventy():
    """Performance score threshold ≥ 0.70 — below that the site is unusable."""
    for entry in _budget():
        perf = entry["assertions"].get("categories:performance")
        if perf:
            score = perf[1].get("minScore", 0)
            assert score >= 0.70, f"{entry['path']}: perf threshold {score} < 0.70"
