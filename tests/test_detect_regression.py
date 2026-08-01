#!/usr/bin/env python3
"""tests/test_detect_regression.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import detect_regression as dr  # noqa: E402


def _make(path: Path, n: int, deptos=("Central", "Asunción", "Itapúa")):
    feats = [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-55, -25]},
         "properties": {
             "state_province": deptos[i % len(deptos)],
             "property_type": "land",
             "currency": "USD",
         }} for i in range(n)
    ]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding="utf-8")


def test_pass_when_count_grows(tmp_path):
    last = tmp_path / "last.geojson"
    cur  = tmp_path / "cur.geojson"
    _make(last, 1000)
    _make(cur, 1100)
    assert dr.main(["--current", str(cur), "--last", str(last), "--max-shrink-pct", "30"]) == 0


def test_fail_when_count_shrinks_too_much(tmp_path):
    last = tmp_path / "last.geojson"
    cur  = tmp_path / "cur.geojson"
    _make(last, 1000)
    _make(cur, 600)  # 40% shrink
    assert dr.main(["--current", str(cur), "--last", str(last), "--max-shrink-pct", "30"]) == 1


def test_fail_when_deptos_collapse(tmp_path):
    last = tmp_path / "last.geojson"
    cur  = tmp_path / "cur.geojson"
    _make(last, 5000, deptos=tuple(f"Depto{i}" for i in range(18)))
    _make(cur,  5000, deptos=("Central",))  # canonicalization broken
    assert dr.main(["--current", str(cur), "--last", str(last)]) == 2