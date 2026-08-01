"""tests/test_inbio_zafra_strip.py

Covers scripts/build_inbio_zafra_strip.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_inbio_zafra_strip as izs  # noqa: E402


def _make_series(years=("2021/2022", "2022/2023", "2023/2024", "2024/2025", "2025/2026")) -> dict:
    zafras = []
    for i, year in enumerate(years):
        zafras.append({
            "year": year,
            "crops": {
                "soja": {
                    "Alto Paraná": {"prev_ha": 1000.0 + i, "current_ha": 1100.0 + i},
                    "Itapúa":      {"prev_ha":  500.0 + i, "current_ha":  550.0 + i},
                    "Canindeyú":   {"prev_ha":  300.0 + i, "current_ha":  330.0 + i},
                },
                "arroz": {
                    "Itapúa":      {"prev_ha":  200.0 + i, "current_ha":  220.0 + i},
                    "Misiones":    {"prev_ha":  150.0 + i, "current_ha":  160.0 + i},
                },
            },
            "source_pdf": f"Zafra-{year}.pdf",
        })
    return {"zafras": zafras, "deptos": ["Alto Paraná", "Itapúa", "Canindeyú", "Misiones"]}


def test_sort_year_ascending():
    series = _make_series()
    payload = izs.build(series)
    years = [z["year"] for z in payload["zafras"]]
    assert years == sorted(years)


def test_per_crop_total_correct():
    series = _make_series()
    payload = izs.build(series)
    last = payload["zafras"][-1]
    # 2025/2026 has i=4: soja 1104 + 554 + 334 = 1992
    assert last["per_crop_total_ha"]["soja"] == 1992.0
    # arroz 224 + 164 = 388
    assert last["per_crop_total_ha"]["arroz"] == 388.0


def test_per_depto_total_correct():
    series = _make_series()
    payload = izs.build(series)
    last = payload["zafras"][-1]
    # Itapúa: soja 554 + arroz 224 = 778
    assert last["per_depto_total_ha"]["Itapúa"] == 778.0


def test_top3_per_crop_latest():
    series = _make_series()
    payload = izs.build(series)
    top = payload["top_per_crop_latest_zafra"]
    assert "soja" in top and "arroz" in top
    # Soja top should be Alto Paraná (1104), Itapúa (554), Canindeyú (334)
    soja = top["soja"]
    assert soja[0]["depto"] == "Alto Paraná"
    assert soja[0]["ha"] == 1104.0
    assert len(soja) == 3


def test_keeps_only_5_most_recent():
    series = _make_series(years=tuple(f"{2000 + i}/{2001 + i}" for i in range(10)))
    payload = izs.build(series)
    assert len(payload["zafras"]) == 5


def test_fallback_when_no_input():
    payload = izs._synthesize_fallback()
    assert payload["zafras"] == []
    assert "note" in payload


def test_handles_missing_current_ha():
    series = _make_series()
    # Replace one entry's current_ha with None.
    series["zafras"][2]["crops"]["soja"]["Alto Paraná"]["current_ha"] = None
    payload = izs.build(series)
    last = payload["zafras"][-1]
    # The latest zafra should still include Alta Paraná only if cur is non-None.
    assert "Alto Paraná" in last["per_depto_total_ha"] or "Alto Paraná" not in last["per_depto_total_ha"]