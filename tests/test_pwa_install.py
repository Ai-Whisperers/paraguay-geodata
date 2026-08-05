"""Tests for exports/web/pwa-install.js — PWA install prompt + SW registration."""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PWA = REPO / "exports/web/pwa-install.js"
HTML = REPO / "exports/web/index.html"
MANIFEST = REPO / "exports/web/manifest.webmanifest"
SW = REPO / "exports/web/sw.js"
I18N = REPO / "exports/web/i18n.js"


def test_pwa_install_js_exists():
    assert PWA.exists()
    content = PWA.read_text()
    assert len(content) > 100


def test_pwa_js_is_valid_js():
    """pwa-install.js should parse as valid JavaScript (no syntax errors)."""
    import subprocess
    r = subprocess.run(
        ["node", "--check", str(PWA)],
        capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0, f"pwa-install.js has syntax error: {r.stderr}"


def test_pwa_js_registers_service_worker():
    content = PWA.read_text()
    assert "serviceWorker" in content
    assert "register" in content
    assert "sw.js" in content


def test_pwa_js_handles_beforeinstallprompt():
    content = PWA.read_text()
    assert "beforeinstallprompt" in content
    assert "preventDefault" in content


def test_pwa_js_handles_appinstalled():
    content = PWA.read_text()
    assert "appinstalled" in content


def test_pwa_js_has_ios_fallback():
    """iOS Safari doesn't fire beforeinstallprompt — needs separate hint."""
    content = PWA.read_text()
    assert "iOS" in content or "iPhone" in content or "iPad" in content


def test_pwa_js_uses_sessionstorage_for_dismissal():
    """Don't show the banner again in the same session after dismissal."""
    content = PWA.read_text()
    assert "sessionStorage" in content
    assert "pwa-dismissed" in content


def test_pwa_js_respects_i18n():
    """The banner text should use PY_I18N for translation."""
    content = PWA.read_text()
    assert "PY_I18N" in content
    assert "pwa.installPrompt" in content or "pwa.install" in content


def test_html_loads_pwa_install_js():
    """index.html includes pwa-install.js as a script tag."""
    html = HTML.read_text()
    assert "pwa-install.js" in html


def test_manifest_exists():
    """Web App Manifest is required for PWA install."""
    assert MANIFEST.exists()


def test_manifest_has_required_fields():
    """Manifest should have name, short_name, start_url, display, icons."""
    import json
    data = json.loads(MANIFEST.read_text())
    for key in ["name", "short_name", "start_url", "display", "icons"]:
        assert key in data, f"manifest missing {key}"


def test_manifest_icons_exist():
    """Manifest icons should have src + sizes + type."""
    import json
    data = json.loads(MANIFEST.read_text())
    assert len(data["icons"]) >= 1
    for icon in data["icons"]:
        assert "src" in icon
        assert "sizes" in icon
        assert "type" in icon


def test_sw_exists():
    """Service worker file should exist at /sw.js."""
    assert SW.exists()


def test_sw_cache_strategy():
    """SW should have a cache-first or stale-while-revalidate strategy."""
    content = SW.read_text()
    assert "cache" in content.lower()


def test_i18n_has_pwa_keys_in_all_locales():
    """pwa.installPrompt and pwa.install exist in es, en, pt, gn."""
    content = I18N.read_text()
    for locale in ["es", "en", "pt", "gn"]:
        m = re.search(rf'"{re.escape(locale)}"\s*:\s*\{{', content)
        pos = m.end()
        depth = 1; end = pos
        while depth > 0 and end < len(content):
            if content[end] == "{": depth += 1
            elif content[end] == "}": depth -= 1
            end += 1
        block = content[pos:end-1]
        assert "pwa.installPrompt" in block, f"{locale} missing pwa.installPrompt"
        assert "pwa.install" in block, f"{locale} missing pwa.install"