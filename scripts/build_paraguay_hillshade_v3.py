#!/usr/bin/env python3
"""Build Paraguay-wide hillshade v3 — OPTIMIZED.

Strategy:
- Fetch 30m DEM tiles from Planetary Computer
- Merge into a single array
- DOWNSAMPLE to 60m (every second source pixel) before hillshade compute
- This makes hillshade ~4x faster AND smaller output
- 60m hillshade is still useful for visual context at national zoom

Output: 4 regions × ~4 MB JPEG = ~16 MB total
Compute time: ~2-3 min per region (down from 6+ min)
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
from rasterio.merge import merge
from affine import Affine
import planetary_computer
import pystac_client

# Class-level terrain/raster technique:
# ~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md

ROOT = Path(__file__).resolve().parents[1]  # repo root = parent of scripts/
DATA = ROOT / 'exports' / 'web' / 'data'
# Only mkdir when running as a script, not when imported by tests.
# Tests don't need write access and shouldn't fail on read-only CI filesystems.
if __name__ == '__main__':
    DATA.mkdir(parents=True, exist_ok=True)

# 4 regions covering Paraguay at 4° x 4°
REGIONS = [
    ('nw', -62.5, -23.5, -58.5, -19.5),
    ('ne', -58.5, -23.5, -54.5, -19.5),
    ('sw', -62.5, -27.5, -58.5, -23.5),
    ('se', -58.5, -27.5, -54.5, -23.5),
]

# Output resolution: 60m (downsample 2x from 30m source)
DOWNSAMPLE = 2  # 30m -> 60m
TARGET_DIM = 6000  # max pixels per side after downsample

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)


def fetch_dem_for_bbox(bbox):
    search = catalog.search(collections=["cop-dem-glo-30"], bbox=bbox)
    items = list(search.item_collection())
    print(f"  Found {len(items)} DEM tiles")
    if not items:
        return None
    datasets = []
    for item in items:
        asset = planetary_computer.sign(item.assets["data"])
        try:
            ds = rasterio.open(asset.href)
            datasets.append(ds)
        except Exception as e:
            print(f"  skip {item.id}: {e}")
    if not datasets:
        return None
    # STAC bbox intersection is inclusive at tile boundaries. Crop while
    # merging so the raster matches the exact requested overlay bounds instead
    # of silently including a fifth tile along each edge.
    try:
        merged, transform = merge(datasets, bounds=bbox)
    finally:
        for ds in datasets:
            ds.close()
    return merged[0], transform


def meters_per_cell(transform, height):
    """Return geographic pixel dimensions in metres at raster center latitude."""
    dx = abs(transform.a)
    dy = abs(transform.e)
    lat_center = transform.f + (height * transform.e / 2)
    m_per_deg_lon = 111320 * math.cos(math.radians(lat_center))
    m_per_deg_lat = 111320
    return dx * m_per_deg_lon, dy * m_per_deg_lat


def compute_hillshade_chunked(dem, transform, azimuth=315, altitude=45, chunk_rows=2000):
    """Horn's method hillshade, computed in chunks to manage memory."""
    az_rad = math.radians(360 - azimuth + 90)
    alt_rad = math.radians(altitude)
    cellsize_x, cellsize_y = meters_per_cell(transform, dem.shape[0])

    dem = dem.astype(np.float32)
    dem = np.nan_to_num(dem, nan=np.nanmean(dem[dem > 0]) if np.any(dem > 0) else 100)

    h, w = dem.shape
    out = np.zeros((h, w), dtype=np.uint8)

    # Pad all four edges. The Horn 3x3 stencil removes one cell from every
    # side; without horizontal padding each chunk becomes two columns narrower
    # than the destination array (e.g. 8998 values for a 9000-column DEM).
    dem_padded = np.pad(dem, ((1, 1), (1, 1)), mode='edge')

    for i in range(0, h, chunk_rows):
        end = min(i + chunk_rows, h)
        # In padded coordinates rows [i:end + 2] contain one halo row above
        # and below the original DEM rows [i:end]. Horizontal halo columns are
        # already present from the four-edge padding above.
        chunk = dem_padded[i:end + 2]

        a = chunk[:-2, :-2]; b = chunk[:-2, 1:-1]; c = chunk[:-2, 2:]
        d = chunk[1:-1, :-2]; f = chunk[1:-1, 2:]
        g = chunk[2:, :-2]; h_ = chunk[2:, 1:-1]; i_ = chunk[2:, 2:]

        dz_dx = ((c + 2*f + i_) - (a + 2*d + g)) / (8 * cellsize_x)
        dz_dy = ((g + 2*h_ + i_) - (a + 2*b + c)) / (8 * cellsize_y)

        slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        aspect = np.arctan2(dz_dy, -dz_dx)
        aspect = np.where(aspect < 0, 2 * math.pi + aspect, aspect)

        shaded = (np.sin(alt_rad) * np.cos(slope) +
                  np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
        shaded = np.clip(shaded, 0, 1)
        out[i:end] = (shaded * 255).astype(np.uint8)

    return out


def process_region(name, bbox):
    print(f"\n=== Region: {name} ===")
    t0 = time.time()
    result = fetch_dem_for_bbox(bbox)
    if result is None:
        return False
    dem, transform = result
    print(f"  DEM: {dem.shape}, {time.time()-t0:.1f}s")

    # Downsample
    if DOWNSAMPLE > 1:
        dem = dem[::DOWNSAMPLE, ::DOWNSAMPLE]
        # Preserve the cropped raster origin and scale its pixel dimensions.
        transform = transform * Affine.scale(DOWNSAMPLE, DOWNSAMPLE)
        print(f"  Downsampled to {dem.shape}")

    t0 = time.time()
    hs = compute_hillshade_chunked(dem, transform)
    print(f"  hillshade: {hs.shape}, {time.time()-t0:.1f}s")

    # Save JPEG with max dimension TARGET_DIM
    out_jpg = DATA / f'hillshade_py_{name}.jpg'
    bounds = {
        'min_lon': float(bbox[0]),
        'min_lat': float(bbox[1]),
        'max_lon': float(bbox[2]),
        'max_lat': float(bbox[3]),
    }

    img = Image.fromarray(hs, mode='L')
    if img.size[0] > TARGET_DIM or img.size[1] > TARGET_DIM:
        # Resize keeping aspect ratio
        ratio = min(TARGET_DIM / img.size[0], TARGET_DIM / img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        print(f"  resized to {new_size}")

    # Publish atomically so an interrupted build never leaves a partial JPEG.
    tmp_jpg = out_jpg.with_suffix('.jpg.tmp')
    img.save(tmp_jpg, 'JPEG', quality=80, optimize=True)
    tmp_jpg.replace(out_jpg)
    out_bounds = DATA / f'hillshade_py_{name}_bounds.json'
    out_bounds.write_text(json.dumps(bounds))
    print(f"  ✓ {out_jpg.name}: {out_jpg.stat().st_size/1024/1024:.2f} MB")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--regions', nargs='+', choices=[region[0] for region in REGIONS],
        default=[region[0] for region in REGIONS],
        help='Region names to build (default: all four)',
    )
    args = parser.parse_args(argv)
    selected = [region for region in REGIONS if region[0] in args.regions]
    failures = []

    for name, *bbox in selected:
        try:
            if not process_region(name, bbox):
                failures.append(name)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failures.append(name)

    union_bounds = {
        'min_lon': min(r[1] for r in REGIONS),
        'min_lat': min(r[2] for r in REGIONS),
        'max_lon': max(r[3] for r in REGIONS),
        'max_lat': max(r[4] for r in REGIONS),
        'regions': [{'name': r[0], 'bbox': [r[1], r[2], r[3], r[4]]} for r in REGIONS],
    }
    (DATA / 'hillshade_py_bounds.json').write_text(json.dumps(union_bounds))
    print(f"\n✓ wrote union bounds")

    if failures:
        print(f"FAILED regions: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"Built {len(selected)} region(s): {', '.join(args.regions)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())