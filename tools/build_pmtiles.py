"""tools/build_pmtiles.py

Convert the canonical properties GeoJSON into a PMTiles point-cloud vector
tile set, served by Cloudflare Pages at `/data/properties.pmtiles`.

Why: the canonical geojson is 11 MB.  Loading it eagerly on every page
view is ~3-5s on 4G.  Vector tiles (PMTiles) load only the tiles currently
in the viewport, which is typically 5-50 KB for our zoom levels.

Outputs:
  exports/web/data/properties.pmtiles  (single-file vector tile set)
  exports/web/data/properties.pmtiles.json  (Tippecanoe metadata sidecar)

Requires:
  - tippecanoe (apt install tippecanoe) — produces .mbtiles
  - pmtiles Python lib (pip install pmtiles) — converts .mbtiles → .pmtiles

Usage:
  python3 -m tools.build_pmtiles
  python3 -m tools.build_pmtiles --zoom-min 8 --zoom-max 16
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flatten_to_ndjson(features: list) -> Path:
    """Convert GeoJSON FeatureCollection to NDJSON (one feature per line)."""
    tmp = ROOT / "data" / "properties" / "cache" / "pymtiles_input.ndjson"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w") as f:
        for feat in features:
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates") or []
            if not coords or geom.get("type") != "Point":
                continue
            row = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [coords[0], coords[1]]},
                "properties": feat.get("properties") or {},
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return tmp


def _run_tippecanoe(nd_path: Path, mbtiles_path: Path, *,
                     zoom_min: int, zoom_max: int, drop: list[str]) -> int:
    """Run tippecanoe to produce .mbtiles from NDJSON."""
    drop_args = []
    for k in drop:
        drop_args += ["-x", k.strip()]
    args = [
        "tippecanoe",
        "-o", str(mbtiles_path),
        "-l", "properties",
        "--minimum-zoom", str(zoom_min),
        "--maximum-zoom", str(zoom_max),
        "--base-zoom", str(zoom_max - 1),
        "--include", "fid",
        "-B", "0",
        "-d", "8",
        "--simplification", "10",
        "--detect-shared-borders",
        "--force",
        "--no-tile-size-limit",
        *drop_args,
        str(nd_path),
    ]
    print(f"  running tippecanoe (zoom {zoom_min}-{zoom_max})…")
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  tippecanoe FAILED:")
        print(f"  stdout: {r.stdout[:2000]}")
        print(f"  stderr: {r.stderr[:2000]}")
        return r.returncode
    print(f"  OK: {mbtiles_path.stat().st_size:,} bytes")
    return 0


def _mbtiles_to_pmtiles(mbtiles_path: Path, pmtiles_path: Path) -> int:
    """Convert .mbtiles to .pmtiles via the pmtiles Python lib + our helper."""
    try:
        import importlib
        importlib.import_module("pmtiles")
    except ImportError:
        print("  ERROR: pmtiles Python lib not installed.  pip install pmtiles")
        return 1
    # Use the bundled module that talks to the pmtiles Python lib directly.
    from tools._mbtiles_to_pmtiles import convert as _convert
    return _convert(mbtiles_path, pmtiles_path)


def _write_sidecar(pmtiles_path: Path, *, zoom_min: int, zoom_max: int, n_features: int) -> None:
    """Write a JSON sidecar with minzoom/maxzoom/center for client libs."""
    meta = {
        "name": "properties",
        "format": "pbf",
        "generator": "tippecanoe + pmtiles",
        "minzoom": zoom_min,
        "maxzoom": zoom_max,
        "bounds": [-63.5, -27.5, -54.0, -19.0],  # PY bbox
        "center": [-58.5, -23.5, 6],
        "feature_count": n_features,
        "attribution": "<a href='https://github.com/Ai-Whisperers/paraguay-geodata'>Ai-Whisperers</a> · CC0",
    }
    meta_path = pmtiles_path.with_suffix(".pmtiles.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"  wrote {meta_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "properties" / "canonical_properties.geojson"),
        help="Path to the canonical geojson (default: %(default)s).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "exports" / "web" / "data"),
        help="Where to write properties.pmtiles (default: %(default)s).",
    )
    parser.add_argument("--zoom-min", type=int, default=6, help="Min zoom (default: 6).")
    parser.add_argument("--zoom-max", type=int, default=16, help="Max zoom (default: 16).")
    parser.add_argument(
        "--exclude-properties",
        default="description,images,address_raw,last_seen_at,scraped_at_utc,pii_scrub_utc,pii_scrub_version",
        help="Comma-separated prop keys to drop (keeps tiles small).",
    )
    parser.add_argument(
        "--no-pmtiles",
        action="store_true",
        help="Skip the .mbtiles → .pmtiles conversion; ship .mbtiles directly.",
    )
    args = parser.parse_args(argv)

    if not shutil.which("tippecanoe"):
        sys.exit("ERROR: tippecanoe not installed.  apt install tippecanoe")

    inp = Path(args.input)
    if not inp.exists():
        sys.exit(f"input not found: {inp}")
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    pmtiles_path = outdir / "properties.pmtiles"
    mbtiles_path = ROOT / "data" / "properties" / "cache" / "properties.mbtiles"
    mbtiles_final = outdir / "properties.mbtiles"
    mbtiles_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  loading {inp}…")
    fc = json.loads(inp.read_text())
    feats = fc.get("features") or []
    print(f"  {len(feats)} features")

    nd_path = _flatten_to_ndjson(feats)
    print(f"  NDJSON: {nd_path}")

    drop = args.exclude_properties.split(",")
    rc = _run_tippecanoe(nd_path, mbtiles_path,
                         zoom_min=args.zoom_min, zoom_max=args.zoom_max, drop=drop)
    if rc != 0:
        sys.exit(rc)

    # Always copy .mbtiles to outdir (CF Pages can serve it directly)
    shutil.copy(mbtiles_path, mbtiles_final)
    print(f"  copied: {mbtiles_final}")

    if not args.no_pmtiles:
        rc = _mbtiles_to_pmtiles(mbtiles_path, pmtiles_path)
        if rc == 0 and pmtiles_path.exists():
            print(f"  PMTiles: {pmtiles_path.stat().st_size:,} bytes")
            _write_sidecar(pmtiles_path,
                           zoom_min=args.zoom_min, zoom_max=args.zoom_max, n_features=len(feats))
    else:
        print(f"  SKIP pmtiles conversion (--no-pmtiles)")

    # Always write a sidecar (clients can use it even if .mbtiles only)
    if not pmtiles_path.with_suffix(".pmtiles.json").exists():
        _write_sidecar(mbtiles_final, zoom_min=args.zoom_min,
                       zoom_max=args.zoom_max, n_features=len(feats))

    return 0


if __name__ == "__main__":
    sys.exit(main())
