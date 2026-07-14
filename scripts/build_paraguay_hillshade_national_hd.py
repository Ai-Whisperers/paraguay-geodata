#!/usr/bin/env python3
"""Generate high-resolution Paraguay-wide hillshade using 1°×1° tiles.

Strategy:
- Tile size: 1° × 1° (8° × 9° Paraguay = 81 tiles)
- DEM: Copernicus GLO-30 (30m native)
- Output: 3600×3600 px JPEG per tile (~2-3 MB)
- Total: ~200 MB but lazy-loaded on zoom

Use 4-direction combined hillshade for more natural appearance:
- 315° (NW), 45° (NE), 135° (SE), 225° (SW)
- Average them weighted (60% NW + 40% others)
"""
import json
import math
import time
from pathlib import Path
import numpy as np
from PIL import Image
import rasterio
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.transform import from_bounds as transform_from_bounds
import planetary_computer
import pystac_client

ROOT = Path('/root/paraguay-geodata')
DATA = ROOT / 'exports' / 'web' / 'data'

# Paraguay bounding box (precise)
BBOX_PY = {
    'min_lon': -62.5,
    'max_lon': -54.3,
    'min_lat': -27.6,
    'max_lat': -19.3,
}

# 1° × 1° tiles covering Paraguay
TILES = []
lat = BBOX_PY['min_lat']
while lat < BBOX_PY['max_lat']:
    lon = BBOX_PY['min_lon']
    while lon < BBOX_PY['max_lon']:
        TILES.append({
            'id': f'py_t{int((BBOX_PY["max_lat"] - (lat + 1.0)) * 10):02d}_l{int((lon - BBOX_PY["min_lon"]) * 10):02d}',
            'bbox': [lon, lat, lon + 1.0, lat + 1.0],
        })
        lon += 1.0
    lat += 1.0

print(f"Total tiles to generate: {len(TILES)}")

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)


def fetch_dem_crop(bbox):
    """Fetch DEM and crop to bbox."""
    search = catalog.search(collections=["cop-dem-glo-30"], bbox=bbox)
    items = list(search.item_collection())
    if not items:
        return None, None
    datasets = []
    for item in items:
        asset = planetary_computer.sign(item.assets['data'])
        try:
            ds = rasterio.open(asset.href)
            datasets.append(ds)
        except Exception:
            pass
    if not datasets:
        return None, None

    if len(datasets) == 1:
        ds = datasets[0]
        window = window_from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], ds.transform)
        window = window.round_offsets().round_lengths()
        dem = ds.read(1, window=window)
        transform = transform_from_bounds(bbox[0], bbox[1], bbox[2], bbox[3],
                                           dem.shape[1], dem.shape[0])
        ds.close()
        return dem, transform
    else:
        from rasterio.merge import merge
        merged, transform = merge(datasets)
        for ds in datasets:
            ds.close()
        dem = merged[0]
        window = window_from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], transform)
        window = window.round_offsets().round_lengths()
        r1, r2 = max(0, window.row_off), min(dem.shape[0], window.row_off + int(window.height))
        c1, c2 = max(0, window.col_off), min(dem.shape[1], window.col_off + int(window.width))
        dem = dem[r1:r2, c1:c2]
        transform = transform_from_bounds(bbox[0], bbox[1], bbox[2], bbox[3],
                                           dem.shape[1], dem.shape[0])
        return dem, transform


def compute_hillshade(dem, transform, azimuth=315, altitude=45):
    """Horn's method hillshade."""
    az_rad = math.radians(360 - azimuth + 90)
    alt_rad = math.radians(altitude)
    dx = abs(transform.a)
    dy = abs(transform.e)
    lat_center = (dem.shape[0] * dy / 2 + transform.f)
    m_per_deg_lon = 111320 * math.cos(math.radians(-lat_center))
    cellsize_x = dx * m_per_deg_lon
    cellsize_y = abs(dy) * 111320
    dem = dem.astype(np.float32)
    dem = np.nan_to_num(dem, nan=100)
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
    return np.clip(shaded, 0, 1)


def compute_multi_dir_hillshade(dem, transform):
    """Multi-directional hillshade: blend 4 azimuths for natural look.

    Weight NW (315°) most, as it's the standard "natural light from upper-left" feel.
    """
    # 60% NW, 20% NE, 10% SE, 10% SW
    weights = {315: 0.6, 45: 0.2, 135: 0.1, 225: 0.1}
    altitudes = {315: 45, 45: 45, 135: 35, 225: 35}

    combined = None
    total_weight = sum(weights.values())
    for az, weight in weights.items():
        hs = compute_hillshade(dem, transform, azimuth=az, altitude=altitudes[az])
        if combined is None:
            combined = hs * weight
        else:
            combined += hs * weight
    combined /= total_weight
    return (combined * 255).astype(np.uint8)


def process_tile(tile, force=False):
    tid = tile['id']
    bbox = tile['bbox']
    out_jpg = DATA / f"hillshade_{tid}.jpg"
    out_bounds = DATA / f"hillshade_{tid}_bounds.json"

    if out_jpg.exists() and out_bounds.exists() and not force:
        if out_jpg.stat().st_size > 1000:
            return 'skipped'

    t0 = time.time()
    dem, transform = fetch_dem_crop(bbox)
    if dem is None:
        print(f"  ✗ {tid}: no DEM data")
        return 'no_data'

    # Compute multi-directional hillshade
    hs = compute_multi_dir_hillshade(dem, transform)

    # Apply 80px edge fade (consistent with city tiles)
    h, w = hs.shape
    fade = min(80, w // 8, h // 8)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(yy, h - 1 - yy), np.minimum(xx, w - 1 - xx))
    mask = np.clip(d / fade, 0, 1).astype(np.float32)
    hs_faded = (hs * mask).astype(np.uint8)

    img = Image.fromarray(hs_faded, mode='L')
    img.save(out_jpg, 'JPEG', quality=85, optimize=True)

    # Save bounds
    out_bounds.write_text(json.dumps({
        'min_lon': bbox[0],
        'min_lat': bbox[1],
        'max_lon': bbox[2],
        'max_lat': bbox[3],
    }))

    elapsed = time.time() - t0
    print(f"  ✓ {tid}: {hs.shape} -> {out_jpg.stat().st_size/1024:.0f}KB ({elapsed:.1f}s)")
    return 'done'


if __name__ == '__main__':
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None

    # If a filter is provided, only process matching tiles
    if only:
        TILES = [t for t in TILES if only in t['id']]
        if not TILES:
            print(f"No tiles match filter '{only}'")
            print("Available IDs: ", end='')
            from importlib import reload
            sys.exit(1)
    print(f"Processing {len(TILES)} tile(s)")
    print(f"Bbox: {BBOX_PY}")

    success = 0
    skipped = 0
    failed = 0
    for tile in TILES:
        try:
            result = process_tile(tile)
            if result == 'done':
                success += 1
            elif result == 'skipped':
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {tile['id']}: ERROR {e}")
            failed += 1

    print(f"\nDone: {success} generated, {skipped} skipped, {failed} failed")

    # Save tile index
    tile_index = {
        'version': 2,
        'method': 'multi-directional hillshade (315/45/135/225 at 60/20/10/10%) from Copernicus GLO-30 DEM',
        'tile_size_deg': 1.0,
        'bounds': BBOX_PY,
        'tiles': TILES,
    }
    (DATA / 'hillshade_national_tiles.json').write_text(json.dumps(tile_index, indent=2))
    print(f"Tile index saved")