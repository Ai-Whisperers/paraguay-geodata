"""Tests for tools/build_jsonld.py — JSON-LD Dataset schema builder."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "build_jsonld",
        REPO / "tools" / "build_jsonld.py",
    )
    assert spec is not None
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


mod = _load()


def test_help():
    r = subprocess.run(
        ["python3", "-m", "tools.build_jsonld", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_dry_run_no_write():
    """--dry-run does not modify index.html."""
    import hashlib
    before = hashlib.sha256((REPO / "exports/web/index.html").read_bytes()).hexdigest()
    r = subprocess.run(
        ["python3", "-m", "tools.build_jsonld", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    after = hashlib.sha256((REPO / "exports/web/index.html").read_bytes()).hexdigest()
    assert before == after


def test_dataset_block_has_required_fields():
    block = mod.build_dataset_block()
    assert block["@context"] == "https://schema.org"
    assert block["@type"] == "Dataset"
    assert "name" in block
    assert "description" in block
    assert "url" in block
    assert "license" in block


def test_dataset_block_spatial_coverage():
    block = mod.build_dataset_block()
    sc = block["spatialCoverage"]
    assert sc["@type"] == "Place"
    assert sc["name"] == "Paraguay"
    assert sc["geo"]["@type"] == "GeoShape"
    # Paraguay bounding box
    box = sc["geo"]["box"]
    coords = box.split()
    assert len(coords) == 4
    min_lon, min_lat, max_lon, max_lat = (float(c) for c in coords)
    assert min_lon < max_lon
    assert min_lat < max_lat
    # Sanity check — Paraguay is around lat -23, lon -58
    assert -65 < min_lon < -50
    assert -30 < min_lat < -15


def test_dataset_block_temporal_coverage():
    """temporalCoverage is an ISO 8601 interval: YYYY-MM-DD/YYYY-MM-DD."""
    block = mod.build_dataset_block()
    tc = block["temporalCoverage"]
    assert "/" in tc, f"missing interval slash: {tc}"
    parts = tc.split("/")
    assert len(parts) == 2
    # Both parts should be YYYY-MM-DD
    for part in parts:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", part), f"bad date format: {part}"


def test_dataset_block_variables():
    block = mod.build_dataset_block()
    variables = block["variableMeasured"]
    assert len(variables) >= 5, f"only {len(variables)} variables"
    # Should cover our key fields
    names = {v["name"] for v in variables}
    for expected in ["price_usd", "area_ha", "bedrooms", "property_type", "state_province"]:
        assert expected in names, f"missing variable {expected}"


def test_dataset_block_providers():
    block = mod.build_dataset_block()
    providers = block["sourceOrganization"]
    assert len(providers) >= 1
    names = {p["name"] for p in providers}
    # Should include at least one of our sources
    assert any(n for n in names), "no providers"


def test_dataset_block_license_is_cc_by():
    block = mod.build_dataset_block()
    assert "creativecommons.org" in block["license"]


def test_dataset_block_distribution():
    block = mod.build_dataset_block()
    dist = block["distribution"]
    assert dist["@type"] == "DataDownload"
    assert dist["encodingFormat"] == "application/geo+json"
    assert dist["contentUrl"].endswith("properties_latest.geojson")


def test_dataset_block_count_in_description():
    """Description includes the actual feature count."""
    block = mod.build_dataset_block()
    desc = block["description"]
    n = len(json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())["features"])
    # Should mention the count with thousands separator
    assert f"{n:,}" in desc, f"description missing count: {desc}"


def test_index_html_has_two_jsonld_blocks():
    """After running, index.html has both WebSite and Dataset schemas."""
    r = subprocess.run(
        ["python3", "-m", "tools.build_jsonld"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    html = (REPO / "exports/web/index.html").read_text()
    blocks = list(re.finditer(r'<script type="application/ld\+json">', html))
    assert len(blocks) >= 2, f"only {len(blocks)} JSON-LD blocks"
    # Check the second one is Dataset — find the matching </script>
    second_start = blocks[1].end()
    # Find the first </script> after second_start
    second_end = html.find('</script>', second_start)
    second = html[second_start:second_end]
    parsed = json.loads(second.strip())
    assert parsed["@type"] == "Dataset", f"second block is {parsed.get('@type')}"