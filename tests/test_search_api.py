"""Tests for tools/build_search_index.py and /functions/api/v1/search.js."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SEARCH_DIR = REPO / "exports" / "web" / "data" / "search"
SEARCH_JS = REPO / "exports" / "web" / "functions" / "api" / "v1" / "search.js"


def test_help():
    r = subprocess.run(
        ["python3", "-m", "tools.build_search_index", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_dry_run_no_write():
    """--dry-run does not modify files in exports/web/data/search/."""
    import hashlib
    # Snapshot one file
    manifest = SEARCH_DIR / "_index.json"
    if manifest.exists():
        before = hashlib.sha256(manifest.read_bytes()).hexdigest()
    else:
        before = None
    r = subprocess.run(
        ["python3", "-m", "tools.build_search_index", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    after = hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.exists() else None
    assert before == after


def test_manifest_lists_all_deptos():
    """_index.json has one entry per depto with the slug + count."""
    manifest = json.loads((SEARCH_DIR / "_index.json").read_text())
    assert "deptos" in manifest
    assert len(manifest["deptos"]) >= 10  # 17 Paraguay deptos + Asunción + unknown
    # Each entry has depto, slug, feature_count, url
    for d in manifest["deptos"]:
        assert "depto" in d
        assert "slug" in d
        assert "feature_count" in d
        assert "url" in d
        assert d["url"].endswith(f"{d['slug']}.json")


def test_total_features_matches_manifest():
    """Total features in manifest equals sum of per-depto feature_counts."""
    manifest = json.loads((SEARCH_DIR / "_index.json").read_text())
    total = sum(d["feature_count"] for d in manifest["deptos"])
    assert total == manifest["total_features"]
    # And this should equal the full dataset
    canon = json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())
    assert total == len(canon["features"])


def test_slug_strips_accents():
    """'Asunción' → 'asuncion', 'Alto Paraná' → 'alto-parana'."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_search_index",
        REPO / "tools" / "build_search_index.py",
    )
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.slug("Asunción") == "asuncion"
    assert mod.slug("Alto Paraná") == "alto-parana"
    assert mod.slug("Ñeembucú") == "neembucu"


def test_per_depto_files_exist():
    """Each depto's file should be on disk."""
    manifest = json.loads((SEARCH_DIR / "_index.json").read_text())
    for d in manifest["deptos"]:
        f = SEARCH_DIR / f"{d['slug']}.json"
        assert f.exists(), f"missing: {f}"


def test_per_depto_files_match_counts():
    """Each per-depto file's feature_count matches its manifest entry."""
    manifest = json.loads((SEARCH_DIR / "_index.json").read_text())
    for d in manifest["deptos"]:
        f = SEARCH_DIR / f"{d['slug']}.json"
        if not f.exists():
            continue
        body = json.loads(f.read_text())
        assert body["feature_count"] == d["feature_count"], f"count mismatch in {d['slug']}"
        assert len(body["features"]) == d["feature_count"], f"features array wrong length in {d['slug']}"


def test_search_records_have_short_keys():
    """Each slim record uses single-letter keys to keep file size down."""
    f = SEARCH_DIR / "asuncion.json"
    if not f.exists():
        return
    body = json.loads(f.read_text())
    if body["features"]:
        keys = set(body["features"][0].keys())
        # All keys should be 1-3 chars (compact format)
        for k in keys:
            assert len(k) <= 3, f"key '{k}' is too long in slim record"


def test_per_depto_file_size_reasonable():
    """Each per-depto file is under 2 MB so CF Functions can read it quickly."""
    manifest = json.loads((SEARCH_DIR / "_index.json").read_text())
    for d in manifest["deptos"]:
        if d["size_kb"] > 2048:
            raise AssertionError(f"{d['slug']} is {d['size_kb']:.1f} KB, > 2 MB")


# ---- CF Function tests ----

def test_search_js_exists():
    assert SEARCH_JS.exists()


def test_search_js_exports_onrequest():
    content = SEARCH_JS.read_text()
    assert "export async function onRequest" in content


def test_search_js_handles_only_get():
    content = SEARCH_JS.read_text()
    assert 'context.request.method !== "GET"' in content or "405" in content


def test_search_js_filters_by_type():
    """Search filters by property_type param."""
    content = SEARCH_JS.read_text()
    assert "r.pt !== type" in content or "pt !== type" in content


def test_search_js_filters_by_price():
    """Search filters by min/max price."""
    content = SEARCH_JS.read_text()
    assert "r.p < min" in content
    assert "r.p > max" in content


def test_search_js_filters_by_bedrooms():
    """Search filters by min bedrooms."""
    content = SEARCH_JS.read_text()
    assert "r.k < minBeds" in content


def test_search_js_filters_by_query():
    """Search filters by title substring (case-insensitive)."""
    content = SEARCH_JS.read_text()
    assert "q &&" in content
    assert "t.toLowerCase()" in content
    assert "includes(q)" in content


def test_search_js_has_cors_header():
    """The response should allow CORS."""
    content = SEARCH_JS.read_text()
    assert "Access-Control-Allow-Origin" in content


def test_search_js_caps_limit_at_200():
    """The limit param is capped at 200."""
    content = SEARCH_JS.read_text()
    assert "200" in content
    # Find the cap logic
    assert "Math.min" in content


def test_search_js_slugifies_depto():
    """The depto param is normalized to a slug."""
    content = SEARCH_JS.read_text()
    assert "deptoSlug" in content or "normalize" in content


def test_search_js_returns_json():
    """The response body is JSON, not text."""
    content = SEARCH_JS.read_text()
    assert "application/json" in content
    assert "JSON.stringify" in content


def test_search_js_loads_manifest_when_no_depto():
    """Without a depto param, it loads the manifest and queries all deptos."""
    content = SEARCH_JS.read_text()
    assert "_index.json" in content
    assert "manifest.deptos" in content