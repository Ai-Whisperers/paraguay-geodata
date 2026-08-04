"""Build exports/web/data/deploy-meta.json from git + filesystem state.

Captures:
  - commit hash (full)
  - branch name
  - deployed_at_utc (ISO 8601)
  - deployer (who triggered)
  - project name
  - data_layers_loaded (per-source feature counts + sizes)
  - live_features_total (sum)
  - deferred_sources (sources that didn't ship)

This is the single source of truth for "what version is live?". The
cron should call this on every deploy — without it, deploy-meta.json
goes stale and the bulletin's "current commit" lies.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


# __file__ = .../tools/build_deploy_meta.py, parents[1] = repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "exports" / "web"
DATA_DIR = EXPORT_DIR / "data"
OUT = DATA_DIR / "deploy-meta.json"

# (id, label, path relative to exports/web/, features_key)
LAYER_SOURCES = [
    ("tile_fabric",        "National tile fabric (10×10 km)",   "data/tile_index.json",                 "tiles"),
    ("priority_tiles",     "Priority tiles (urban anchors)",   "data/priority_tiles.json",              "tiles"),
    ("departamentos_py",   "Departamentos boundaries (OSM)",   "data/admin/departamentos.geojson",      "features"),
    ("distritos_py",       "Distritos boundaries (OSM)",       "data/admin/distritos.geojson",          "features"),
    ("barrios_py",         "Barrios / Localidades (OSM)",       "data/admin/barrios_py.geojson",         "features"),
    ("catastro_parcels",   "Catastro · parcelas sample",        "data/admin/catastro_parcels_sample.geojson", "features"),
    ("catastro_dpto",      "Catastro · deptos",                 "data/admin/catastro_dpto.geojson",      "features"),
    ("catastro_dist",      "Catastro · distritos",              "data/admin/catastro_dist.geojson",      "features"),
    ("catastro_urba",      "Catastro · urban zoning",           "data/admin/catastro_urba.geojson",      "features"),
    ("properties",         "Real-estate listings (canonical)",  "data/properties_enriched_lite.geojson", "features"),
    ("gbif_paraguay",      "GBIF biodiversity (PY)",            "data/gbif_paraguay.geojson",            "features"),
    ("roads",              "OSM roads",                          "data/roads.geojson",                    "features"),
    ("water",              "OSM water",                          "data/water.geojson",                    "features"),
    ("buildings_asuncion", "Buildings (Asunción footprint)",    "data/buildings_asuncion.geojson",       "features"),
    ("indigenous",         "Indigenous territories (10)",       "data/indigenous_territories.geojson",   "features"),
    ("flood_risk",         "Flood zones (5 SEN)",               "data/flood_risk.geojson",               "features"),
    ("climate_risk",       "Climate risk by depto",             "data/climate_risk.geojson",             "features"),
    ("construction_zones", "Construction zones (Asunción)",     "data/construction_zones.json",          "zones"),
    ("bcp_snapshot",       "BCP macro/monetary/rates",          "data/bcp_snapshot.json",                None),
    ("nasa_power",         "NASA POWER (Asunción climate)",     "data/nasa_power_asuncion.json",         None),
    ("inbio_zafra",        "INBIO zafra 2025/2026 (per depto)", "data/inbio_zafra_2025_2026.json",       None),
    ("days_on_market",     "Days-on-market by depto",           "data/days_on_market.json",              None),
    ("property_risk",      "Per-property risk index",           "data/property_risk_index.json",         None),
]


def git(*args: str) -> str:
    """Run a git command and return stripped stdout. Empty on error."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def count_features(path: Path) -> int | None:
    """Count features in a GeoJSON / features JSON. None for non-feature files."""
    if not path.exists():
        return None
    try:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data, dict) and "features" in data:
            return len(data["features"])
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict) and "tiles" in data:
            return len(data["tiles"])
        if isinstance(data, dict) and "zones" in data:
            return len(data["zones"])
        return None
    except Exception:
        return None


def size_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployer", default=os.environ.get("USER", "unknown"))
    parser.add_argument("--out", default=str(OUT), help="Output path")
    args = parser.parse_args()

    layers = []
    total = 0
    deferred = []

    for layer_id, label, rel_path, count_key in LAYER_SOURCES:
        path = EXPORT_DIR / rel_path
        if not path.exists():
            deferred.append({"id": layer_id, "label": label, "missing": rel_path})
            continue
        sz = size_bytes(path)
        features = count_features(path) if count_key else None
        entry = {
            "id": layer_id,
            "label": label,
            "file": rel_path,
            "size_b": sz,
        }
        if features is not None:
            entry["features"] = features
            total += features
        layers.append(entry)

    meta = {
        "commit": git("rev-parse", "HEAD"),
        "commit_short": git("rev-parse", "--short", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "deployed_at_utc": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
            capture_output=True, text=True,
        ).stdout.strip(),
        "deployer": args.deployer,
        "project": "paraguay-geodata",
        "live_features_total": total,
        "data_layers_loaded": layers,
        "deferred_sources": deferred,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(meta, f, indent=2)

    print(f"wrote {out_path}")
    print(f"  commit: {meta['commit_short']}")
    print(f"  layers: {len(layers)} loaded, {len(deferred)} deferred")
    print(f"  total features: {total:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
