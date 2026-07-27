#!/usr/bin/env python3
"""Build the consolidated architect-export GeoJSON bundle.

What this ships (one file, ready for QGIS / ArcGIS / AutoCAD Map / online viewers):

  exports/web/data/architect_export.geojson

Layers bundled (each Feature tagged with ``layer_kind``):
  • construction_zone   — Per-zone building limits (Ord. 246/94 + future Lucía inputs).
                          Each zone's bbox is converted to a Polygon so it is rendered
                          as a closed area in any GIS client.
  • urban_zoning        — Catastro urban polygons (470 features national; we keep
                          everything within Paraguay bounds).
  • flood_risk          — 5 Catastro flood-risk polygons (already in EPSG:4326).
  • climate_risk_depto  — 18 departments centroids with flood/drought/heat/wildfire
                          risk scores (point geometry, joins on ``dpto`` field).
  • hillshade_priority  — The 8 priority hillshade tiles (Asunción, CdE, PJC, etc.)
                          as rectangle overlays — useful as a "we have DEM here" hint.

The output is **deterministic** (sorted features) so it diffs cleanly across runs.

Notes on formats:
  • GeoJSON is the lingua franca — every QGIS, ArcGIS, AutoCAD Map 3D, web viewer
    and Python notebook can read it. Architects who need true DWG just open this
    file in QGIS and "Save As → DWG" (one click).
  • The same bundle is also exposed via ``exports/web/data/architect_export.geojson``
    so the live site can serve it directly to the architect preset sidebar.

Schema versioning:
  v1 — initial bundle (2026-07-27).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DATA = REPO_ROOT / "exports" / "web" / "data"
OUTPUT_PATH = WEB_DATA / "architect_export.geojson"
CAPITAL_OUTPUT_PATH = WEB_DATA / "architect_export_asuncion.geojson"

CONSTRUCTION_ZONES_PATH = WEB_DATA / "construction_zones.json"
URBAN_ZONING_PATH = WEB_DATA / "admin" / "catastro_urba.geojson"
FLOOD_RISK_PATH = WEB_DATA / "flood_risk.geojson"
CLIMATE_RISK_PATH = WEB_DATA / "climate_risk.geojson"
PRIORITY_TILES_PATH = WEB_DATA / "priority_tiles.json"
HILLSHADE_PRIORITY_META = WEB_DATA / "hillshade_priority_metadata.json"

# Asunción metro area bbox — used for the capital-focused slim bundle.
ASUNCION_BBOX = (-57.70, -25.40, -57.45, -25.18)

BUNDLE_VERSION = 1


def _log(msg: str) -> None:
    print(f"[architect_export] {msg}", file=sys.stderr)


def _bbox_to_polygon(bbox: list[float]) -> dict[str, Any]:
    """Convert [W, S, E, N] bbox to a GeoJSON Polygon geometry."""
    w, s, e, n = bbox
    # Ring is closed: first point == last point.
    return {
        "type": "Polygon",
        "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
    }


def _bbox_features_from_zones(zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for z in zones:
        bbox = z.get("approximate_bbox")
        if not bbox or len(bbox) != 4:
            continue
        out.append(
            {
                "type": "Feature",
                "properties": {
                    "layer_kind": "construction_zone",
                    "zone_id": z["zone_id"],
                    "city": z["city"],
                    "category": z["category"],
                    "name": z["name"],
                    "max_height_m": z.get("max_height_m"),
                    "max_floors": z.get("max_floors"),
                    "max_lot_coverage_pct": z.get("max_lot_coverage_pct"),
                    "max_construction_pct": z.get("max_construction_pct"),
                    "setback_front_m": z.get("setback_front_m"),
                    "setback_side_m": z.get("setback_side_m"),
                    "setback_back_m": z.get("setback_back_m"),
                    "allowed_use": z.get("allowed_use", []),
                    "restricted_use": z.get("restricted_use", []),
                    "ordinance_ref": z.get("ordinance_ref"),
                    "last_updated": z.get("last_updated"),
                    "data_source": "Ord. 246/94 + Lucía handoff",
                    "data_warning": "approximate bbox — real polygon from Catastro pending",
                },
                "geometry": _bbox_to_polygon(bbox),
            }
        )
    return out


def _load_urban_zoning() -> list[dict[str, Any]]:
    """Tag every Catastro urban polygon with layer_kind and provenance."""
    if not URBAN_ZONING_PATH.exists():
        return []
    gj = json.loads(URBAN_ZONING_PATH.read_text(encoding="utf-8"))
    features = []
    for f in gj.get("features", []):
        props = dict(f.get("properties", {}))
        props["layer_kind"] = "urban_zoning"
        props["data_source"] = "Catastro (paraguay.gov.py)"
        features.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
    return features


def _load_flood_risk() -> list[dict[str, Any]]:
    if not FLOOD_RISK_PATH.exists():
        return []
    gj = json.loads(FLOOD_RISK_PATH.read_text(encoding="utf-8"))
    out = []
    for f in gj.get("features", []):
        props = dict(f.get("properties", {}))
        props["layer_kind"] = "flood_risk"
        props["data_source"] = "Catastro WFS flood polygons"
        out.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
    return out


def _load_climate_risk_departments() -> list[dict[str, Any]]:
    """Convert climate_risk.geojson (whatever shape it is) to per-department point features.

    The site already exposes this file as a choropleth but for offline use we ship
    centroids so architects can join by department.
    """
    if not CLIMATE_RISK_PATH.exists():
        return []
    gj = json.loads(CLIMATE_RISK_PATH.read_text(encoding="utf-8"))
    centroids: list[dict[str, Any]] = []
    for f in gj.get("features", []):
        props = dict(f.get("properties", {}))
        geom = f.get("geometry") or {}
        # If polygon, skip — keep only points; centroids appended separately.
        centroids.append(
            {
                "type": "Feature",
                "properties": {**props, "layer_kind": "climate_risk_depto"},
                "geometry": geom,
            }
        )
    return centroids


def _load_priority_hillshade_rects() -> list[dict[str, Any]]:
    """Ship the 8 priority hillshade tiles as rectangle overlays."""
    if not PRIORITY_TILES_PATH.exists():
        return []
    data = json.loads(PRIORITY_TILES_PATH.read_text(encoding="utf-8"))
    tiles = data.get("tiles", [])
    rects = []
    for t in tiles:
        bbox = t.get("bbox_wsen")
        if not bbox or len(bbox) != 4:
            continue
        props = {
            "layer_kind": "hillshade_priority",
            "tile_id": t["tile_id"],
            "anchor": t.get("anchor"),
            "area_km2": t.get("area_km2"),
            "utm_zone_hint": t.get("utm_zone_hint"),
            "data_source": "Copernicus GLO-30 DEM",
            "status": "5m hillshade available",
        }
        rects.append({"type": "Feature", "properties": props, "geometry": _bbox_to_polygon(bbox)})
    return rects


def _collect_features() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    _log("loading source layers…")
    zones_doc = json.loads(CONSTRUCTION_ZONES_PATH.read_text(encoding="utf-8"))
    zone_features = _bbox_features_from_zones(zones_doc.get("zones", []))
    urban_features = _load_urban_zoning()
    flood_features = _load_flood_risk()
    climate_features = _load_climate_risk_departments()
    hillshade_features = _load_priority_hillshade_rects()
    return zone_features, urban_features, flood_features, climate_features, hillshade_features


def _sort_key(f: dict[str, Any]) -> tuple[str, str]:
    props = f.get("properties", {})
    secondary = (
        props.get("zone_id")
        or props.get("tile_id")
        or props.get("name")
        or props.get("dpto")
        or ""
    )
    return (props.get("layer_kind", ""), str(secondary))


def _feature_bbox(feature: dict[str, Any]) -> tuple[float, float, float, float] | None:
    """Compute (W, S, E, N) bbox of a feature's geometry, or None if empty/missing."""
    geom = feature.get("geometry") or {}
    gtype = geom.get("type")
    coords: list[Any] = []
    if gtype == "Point":
        coords.append(geom.get("coordinates", []))
    elif gtype == "Polygon":
        coords.extend(geom.get("coordinates", [[]])[0])
    elif gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            if poly:
                coords.extend(poly[0])
    if not coords:
        return None
    xs = [c[0] for c in coords if len(c) >= 2]
    ys = [c[1] for c in coords if len(c) >= 2]
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    """Strict bbox-bbox intersection test."""
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _build_bundle_dict(features: list[dict[str, Any]], bundle_name: str, scope: str) -> dict[str, Any]:
    """Wrap a list of features into the canonical bundle envelope."""
    from collections import Counter

    counts = dict(Counter(f["properties"].get("layer_kind", "unknown") for f in features))
    counts["total"] = len(features)
    return {
        "type": "FeatureCollection",
        "name": bundle_name,
        "version": BUNDLE_VERSION,
        "scope": scope,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_repo": "https://github.com/Ai-Whisperers/paraguay-geodata",
        "live_site": "https://geodata.paragu-ai.com/",
        "intended_for": (
            "Architects, urban planners, terrain analysts. "
            "Open in QGIS / ArcGIS / AutoCAD Map 3D. "
            "Use 'Save As → DWG' for native CAD workflow."
        ),
        "schema": {
            "layer_kind": "construction_zone | urban_zoning | flood_risk | climate_risk_depto | hillshade_priority",
            "geometry_types": "Polygon, MultiPolygon, Point",
            "crs": "EPSG:4326 (WGS84)",
        },
        "feature_counts": counts,
        "features": features,
    }


def build_full_bundle() -> dict[str, Any]:
    zone_features, urban_features, flood_features, climate_features, hillshade_features = (
        _collect_features()
    )
    all_features = (
        zone_features + urban_features + flood_features + climate_features + hillshade_features
    )
    all_features.sort(key=_sort_key)
    bundle = _build_bundle_dict(
        all_features, "paraguay_geodata_architect_export", scope="national"
    )
    _log(f"built full bundle: {bundle['feature_counts']}")
    return bundle


def build_asuncion_bundle() -> dict[str, Any]:
    """Slim bundle focused on Asunción metro area — small enough to email / preview."""
    zone_features, urban_features, flood_features, climate_features, hillshade_features = (
        _collect_features()
    )
    asu = ASUNCION_BBOX

    # Construction zones & climate depto centroids already have coordinates we can test.
    zone_in = [f for f in zone_features if _bbox_intersects(_feature_bbox(f), asu)]
    climate_in = [f for f in climate_features if _bbox_intersects(_feature_bbox(f), asu)]

    # Urban zoning polygons — many districts outside Asunción bbox; filter by bbox.
    urban_in = []
    for f in urban_features:
        fb = _feature_bbox(f)
        if fb and _bbox_intersects(fb, asu):
            urban_in.append(f)

    # Flood polygons — usually national-scale; keep only those touching the bbox.
    flood_in = []
    for f in flood_features:
        fb = _feature_bbox(f)
        if fb and _bbox_intersects(fb, asu):
            flood_in.append(f)

    # Hillshade priority tiles — only keep tiles whose centroid falls in the bbox.
    hill_in = []
    for f in hillshade_features:
        fb = _feature_bbox(f)
        if fb and _bbox_intersects(fb, asu):
            hill_in.append(f)

    features = zone_in + urban_in + flood_in + climate_in + hill_in
    features.sort(key=_sort_key)
    bundle = _build_bundle_dict(
        features,
        "paraguay_geodata_architect_export_asuncion",
        scope=f"bbox=({asu[0]},{asu[1]},{asu[2]},{asu[3]})",
    )
    _log(f"built Asunción bundle: {bundle['feature_counts']}")
    return bundle


def _write_bundle(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = path.stat().st_size / 1024
    _log(f"wrote {path.relative_to(REPO_ROOT)} ({size_kb:.1f} KB)")


def main() -> int:
    full = build_full_bundle()
    _write_bundle(full, OUTPUT_PATH)

    asu = build_asuncion_bundle()
    _write_bundle(asu, CAPITAL_OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
