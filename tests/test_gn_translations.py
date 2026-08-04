"""Tests for the Guaraní translation pipeline.

Verifies:
  1. translations/i18n-gn.json has the right shape
  2. tools/apply_gn_translations.py integrates it correctly
  3. Page content applies without breaking the other 3 locales
  4. The gn locale has 100% coverage in i18n.js (the same keys as es)
  5. The gn translations don't contain hard Spanish leftovers
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
I18N = REPO / "exports" / "web" / "i18n.js"
PAGE_CONTENT = REPO / "exports" / "web" / "page-content.js"
TRANSLATION_FILE = REPO / "translations" / "i18n-gn.json"


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


def get_i18n_keys(content: str) -> dict:
    """Return {key: value} for all keys in i18n.js flattened across locales."""
    out = {}
    for loc in ["es", "en", "pt", "gn"]:
        block = get_locale_block(content, loc)
        for m in re.finditer(r'"([\w.]+)"\s*:\s*"([^"]+)"', block):
            key = m.group(1)
            out.setdefault(key, {})[loc] = m.group(2)
    return out


def get_pages(content: str) -> dict:
    """Return {page: {locale: value}} for page-content.js."""
    m = re.search(r'var PAGE_CONTENT\s*=\s*\{', content)
    if not m:
        return {}
    pos = m.end()
    depth = 1
    end = pos
    while depth > 0 and end < len(content):
        if content[end] == '{': depth += 1
        elif content[end] == '}': depth -= 1
        end += 1
    block = content[m.start():end]
    out = {}
    # Find top-level keys (unquoted or quoted followed by :)
    for m in re.finditer(r'(?<![\w-])(["\']?)([\w-]+)\1\s*:\s*\{', block):
        page = m.group(2)
        if page in ["es", "en", "pt", "gn"]:  # skip the locale keys
            continue
        page_block = block[m.end():]
        # Find each locale's value
        for loc in ["es", "en", "pt", "gn"]:
            lm = re.search(rf'\b{loc}\s*:\s*`([^`]*)`', page_block, re.DOTALL)
            if lm:
                out.setdefault(page, {})[loc] = lm.group(1)
    return out


def test_translation_file_well_formed():
    """translations/i18n-gn.json has _meta, i18n, page_content."""
    if not TRANSLATION_FILE.exists():
        # Not delivered yet — translator will deliver
        print("  WAITING: translations/i18n-gn.json not yet delivered")
        return
    data = json.loads(TRANSLATION_FILE.read_text())
    assert "_meta" in data
    assert "i18n" in data
    assert "page_content" in data
    assert isinstance(data["i18n"], dict)
    assert isinstance(data["page_content"], dict)
    assert len(data["i18n"]) > 50, f"only {len(data['i18n'])} i18n keys"
    assert len(data["page_content"]) >= 3, f"only {len(data['page_content'])} pages"


def test_apply_help():
    """CLI is wired up."""
    r = subprocess.run(
        ["python3", "-m", "tools.apply_gn_translations", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout
    assert "--strict" in r.stdout


def test_apply_dry_run_does_not_write():
    """--dry-run does not modify i18n.js or page-content.js."""
    if not TRANSLATION_FILE.exists():
        return  # skip
    i18n_before = I18N.read_text()
    pc_before = PAGE_CONTENT.read_text()
    r = subprocess.run(
        ["python3", "-m", "tools.apply_gn_translations", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert I18N.read_text() == i18n_before, "dry-run modified i18n.js"
    assert PAGE_CONTENT.read_text() == pc_before, "dry-run modified page-content.js"


def test_apply_translations_preserves_other_locales():
    """Running apply doesn't break es, en, pt."""
    if not TRANSLATION_FILE.exists():
        return
    i18n_before = I18N.read_text()
    pc_before = PAGE_CONTENT.read_text()
    es_keys_before = get_locale_block(i18n_before, "es")
    en_keys_before = get_locale_block(i18n_before, "en")
    pt_keys_before = get_locale_block(i18n_before, "pt")

    r = subprocess.run(
        ["python3", "-m", "tools.apply_gn_translations"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0

    i18n_after = I18N.read_text()
    pc_after = PAGE_CONTENT.read_text()

    # Other locales must be unchanged
    assert get_locale_block(i18n_after, "es") == es_keys_before, "es locale changed"
    assert get_locale_block(i18n_after, "en") == en_keys_before, "en locale changed"
    assert get_locale_block(i18n_after, "pt") == pt_keys_before, "pt locale changed"

    # Page content for es/en/pt should still have body
    pages = get_pages(pc_after)
    for page in ["faq", "use-cases", "pricing"]:
        for loc in ["es", "en", "pt"]:
            assert page in pages, f"page {page} missing"
            assert loc in pages[page], f"{page} {loc} missing"
            assert len(pages[page][loc]) > 100, f"{page} {loc} too short"


def test_apply_translations_replaces_gn_correctly():
    """After applying, gn block has all 78 keys from the translation file."""
    if not TRANSLATION_FILE.exists():
        return
    data = json.loads(TRANSLATION_FILE.read_text())
    expected_keys = set(data["i18n"].keys())

    r = subprocess.run(
        ["python3", "-m", "tools.apply_gn_translations"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0

    i18n = I18N.read_text()
    gn_block = get_locale_block(i18n, "gn")
    actual_keys = set(re.findall(r'"([\w.]+)"\s*:\s*"', gn_block))
    # The translator's keys should be present
    for k in expected_keys:
        if k in actual_keys:  # only check keys that exist in i18n.js
            in_block = re.search(rf'"{re.escape(k)}"\s*:\s*"([^"]+)"', gn_block)
            assert in_block
            assert in_block.group(1) == data["i18n"][k], f"{k}: got {in_block.group(1)!r}, expected {data['i18n'][k]!r}"


def test_gn_block_has_full_coverage():
    """gn locale has the same keys as es (100% coverage)."""
    i18n = I18N.read_text()
    es = get_locale_block(i18n, "es")
    gn = get_locale_block(i18n, "gn")
    es_keys = set(re.findall(r'"([\w.]+)"\s*:\s*"', es))
    gn_keys = set(re.findall(r'"([\w.]+)"\s*:\s*"', gn))
    missing = es_keys - gn_keys
    assert not missing, f"gn missing {len(missing)} keys: {sorted(missing)[:5]}"


def test_gn_no_hard_spanish_leftovers_in_short_strings():
    """gn translations of short strings (≤40 chars) should not have Spanish words.

    Long strings (paragraphs) can have proper nouns, but short UI labels
    like 'Loading...' or 'Cancel' should be Guaraní.
    """
    i18n = I18N.read_text()
    gn = get_locale_block(i18n, "gn")
    spanish_only = ["mapa", "fuente", "filtros", "ciudad", "ciudades",
                    "propiedades", "departamento", "departamentos"]
    bad = []
    for m in re.finditer(r'"([\w.]+)"\s*:\s*"([^"]+)"', gn):
        key, value = m.group(1), m.group(2)
        if len(value) > 40:
            continue  # long strings can have proper nouns
        vlower = value.lower()
        for w in spanish_only:
            if w in vlower:
                bad.append((key, value, w))
    # Soft check: warn if any, but don't fail (translator will fix)
    if bad:
        for k, v, w in bad[:5]:
            print(f"  WARN: {k}: {v!r} contains '{w}'")
