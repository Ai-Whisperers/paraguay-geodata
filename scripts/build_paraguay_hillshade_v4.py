#!/usr/bin/env python3
"""Build Paraguay-wide hillshade v4 — simpler & correct.

Strategy: downsample DEM to ~120m before hillshade compute.
This makes the arrays manageable AND keeps visual quality acceptable.
- 4° × 4° region at 120m = 30,000 × 33,000 px (manageable)
- Wait no: 4° × 4° × 30 px/arcsec × 3600 arcsec/° = 4 × 4 × 3600 = 57,600 px
- At 120m (4x downsample): 14,400 × 14,400 px = 207 megapixels = 800 MB RAM float32
- At 200m (6.7x downsample): 8,640 × 8,640 = 75 megapixels = 300 MB RAM
- Better: downsample to 200m

Final output: max 6,000 × 6,000 px JPEG per region
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
from rasterio.transform import from_bounds
import planetary_computer
import pystac_client

ROOT = Path('/root/paraguay-geodata')
DATA = ROOT / 'exports' / 'web' / 'data'
DATA.mkdir(parents=True, exist_ok=True)

# 4 regions covering Paraguay at 4° x 4°
REGIONS = [
    ('nw', -62.5, -23.5, -58.5, -19.5),
    ('ne', -58.5, -23.5, -54.5, -19.5),
    ('sw', -62.5, -27.5, -58.5, -23.5),
    ('se', -58.5, -27.5, -54.5, -23.5),
]

# At 30m source: 1° lon ~ 3600 px. So 4° x 4° = 14400 x 14400 px raw.
# Downsample 4x: 3600 x 3600 px (4 MB JPEG)
DOWNSAMPLE = 4
TARGET_DIM = 6000

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


def compute_hillshade_simple(dem, transform, azimuth=315, altitude=45):
    """Horn's method hillshade on downsampled DEM. No chunking needed."""
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
    dem = np.nan_to_num(dem, nan=np.nanmean(dem[dem > 0]) if np.any(dem > 0) else 100)

    # Pad with 1 row/col on each side
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
    print(f"\n=== Region: {name} ===")
    t0 = time.time()
    result = fetch_dem_for_bbox(bbox)
    if result is None:
        return False
    dem, transform = result
    print(f"  DEM: {dem.shape}, {time.time()-t0:.1f}s")

    # Downsample
    dem = dem[::DOWNSAMPLE, ::DOWNSAMPLE]
    new_transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3],
                                 dem.shape[1], dem.shape[0])
    print(f"  Downsampled to {dem.shape}")

    t0 = time.time()
    hs = compute_hillshade_simple(dem, new_transform)
    print(f"  hillshade: {hs.shape}, {time.time()-t0:.1f}s")

    out_jpg = DATA / f'hillshade_py_{name}.jpg'
    bounds = {
        'min_lon': float(bbox[0]),
        'min_lat': float(bbox[1]),
        'max_lon': float(bbox[2]),
        'max_lat': float(bbox[3]),
    }

    img = Image.fromarray(hs, mode='L')
    if img.size[0] > TARGET_DIM or img.size[1] > TARGET_DIM:
        ratio = min(TARGET_DIM / img.size[0], TARGET_DIM / img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        print(f"  resized to {new_size}")

    img.save(out_jpg, 'JPEG', quality=82, optimize=True)
    out_bounds = DATA / f'hillshade_py_{name}_bounds.json'
    out_bounds.write_text(json.dumps(bounds))
    print(f"  ✓ {out_jpg.name}: {out_jpg.stat().st_size/1024/1024:.2f} MB")
    return True


if __name__ == '__main__':
    for name, *bbox in REGIONS:
        try:
            process_region(name, bbox)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    union_bounds = {
        'min_lon': min(r[1] for r in REGIONS),
        'min_lat': min(r[2] for r in REGIONS),
        'max_lon': max(r[3] for r in REGIONS),
        'max_lat': max(r[4] for r in REGIONS),
        'regions': [{'name': r[0], 'bbox': [r[1], r[2], r[3], r[4]]} for r in REGIONS],
    }
    (DATA / 'hillshade_py_bounds.json').write_text(json.dumps(union_bounds))
    print(f"\n✓ wrote union bounds")