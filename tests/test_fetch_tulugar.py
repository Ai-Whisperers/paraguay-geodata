"""tests/test_fetch_tulugar.py

Covers tools/fetch_tulugar.py with the new v1 API schema:
- URL pattern /api/v1/listings
- response shape: {"data":[...]}
- new source_url pattern /propiedades/<slug> (plural)
- price/currency discriminator
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fetch_tulugar as ft  # noqa: E402


SAMPLE_ITEM = {
    "id": "01103c22-0192-44c5-b795-97c6000d66c3",
    "slug": "01103c22-casa-en-venta-tres-bocas-fernando-de-la-mora",
    "title": "Casa de 5 dormitorios en Venta en Tres Bocas, Fernando de la Mora",
    "price": 1300000000,
    "currency": "PYG",
    "listing_type": "sale",
    "property_type": "house",
    "bedrooms": 5,
    "bathrooms": 5,
    "area_sqm": 439,
    "lot_size_sqm": 360,
    "city": "Fernando de la Mora",
    "neighborhood": "Tres Bocas",
    "country": "Paraguay",
    "latitude": -25.3509,
    "longitude": -57.5703,
    "parking_spaces": 3,
    "verified": False,
    "images": ["https://cdn.tulugar.com/listings/x.webp"],
    "views": 8,
    "created_at": "2026-07-17T11:56:28.472+00:00",
}


def test_api_base_is_v1():
    assert ft.API_BASE.endswith("/api/v1/listings")


def test_to_feature_returns_none_without_lat_lon():
    bad = dict(SAMPLE_ITEM)
    bad["latitude"] = None
    bad["longitude"] = None
    assert ft.to_feature(bad) is None


def test_to_feature_uses_new_url_pattern_propiedades():
    f = ft.to_feature(dict(SAMPLE_ITEM))
    assert "/propiedades/" in f["properties"]["source_url"], (
        "URL pattern must be the new plural /propiedades/ "
        "— the old /propiedad/ pattern 301s twice on the live site"
    )
    assert "/propiedad/" not in f["properties"]["source_url"]


def test_to_feature_pyg_price_derives_usd():
    f = ft.to_feature(dict(SAMPLE_ITEM))
    p = f["properties"]
    assert p["price_pyg"] == 1300000000
    # USD should be derived at FX 7500
    assert p["price_usd"] == round(1300000000 / 7500, 2)


def test_to_feature_usd_price_passes_through():
    item = dict(SAMPLE_ITEM)
    item["price"] = 133000
    item["currency"] = "USD"
    f = ft.to_feature(item)
    p = f["properties"]
    assert p["price_usd"] == 133000
    assert p["price_pyg"] is None


def test_to_feature_geometry_is_py_box():
    f = ft.to_feature(dict(SAMPLE_ITEM))
    lon, lat = f["geometry"]["coordinates"]
    assert -63.5 <= lon <= -54.0
    assert -27.5 <= lat <= -19.0


def test_to_feature_source_label_is_tulugar():
    f = ft.to_feature(dict(SAMPLE_ITEM))
    assert f["properties"]["source"] == "tulugar"


def test_to_feature_id_is_deterministic():
    a = ft.to_feature(dict(SAMPLE_ITEM))["properties"]["id"]
    b = ft.to_feature(dict(SAMPLE_ITEM))["properties"]["id"]
    assert a == b
    assert a.startswith("tl_")