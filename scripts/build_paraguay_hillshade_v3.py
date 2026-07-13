#!/usr/bin/env python3
"""Build Paraguay-wide hillshade v3 — OPTIMIZED.

Strategy:
- Fetch 30m DEM tiles from Planetary Computer
- Merge into a single array
- DOWNSAMPLE to 60m (every 2x2 average) before hillshade compute
- This makes hillshade ~4x faster AND smaller output
- 60m hillshade is still useful for visual context at national zoom

Output: 4 regions × ~4 MB JPEG = ~16 MB total
Compute time: ~2-3 min per region (down from 6+ min)
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


def compute_hillshade_chunked(dem, transform, azimuth=315, altitude=45, chunk_rows=2000):
    """Horn's method hillshade, computed in chunks to manage memory."""
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

    h, w = dem.shape
    out = np.zeros((h, w), dtype=np.uint8)

    # Pad DEM with 1 row on top and bottom for gradient computation
    dem_padded = np.pad(dem, ((1, 1), (0, 0)), mode='edge')

    for i in range(0, h, chunk_rows):
        end = min(i + chunk_rows, h)
        # chunk_rows are in the original DEM space; padded indices are +1
        chunk = dem_padded[i+1:end+1]  # rows i+1 to end+1 in padded
        # Need also the row above (i) and below (end+1) for gradient
        top_row = dem_padded[i:i+1]      # row above this chunk
        bot_row = dem_padded[end+1:end+2] if end < h else dem_padded[end+1:end+2]
        # Build chunk with top + data + bottom
        chunk = np.vstack([top_row, chunk, bot_row])

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
        # Update transform to reflect downsampling
        from rasterio.transform import from_bounds
        new_transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3],
                                     dem.shape[1], dem.shape[0])
        transform = new_transform
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

    img.save(out_jpg, 'JPEG', quality=80, optimize=True)
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