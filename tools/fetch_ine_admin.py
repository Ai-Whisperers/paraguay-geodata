#!/usr/bin/env python3
"""tools/fetch_ine_admin.py — Overpass-based admin boundary fetcher (LIVE).

Class-level technique: docs/sources/administrative.md

Run:
    python3 -m tools.fetch_ine_admin --layer departamentos
    python3 -m tools.fetch_ine_admin --layer all --apply

Output: exports/web/data/admin/<layer>.geojson (Pages-deployable)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "exports" / "web" / "data" / "admin"

LAYERS = {
    "departamentos":         {"label": "Departamentos (17)",          "admin_level": 4,  "approx": 17},
    "distritos":             {"label": "Distritos (~262)",            "admin_level": 6,  "approx": 262},
    "barrios":               {"label": "Barrios / Localidades",       "admin_level": 8,  "approx": 15000},
    "vias_principales":      {"label": "Vías principales",            "type_filter": "way", "highway_filter": True, "approx": 1500},
    "hidrografia":           {"label": "Hidrografía",                 "type_filter": "way", "waterway_filter": True, "approx": 5000},
    "comunidades_indigenas": {"label": "Comunidades indígenas",       "tag_filter": "boundary=protected_area", "approx": 700},
    "locales_salud":         {"label": "Locales de Salud",            "tag_filter": "amenity=clinic,hospital,doctors,pharmacy", "approx": 2500},
    "locales_policial":      {"label": "Locales Policiales",          "tag_filter": "amenity=police", "approx": 1500},
    "locales_educacion":     {"label": "Locales de Educación",        "tag_filter": "amenity=school,college,university,kindergarten", "approx": 9000},
}


OVERPASS_REL = '[out:json][timeout:120];(rel["admin_level"="{al}"]["ISO3166-2"~"^PY-"];);out geom;'
OVERPASS_WAY = (
    '[out:json][timeout:120];area["ISO3166-2"~"^PY-"]->.a;'
    '(way["highway"](area.a););out geom;'
)
OVERPASS_WATER = (
    '[out:json][timeout:120];area["ISO3166-2"~"^PY-"]->.a;'
    '(way["waterway"](area.a););out geom;'
)
OVERPASS_AMENITY = (
    '[out:json][timeout:120];area["ISO3166-2"~"^PY-"]->.a;'
    '(node["amenity"~"{amen}"](area.a););out;'
)


def fetch_admin_relations(admin_level: int) -> list[dict]:
    """Fetch admin_level relations for PY via Overpass."""
    q = OVERPASS_REL.format(al=admin_level)
    return _query_overpass(q)


def fetch_highways() -> list[dict]:
    return _query_overpass(OVERPASS_WAY)


def fetch_waterways() -> list[dict]:
    return _query_overpass(OVERPASS_WATER)


def fetch_amenity_nodes(amenity_pattern: str) -> list[dict]:
    q = OVERPASS_AMENITY.format(amen=amenity_pattern)
    return _query_overpass(q)


def _query_overpass(query: str, max_retries: int = 3) -> list[dict]:
    """POST query to Overpass, return elements[]."""
    url = "https://overpass-api.de/api/interpreter"
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            r = httpx.post(
                url,
                data={"data": query},
                headers={"User-Agent": "paraguay-geodata/0.1 (Erebus)"},
                timeout=180,
            )
            r.raise_for_status()
            return r.json().get("elements", [])
        except Exception as e:
            last_err = e
            print(f"[fetch_ine_admin] Overpass attempt {attempt} failed: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Overpass failed after {max_retries} attempts: {last_err}")


def elements_to_geojson_admin(elements: list[dict], layer: str) -> dict:
    """Convert Overpass relation elements to GeoJSON Polygon features."""
    features = []
    for e in elements:
        tags = e.get("tags", {})
        if "geometry" not in e:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in e["geometry"]]
        if not coords:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {
                "iso_code": tags.get("ISO3166-2", tags.get("ref", "")),
                "name": tags.get("name", tags.get("name:en", "")),
                "name_es": tags.get("name:es", tags.get("name", "")),
                "admin_level": e.get("type"),
                "osm_id": e.get("id"),
                "wikidata": tags.get("wikidata", ""),
                "layer": layer,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def elements_to_geojson_lines(elements: list[dict], layer: str) -> dict:
    features = []
    for e in elements:
        if "geometry" not in e:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in e["geometry"]]
        if not coords:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"osm_id": e.get("id"), "layer": layer, **e.get("tags", {})},
        })
    return {"type": "FeatureCollection", "features": features}


def elements_to_geojson_points(elements: list[dict], layer: str) -> dict:
    features = []
    for e in elements:
        if e.get("type") != "node":
            continue
        tags = e.get("tags", {})
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
            "properties": {
                "osm_id": e.get("id"),
                "name": tags.get("name", ""),
                "amenity": tags.get("amenity", ""),
                "layer": layer,
                **tags,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def fetch_layer(layer: str) -> dict:
    """Fetch one layer, save to exports/web/data/admin/<layer>.geojson."""
    if layer not in LAYERS:
        raise ValueError(f"unknown layer: {layer}")

    cfg = LAYERS[layer]
    print(f"[fetch_ine_admin] fetching {layer} (label={cfg['label']})")

    if layer == "departamentos":
        elems = fetch_admin_relations(4)
        geo = elements_to_geojson_admin(elems, layer)
    elif layer == "distritos":
        elems = fetch_admin_relations(6)
        geo = elements_to_geojson_admin(elems, layer)
    elif layer == "vias_principales":
        elems = fetch_highways()
        geo = elements_to_geojson_lines(elems, layer)
    elif layer == "hidrografia":
        elems = fetch_waterways()
        geo = elements_to_geojson_lines(elems, layer)
    elif layer in ("locales_salud", "locales_policial", "locales_educacion"):
        amenity_map = {
            "locales_salud":     "clinic|hospital|doctors|pharmacy",
            "locales_policial":  "police",
            "locales_educacion": "school|college|university|kindergarten",
        }
        elems = fetch_amenity_nodes(amenity_map[layer])
        geo = elements_to_geojson_points(elems, layer)
    else:
        raise NotImplementedError(f"layer {layer} not implemented yet")

    out_path = OUT_DIR / f"{layer}.geojson"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(geo, indent=2))
    print(f"[fetch_ine_admin] {layer}: {len(geo['features'])} features → {out_path}")
    return geo


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="INE admin + OSM layers fetcher (LIVE).")
    parser.add_argument("--layer", default=None, choices=list(LAYERS) + ["all"])
    parser.add_argument("--apply", action="store_true", help="Actually fetch (default dry-run).")
    args = parser.parse_args(argv)

    if not args.apply:
        for k, v in LAYERS.items():
            print(f"  [DRY] {k}: {v['label']} (~{v['approx']} features)")
        print("Re-run with --apply to actually fetch.")
        return 0

    layers = list(LAYERS) if args.layer == "all" or args.layer is None else [args.layer]
    for layer in layers:
        try:
            fetch_layer(layer)
        except Exception as e:
            print(f"[fetch_ine_admin] ERROR fetching {layer}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))