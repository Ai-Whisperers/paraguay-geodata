"""tests/test_get_value_from_url.py

Smoke tests for the "build_" tools that don't have unit tests.  These
cover the public surface only (no network, no files) and give us a
dev-time alarm if the imports break.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _importable(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


def test_build_api_summary_importable():
    assert _importable("tools.build_api_summary")


def test_build_bulletin_importable():
    assert _importable("tools.build_bulletin")


def test_build_data_freshness_importable():
    assert _importable("tools.build_data_freshness")


def test_build_days_on_market_importable():
    assert _importable("tools.build_days_on_market")


def test_build_facets_importable():
    assert _importable("tools.build_facets")


def test_build_pmtiles_importable():
    assert _importable("tools.build_pmtiles")


def test_detect_regression_importable():
    assert _importable("tools.detect_regression")


def test_merge_fresh_sources_importable():
    assert _importable("tools.merge_fresh_sources")


def test_cache_prune_importable():
    assert _importable("tools.cache_prune")


def test_scrub_pii_importable():
    assert _importable("tools.scrub_pii")


def test_mirror_to_r2_importable():
    assert _importable("tools.mirror_to_r2")


def test_all_build_tools_exit_zero():
    """Each build tool must print or exit cleanly when run with --help."""
    import subprocess
    for module in [
        "build_api_summary",
        "build_bulletin",
        "build_data_freshness",
        "build_days_on_market",
        "build_facets",
        "build_pmtiles",
    ]:
        r = subprocess.run(
            ["python3", "-m", f"tools.{module}", "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=10,
        )
        # --help exits 0 with usage printed
        assert r.returncode == 0, f"tools.{module} --help failed: {r.stderr}"


def test_detect_regression_flags_big_drop(tmp_path):
    """If the canonical shrinks by >30%, detect_regression should exit 1."""
    # Create two minimal fake geojson files
    current = tmp_path / "current.geojson"
    last = tmp_path / "last.geojson"
    current.write_text(
        '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"state_province": "A"}, "geometry": null}]}'
    )
    last.write_text(
        '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"state_province": "A"}, "geometry": null}, {"type": "Feature", "properties": {"state_province": "B"}, "geometry": null}]}'
    )
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.detect_regression",
         "--current", str(current), "--last", str(last),
         "--max-shrink-pct", "30"],
        capture_output=True, text=True, cwd=ROOT, timeout=10,
    )
    # 50% drop → exit 1
    assert r.returncode == 1, f"expected 1, got {r.returncode}: {r.stderr}"


def test_detect_regression_passes_unchanged(tmp_path):
    current = tmp_path / "current.geojson"
    last = tmp_path / "last.geojson"
    feat = (
        '{"type": "FeatureCollection", "features": ['
        '{"type": "Feature", "properties": {"state_province": "A"}, "geometry": null}, '
        '{"type": "Feature", "properties": {"state_province": "B"}, "geometry": null}, '
        '{"type": "Feature", "properties": {"state_province": "C"}, "geometry": null}, '
        '{"type": "Feature", "properties": {"state_province": "D"}, "geometry": null}, '
        '{"type": "Feature", "properties": {"state_province": "E"}, "geometry": null}'
        ']}'
    )
    current.write_text(feat)
    last.write_text(feat)
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.detect_regression",
         "--current", str(current), "--last", str(last),
         "--max-shrink-pct", "30"],
        capture_output=True, text=True, cwd=ROOT, timeout=10,
    )
    assert r.returncode == 0, f"expected 0, got {r.returncode}: {r.stderr}"
