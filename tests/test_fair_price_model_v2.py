"""tests/test_fair_price_model_v2.py

Covers tools/build_fair_price_model_v2.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_fair_price_model_v2 as fpm  # noqa: E402


def _make_features(n_per_depto: int = 40) -> list[dict]:
    """Synthetic deterministic features for two deptos."""
    out = []
    for d_idx, depto in enumerate(("Central", "Asunción")):
        for i in range(n_per_depto):
            # Generated area_ha and bedrooms, plus a price that scales linearly.
            area_ha = 0.5 + (i % 10) * 0.1
            bedrooms = 1 + (i % 4)
            # Strong signal: price ≈ 100,000 + area*200,000 + bedrooms*5,000 + noise
            price = 100_000 + area_ha * 200_000 + bedrooms * 5_000 + d_idx * 10_000 + (i % 3) * 1_000
            out.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-55, -25]},
                "properties": {
                    "id": f"x_{d_idx}_{i}",
                    "state_province": depto,
                    "listing_type": "sale",
                    "price_usd": price,
                    "area_ha": area_ha,
                    "bedrooms": bedrooms,
                    "bathrooms": 1,
                    "parking_spaces": 1,
                    "canonical_features": ["pool", "airConditioning"] if i % 2 == 0 else [],
                    "quality_flags": [],
                },
            })
    return out


def test_skips_currency_conflict_rows():
    feats = _make_features(10)
    feats[0]["properties"]["quality_flags"] = ["currency_conflict"]
    result = fpm._build_per_depto(feats)
    # The skipped row is dropped from training
    assert result["skipped_quality_or_unusable"] == 1


def test_skips_rent_rows():
    feats = _make_features(10)
    feats[0]["properties"]["listing_type"] = "rent"
    result = fpm._build_per_depto(feats)
    assert result["skipped_quality_or_unusable"] == 1


def test_too_few_rows_uses_global_fallback():
    # 6 per depto × 2 deptos = 12 total.  Each depto is "too few" (n<10) but
    # the union is enough to fit a global model.
    feats = _make_features(n_per_depto=6)
    result = fpm._build_per_depto(feats)
    for d in ("Central", "Asunción"):
        assert result["per_depto"][d]["r2"] is None
        assert "too_few_rows" in result["per_depto"][d]["note"]
    # Global fallback is built from the union of all rows
    assert "_global_" in result["per_depto"]
    assert result["per_depto"]["_global_"]["r2"] is not None


def test_per_depto_r2_reasonable():
    feats = _make_features(n_per_depto=40)
    result = fpm._build_per_depto(feats)
    for d in ("Central", "Asunción"):
        m = result["per_depto"][d]
        # Synthetic data has a strong linear signal but with small noise from
        # (i%3)*1000; expect R² >= 0.85 — better than the v1 model's 0.017.
        assert m["r2"] > 0.85, f"{d} R²={m['r2']} should be near 1"
        # MAE on noisy synthetic data — keep the bound generous.
        assert m["mae_usd"] < 20_000


def test_deterministic_seed():
    feats = _make_features(40)
    a = fpm._build_per_depto(feats)["per_depto"]["Central"]
    b = fpm._build_per_depto(feats)["per_depto"]["Central"]
    assert a["coefficients"] == b["coefficients"]


def test_empty_input_safe():
    result = fpm._build_per_depto([])
    assert result["per_depto"] == {}
    assert result["skipped_quality_or_unusable"] == 0


def test_missing_depto_falls_back_to_global():
    feats = _make_features(40)
    # Replace one Central row with an unknown depto — model still trains.
    feats[0]["properties"]["state_province"] = "_unknown_"
    result = fpm._build_per_depto(feats)
    assert result["per_depto"]["_global_"]["r2"] > 0.9