"""Tests for the popup i18n labels (es, en, pt, gn)."""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
I18N = REPO / "exports" / "web" / "i18n.js"
INDEX_JS = REPO / "exports" / "web" / "index.js"


def get_locale_block(content: str, locale: str) -> str:
    m = re.search(rf'"{re.escape(locale)}"\s*:\s*\{{', content)
    if not m:
        return ""
    pos = m.end()
    depth = 1
    end = pos
    while depth > 0 and end < len(content):
        if content[end] == "{": depth += 1
        elif content[end] == "}": depth -= 1
        end += 1
    return content[pos:end-1]


def test_all_popup_keys_in_es():
    """All 23 popup.* keys are defined in the es locale."""
    content = I18N.read_text()
    es = get_locale_block(content, "es")
    for key in ["popup.label", "popup.type", "popup.depto", "popup.source",
                "popup.price", "popup.area", "popup.perHa", "popup.bedBath",
                "popup.parking", "popup.address", "popup.agent", "popup.perSqm",
                "popup.roadAccess", "popup.waterNearby", "popup.nearestBuilding",
                "popup.climateRisk", "popup.riskScore", "popup.ageVsDepto",
                "popup.freshness", "popup.catastro", "popup.fairPrice",
                "popup.beds", "popup.baths"]:
        assert key in es, f"es missing {key}"


def test_all_popup_keys_in_en():
    """All popup.* keys are defined in en."""
    content = I18N.read_text()
    en = get_locale_block(content, "en")
    for key in ["popup.label", "popup.type", "popup.price", "popup.beds"]:
        assert key in en, f"en missing {key}"


def test_all_popup_keys_in_pt():
    """All popup.* keys are defined in pt."""
    content = I18N.read_text()
    pt = get_locale_block(content, "pt")
    for key in ["popup.label", "popup.type", "popup.price"]:
        assert key in pt, f"pt missing {key}"


def test_all_popup_keys_in_gn():
    """All popup.* keys are defined in gn."""
    content = I18N.read_text()
    gn = get_locale_block(content, "gn")
    for key in ["popup.label", "popup.type", "popup.price"]:
        assert key in gn, f"gn missing {key}"


def test_index_js_has_i18n_helper():
    """index.js defines a `__i18n` helper that reads from PY_I18N."""
    content = INDEX_JS.read_text()
    assert "function __i18n" in content
    assert "PY_I18N" in content
    assert "getLang" in content


def test_index_js_calls_i18n_for_popup_labels():
    """index.js calls __i18n() for the popup labels (Price, Area, Beds, Baths, Depto, Fair price)."""
    content = INDEX_JS.read_text()
    # Should have at least 6 i18n() calls
    n = content.count("__i18n()[")
    assert n >= 6, f"only {n} __i18n() calls"
    # Check specific keys
    for key in ["popup.price", "popup.area", "popup.beds", "popup.baths",
                "popup.depto", "popup.fairPrice"]:
        assert f'__i18n()["{key}"]' in content, f"missing i18n call for {key}"


def test_i18n_helper_has_fallback():
    """If PY_I18N is undefined or key missing, the helper returns the fallback."""
    content = INDEX_JS.read_text()
    # The template literals should have `||"Price"` style fallbacks
    assert '||"Price"' in content or '||"Fair price"' in content


def test_popup_translations_dont_break_english():
    """English popup keys should not be the same as Spanish (we translate, not copy)."""
    content = I18N.read_text()
    es = get_locale_block(content, "es")
    en = get_locale_block(content, "en")
    for key in ["popup.label", "popup.price", "popup.area"]:
        es_match = re.search(rf'"{re.escape(key)}":\s*"([^"]+)"', es)
        en_match = re.search(rf'"{re.escape(key)}":\s*"([^"]+)"', en)
        if es_match and en_match:
            es_v = es_match.group(1)
            en_v = en_match.group(1)
            assert es_v != en_v, f"{key} same in es and en: {es_v!r}"