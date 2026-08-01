"""Regression tests for tools/fetch_properties.py area extraction.

The historical `1HA` false-match bug: a regex that scanned the whole HTML
matched a base64 substring `1HA` and returned area_ha=1.0 for a listing
that was actually 525 m².  These tests pin the fix in place.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_properties as fp  # noqa: E402


def _with_base64_padding(real_area_m2: int):
    """Wrap a small snippet in synthetic HTML with a base64 block that
    contains "1HA" — the exact bug pattern from production data."""
    import base64
    blob = base64.b64encode(b"AAAA1HA" + b"X" * 200).decode("ascii")
    return (
        '<html><head><meta name="description" content="Terreno de '
        f'{real_area_m2} m2"></head>'
        '<body><img src="data:image/png;base64,' + blob + '" /></body></html>'
    )


def test_extract_area_ha_from_structured_json():
    """The primary fix: read m2 from the structured JSON line."""
    html = (
        '<html><body>'
        '{"field":"m2Terrain","value":"525 m2","text":"M2 del terreno"},'
        '{"field":"m2Cubiertos","value":"120 m2","text":"M2 cubiertos"}'
        '</body></html>'
    )
    assert fp._extract_area_ha(html) == 0.0525  # 525 m² → 0.0525 ha


def test_extract_area_ha_avoids_base64_false_match():
    """The actual bug: a base64 string containing '1HA' would be picked
    up by the loose regex and return 1.0 instead of 0.0525."""
    html = _with_base64_padding(525)
    result = fp._extract_area_ha(html)
    # Must NOT be 1.0 (the buggy value).
    assert result != 1.0
    assert result == 0.0525


def test_extract_area_ha_from_m2_in_head():
    """Plain m² in the head (first 30K chars) parses correctly."""
    html = '<html><head><title>Terreno 525 m2 en Obligado</title></head></html>'
    assert fp._extract_area_ha(html) == 0.0525


def test_extract_area_ha_from_hectares():
    # ASCII variant (the é variant also matches the same regex pattern
    # because regex is case-insensitive across byte boundaries).
    html = '<html><body>Terreno de 20 hectareas en Encarnacion</body></html>'
    assert fp._extract_area_ha(html) == 20.0


def test_extract_area_ha_handles_thousands_separator():
    html = '<html><body>1,200 m2 cubiertos</body></html>'
    assert fp._extract_area_ha(html) == 0.12


def test_extract_area_ha_returns_none_when_no_signal():
    html = '<html><body>No area mentioned here</body></html>'
    assert fp._extract_area_ha(html) is None