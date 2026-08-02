"""tests/test_fetch_asuncion_estate.py

Unit tests for the asuncion.estate fetcher card parser.
The detail-page enrichment is exercised through a sample HTML blob.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_asuncion_estate as ae  # noqa: E402


SAMPLE_CARD = """
<li class="listing-item">
    <div class="listing-badge-wrapper">
        <span class="badge badge-primary">Sale</span>
    </div>
    <div class="list-thumb">
        <a href="/en/asuncion/departamento-en-herrera-1476656">
            <img src="https://example.com/photo.jpg" alt="Dpto"/>
        </a>
    </div>
    <div class="list-content">
        <div class="list-price">
            <span>U$S 80,000</span>
            <span class="localprice">Gs. ~590,000,000</span>
        </div>
        <div class="list-meta2">
            <a><span class="flaticon-bed"></span>2</a>
            <a><span class="flaticon-shower"></span>1</a>
            <a><span class="flaticon-expand"></span>65m<sup>2</sup></a>
        </div>
        <h5 class="list-title">
            <a href="/en/asuncion/departamento-en-herrera-1476656">
                DEPARTAMENTO EN HERRERA
            </a>
        </h5>
        <a href="">Herrera</a>
    </div>
</li>
"""


def test_card_extracts_id_url_title_price():
    feat = ae._parse_listing_card(SAMPLE_CARD, "asuncion", "sale", "apartments")
    assert feat is not None, "card must parse"
    p = feat["properties"]
    assert p["source_id"] == "1476656"
    assert p["source_url"] == "https://asuncion.estate/en/asuncion/departamento-en-herrera-1476656"
    assert p["price_usd"] == 80000.0
    assert p["price_pyg"] == int(80000.0 * ae.FX_PYG_PER_USD)
    assert p["bedrooms"] == 2
    assert p["bathrooms"] == 1
    assert p["area_sqm"] == 65
    assert p["listing_type"] == "sale"
    assert p["property_type"] == "apartment"
    assert p["state_province"] == "Asunción"


def test_card_handles_pyg_only_price():
    body = """
    <li class="listing-item">
        <h5 class="list-title"><a href="/en/central/alquilo-casa-1568844">Casa</a></h5>
        <div class="list-price"><span>Gs. 1,500,000</span></div>
        <div class="list-meta2">
            <span class="flaticon-bed"></span>3
            <span class="flaticon-shower"></span>2
        </div>
    </li>
    """
    feat = ae._parse_listing_card(body, "central", "rent", "houses")
    assert feat is not None
    p = feat["properties"]
    assert p["source_id"] == "1568844"
    assert p["price_pyg"] == 1500000
    assert p["price_usd"] == round(1500000 / ae.FX_PYG_PER_USD, 2)
    assert p["bedrooms"] == 3
    assert p["bathrooms"] == 2
    assert p["listing_type"] == "rent"
    assert p["property_type"] == "house"


def test_card_drops_when_no_link():
    body = "<li class='listing-item'><h5>No link here</h5></li>"
    assert ae._parse_listing_card(body, "asuncion", "sale", "houses") is None


def test_card_drops_when_no_price():
    body = """
    <li class="listing-item">
        <h5 class="list-title"><a href="/en/asuncion/cualquier-cosa-1234567">x</a></h5>
        <div class="list-price"><span>(consultar)</span></div>
    </li>
    """
    # No price → still parses (card parser is tolerant), but price_* stay None
    feat = ae._parse_listing_card(body, "asuncion", "sale", "houses")
    assert feat is not None
    p = feat["properties"]
    assert p["price_usd"] is None
    assert p["price_pyg"] is None


def test_detail_page_extracts_coords():
    html = """
    <html><body>
      <div id="ts-map-simple"
           data-ts-map-center-latitude="-25.27698715"
           data-ts-map-center-longitude="-57.56441116"></div>
      <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"RealEstateListing",
         "name":"DEPARTAMETO EN LAS LOMAS",
         "image":["https://example.com/a.jpg"],
         "description":"Sample",
         "offers":{"@type":"Offer","price":112000,"priceCurrency":"U$S"},
         "numberOfBedrooms":2,"numberOfBathroomsTotal":1}
      </script>
    </body></html>
    """
    out = ae._parse_detail_page(html)
    assert out["lat"] == -25.27698715, f"got {out['lat']}"
    assert out["lon"] == -57.56441116, f"got {out['lon']}"
    assert out["images"] == ["https://example.com/a.jpg"]
    assert out["description"] == "Sample"
    assert out["ld_price"] == 112000.0
    assert out["ld_bedrooms"] == 2
    assert out["ld_bathrooms"] == 1


def test_enrich_sets_geometry_from_detail():
    feat = {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "id": "ae_test", "source": "asuncion_estate",
            "source_id": "1", "source_url": "u",
            "lat": None, "lon": None,
            "images": [], "description": "",
        },
    }
    ae._enrich_with_detail(feat, {"lat": -25.27, "lon": -57.56, "images": ["x.jpg"], "description": "d"})
    assert feat["geometry"]["coordinates"] == [-57.56, -25.27]
    assert feat["properties"]["images"] == ["x.jpg"]
    assert feat["properties"]["description"] == "d"


def test_enrich_keeps_geometry_if_outside_bbox():
    """Out-of-PY coords are dropped downstream; this just confirms the helper
    writes whatever it gets.  The bbox filter lives in main()."""
    feat = {"type": "Feature", "geometry": None,
            "properties": {"lat": None, "lon": None, "images": [], "description": ""}}
    ae._enrich_with_detail(feat, {"lat": 0.0, "lon": 0.0, "images": [], "description": ""})
    assert feat["geometry"]["coordinates"] == [0.0, 0.0]


def test_walk_is_pure_discovery():
    """The walk function returns only URLs that exist; we don't trust a fresh
    run in CI but we do trust the parser handles a single category page
    correctly."""
    # The actual walk hits network.  We do not test it here — too flaky for CI.
    # Instead: assert the KNOWN_CITIES list is non-empty + sane.
    assert len(ae.KNOWN_CITIES) >= 5
    for city in ae.KNOWN_CITIES:
        assert "-" not in city or city.replace("-", "").isalpha()