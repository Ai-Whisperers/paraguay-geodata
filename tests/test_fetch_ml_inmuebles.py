"""tests/test_fetch_ml_inmuebles.py

Covers tools/fetch_ml_inmuebles.py with synthetic polycard JSON.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_ml_inmuebles as fml  # noqa: E402


def _polycard(**over):
    base = {
        "id": "MLA-12345678",
        "title": "Casa 3 dormitorios en San Lorenzo",
        "permalink": "https://articulo.mercadolibre.com.py/MLA-12345678-casa-_JM",
        "price": {"amount": 500_000_000, "currency_id": "PYG"},
        "currency_id": "PYG",
        "attributes": [
            {"name": "COVERED_AREA", "value_name": "180 m² cubiertos"},
            {"name": "BEDROOMS", "value_name": "3"},
            {"name": "FULL_BATHROOMS", "value_name": "2"},
        ],
        "location": {"latitude": -25.34, "longitude": -57.52},
        "address": {"city_name": "San Lorenzo", "state_name": "Central"},
        "pictures": ["https://http2.mlstatic.com/D_NQ_NP_2x_test.jpg"],
    }
    base.update(over)
    return base


def test_parse_polycard_core_fields():
    feat = fml._parse_polycard(_polycard(), "https://inmuebles.mercadolibre.com.py/casa/venta")
    assert feat is not None
    p = feat["properties"]
    assert p["source"] == "mercadolibre"
    assert p["city"] == "San Lorenzo"
    assert p["state_province"] == "Central"
    assert p["price_pyg"] == 500_000_000
    assert p["price_usd"] == round(500_000_000 / 7500, 2)
    assert p["area_sqm"] == 180.0
    assert p["bedrooms"] == 3
    assert p["bathrooms"] == 2


def test_parse_polycard_usd():
    feat = fml._parse_polycard(_polycard(
        price={"amount": 80_000, "currency_id": "USD"},
        currency_id="USD",
    ), "https://x")
    p = feat["properties"]
    assert p["price_usd"] == 80_000
    assert p["price_pyg"] == 600_000_000


def test_parse_polycard_drops_missing_coords():
    pc = _polycard()
    pc["location"] = {"latitude": None, "longitude": None}
    assert fml._parse_polycard(pc, "https://x") is None


def test_parse_polycard_drops_out_of_bounds():
    pc = _polycard(location={"latitude": -34.9, "longitude": -56.0})  # Montevideo
    assert fml._parse_polycard(pc, "https://x") is None


def test_parse_polycard_drops_unknown_currency():
    pc = _polycard()
    pc["price"]["currency_id"] = "BRL"
    assert fml._parse_polycard(pc, "https://x") is None


def test_property_type_mapping():
    assert fml._map_property_type("Casa en venta") == "house"
    assert fml._map_property_type("Departamento de 2 dormitorios") == "apartment"
    assert fml._map_property_type("Terreno en San Lorenzo") == "land"
    assert fml._map_property_type("Oficina comercial") == "commercial"
    assert fml._map_property_type("Local comercial") == "commercial"


def test_no_fetch_emits_empty_envelope(tmp_path):
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_ml_inmuebles", "--no-fetch",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stderr
    files = list(tmp_path.glob("mercadolibre_*.geojson"))
    assert len(files) == 1
    d = json.loads(files[0].read_text())
    assert d["feature_count"] == 0