"""Tests for tools/extract_listing_metadata.py — extract area, bedrooms, address, barrio from title."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "extract_listing_metadata",
        REPO / "tools" / "extract_listing_metadata.py",
    )
    assert spec is not None
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


mod = _load()


def test_help():
    """CLI is wired up."""
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.extract_listing_metadata", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_parse_decimal_spanish():
    """Spanish-style '1.000,59' parses as 1000.59."""
    assert mod.parse_decimal("1.000,59") == 1000.59
    assert mod.parse_decimal("1.000") == 1000
    assert mod.parse_decimal("350") == 350


def test_parse_decimal_english():
    """English-style '1,000.59' parses as 1000.59."""
    assert mod.parse_decimal("1,000.59") == 1000.59
    assert mod.parse_decimal("1,000") == 1000


def test_parse_decimal_argentine():
    """Argentine-style '2.200.000' parses as 2200000 (no decimal)."""
    assert mod.parse_decimal("2.200.000") == 2200000
    assert mod.parse_decimal("1.080") == 1080


def test_extract_area_m2():
    """Extract area from 'Terreno de 1,000.59m²'."""
    result = mod.extract_area("Terreno de 1,000.59m² en Venta")
    assert result is not None
    assert result[0] == 0.1001  # 1000.59 sqm / 10000 = 0.1001 ha
    assert result[1] == "title_m2"


def test_extract_area_m2_alt():
    """Extract area from 'Vendo 1.080 Mts2'."""
    result = mod.extract_area("Vendo 1.080 Mts2. Barrio San Jorge")
    assert result is not None
    assert result[0] == 0.108  # 1080 sqm / 10000 = 0.108 ha


def test_extract_area_ha():
    """Extract area from '5 hectareas'."""
    result = mod.extract_area("5 hectáreas en Itapúa")
    assert result is not None
    assert result[0] == 5.0
    assert result[1] == "title_ha"


def test_extract_area_no_match():
    """Returns None when no area pattern found."""
    assert mod.extract_area("Casa en venta en Asunción") is None
    assert mod.extract_area("") is None
    assert mod.extract_area(None) is None


def test_extract_area_ignores_distance():
    """Distance-to-reference like 'A 30 metros de la Avenida' should NOT match."""
    result = mod.extract_area("En Venta Terreno A 30 Metros De La Avenida")
    assert result is None, f"false positive: {result}"


def test_extract_bedrooms_number():
    """Extract from '3 dormitorios'."""
    assert mod.extract_bedrooms("Departamento 3 dormitorios en Recoleta") == 3
    assert mod.extract_bedrooms("Casa de 4 dormitorios") == 4
    assert mod.extract_bedrooms("Vendo 1 ambiente") == 1


def test_extract_bedrooms_monoambiente():
    """Monoambiente = 0 bedrooms."""
    assert mod.extract_bedrooms("Alquilo Dpto Monoambiente") == 0


def test_extract_bedrooms_no_match():
    assert mod.extract_bedrooms("Terreno en venta") is None
    assert mod.extract_bedrooms("") is None


def test_extract_address_av():
    """Extract 'Avda.' / 'Av.' references."""
    assert "Avda" in (mod.extract_address("Casa en Avda. España") or "")
    assert "Av" in (mod.extract_address("Casa en Av. Mariscal López") or "")


def test_extract_address_calle():
    """Extract 'Calle' references."""
    assert "Calle" in (mod.extract_address("Departamento en Calle Palma 123") or "")


def test_extract_address_km():
    """Extract 'km' route markers."""
    result = mod.extract_address("Terreno en km 4.5 Ruta 2")
    assert "km" in (result or "")


def test_extract_barrio():
    """Extract 'barrio X' marker."""
    assert mod.extract_barrio("Casa en barrio Recoleta") == "Recoleta"
    assert mod.extract_barrio("Vendo Casa en B° Trinidad") == "Trinidad"


def test_dry_run_does_not_write():
    """--dry-run does not modify canonical_properties.geojson."""
    import subprocess
    import hashlib
    before = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    r = subprocess.run(
        ["python3", "-m", "tools.extract_listing_metadata", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0
    after = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    assert before == after, "dry-run modified canonical_properties.geojson"
