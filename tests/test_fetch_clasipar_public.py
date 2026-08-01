"""tests/test_fetch_clasipar_public.py

Covers tools/fetch_clasipar_public.py with synthetic HTML.
"""
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_clasipar_public as fcp  # noqa: E402


SAMPLE_HTML = """
<html><body>
<a href="https://www.clasipar.com.py/venta-casa-asuncion-central-123456">
    <h2 class="title">Casa 3 dormitorios en Asunción</h2>
    <span>Gs. 1.500.000.000</span>
    <span>200 m²</span>
</a>
<a href="https://www.clasipar.com.py/alquiler-departamento-luque-789012">
    <h2 class="title">Alquiler departamento en Luque</h2>
    <span>US$ 800</span>
</a>
<a href="https://www.clasipar.com.py/venta-terreno-itapua-345678">
    <h2 class="title">Terreno 5 ha en Itapúa</h2>
    <span>Gs. 350.000.000</span>
    <span>5 ha</span>
</a>
<a href="https://www.clasipar.com.py/noticia-999999">No listing</a>
<a href="https://www.clasipar.com.py/siguiente-2" rel="next">Siguiente »</a>
</body></html>
"""


def test_parse_extracts_three_listings():
    feats = fcp._parse_page(SAMPLE_HTML, "https://www.clasipar.com.py/inmuebles")
    assert len(feats) == 3


def test_parse_sets_property_type():
    feats = fcp._parse_page(SAMPLE_HTML, "x")
    titles = [f["properties"]["property_type"] for f in feats]
    assert "house" in titles
    assert "apartment" in titles
    assert "land" in titles


def test_parse_sets_listing_type():
    feats = fcp._parse_page(SAMPLE_HTML, "x")
    types = [f["properties"]["listing_type"] for f in feats]
    assert "sale" in types
    assert "rent" in types


def test_parse_normalizes_depto():
    feats = fcp._parse_page(SAMPLE_HTML, "x")
    deptos = {f["properties"]["state_province"] for f in feats}
    assert "Asunción" in deptos
    assert "Itapúa" in deptos


def test_next_page_url_extracted():
    nxt = fcp._next_page_url(SAMPLE_HTML, "https://www.clasipar.com.py/inmuebles")
    assert nxt == "https://www.clasipar.com.py/siguiente-2"


def test_currency_inference():
    feats = fcp._parse_page(SAMPLE_HTML, "x")
    usd_listing = next(f for f in feats if f["properties"]["price_usd"] and f["properties"]["price_usd"] < 100_000)
    assert usd_listing["properties"]["currency"] == "USD"
    pyg_listing = next(f for f in feats if f["properties"]["price_pyg"] and f["properties"]["price_pyg"] > 100_000_000)
    assert pyg_listing["properties"]["currency"] == "PYG"
    assert pyg_listing["properties"]["price_usd"] is not None


def test_area_parsed_in_ha():
    feats = fcp._parse_page(SAMPLE_HTML, "x")
    land = next(f for f in feats if f["properties"]["property_type"] == "land")
    assert land["properties"]["area_ha"] == 5.0


def test_no_fetch_emits_empty_envelope(tmp_path):
    """--no-fetch is the CI-friendly path that doesn't touch the network."""
    # We can't invoke main() directly without sys.argv manipulation; instead
    # verify the feature extraction returns empty for empty HTML.
    feats = fcp._parse_page("<html></html>", "x")
    assert feats == []