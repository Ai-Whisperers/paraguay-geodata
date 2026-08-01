"""tests/test_fetch_argenprop.py

Covers tools/fetch_argenprop.py with a synthetic ld+json ItemPage response.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_argenprop as fap  # noqa: E402


def _py_record(detail_url):
    return {
        "@context": "https://schema.org",
        "@type": "SingleFamilyResidence",
        "@id": detail_url,
        "name": "Casa 3 dormitorios en San Lorenzo",
        "description": "Amplia casa con jardín y quincho",
        "url": detail_url,
        "geo": {"latitude": -25.34, "longitude": -57.52},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "San Lorenzo",
            "addressRegion": "Central",
            "addressCountry": "PY",
        },
        "offers": {
            "@type": "Offer",
            "price": "180000",
            "priceCurrency": "USD",
        },
    }


def test_parse_argenprop_record_extracts_core_fields():
    rec = _py_record("https://www.argenprop.com/casa-en-san-lorenzo--123456")
    feat = fap._parse_argenprop_record(rec, rec["url"])
    assert feat is not None
    p = feat["properties"]
    assert p["source"] == "argenprop"
    assert p["state_province"] == "Central"
    assert p["city"] == "San Lorenzo"
    assert p["currency"] == "USD"
    assert p["price_usd"] == 180_000
    assert p["price_pyg"] == 1_350_000_000  # 180_000 * 7500


def test_parse_argenprop_record_pyg_currency():
    rec = _py_record("https://www.argenprop.com/x--1")
    rec["offers"]["priceCurrency"] = "PYG"
    rec["offers"]["price"] = "500000000"
    feat = fap._parse_argenprop_record(rec, rec["url"])
    assert feat["properties"]["price_pyg"] == 500_000_000
    assert feat["properties"]["price_usd"] == round(500_000_000 / 7500, 2)


def test_parse_argenprop_drops_out_of_bounds():
    rec = _py_record("https://www.argenprop.com/x--1")
    rec["geo"] = {"latitude": -34.9, "longitude": -56.0}  # Montevideo
    assert fap._parse_argenprop_record(rec, rec["url"]) is None


def test_parse_argenprop_drops_missing_coords():
    rec = _py_record("https://www.argenprop.com/x--1")
    rec["geo"] = None
    assert fap._parse_argenprop_record(rec, rec["url"]) is None


def test_parse_argenprop_drops_missing_price():
    rec = _py_record("https://www.argenprop.com/x--1")
    rec["offers"]["price"] = None
    assert fap._parse_argenprop_record(rec, rec["url"]) is None


def test_argenprop_dedup_by_source_url():
    """Same id must not produce two features."""
    rec = _py_record("https://www.argenprop.com/casa-asuncion--789")
    feat1 = fap._parse_argenprop_record(rec, rec["url"])
    feat2 = fap._parse_argenprop_record(rec, rec["url"])
    assert feat1["properties"]["id"] == feat2["properties"]["id"]


def test_no_fetch_emits_empty_envelope(tmp_path):
    import subprocess
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_argenprop", "--no-fetch",
         "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stderr
    files = list(tmp_path.glob("argenprop_*.geojson"))
    assert len(files) == 1
    d = json.loads(files[0].read_text())
    assert d["feature_count"] == 0