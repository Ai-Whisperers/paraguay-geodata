#!/usr/bin/env python3
"""Build Paraguay-wide hillshade from Copernicus GLO-30 DEM.

Approach: tile-by-tile fetch from Planetary Computer, compute hillshade
in memory, write a single large JPEG for the entire country.

For 30m resolution, Paraguay is ~700 km x 800 km = ~620,000 px.
That's too large for a single image. Strategy:
- Generate 7 regional hillshades (one per INBIO region / major deptos cluster)
- Each region: ~3,000-5,000 px square
- Total size: ~5-10 MB JPEGs
- Loaded as imageOverlays with z-index based on zoom

Output:
  exports/web/data/hillshade_py_central.jpg
  exports/web/data/hillshade_py_east.jpg
  exports/web/data/hillshade_py_west.jpg
  exports/web/data/hillshade_py_south.jpg
  exports/web/data/hillshade_py_north.jpg
  ... + bounds JSONs

Alternative cheaper approach: just generate for the 7,912 priority tiles
(each already has a bbox). One hillshade per tile = 7,912 JPEGs.
That's actually more practical: user zooms in, the tile-level hillshade
loads.
"""
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import xy
import planetary_computer
import pystac_client

# Paraguay bbox
PY_BBOX = [-62.5210, -27.4498, -54.3035, -19.3111]  # [min_lon, min_lat, max_lon, max_lat]

# Setup STAC client
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)


def fetch_dem_for_bbox(bbox, max_retries=3):
    """Fetch + merge Copernicus GLO-30 DEM tiles for a bbox.

    Returns: (height_array, transform, crs)
    """
    search = catalog.search(
        collections=["cop-dem-glo-30"],
        bbox=bbox,
    )
    items = list(search.item_collection())
    print(f"  Found {len(items)} DEM tiles for bbox {bbox}")

    if not items:
        return None

    # Fetch first item (simplest case)
    # For multi-tile merge, we'd use rioxarray.merge
    # For now: just use the first item that covers most of bbox
    # Copernicus GLO-30 tiles are 1° x 1° each

    # Stack tiles: use rasterio.merge
    from rasterio.io import MemoryFile
    from rasterio.merge import merge

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
        crs = ds.crs
        ds.close()
        return data, transform, crs

    # Multi-tile merge
    merged, transform = merge(datasets)
    for ds in datasets:
        ds.close()
    return merged[0], transform, datasets[0].crs


def compute_hillshade(dem, transform, azimuth=315, altitude=45):
    """Compute hillshade array from DEM using Horn's method.

    Args:
        dem: 2D numpy array of elevations
        transform: rasterio transform for cell size
        azimuth: sun azimuth (315 = NW)
        altitude: sun altitude in degrees (45 = mid)
    """
    az_rad = math.radians(360 - azimuth + 90)
    alt_rad = math.radians(altitude)

    # Cell sizes (in degrees)
    dx = transform.a  # pixel width in degrees
    dy = transform.e  # pixel height (negative, e.g. -0.0003)

    # Convert to meters for slope/aspect (rough at Paraguay's lat)
    # Paraguay is ~23°S, so 1° lon ≈ 102 km, 1° lat ≈ 111 km
    lat_center = (dem.shape[0] * dy / 2 + transform.f)  # approximate
    m_per_deg_lon = 111320 * math.cos(math.radians(-lat_center))
    m_per_deg_lat = 111320

    cellsize_x = abs(dx) * m_per_deg_lon
    cellsize_y = abs(dy) * m_per_deg_lat

    # Compute gradients with Horn's method
    # dz/dx = ((c+2f+i) - (a+2d+g)) / (8 * cellsize)
    # dz/dy = ((g+2h+i) - (a+2b+c)) / (8 * cellsize)
    dem = dem.astype(np.float32)
    # Pad with zeros
    padded = np.pad(dem, 1, mode='edge')
    a = padded[:-2, :-2]
    b = padded[:-2, 1:-1]
    c = padded[:-2, 2:]
    d = padded[1:-1, :-2]
    f = padded[1:-1, 2:]
    g = padded[2:, :-2]
    h = padded[2:, 1:-1]
    i = padded[2:, 2:]

    dz_dx = ((c + 2*f + i) - (a + 2*d + g)) / (8 * cellsize_x)
    dz_dy = ((g + 2*h + i) - (a + 2*b + c)) / (8 * cellsize_y)

    # Slope and aspect
    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect = np.arctan2(dz_dy, -dz_dx)
    aspect = np.where(aspect < 0, 2 * math.pi + aspect, aspect)

    # Hillshade
    shaded = np.sin(alt_rad) * np.cos(slope) + np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect)
    shaded = np.clip(shaded, 0, 1)
    shaded = (shaded * 255).astype(np.uint8)
    return shaded


def test_one_region():
    """Test pipeline with one region before scaling to all."""
    # Pick a 1° x 1° tile near Asunción for fast test
    bbox = [-57.5, -25.5, -56.5, -24.5]  # ~1° x 1° around Asunción

    print(f"Fetching DEM for {bbox}...")
    t0 = time.time()
    result = fetch_dem_for_bbox(bbox)
    if result is None:
        print("ERROR: no DEM tiles found")
        return
    dem, transform, crs = result
    print(f"  DEM shape: {dem.shape}, transform: {transform}")
    print(f"  loaded in {time.time()-t0:.1f}s")

    print("Computing hillshade...")
    t0 = time.time()
    hs = compute_hillshade(dem, transform)
    print(f"  hillshade shape: {hs.shape}")
    print(f"  computed in {time.time()-t0:.1f}s")

    # Save as JPEG
    print("Saving JPEG...")
    out = Path('/tmp/test_hillshade.jpg')
    img = Image.fromarray(hs, mode='L')
    img.save(out, 'JPEG', quality=85, optimize=True)
    print(f"  saved {out} ({out.stat().st_size/1024:.1f} KB)")

    # Save bounds
    bounds = {
        'min_lon': bbox[0], 'min_lat': bbox[1],
        'max_lon': bbox[2], 'max_lat': bbox[3],
    }
    Path('/tmp/test_hillshade_bounds.json').write_text(json.dumps(bounds))
    print(f"  saved bounds {bounds}")


if __name__ == '__main__':
    test_one_region()