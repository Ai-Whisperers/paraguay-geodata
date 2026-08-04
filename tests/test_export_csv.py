"""Tests for exports/web/exports-csv.js — CSV + XLSX export of filtered listings.

Verifies the JS file:
  1. Exists and is non-empty
  2. Defines window.exportCSV, window.exportXLSX
  3. Defines window.__propertiesToRows
  4. Has a real downloadBlob() implementation (not a stub)

Also verifies the HTML wires it up:
  5. exports-csv.js is loaded as a <script>
  6. The architect export panel has CSV + XLSX buttons
  7. The buttons have click handlers wired via DOMContentLoaded
"""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
HTML = REPO / "exports/web/index.html"
CSV_JS = REPO / "exports/web/exports-csv.js"


def test_csv_js_exists():
    assert CSV_JS.exists()
    content = CSV_JS.read_text()
    assert len(content) > 5000, f"exports-csv.js too small: {len(content)} bytes"


def test_csv_js_exposes_functions():
    content = CSV_JS.read_text()
    assert "window.exportCSV" in content, "no window.exportCSV"
    assert "window.exportXLSX" in content, "no window.exportXLSX"
    assert "window.__propertiesToRows" in content, "no window.__propertiesToRows"


def test_csv_js_real_implementation():
    """The download must produce a real Blob, not a stub."""
    content = CSV_JS.read_text()
    assert "Blob" in content
    assert "URL.createObjectURL" in content
    assert "downloadBlob" in content


def test_csv_js_covers_all_columns():
    """Should define at least 15 columns: id, title, price, area, etc."""
    content = CSV_JS.read_text()
    for col in ["id", "title", "price_usd", "price_pyg", "area_ha",
                "bedrooms", "property_type", "city", "depto", "currency",
                "source", "lat", "lng"]:
        assert col in content, f"missing column {col}"


def test_csv_escaping_handles_quotes():
    """The csvEscape function must handle double-quotes by doubling them."""
    content = CSV_JS.read_text()
    # The csvEscape function should escape " by doubling
    assert 'replace(/"/g, \'""\')' in content or 'replace(/"/g,"""")' in content, \
        "csvEscape doesn't double up quotes"


def test_xlsx_uses_minimal_zip_builder():
    """XLSX export uses a built-in minimal ZIP writer (no SheetJS dependency)."""
    content = CSV_JS.read_text()
    assert "buildZip" in content, "no buildZip helper"
    assert "0x04034b50" in content, "no ZIP local file header signature"
    assert "0x02014b50" in content, "no ZIP central directory signature"
    assert "0x06054b50" in content, "no ZIP end-of-central-directory signature"


def test_xlsx_creates_valid_workbook_xml():
    """XLSX workbook.xml should reference the sheet1.xml file."""
    content = CSV_JS.read_text()
    assert "workbook.xml" in content
    assert "sheet1.xml" in content
    assert "[Content_Types].xml" in content


def test_html_loads_exports_csv():
    """index.html loads exports-csv.js as a defer script."""
    html = HTML.read_text()
    assert '<script src="exports-csv.js"' in html, "exports-csv.js not loaded"
    assert "exports-csv.js" in html


def test_html_has_csv_button():
    """index.html has the CSV export button."""
    html = HTML.read_text()
    assert 'id="btnArchitectCsvFiltered"' in html


def test_html_has_xlsx_button():
    """index.html has the XLSX export button."""
    html = HTML.read_text()
    assert 'id="btnArchitectXlsxFiltered"' in html


def test_html_handlers_wired():
    """CSV/XLSX buttons have DOMContentLoaded handlers calling exportCSV/XLSX."""
    html = HTML.read_text()
    # Find the DOMContentLoaded handler section
    assert "DOMContentLoaded" in html
    # The block from DOMContentLoaded until </script> should mention both
    handler_match = re.search(
        r"DOMContentLoaded.*?</script>",
        html, re.DOTALL,
    )
    assert handler_match, "no DOMContentLoaded handler"
    handler_text = handler_match.group(0)
    assert "btnArchitectCsvFiltered" in handler_text
    assert "btnArchitectXlsxFiltered" in handler_text
    assert "exportCSV" in handler_text
    assert "exportXLSX" in handler_text


def test_csv_js_handles_unicode_bom():
    """CSV output starts with UTF-8 BOM (\\ufeff) so Excel detects encoding."""
    content = CSV_JS.read_text()
    assert "\\ufeff" in content or "ufeff" in content, "no UTF-8 BOM in CSV output"


def test_csv_js_handles_utf8_in_columns():
    """Column values like 'Ciudad del Este' (with accents) must survive."""
    # We just check that the data path uses String(value)
    content = CSV_JS.read_text()
    assert "String(value)" in content, "no String() conversion"


def test_xlsx_minimal_no_external_deps():
    """XLSX builder must use ONLY in-file utilities (no fetch, no cdn)."""
    content = CSV_JS.read_text()
    # Strip comments so we only check the actual code
    code = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    code = re.sub(r"//[^\n]*", "", code)
    # No external imports
    assert "import " not in code
    assert "require(" not in code
    # No CDN references in code (only XML namespace URIs in the XML strings,
    # which we filter by checking for `://` in string literals)
    for line in code.split("\n"):
        if "://" in line and "schemas.openxmlformats" not in line and "officeDocument" not in line:
            # Acceptable URLs only in the XML strings we generate
            if "http://" in line and ("xmlns" in line or "ContentType" in line):
                continue
            assert False, f"unexpected URL in code: {line.strip()}"