"""Tests for tools/build_home_stats.py — refresh home page numbers from live data."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_help():
    """CLI is wired up."""
    r = subprocess.run(
        ["python3", "-m", "tools.build_home_stats", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_dry_run_no_write():
    """--dry-run does not modify index.html or i18n.js."""
    idx = (REPO / "exports" / "web" / "index.html").read_text()
    i18n = (REPO / "exports" / "web" / "i18n.js").read_text()
    r = subprocess.run(
        ["python3", "-m", "tools.build_home_stats", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    after_idx = (REPO / "exports" / "web" / "index.html").read_text()
    after_i18n = (REPO / "exports" / "web" / "i18n.js").read_text()
    assert idx == after_idx, "dry-run modified index.html"
    assert i18n == after_i18n, "dry-run modified i18n.js"


def test_no_stale_5_784():
    """After running, neither index.html nor i18n.js should contain '5,784'."""
    subprocess.run(
        ["python3", "-m", "tools.build_home_stats"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    idx = (REPO / "exports" / "web" / "index.html").read_text()
    i18n = (REPO / "exports" / "web" / "i18n.js").read_text()
    assert "5,784" not in idx, f"index.html still has 5,784: {idx.count('5,784')}x"
    assert "5,784" not in i18n, f"i18n.js still has 5,784: {i18n.count('5,784')}x"


def test_home_stats_json_written():
    """Tool writes home_stats.json with the right shape."""
    subprocess.run(
        ["python3", "-m", "tools.build_home_stats"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    p = REPO / "exports" / "web" / "data" / "home_stats.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert "feature_count" in data
    assert "deptos_count" in data
    assert "sources_count" in data
    assert data["feature_count"] > 0
    assert data["deptos_count"] > 0
    assert data["sources_count"] >= 3


def test_index_html_meta_descriptions_match_live_count():
    """Meta description, og:description, twitter:description use live count."""
    subprocess.run(
        ["python3", "-m", "tools.build_home_stats"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    stats = json.loads((REPO / "exports" / "web" / "data" / "home_stats.json").read_text())
    n = f"{stats['feature_count']:,}"
    idx = (REPO / "exports" / "web" / "index.html").read_text()

    # meta description should contain the live count
    m = re.search(r'<meta name="description" content="([^"]+)"', idx)
    assert m, "no meta description"
    assert n in m.group(1), f"meta description missing {n}: {m.group(1)[:200]}"

    # og:description should contain the live count
    m = re.search(r'<meta property="og:description" content="([^"]+)"', idx)
    assert m, "no og:description"
    assert n in m.group(1), f"og:description missing {n}: {m.group(1)[:200]}"

    # twitter:description should contain the live count
    m = re.search(r'<meta name="twitter:description" content="([^"]+)"', idx)
    assert m, "no twitter:description"
    assert n in m.group(1), f"twitter:description missing {n}: {m.group(1)[:200]}"


def test_i18n_js_all_locales_updated():
    """All 4 locales (es, en, pt, gn) have the live count in home.title."""
    subprocess.run(
        ["python3", "-m", "tools.build_home_stats"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    stats = json.loads((REPO / "exports" / "web" / "data" / "home_stats.json").read_text())
    n = f"{stats['feature_count']:,}"
    i18n = (REPO / "exports" / "web" / "i18n.js").read_text()

    for loc in ["es", "en", "pt", "gn"]:
        # Find the home.title key inside this locale's block
        m = re.search(
            rf'"{loc}"\s*:\s*\{{[^}}]*"home\.title"\s*:\s*"([^"]+)"',
            i18n, re.DOTALL,
        )
        assert m, f"{loc}: home.title not found"
        assert n in m.group(1), f"{loc} home.title missing {n}: {m.group(1)}"


def test_load_stats_returns_required_keys():
    """load_stats() returns feature_count, deptos_count, sources_count."""
    # Use Python import to test directly
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    from build_home_stats import load_stats
    stats = load_stats()
    assert "feature_count" in stats
    assert "deptos_count" in stats
    assert "sources_count" in stats
    assert "sources" in stats
    assert isinstance(stats["sources"], list)


def test_render_i18n_values_has_all_locales():
    """render_i18n_values returns all 4 locales for every key."""
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    from build_home_stats import load_stats, render_i18n_values
    stats = load_stats()
    values = render_i18n_values(stats)
    for key, by_locale in values.items():
        for loc in ["es", "en", "pt", "gn"]:
            assert loc in by_locale, f"{key} missing {loc} locale"
            assert by_locale[loc], f"{key}/{loc} is empty"
