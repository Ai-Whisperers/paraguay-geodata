"""Tests for tools/infer_property_type.py — infer property_type from title/area/bedrooms."""
from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "infer_property_type",
        REPO / "tools" / "infer_property_type.py",
    )
    assert spec is not None
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


mod = _load()


def test_help():
    """CLI is wired up."""
    r = subprocess.run(
        ["python3", "-m", "tools.infer_property_type", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_dry_run_no_write():
    """--dry-run does not modify canonical_properties.geojson."""
    import hashlib
    before = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    r = subprocess.run(
        ["python3", "-m", "tools.infer_property_type", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0
    after = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    assert before == after, "dry-run modified canonical_properties.geojson"


def test_infer_from_title_casa():
    assert mod.infer_from_title("Casa en venta en Asunción") == "house"


def test_infer_from_title_departamento():
    assert mod.infer_from_title("Departamento 3 dormitorios") == "apartment"
    assert mod.infer_from_title("Depto en Recoleta") == "apartment"


def test_infer_from_title_terreno():
    assert mod.infer_from_title("Terreno de 1,000m² en Venta") == "land"
    assert mod.infer_from_title("Lote en San Bernardino") == "land"


def test_infer_from_title_commercial():
    assert mod.infer_from_title("Galpón en zona industrial") == "commercial"
    assert mod.infer_from_title("Local comercial en centro") == "commercial"


def test_infer_from_title_office():
    assert mod.infer_from_title("Oficina amoblada") == "office"


def test_infer_from_title_casa_wins_over_terreno():
    """Casa + terreno → house (casa mentioned first)."""
    result = mod.infer_from_title("Casa con terreno de 1,000m² en Asunción")
    assert result == "house"


def test_infer_from_title_no_match():
    assert mod.infer_from_title("XYZ") is None
    assert mod.infer_from_title("") is None
    assert mod.infer_from_title(None) is None


def test_infer_from_area_50ha_plus_is_land():
    """50+ ha is unmistakably land."""
    assert mod.infer_from_area(50) == "land"
    assert mod.infer_from_area(1000) == "land"


def test_infer_from_area_200sqm_plus_is_house():
    """200+ sqm (0.02 ha) is likely a house."""
    assert mod.infer_from_area(0.02) == "house"
    assert mod.infer_from_area(0.05) == "house"


def test_infer_from_area_30_to_200sqm_is_apartment():
    """30-200 sqm is the typical apartment range."""
    assert mod.infer_from_area(0.003) == "apartment"
    assert mod.infer_from_area(0.015) == "apartment"


def test_infer_from_bedrooms_3_plus_is_house():
    assert mod.infer_from_bedrooms(3) == "house"
    assert mod.infer_from_bedrooms(5) == "house"


def test_infer_from_bedrooms_1_to_2_is_apartment():
    assert mod.infer_from_bedrooms(1) == "apartment"
    assert mod.infer_from_bedrooms(2) == "apartment"


def test_infer_from_bedrooms_0_is_land():
    assert mod.infer_from_bedrooms(0) == "land"


def test_infer_property_type_priority_title_beats_area():
    """Title wins over area when both could give signals."""
    result = mod.infer_property_type({
        "property_type": None,
        "title": "Casa en venta",
        "area_ha": 0.5,  # would say apartment
    })
    assert result == ("house", "title")


def test_infer_property_type_fallback_to_bedrooms():
    """When title is empty, fall back to bedrooms."""
    result = mod.infer_property_type({
        "property_type": None,
        "title": "",
        "area_ha": None,
        "bedrooms": 4,
    })
    assert result == ("house", "bedrooms")


def test_infer_property_type_no_signal():
    """All empty → None."""
    result = mod.infer_property_type({
        "property_type": None,
        "title": "",
        "area_ha": None,
        "bedrooms": None,
    })
    assert result is None


def test_infer_dry_run_reduces_unknown_count():
    """A dry run with the current data should infer >1000 unknowns."""
    r = subprocess.run(
        ["python3", "-m", "tools.infer_property_type", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0
    m = re.search(r"inferred:\s+([\d,]+)", r.stdout)
    assert m, f"no 'inferred:' line in output: {r.stdout[-500:]}"
    n = int(m.group(1).replace(",", ""))
    assert n >= 1000, f"only inferred {n} (expected ≥1000)"
