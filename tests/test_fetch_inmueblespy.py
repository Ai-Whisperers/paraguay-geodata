"""tests/test_fetch_inmueblespy.py

Tests for the inmueblespy fetcher. Pure unit tests using synthetic HTML.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_inmueblespy as fip  # noqa: E402


HTML_REAL_ESTATE = """
<!doctype html>
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "RealEstateListing",
  "url": "https://inmueblespy.com/inmueble/casa-en-asuncion-123/",
  "name": "Casa 3 dormitorios en Asunción",
  "geo": {"@type": "GeoCoordinates", "latitude": -25.28, "longitude": -57.63},
  "offers": {
    "@type": "Offer",
    "price": "180000",
    "priceCurrency": "USD"
  },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Asunción",
    "addressRegion": "PY"
  }
}
</script>
</head>
<body>
<h1>Casa 3 dormitorios en Asunción</h1>
<p>3 dormitorios, 2 baños, 200 m²</p>
<span class="wp:term_name">Venta</span>
<span class="wp:term_name">Casa</span>
<span class="wp:term_name">Asunción</span>
<span class="wp:term_name">Recoleta</span>
</body>
</html>
"""


def _fe(html: str):
    return fip._parse_detail(
        "https://inmueblespy.com/inmueble/casa-en-asuncion-123/",
        html,
    )


def test_parse_detail_extracts_geo_and_price():
    feat = _fe(HTML_REAL_ESTATE)
    assert feat is not None
    p = feat["properties"]
    assert p["source"] == "inmueblespy"
    assert p["lat"] == -25.28
    assert p["lon"] == -57.63
    assert p["price_usd"] == 180_000
    assert p["price_pyg"] == 180_000 * 7_500
    assert p["city"] == "Asunción"
    assert p["state_province"] == "Asunción"
    assert p["property_type"] == "house"
    assert p["listing_type"] == "sale"


def test_parse_detail_strips_venta_prefix():
    """`en-venta-casa-...` → property_type == house after stripping en-venta-."""
    html = """
    <script type="application/ld+json">
    {"@type": "RealEstateListing",
     "name": "Casa en venta",
     "geo": {"latitude": -25.28, "longitude": -57.63},
     "offers": {"price": "100000", "priceCurrency": "USD"}}
    </script>
    """
    feat = fip._parse_detail(
        "https://inmueblespy.com/inmueble/en-venta-casa-en-asuncion-2025/",
        html,
    )
    assert feat is not None
    # The slug is "en-venta-casa-en-asuncion-2025", stripped to "casa-en-asuncion-2025"
    # PROPERTY_TYPE_HINTS: "casa" → "house"
    assert feat["properties"]["property_type"] == "house"


def test_parse_detail_property_type_from_text():
    """When the slug is generic, fall back to ld+json.name."""
    html = """
    <script type="application/ld+json">
    {"@type": "RealEstateListing",
     "name": "Departamento en Pocitos",
     "description": "",
     "geo": {"latitude": -25.28, "longitude": -57.63},
     "offers": {"price": "100000", "priceCurrency": "USD"}}
    </script>
    """
    feat = fip._parse_detail(
        "https://inmueblespy.com/inmueble/generic-slug-2025/",
        html,
    )
    assert feat is not None
    assert feat["properties"]["property_type"] == "apartment"


def test_parse_detail_drops_out_of_bounds():
    html = """
    <script type="application/ld+json">
    {"@type": "RealEstateListing", "geo": {"latitude": -34.6, "longitude": -58.4},
     "offers": {"price": "100", "priceCurrency": "USD"}}
    </script>
    """
    assert _fe(html) is None


def test_parse_detail_handles_pyg_price():
    html = """
    <script type="application/ld+json">
    {"@type": "RealEstateListing",
     "geo": {"latitude": -25.28, "longitude": -57.63},
     "offers": {"price": "1500000000", "priceCurrency": "PYG"}}
    </script>
    """
    feat = _fe(html)
    assert feat["properties"]["price_pyg"] == 1_500_000_000
    assert feat["properties"]["price_usd"] == 200_000


def test_parse_detail_missing_ld_json_returns_none():
    """If there's no ld+json, the fetcher should skip the page."""
    html = "<html><body>no script here</body></html>"
    assert _fe(html) is None


def test_parse_detail_handles_array_ld_json():
    """Inmueblespy sometimes returns an array of items."""
    html = """
    <script type="application/ld+json">
[
  {"@type": "BreadcrumbList"},
  {"@type": "RealEstateListing",
   "geo": {"latitude": -25.28, "longitude": -57.63},
   "offers": {"price": "180000", "priceCurrency": "USD"}}
]
</script>
"""
    feat = _fe(html)
    assert feat is not None
    assert feat["properties"]["source"] == "inmueblespy"


def test_sitemap_urls_filters_property_paths():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset>
  <url><loc>https://inmueblespy.com/inmueble/casa-1/</loc></url>
  <url><loc>https://inmueblespy.com/inmueble/casa-2/</loc></url>
  <url><loc>https://inmueblespy.com/contacto/</loc></url>
  <url><loc>https://inmueblespy.com/blog/post/</loc></url>
</urlset>
"""
    urls = fip._sitemap_urls(xml)
    assert len(urls) == 2
    assert all("/inmueble/" in u for u in urls)


def test_depto_from_city_handles_known_cities():
    assert fip._depto_from_city("Asunción") == "Asunción"
    assert fip._depto_from_city("Encarnacion") == "Itapúa"  # Spanish without accent for slug lookup
    assert fip._depto_from_city("Ciudad del Este") == "Alto Paraná"
    assert fip._depto_from_city("Hernandarias") == "Alto Paraná"
    assert fip._depto_from_city("San Lorenzo") == "Central"
    assert fip._depto_from_city("Unknown") is None


def test_slug_to_id_is_stable():
    a = fip._slug_to_id("https://inmueblespy.com/inmueble/casa-1/")
    b = fip._slug_to_id("https://inmueblespy.com/inmueble/casa-1/")
    assert a == b
    assert a.startswith("ip_")
    assert len(a) == 15  # 'ip_' + 12 hex


def test_in_py_helper():
    assert fip._in_py([-57.63, -25.28]) is True
    assert fip._in_py([-58.4, -34.6]) is False  # Buenos Aires
    assert fip._in_py([None, None]) is False
    assert fip._in_py([]) is False


def test_parse_price_handles_currency():
    pyg, usd = fip._parse_price("1500000000", "PYG")
    assert pyg == 1_500_000_000
    assert usd == 200_000
    pyg, usd = fip._parse_price(180_000, "USD")
    assert pyg == 180_000 * 7_500
    assert usd == 180_000
    pyg, usd = fip._parse_price("not a number", "USD")
    assert pyg is None
    assert usd is None
    pyg, usd = fip._parse_price(None, "USD")
    assert pyg is None
    assert usd is None
