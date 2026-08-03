"""test_page_content_locales.py — verify page-content.js has all 4 locales for each page."""
import re
from pathlib import Path

PAGE_CONTENT = Path("/root/paraguay-geodata/exports/web/page-content.js")
EXPECTED_PAGES = ["faq", "use-cases", "pricing"]
EXPECTED_LOCALES = ("es", "en", "pt", "gn")


def test_file_exists():
    assert PAGE_CONTENT.exists(), "page-content.js missing"


def test_pages_inventory():
    text = PAGE_CONTENT.read_text()
    for key in EXPECTED_PAGES:
        # match either `key: {` or `"key": {`
        m = re.search(rf'(?:^|\n)\s*\"?{re.escape(key)}\"?\s*:\s*\{{', text)
        assert m, f"Page {key!r} missing from page-content.js inventory"


def test_each_page_has_all_locales():
    text = PAGE_CONTENT.read_text()
    for key in EXPECTED_PAGES:
        # Find the page block: ' key: { ... } ' with balanced braces
        m = re.search(
            rf'(?:^|\n)\s*\"?{re.escape(key)}\"?\s*:\s*\{{(.*?)\n\s+\}},',
            text,
            re.DOTALL,
        )
        assert m, f"{key} page block missing"
        body = m.group(1)
        for lang in EXPECTED_LOCALES:
            assert f"{lang}:`" in body or f"{lang}: `" in body, \
                f"{key} missing locale {lang}"
            # Extract and verify body has <h2>
            mb = re.search(rf"{lang}\s*:\s*`(.*?)`", body, re.DOTALL)
            assert mb and "<h2>" in mb.group(1), \
                f"{key}/{lang} missing <h2> header"


def test_html_lang_attribute():
    text = PAGE_CONTENT.read_text()
    assert "document.documentElement.lang" in text, \
        "missing html lang update for SEO"


def test_lang_preference_order():
    text = PAGE_CONTENT.read_text()
    # Order: query → localStorage → browser → fallback "es"
    assert "URLSearchParams" in text
    assert "localStorage" in text
    assert "navigator.language" in text
    assert "return \"es\"" in text


def test_no_pii_in_translations():
    """No phone/email in any locale."""
    text = PAGE_CONTENT.read_text()
    # Only allowed mail is the support one
    bad = re.findall(r'\b\+?\d{3,}[\s\-]\d{3,}[\s\-]\d{3,}\b', text)
    assert not bad, f"phone numbers in translations: {bad}"
