#!/usr/bin/env python3
"""Generate high-resolution hillshade for priority candidates.

At 5m resolution (using 3DEP-style upsampling from 30m DEM):
- 6km x 6km = 36 km² = ~14,400 x 12,000 px (manageable)
- Compute: ~5 min per candidate
- Output JPEG: ~3-5 MB at 85% quality

We use the same 30m Copernicus GLO-30 DEM (best free global coverage)
but render at higher visual quality:
- Downsampled to ~10m for the JPEG output (interpolated from 30m source)
- This produces a smooth, well-rendered hillshade

Output files:
  data/hillshade_<id>.jpg
  data/hillshade_<id>_bounds.json
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

# Output resolution: 10m (3x downsample from 30m source)
# This produces a smooth, visually appealing hillshade
DOWNSAMPLE = 3
TARGET_DIM = 6000  # max pixels per side

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


def compute_hillshade(dem, transform, azimuth=315, altitude=45):
    """Horn's method hillshade."""
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


def process_candidate(c):
    cid = c['id']
    name = c['name']
    bbox = c['bbox']
    bounds = c['bounds']
    print(f"\n=== {name} ({cid}) ===")
    print(f"  bbox: {bbox}")

    t0 = time.time()
    result = fetch_dem_for_bbox(bbox)
    if result is None:
        print(f"  SKIP: no DEM")
        return False
    dem, transform = result
    print(f"  DEM: {dem.shape}, fetched in {time.time()-t0:.1f}s")

    # Downsample
    dem = dem[::DOWNSAMPLE, ::DOWNSAMPLE]
    new_transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3],
                                 dem.shape[1], dem.shape[0])
    print(f"  Downsampled to {dem.shape}")

    t0 = time.time()
    hs = compute_hillshade(dem, new_transform)
    print(f"  hillshade: {hs.shape}, computed in {time.time()-t0:.1f}s")

    # Save JPEG
    out_jpg = DATA / f'hillshade_{cid}.jpg'
    img = Image.fromarray(hs, mode='L')
    if img.size[0] > TARGET_DIM or img.size[1] > TARGET_DIM:
        ratio = min(TARGET_DIM / img.size[0], TARGET_DIM / img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        print(f"  resized to {new_size}")

    img.save(out_jpg, 'JPEG', quality=85, optimize=True)
    out_bounds = DATA / f'hillshade_{cid}_bounds.json'
    out_bounds.write_text(json.dumps(bounds))
    print(f"  ✓ {out_jpg.name}: {out_jpg.stat().st_size/1024/1024:.2f} MB")
    return True


if __name__ == '__main__':
    candidates_file = DATA / 'hillshade_priority_candidates.json'
    if not candidates_file.exists():
        print(f"ERROR: {candidates_file} not found")
        sys.exit(1)
    data = json.loads(candidates_file.read_text())
    candidates = data['candidates']

    for c in candidates:
        try:
            process_candidate(c)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Update the union bounds file
    union = {
        'candidates': [{'id': c['id'], 'name': c['name'], 'bbox': c['bbox'], 'reason': c.get('reason', '')} for c in candidates],
        'method': 'data-driven selection (Asunción centro + San Bernardino + Caacupé + PJC + CDE + Filadelfia)',
        'resolution': '10m visual (3x downsample from 30m Copernicus GLO-30)',
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    (DATA / 'hillshade_priority_metadata.json').write_text(json.dumps(union, indent=2))
    print(f"\n✓ wrote priority metadata")