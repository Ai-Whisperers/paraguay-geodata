#!/usr/bin/env python3
"""Build Paraguay-wide hillshade — production version.

Strategy: 7 regional rasters covering Paraguay at 30m resolution.
Each region: ~1.5-2 GB raw DEM, ~3-5 MB JPEG hillshade.

Regions (chosen for ~similar pixel counts):
  1. Occidental (Chaco): -62 to -56, -23 to -19
  2. Occidental-South:    -62 to -56, -27 to -23
  3. Oriental-North:       -56 to -54, -23 to -19
  4. Oriental-Central:     -56 to -54, -25 to -23 (Asunción region)
  5. Oriental-South:       -56 to -54, -27 to -25
  6. Oriental-Center-East: -54 to -52, -25 to -21
  7. Oriental-East:        -54 to -52, -27 to -25 (Ciudad del Este)

Total: 7 regions × ~3-5 MB JPEG = ~25-35 MB total
Plus 7 × bounds JSON (~50 bytes each)

Each region: 2° lat × 2° lon at 30m ≈ 7,400 × 7,400 px ≈ 54M pixels
Hillshade computation: ~30-90s per region

Output:
  exports/web/data/hillshade_py_1.jpg + bounds
  exports/web/data/hillshade_py_2.jpg + bounds
  ...
"""
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
import planetary_computer
import pystac_client

ROOT = Path('/root/paraguay-geodata')
DATA = ROOT / 'exports' / 'web' / 'data'
DATA.mkdir(parents=True, exist_ok=True)

# 4 regional bboxes [min_lon, min_lat, max_lon, max_lat] — 4° x 4° each, full Paraguay
REGIONS = [
    ('nw', -62.5, -23.5, -58.5, -19.5),  # NW Chaco
    ('ne', -58.5, -23.5, -54.5, -19.5),  # NE Oriental
    ('sw', -62.5, -27.5, -58.5, -23.5),  # SW Chaco + Paraguarí
    ('se', -58.5, -27.5, -54.5, -23.5),  # SE Oriental + Asunción
]

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)


def fetch_dem_for_bbox(bbox):
    """Fetch + merge Copernicus GLO-30 DEM tiles for a bbox."""
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
    if len(datasets) == 1:
        ds = datasets[0]
        data = ds.read(1)
        transform = ds.transform
        ds.close()
        return data, transform
    merged, transform = merge(datasets)
    for ds in datasets:
        ds.close()
    return merged[0], transform


def compute_hillshade(dem, transform, azimuth=315, altitude=45):
    """Horn's method hillshade, 30m DEM at Paraguay latitudes."""
    az_rad = math.radians(360 - azimuth + 90)
    alt_rad = math.radians(altitude)
    dx = abs(transform.a)
    dy = abs(transform.e)
    lat_center = (dem.shape[0] * dy / 2 + transform.f)
    m_per_deg_lon = 111320 * math.cos(math.radians(-lat_center))
    m_per_deg_lat = 111320
    cellsize_x = dx * m_per_deg_lon
    cellsize_y = dy * m_per_deg_lat

    dem = dem.astype(np.float32)
    # Fill NaN with neighbor average
    dem = np.nan_to_num(dem, nan=np.nanmean(dem[dem > 0]) if np.any(dem > 0) else 100)

    padded = np.pad(dem, 1, mode='edge')
    a = padded[:-2, :-2]; b = padded[:-2, 1:-1]; c = padded[:-2, 2:]
    d = padded[1:-1, :-2]; f = padded[1:-1, 2:]
    g = padded[2:, :-2]; h = padded[2:, 1:-1]; i = padded[2:, 2:]

    dz_dx = ((c + 2*f + i) - (a + 2*d + g)) / (8 * cellsize_x)
    dz_dy = ((g + 2*h + i) - (a + 2*b + c)) / (8 * cellsize_y)

    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect = np.arctan2(dz_dy, -dz_dx)
    aspect = np.where(aspect < 0, 2 * math.pi + aspect, aspect)

    shaded = (np.sin(alt_rad) * np.cos(slope) +
              np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
    shaded = np.clip(shaded, 0, 1)
    return (shaded * 255).astype(np.uint8)


def process_region(name, bbox):
    print(f"\n=== Region: {name} (bbox {bbox}) ===")
    t0 = time.time()
    result = fetch_dem_for_bbox(bbox)
    if result is None:
        print(f"  SKIP: no DEM")
        return False
    dem, transform = result
    print(f"  DEM: {dem.shape}, {time.time()-t0:.1f}s")

    t0 = time.time()
    hs = compute_hillshade(dem, transform)
    print(f"  hillshade: {hs.shape}, {time.time()-t0:.1f}s")

    # Save JPEG with reduced size (max 4096 px wide)
    out_jpg = DATA / f'hillshade_py_{name}.jpg'
    bounds = {
        'min_lon': float(bbox[0]),
        'min_lat': float(bbox[1]),
        'max_lon': float(bbox[2]),
        'max_lat': float(bbox[3]),
    }
    if hs.shape[0] > 4096 or hs.shape[1] > 4096:
        img = Image.fromarray(hs, mode='L')
        img.thumbnail((4096, 4096), Image.LANCZOS)
        img.save(out_jpg, 'JPEG', quality=82, optimize=True)
        print(f"  downscaled to {img.size}")
    else:
        img = Image.fromarray(hs, mode='L')
        img.save(out_jpg, 'JPEG', quality=85, optimize=True)

    out_bounds = DATA / f'hillshade_py_{name}_bounds.json'
    out_bounds.write_text(json.dumps(bounds))
    print(f"  saved {out_jpg.name}: {out_jpg.stat().st_size/1024/1024:.2f} MB")
    return True


if __name__ == '__main__':
    for name, *bbox in REGIONS:
        try:
            process_region(name, bbox)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Also write a "national bounds" file that's the union (for backward-compat)
    union_bounds = {
        'min_lon': min(r[1] for r in REGIONS),
        'min_lat': min(r[2] for r in REGIONS),
        'max_lon': max(r[3] for r in REGIONS),
        'max_lat': max(r[4] for r in REGIONS),
        'regions': [{'name': r[0], 'bbox': [r[1], r[2], r[3], r[4]]} for r in REGIONS],
    }
    (DATA / 'hillshade_py_bounds.json').write_text(json.dumps(union_bounds))
    print(f"\n✓ wrote union bounds")