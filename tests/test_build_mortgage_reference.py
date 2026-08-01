"""tests/test_build_mortgage_reference.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_mortgage_reference as bmr  # noqa: E402


def test_monthly_payment_known_value():
    # 100,000 USD at 10% over 10 years ≈ 1,321 USD/mo (amortization formula)
    p = bmr._monthly_payment(100_000, 10.0, 10)
    assert 1_310 < p < 1_330


def test_zero_rate_is_principal_over_n():
    p = bmr._monthly_payment(120_000, 0, 10)
    assert p == 1_000.0


def test_build_emits_5_scenarios():
    payload = bmr.build(median_price_usd=90_000, rate_pct=11.5, ltv=0.70)
    assert len(payload["scenarios"]) == 5
    years = [s["years"] for s in payload["scenarios"]]
    assert years == [10, 15, 20, 25, 30]


def test_ltv_applied_to_principal():
    payload = bmr.build(median_price_usd=100_000, rate_pct=11.5, ltv=0.80)
    assert payload["scenarios"][0]["loan_usd"] == 80_000


def test_interest_increases_with_term():
    payload = bmr.build(median_price_usd=90_000, rate_pct=11.5, ltv=0.70)
    interests = [s["interest_usd"] for s in payload["scenarios"]]
    # Longer terms pay more total interest at fixed rate.
    for a, b in zip(interests, interests[1:]):
        assert a < b


def test_monthly_decreases_with_term():
    payload = bmr.build(median_price_usd=90_000, rate_pct=11.5, ltv=0.70)
    monthly = [s["monthly_usd"] for s in payload["scenarios"]]
    # At fixed rate + fixed principal, monthly payment decreases with term.
    for a, b in zip(monthly, monthly[1:]):
        assert a > b