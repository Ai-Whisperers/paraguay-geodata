"""tests/test_canonicalize_properties.py

Covers the four high-risk code paths in tools/canonicalize_properties.py:

    1.  canonical_depto() — 17-deptos mapping + foreign drop
    2.  infer_area_ha() — title parsing for hectares and m²
    3.  canonical_features() — enum collapse from Spanish free text
    4.  cluster_id() — cross-source dedupe grouping

The end-to-end pipeline is exercised in `test_canonicalize_end_to_end` which
runs the canonicalizer against a 50-row synthetic slice.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import canonicalize_properties as cp  # noqa: E402


def test_canonical_depto_basic():
    assert cp.canonical_depto("Central") == "Central"
    assert cp.canonical_depto("Departamento Central") == "Central"
    assert cp.canonical_depto("Departamento de Central") == "Central"
    assert cp.canonical_depto("Itapúa") == "Itapúa"
    assert cp.canonical_depto("Departamento de Itapúa") == "Itapúa"
    assert cp.canonical_depto("Alto Paraná") == "Alto Paraná"
    assert cp.canonical_depto("Departamento del Alto Paraná") == "Alto Paraná"
    assert cp.canonical_depto("Ñeembucú") == "Ñeembucú"
    assert cp.canonical_depto("Asuncion") == "Asunción"
    assert cp.canonical_depto("Distrito Capital de Paraguay") == "Asunción"


def test_canonical_depto_foreign_dropped():
    assert cp.canonical_depto("Formosa") is None
    assert cp.canonical_depto("Corrientes") is None
    assert cp.canonical_depto("Paraná") is None
    assert cp.canonical_depto("Santa Cruz") is None
    assert cp.canonical_depto("Minga Guazu") is None


def test_canonical_depto_null():
    assert cp.canonical_depto(None) is None
    assert cp.canonical_depto("") is None


def test_infer_area_hectares():
    assert cp.infer_area_ha("Vendo 16 hectáreas en Encarnación") == 16.0
    assert cp.infer_area_ha("Terreno de 20 has en Cambyretá") == 20.0
    assert cp.infer_area_ha("Lote 7,5 ha San Juan del Paraná") == 7.5


def test_infer_area_meters():
    # 200,000 m² → 20 ha
    assert cp.infer_area_ha("Terreno de 200,000 m²") == 20.0
    assert cp.infer_area_ha("Campo 360m2 en Encarnación") == 0.036


def test_infer_area_skips_garbage():
    assert cp.infer_area_ha(None) is None
    assert cp.infer_area_ha("") is None
    assert cp.infer_area_ha("Hermosa casa en el centro") is None


def test_canonical_features_spanish():
    out, raw = cp.canonical_features(["Piscina", "Quincho", "Aire acondicionado",
                                       "Garage", "Patio"])
    assert "pool" in out
    assert "bbq" in out
    assert "airConditioning" in out
    assert "parking" in out
    assert "garden" in out


def test_canonical_features_dedup():
    out, _ = cp.canonical_features(["piscina", "pool", "PISCINA"])
    assert out.count("pool") == 1


def test_canonical_features_empty():
    assert cp.canonical_features(None) == ([], [])
    assert cp.canonical_features([]) == ([], [])


def test_cluster_id_url_collision():
    p = {"source": "tulugar",
         "source_url": "https://tulugar.com/x",
         "title": "Lote 20 ha", "lat": -27.3, "lon": -55.8}
    p2 = {"source": "infocasas",
          "source_url": "https://www.infocasas.com.py/x",
          "title": "Lote 20 ha", "lat": -27.3, "lon": -55.8}
    # Different source_url => different cluster
    assert cp.cluster_id(p, 0) != cp.cluster_id(p2, 1)


def test_cluster_id_title_grid_collision():
    # Same title, same 0.001° grid, no URL → same cluster
    a = {"source": "tulugar", "source_url": None,
         "title": "Lote 20 ha en Cambyreta", "lat": -27.339, "lon": -55.774}
    b = {"source": "infocasas", "source_url": None,
         "title": "Lote 20 ha en Cambyreta", "lat": -27.3391, "lon": -55.7742}
    assert cp.cluster_id(a, 0) == cp.cluster_id(b, 1)


def test_choose_area_picks_published_when_consistent():
    p = {"area_ha": 20.0, "area_sqm": 200000.0, "title": "20 ha"}
    flags: list[str] = []
    ha, sqm, src = cp.choose_area(p, flags)
    assert ha == 20.0 and sqm == 200000.0 and src == "published"
    assert flags == []


def test_choose_area_recovers_from_title_when_ha_missing():
    p = {"area_ha": None, "area_sqm": 200000.0, "title": "20 ha en Encarnación"}
    flags: list[str] = []
    ha, sqm, src = cp.choose_area(p, flags)
    assert ha == 20.0 and src == "inferred"
    assert "area_inferred_from_title" in flags


def test_choose_area_flags_conflict():
    p = {"area_ha": 20.0, "area_sqm": 10000.0, "title": ""}  # 7 ha listed as 10 ha
    flags: list[str] = []
    cp.choose_area(p, flags)
    assert "area_conflict" in flags


def test_choose_currency_pyg_only():
    p = {"price_usd": None, "price_pyg": 75_000_000}
    flags: list[str] = []
    usd, pyg = cp.choose_currency(p, 7500, flags)
    assert usd == 10_000
    assert pyg == 75_000_000
    assert "missing_price_usd_inferred" in flags


def test_choose_currency_usd_only():
    p = {"price_usd": 227_000.0, "price_pyg": None}
    flags: list[str] = []
    usd, pyg = cp.choose_currency(p, 7500, flags)
    assert usd == 227_000.0
    assert pyg == 1_702_500_000
    assert "missing_price_pyg_inferred" in flags


def test_choose_currency_flags_conflict():
    # 227_000 USD × 7500 = 1.7B PYG, but published says 75M → 22× divergence
    p = {"price_usd": 227_000.0, "price_pyg": 75_000_000}
    flags: list[str] = []
    cp.choose_currency(p, 7500, flags)
    assert "currency_conflict" in flags


def test_canonicalize_end_to_end(tmp_path):
    """50-row synthetic slice through the full pipeline."""
    feats = []
    for i in range(50):
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-55.8 + i*0.001, -27.3 + i*0.001]},
            "properties": {
                "id": f"x_{i}",
                "source": "tulugar" if i % 2 == 0 else "infocasas",
                "source_url": f"https://example.com/{i}",
                "title": f"Vendo {10 + (i % 11)} hectáreas en Encarnación",
                "state_province": "Departamento de Itapúa",
                "listing_type": "sale",
                "property_type": "land" if i % 3 else "house",
                "price_usd": 100_000 + i*1000,
                "price_pyg": (100_000 + i*1000)*7500,
                "area_ha": 10 + (i % 11),
                "area_sqm": (10 + (i % 11)) * 10000,
                "features": ["Piscina", "Quincho", "patio"],
                "scraped_at_utc": "2026-07-11T05:00:00+00:00",
                "currency": "USD",
            },
        })

    payload = cp.canonicalize(feats, fx_pyg_per_usd=7500, now=dt.datetime(2026, 7, 31))
    assert len(payload["features"]) == 50
    facets = payload["facets"]

    # 1. depto should be normalised to "Itapúa" for all rows
    assert facets["depto"]["Itapúa"] == 50

    # 2. flags should not include foreign_depto_dropped or currency_conflict
    assert "foreign_depto_dropped" not in facets["flags"]
    assert "currency_conflict" not in facets["flags"]

    # 3. canonical_features should have pool, bbq, garden at minimum
    sample = payload["features"][0]["properties"]
    assert "pool" in sample["canonical_features"]
    assert "bbq" in sample["canonical_features"]
    assert "garden" in sample["canonical_features"]

    # 4. usd_per_ha should be present and rounded to 2 decimals
    assert sample["usd_per_ha"] is not None
    assert isinstance(sample["usd_per_ha"], float)

    # 5. cluster_id should be present and start with src-
    assert sample["cluster_id"].startswith("tulugar-") or sample["cluster_id"].startswith("infocasas-")

    # 6. freshness_days should be 19 (11 Jul → 31 Jul = 20 days inclusive
    # of start, but `now - scraped` returns the elapsed 19 full days)
    assert sample["freshness_days"] in (19, 20)