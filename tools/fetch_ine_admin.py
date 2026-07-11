"""
tools/fetch_ine_admin.py — Download INE administrative boundaries + locales.

Source: https://www.ine.gov.py/microdatos/ → CARTOGRAFÍA DIGITAL 2012
Layers: Departamentos, Distritos, Barrios, Manzanas, Vías, Hidrografía,
        Comunidades indígenas, Locales Salud/Policial/Educación
Format: KML, Shapefile, GeoJSON
License: Licencia de Uso de la Información Pública del Gobierno Paraguayo

Class-level technique: see `docs/sources/administrative.md`

Run:
    python3 -m tools.fetch_ine_admin --layer departamentos
    python3 -m tools.fetch_ine_admin --all-layers --dry-run

TODO(Phase 1.5): implement the actual download + clipping per-tile.
The cartography ZIPs are hosted on INE's microdatos server with URLs that
follow predictable patterns; we need to (a) probe the index page to find
the current ZIP URLs, (b) download + unzip, (c) convert to GeoJSON
via ogr2ogr, (d) clip each per-tile, (e) ship to exports/web/data/admin/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# Layer definitions (NAME → description, geometry type, est. features)
LAYERS = {
    "departamentos":         {"label": "Departamentos (17)",          "geom": "Polygon",     "approx": 17,    "phase": "1"},
    "distritos":             {"label": "Distritos (~262)",            "geom": "Polygon",     "approx": 262,   "phase": "1"},
    "barrios":               {"label": "Barrios / Localidades",       "geom": "Polygon",     "approx": 15000, "phase": "1"},
    "manzanas":              {"label": "Manzanas (urban)",            "geom": "Polygon",     "approx": 80000, "phase": "1.5"},
    "vias_principales":      {"label": "Vías principales",            "geom": "LineString",  "approx": 1500,  "phase": "1"},
    "hidrografia":           {"label": "Hidrografía",                 "geom": "LineString",  "approx": 5000,  "phase": "1"},
    "comunidades_indigenas": {"label": "Comunidades indígenas",       "geom": "Polygon",     "approx": 700,   "phase": "1"},
    "locales_salud":         {"label": "Locales de Salud",            "geom": "Point",       "approx": 2500,  "phase": "1"},
    "locales_policial":      {"label": "Locales Policiales",          "geom": "Point",       "approx": 1500,  "phase": "1"},
    "locales_educacion":     {"label": "Locales de Educación",        "geom": "Point",       "approx": 9000,  "phase": "1"},
}


def fetch_layer(layer_name: str, dry_run: bool = True) -> int:
    """Stub — Phase 1.5 implements. Returns count of features."""
    if layer_name not in LAYERS:
        print(f"  [fetch_ine_admin] ERROR: unknown layer '{layer_name}'. Known: {list(LAYERS)}")
        return 0
    meta = LAYERS[layer_name]
    if dry_run:
        print(f"  [fetch_ine_admin] STUB layer={layer_name}  "
              f"label={meta['label']}  approx={meta['approx']}  phase={meta['phase']}")
    else:
        # TODO: actually download the cartography ZIP, unzip, ogr2ogr → GeoJSON
        # Per-tile clip with tools/fetch_tile.py once Phase 1 wires the chain
        pass
    return meta["approx"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="INE admin boundaries + locales fetcher (Phase 1.5 stub).")
    parser.add_argument("--layer", default=None, choices=list(LAYERS) + ["all"],
                        help="Single layer, or 'all'.")
    parser.add_argument("--all-layers", action="store_true", help="Same as --layer all.")
    parser.add_argument("--apply", action="store_true", help="Actually fetch (Phase 1.5). Default dry-run.")
    args = parser.parse_args(argv)

    dry_run = not args.apply
    layer_names = list(LAYERS) if (args.all_layers or args.layer == "all") else [args.layer] if args.layer else []
    if not layer_names:
        print("ERROR: --layer or --all-layers required.", file=sys.stderr)
        return 1
    for layer in layer_names:
        fetch_layer(layer, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))