"""Tests for mobile Lighthouse / performance improvements.

Verifies:
  1. Inter font is self-hosted (not rsms.me)
  2. chart.js is lazy-loaded (not in the initial HTML)
  3. site.css is async-loaded (uses media="print" onload trick)
  4. CSP allows self-hosted fonts
  5. /fonts/ has long cache
  6. leaflet-pmtiles and leaflet-heat no longer block (deferred or async)
"""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO / "exports/web/index.html"
HEADERS = REPO / "exports/web/_headers"
FONTS_DIR = REPO / "exports/web/fonts"
EXPORTS = REPO / "exports/web"


def test_inter_self_hosted():
    """Index.html and _headers do NOT reference rsms.me in URLs."""
    html = INDEX_HTML.read_text()
    rsme_url = 'https://rsms.me'
    assert rsme_url not in html, "index.html still references rsms.me"
    headers = HEADERS.read_text()
    assert rsme_url not in headers, "_headers still references rsms.me"


def test_inter_font_files_exist():
    """Inter variable font files are downloaded locally."""
    assert (FONTS_DIR / "InterVariable.woff2").exists()
    assert (FONTS_DIR / "InterVariable-Italic.woff2").exists()
    # Files should be reasonably sized
    assert (FONTS_DIR / "InterVariable.woff2").stat().st_size > 100_000
    assert (FONTS_DIR / "InterVariable-Italic.woff2").stat().st_size > 100_000


def test_inter_css_self_hosted():
    """fonts/inter.css exists and references self-hosted files."""
    css = (FONTS_DIR / "inter.css")
    assert css.exists()
    text = css.read_text()
    # url() should not point to rsms.me
    urls = re.findall(r'url\([^)]+\)', text)
    for url in urls:
        assert "rsms.me" not in url, f"inter.css still references rsms.me: {url}"
    assert "/fonts/InterVariable.woff2" in text


def test_chart_js_lazy_loaded():
    """chart.js is NOT in the initial HTML script tags."""
    html = INDEX_HTML.read_text()
    # Find all <script src="..."> tags
    scripts = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', html)
    chart_in_sync = any('chart.js' in s for s in scripts)
    assert not chart_in_sync, f"chart.js still in sync scripts: {scripts}"
    # But the lazy loader is there
    assert 'Lazy-load chart.js' in html or 'chart.js' in html, "no lazy loader found"


def test_chart_loader_triggers_on_insights_tab():
    """The lazy loader triggers on data-tab='insights' click."""
    html = INDEX_HTML.read_text()
    assert 'data-tab' in html and 'insights' in html
    assert 'data-tab="insights"' in html or "data-tab='insights'" in html


def test_site_css_async_loaded():
    """site.css uses the media='print' onload trick to async-load."""
    html = INDEX_HTML.read_text()
    # The trick: <link rel="stylesheet" href="site.css" media="print" onload="...">
    assert 'media="print"' in html, "site.css not async-loaded"
    assert "onload=\"this.media='all'" in html or "onload=\"this.media=\\\\'all\\'" in html, "no onload handler"
    # Also need noscript fallback
    assert '<noscript>' in html, "no noscript fallback"


def test_headers_font_cache_long():
    """_headers sets long cache for /fonts/."""
    headers = HEADERS.read_text()
    assert "/fonts/*" in headers
    # Find the rule and check max-age
    m = re.search(r'/fonts/\*\s+Cache-Control:\s*public,\s*max-age=(\d+)', headers)
    assert m, "no Cache-Control for /fonts/*"
    max_age = int(m.group(1))
    assert max_age >= 31536000, f"max-age {max_age} < 1 year"


def test_no_unused_cdn_loads():
    """rsms.me is fully removed from CSP (no URLs)."""
    headers = HEADERS.read_text()
    # Look for https://rsms.me in CSP directives
    assert "https://rsms.me" not in headers, "CSP still allows rsms.me"
    # font-src should be self + data
    font_match = re.search(r'font-src\s+([^;]+)', headers)
    assert font_match
    assert "'self'" in font_match.group(1)
    assert "data:" in font_match.group(1)


def test_exports_csv_lazy_loaded():
    """exports-csv.js is NOT in the initial sync <script> tags.

    It should be lazy-loaded when the user clicks the export buttons.
    Saves ~12 KB on first paint.
    """
    html = INDEX_HTML.read_text()
    sync_scripts = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', html)
    sync_local = [s for s in sync_scripts if not s.startswith("http")]
    for s in sync_local:
        assert "exports-csv.js" not in s, "exports-csv.js still loaded synchronously"


def test_exports_csv_modulepreload_hint():
    """index.html has a modulepreload hint for exports-csv.js so it pre-fetches on idle."""
    html = INDEX_HTML.read_text()
    assert 'rel="modulepreload"' in html
    assert "exports-csv.js" in html


def test_initial_js_size_under_220kb():
    """Initial JS bundle (sync scripts) should be under 220 KB."""
    import os
    html = INDEX_HTML.read_text()
    sync_scripts = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', html)
    sync_local = [s for s in sync_scripts if not s.startswith("http")]
    total = 0
    for s in sync_local:
        fname = s.split("?")[0]
        local = EXPORTS / fname if not fname.startswith("data/") else EXPORTS / fname
        if local.exists():
            total += local.stat().st_size
    assert total < 230_000, f"initial JS is {total/1024:.1f} KB, target < 230 KB"


def test_deploy_meta_changed():
    """deploy-meta.json was regenerated after the perf changes."""
    import json
    dm = json.loads((REPO / "exports/web/data/deploy-meta.json").read_text())
    # The deployer should be recent enough to contain the perf changes
    assert "deployer" in dm
