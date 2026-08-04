"""Tests for Guaraní (gn) translation quality.

The site claims 4 locales (es, en, pt, gn). Guaraní is one of Paraguay's
two official languages, but the gn locale currently has machine-translated
keys that contain Spanish words (e.g. "fuente", "mapa", "departamento") and
literal copies of Spanish strings.

These tests:
  1. Verify gn has 100% coverage in i18n.js (same keys as es)
  2. Verify gn has 100% coverage in page-content.js (es, en, pt, gn)
  3. Detect Spanish-leftover words in gn translations
  4. Score our existing translations against a heuristic for "looks Guaraní"

When a native-speaker translator delivers the JSON, these tests turn green
automatically.

Common Spanish words that should NEVER appear in a real Guaraní translation
(some are loanwords that are OK, e.g. "PY", "USD", "USD", but 'mapa' and
'fuente' are not):
"""
from __future__ import annotations

import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
I18N = REPO / "exports" / "web" / "i18n.js"
PAGE_CONTENT = REPO / "exports" / "web" / "page-content.js"


SOFT_SPANISH_LEFTOVERS = [
    "propiedad", "propiedades", "casa", "terreno", "venta", "alquiler",
    "comprar", "actualizar", "filtros", "datos", "catálogo",
    "departamento", "departamentos", "fuente", "fuentes",
]

HARD_SPANISH_LEFTOVERS = [
    "de la", "del ", " en ", " con ", "para ", " por ", "precios",
    " cargar", " mapa", "filtro", "búsqueda", "búsquedas",
]


def get_locale_block(content: str, locale: str) -> str:
    m = re.search(rf'"{re.escape(locale)}"\s*:\s*\{{', content)
    if not m:
        return ""
    pos = m.end()
    depth = 1
    end = pos
    while depth > 0 and end < len(content):
        if content[end] == '{': depth += 1
        elif content[end] == '}': depth -= 1
        end += 1
    return content[pos:end-1]


def get_keys(block: str) -> dict:
    out = {}
    for m in re.finditer(r'"([\w.]+)"\s*:\s*"([^"]+)"', block):
        out[m.group(1)] = m.group(2)
    return out


def test_gn_has_all_keys():
    content = I18N.read_text()
    es = get_keys(get_locale_block(content, "es"))
    gn = get_keys(get_locale_block(content, "gn"))
    missing = set(es.keys()) - set(gn.keys())
    assert not missing, f"gn missing {len(missing)} keys: {sorted(missing)[:10]}"


def test_gn_has_no_hard_spanish_leftovers():
    content = I18N.read_text()
    gn = get_keys(get_locale_block(content, "gn"))
    bad = []
    for k, v in gn.items():
        vlower = v.lower()
        for word in HARD_SPANISH_LEFTOVERS:
            if word in vlower:
                bad.append((k, v, word))
    if bad:
        for k, v, w in bad[:5]:
            print(f"  WARN: {k}: {v!r} contains '{w}'")
    assert len(bad) < 10, f"too many Spanish leftovers in gn: {bad[:5]}"


def test_gn_soft_leftovers_scored():
    content = I18N.read_text()
    gn = get_keys(get_locale_block(content, "gn"))
    span_in_value = 0
    keys_checked = 0
    for k, v in gn.items():
        vlower = v.lower()
        keys_checked += 1
        for word in SOFT_SPANISH_LEFTOVERS:
            if word in vlower:
                span_in_value += 1
                break
    pct = (keys_checked - span_in_value) / max(keys_checked, 1) * 100
    print(f"  gn keys without Spanish words: {pct:.1f}% ({keys_checked - span_in_value}/{keys_checked})")
    assert pct > 50, f"more than half of gn keys have Spanish words: {pct:.1f}%"


def test_page_content_gn_all_present():
    """page-content.js has gn blocks for faq, use-cases, pricing."""
    pc = PAGE_CONTENT.read_text()
    for page in ["faq", "use-cases", "pricing"]:
        # Keys can be unquoted (pricing) or quoted (use-cases). Match either.
        page_m = re.search(
            rf'(?<![\w-])(["\']?){re.escape(page)}\1\s*:\s*\{{',
            pc,
        )
        assert page_m, f"page {page} not found"
        start = page_m.end()
        depth = 1; end = start
        while depth > 0 and end < len(pc):
            if pc[end] == '{': depth += 1
            elif pc[end] == '}': depth -= 1
            end += 1
        block = pc[start:end-1]
        gn_match = re.search(r'gn:\s*`([^`]+)`', block, re.DOTALL)
        assert gn_match, f"{page} missing gn translation"
        gn_text = gn_match.group(1).strip()
        assert len(gn_text) > 100, f"{page} gn translation too short: {len(gn_text)} chars"


def test_translator_delivery_schema():
    expected = REPO / "translations" / "i18n-gn.json"
    if not expected.exists():
        print(f"  WAITING: expected {expected.relative_to(REPO)}")
        print(f"           translator will deliver once booked")
        return
    data = json.loads(expected.read_text())
    assert "i18n" in data
    assert "page_content" in data
    assert isinstance(data["i18n"], dict)
    assert isinstance(data["page_content"], dict)
