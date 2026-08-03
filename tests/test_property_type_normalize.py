"""Tests for the property_type normalisation in canonicalize_properties."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import canonicalize_properties as cp  # noqa: E402


def test_normalize_none_and_empty():
    assert cp._normalize_property_type(None) == "unknown"
    assert cp._normalize_property_type("") == "unknown"


def test_normalize_unknown_markers():
    for v in ("?", "na", "n/a", "none", "null"):
        assert cp._normalize_property_type(v) == "unknown", v


def test_normalize_exact_aliases():
    assert cp._normalize_property_type("house") == "house"
    assert cp._normalize_property_type("houses") == "house"
    assert cp._normalize_property_type("casa") == "house"
    assert cp._normalize_property_type("casas") == "house"
    assert cp._normalize_property_type("departamento") == "apartment"
    assert cp._normalize_property_type("departamentos") == "apartment"
    assert cp._normalize_property_type("depto") == "apartment"
    assert cp._normalize_property_type("terreno") == "land"
    assert cp._normalize_property_type("terrenos") == "land"
    assert cp._normalize_property_type("lote") == "land"
    assert cp._normalize_property_type("quinta") == "house"
    assert cp._normalize_property_type("oficina") == "office"
    assert cp._normalize_property_type("oficinas") == "office"
    assert cp._normalize_property_type("local") == "commercial"
    assert cp._normalize_property_type("locales") == "commercial"
    assert cp._normalize_property_type("galpon") == "commercial"
    assert cp._normalize_property_type("galpón") == "commercial"


def test_normalize_substring_matching():
    """When the value contains a known alias, we should match."""
    assert cp._normalize_property_type("casa con piscina") == "house"
    assert cp._normalize_property_type("departamento amoblado") == "apartment"
    assert cp._normalize_property_type("terreno en venta") == "land"


def test_normalize_case_insensitive():
    assert cp._normalize_property_type("CASA") == "house"
    assert cp._normalize_property_type("Departamento") == "apartment"
    assert cp._normalize_property_type("TERRENO") == "land"


def test_normalize_unknown_values():
    """Random values return 'unknown'."""
    assert cp._normalize_property_type("xyz") == "unknown"
    assert cp._normalize_property_type("foo123") == "unknown"
    assert cp._normalize_property_type("~~~") == "unknown"
