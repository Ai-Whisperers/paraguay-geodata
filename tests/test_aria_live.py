"""Tests for the aria-live region and announce() helper."""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
HTML = REPO / "exports/web/index.html"
INDEX_JS = REPO / "exports/web/index.js"


def test_html_has_aria_live_region():
    """index.html has a hidden aria-live region for screen reader announcements."""
    html = HTML.read_text()
    assert 'aria-live="polite"' in html, "no aria-live region"
    # Hidden off-screen positioning
    assert "left:-9999px" in html or "left: -9999px" in html, "announcer not hidden"
    assert 'id="srAnnouncer"' in html, "announcer missing ID"


def test_html_has_announce_helper():
    """index.html defines window.announce() for pushing messages."""
    html = HTML.read_text()
    assert "window.announce" in html, "no window.announce helper"
    # The function should clear+setTimeout to ensure screen readers re-read
    assert "el.textContent" in html, "announce doesn't set textContent"
    assert "setTimeout" in html, "announce doesn't reset via timeout"


def test_index_js_calls_announce_on_filter():
    """The filter handler in index.js calls window.announce()."""
    content = INDEX_JS.read_text()
    # Look for window.announce near filter logic
    assert "window.announce&&window.announce" in content, "no announce call"
    # The call should mention listing counts
    # Find the call
    matches = list(re.finditer(r'window\.announce&&window\.announce\(`([^`]+)`\)', content))
    assert len(matches) >= 1, "no announce call found"
    for m in matches:
        msg = m.group(1)
        assert "toLocaleString" in msg, f"announce message missing count formatting: {msg}"


def test_announce_in_spanish():
    """The announce message is in Spanish (matches the rest of the UI)."""
    content = INDEX_JS.read_text()
    # Find announce calls with their message
    m = re.search(r'window\.announce&&window\.announce\(`([^`]+)`\)', content)
    if m:
        msg = m.group(1)
        # Spanish words like "de", "con", "los", "propiedades", "coinciden"
        assert any(w in msg for w in ["propiedades", "coinciden", "filtros"]), \
            f"announce message not in Spanish: {msg}"


def test_aria_region_safe_positioning():
    """The aria-live region is positioned offscreen but readable by AT.

    Using position:absolute + left:-9999px is the WCAG-recommended
    pattern for screen-reader-only text. Some teams use clip-path which
    is also valid; this test accepts the absolute pattern.
    """
    html = HTML.read_text()
    m = re.search(r'<div[^>]*aria-live[^>]*>', html)
    assert m, "no aria-live div"
    div = m.group(0)
    # Should have width/height of 1px (or 0) AND position absolute
    assert "position:absolute" in div or "position: absolute" in div, "no absolute positioning"
    assert "left:-9999px" in div or "left: -9999px" in div, "not offscreen"
    assert "overflow:hidden" in div or "overflow: hidden" in div, "no overflow hidden"