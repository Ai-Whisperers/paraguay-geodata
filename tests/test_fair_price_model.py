"""Fair-price ML model contract tests — T4 from the audit matrix.

covers exports/web/data/ml/fair_price_model.json
The model is r² ≈ 0.017 (ui decoration per status.md), but the *shape*
must remain stable so index.html never crashes loading it. a model that
switches from dict-of-coefs to a nested object would silently break every
popup that shows a fair-price badge.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


REQUIRED_BUCKET_KEYS = {"intercept", "coefs", "r2", "samples"}
REQUIRED_TOP_KEYS = {
    "as_of", "model_version", "training_samples",
    "feature_columns", "depto_models", "global_fallback",
}
REQUIRED_FALLBACK_KEYS = {"intercept", "coefs", "r2"}


@pytest.fixture
def fpm(data_root):
    f = data_root / "ml" / "fair_price_model.json"
    if not f.exists():
        pytest.skip("fair_price_model.json not built yet")
    return f


@pytest.fixture
def model(fpm):
    return json.load(open(fpm))


# ---------- Top-level schema ----------

def test_top_level_keys(model):
    expected = {
        "as_of", "model_version", "training_samples",
        "feature_columns", "depto_models", "global_fallback",
    }
    missing = expected - set(model.keys())
    assert not missing, f"missing required keys: {missing}"


def test_as_of_is_iso_datetime(model):
    """as_of is documented as datetime.now(timezone.utc).isoformat()."""
    as_of = model["as_of"]
    assert isinstance(as_of, str)
    # Accept date-only or full ISO with optional microseconds + offset
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}:\d{2})?)?$",
        as_of,
    ), f"not an iso datetime: {as_of!r}"


def test_model_version_is_semver_style(model):
    v = model["model_version"]
    parts = v.split(".")
    assert len(parts) >= 2 and all(p.isdigit() for p in parts), (
        f"model_version {v!r} should be semver (MAJOR.MINOR)"
    )


def test_training_samples_is_positive_int(model):
    n = model["training_samples"]
    assert isinstance(n, int) and n > 0


def test_feature_columns_are_known_features(model):
    cols = model["feature_columns"]
    expected_subset = {"log_area", "lat", "lon", "beds"}
    assert expected_subset.issubset(set(cols)), (
        f"feature_columns missing known features: "
        f"got {cols}, expected subset {expected_subset}"
    )


def test_global_stats_when_present_has_known_keys(model):
    gs = model.get("global_stats")
    if gs is None:
        return  # optional
    expected_subset = {"mean_per_ha", "median_per_ha"}
    missing = expected_subset - set(gs.keys())
    assert not missing, f"global_stats missing {missing}"


# ---------- Depto models (per-depto bucket) ----------

def test_depto_models_is_dict(model):
    assert isinstance(model.get("depto_models"), dict)


def test_depto_models_have_required_keys(model):
    bad = []
    for depto, payload in model["depto_models"].items():
        missing = REQUIRED_BUCKET_KEYS - set(payload.keys())
        if missing:
            bad.append((depto, missing))
    assert not bad, f"depto_models missing keys: {bad}"


def test_depto_models_have_min_30_samples(model):
    for depto, payload in model["depto_models"].items():
        if "samples" in payload:
            assert payload["samples"] >= 30, (
                f"{depto} has only {payload['samples']} samples — "
                "should have been suppressed"
            )


def test_depto_models_coefs_have_feature_keys(model):
    expected = {"log_area", "lat", "lon", "beds"}
    for depto, payload in model["depto_models"].items():
        coefs = payload.get("coefs") or {}
        missing = expected - set(coefs.keys())
        assert not missing, f"{depto} coefs missing {missing}"


def test_depto_models_keys_are_paraguayan_deptos(model):
    for depto in model.get("depto_models", {}):
        assert re.match(r"^[A-ZÁÉÍÓÚÑ][\w\s\-\(\)]+$", depto, re.UNICODE), (
            f"non-standard depto key: {depto!r}"
        )


# ---------- Global fallback ----------

def test_global_fallback_has_minimum_keys(model):
    fb = model["global_fallback"]
    missing = REQUIRED_FALLBACK_KEYS - set(fb.keys())
    assert not missing, f"global_fallback missing: {missing}"


# ---------- R² sanity ----------

def test_r2_is_finite_nonnegative(model):
    for depto, payload in model["depto_models"].items():
        r2 = payload.get("r2")
        assert isinstance(r2, (int, float)), f"{depto} r2 is not numeric"
        assert 0 <= r2 <= 1.001, f"{depto} r²={r2} out of bounds"
    fg = model.get("global_fallback", {})
    if "r2" in fg:
        r2 = fg["r2"]
        assert isinstance(r2, (int, float))
        assert 0 <= r2 <= 1.001, f"global_fallback r²={r2} out of bounds"


# ---------- Cross-checks ----------

def test_total_per_depto_samples_does_not_exceed_training_count(model):
    total = sum(b.get("samples", 0) for b in model["depto_models"].values())
    n = model["training_samples"]
    assert total <= n, f"depto total {total} > training_samples {n}"


def test_model_file_size_is_small(fpm):
    sz = fpm.stat().st_size
    assert sz < 50_000, f"{sz} bytes — too large for a UI decoration model"
