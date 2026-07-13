#!/usr/bin/env python3
"""Faster risk analysis — for testing the pipeline.
Skips expensive shadow analysis and reduces water search to bbox-only.
"""
import json
import math
import os
import time
from pathlib import Path
from collections import defaultdict

DATA = Path('/root/paraguay-geodata/exports/web/data')

print('Loading...')
with open(DATA / 'properties_latest.geojson') as f:
    properties = json.load(f)
with open(DATA / 'water.geojson') as f:
    water = json.load(f)
with open(DATA / 'climate_risk.geojson') as f:
    climate_risk = json.load(f)
with open(DATA / 'flood_risk.geojson') as f:
    flood_risk = json.load(f)
with open(DATA / 'gbif_paraguay.geojson') as f:
    gbif = json.load(f)
with open(DATA / 'indigenous_territories.geojson') as f:
    indigenous = json.load(f)


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def point_in_ring(lon, lat, ring):
    if not ring or len(ring) < 3: return False
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj-xi) * (lat-yi) / (yj-yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def get_outer_ring(geom):
    if not geom or not geom.get('coordinates'): return None
    if geom['type'] == 'Polygon': return geom['coordinates'][0]
    if geom['type'] == 'MultiPolygon':
        biggest = max(geom['coordinates'], key=lambda p: len(p[0]) if p and p[0] else 0)
        return biggest[0] if biggest else None
    return None


def bbox(coords):
    if not coords: return None
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


# Index
deptos = []
for f in climate_risk['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords: deptos.append({'name': f['properties'].get('name', '?'), 'coords': coords, 'bbox': bbox(coords), 'props': f['properties']})

flood_zones = []
for f in flood_risk['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords: flood_zones.append({'name': f['properties'].get('name', '?'), 'coords': coords, 'bbox': bbox(coords), 'props': f['properties']})

indigenous_zones = []
for f in indigenous['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords: indigenous_zones.append({'name': f['properties'].get('name', '?'), 'coords': coords, 'bbox': bbox(coords), 'props': f['properties']})

# Water polylines
water_features = []
for f in water['features']:
    geom = f.get('geometry')
    if not geom or not geom.get('coordinates'): continue
    lines = []
    if geom['type'] == 'LineString': lines = [geom['coordinates']]
    elif geom['type'] == 'MultiLineString': lines = geom['coordinates']
    elif geom['type'] == 'Polygon': lines = [geom['coordinates'][0]]
    elif geom['type'] == 'MultiPolygon': lines = [p[0] for p in geom['coordinates']]
    for line in lines:
        if line and len(line) >= 2:
            water_features.append({'coords': line, 'name': f['properties'].get('name', ''), 'type': f['properties'].get('water_type', 'water'), 'bbox': bbox(line)})

# Water grid index
GRID_DEG = 0.05
water_by_cell = defaultdict(list)
for wf in water_features:
    if not wf['bbox']: continue
    margin = 0.05
    gx_min, gx_max = int((wf['bbox'][0]-margin)/GRID_DEG), int((wf['bbox'][2]+margin)/GRID_DEG)
    gy_min, gy_max = int((wf['bbox'][1]-margin)/GRID_DEG), int((wf['bbox'][3]+margin)/GRID_DEG)
    for gx in range(gx_min, gx_max+1):
        for gy in range(gy_min, gy_max+1):
            water_by_cell[(gx, gy)].append(wf)

# GBIF grid
gbif_by_cell = defaultdict(list)
for gf in gbif['features']:
    geom2 = gf.get('geometry')
    if not geom2 or not geom2.get('coordinates'): continue
    lon2, lat2 = geom2['coordinates']
    gx, gy = int(lon2/GRID_DEG), int(lat2/GRID_DEG)
    gbif_by_cell[(gx, gy)].append({'lon': lon2, 'lat': lat2, 'species': gf['properties'].get('species', gf['properties'].get('name', '?'))})


# Analyze
print(f'Analyzing {len(properties["features"]):,} properties...')
t0 = time.time()
results = []

for idx, feat in enumerate(properties['features']):
    p = feat['properties']
    geom = feat.get('geometry')
    if not geom or not geom.get('coordinates'): continue
    lon, lat = geom['coordinates']

    risks = {'flood': None, 'climate': None, 'indigenous': None, 'water_proximity': None, 'shadow': None, 'lighting': None}
    pros = {'near_water': None, 'biodiversity': None}

    # Flood
    for fz in flood_zones:
        if fz['bbox'] and fz['bbox'][0] <= lon <= fz['bbox'][2] and fz['bbox'][1] <= lat <= fz['bbox'][3]:
            if point_in_ring(lon, lat, fz['coords']):
                rl = fz['props'].get('risk', fz['props'].get('level', 'unknown'))
                rl_str = str(rl).lower()
                sev = 'high' if rl_str in ('high', '3', 'alto', 'alta') else 'medium' if rl_str in ('medium', '2', 'medio', 'media') else 'low'
                risks['flood'] = {'zone': fz['name'], 'level': str(rl), 'severity': sev}
                break

    # Climate
    for d in deptos:
        if d['bbox'] and d['bbox'][0] <= lon <= d['bbox'][2] and d['bbox'][1] <= lat <= d['bbox'][3]:
            if point_in_ring(lon, lat, d['coords']):
                p2 = d['props']
                risks['climate'] = {
                    'depto': d['name'],
                    'flood_risk': p2.get('flood_risk'),
                    'drought_risk': p2.get('drought_risk'),
                    'heatwave_risk': p2.get('heatwave_risk'),
                    'wildfire_risk': p2.get('wildfire_risk'),
                }
                break

    # Indigenous
    for iz in indigenous_zones:
        if iz['bbox'] and iz['bbox'][0] <= lon <= iz['bbox'][2] and iz['bbox'][1] <= lat <= iz['bbox'][3]:
            if point_in_ring(lon, lat, iz['coords']):
                risks['indigenous'] = {
                    'territory': iz['name'],
                    'people': iz['props'].get('people'),
                    'severity': 'high',
                    'note': 'Property is within (or near) an indigenous territory. Land tenure and legal restrictions may apply.',
                }
                break

    # Water proximity
    gx, gy = int(lon/GRID_DEG), int(lat/GRID_DEG)
    min_water_km = None
    closest_water = None
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            for wf in water_by_cell.get((gx+dx, gy+dy), []):
                if not wf['bbox']: continue
                if wf['bbox'][0] - 0.05 > lon or wf['bbox'][2] + 0.05 < lon: continue
                if wf['bbox'][1] - 0.05 > lat or wf['bbox'][3] + 0.05 < lat: continue
                for i in range(len(wf['coords'])-1):
                    x1, y1 = wf['coords'][i]
                    x2, y2 = wf['coords'][i+1]
                    dx_, dy_ = x2-x1, y2-y1
                    if dx_ == 0 and dy_ == 0:
                        dlat = lat-y1; dlon = lon-x1
                    else:
                        t = ((lon-x1)*dx_ + (lat-y1)*dy_) / (dx_*dx_ + dy_*dy_)
                        t = max(0, min(1, t))
                        px = x1 + t*dx_; py = y1 + t*dy_
                        dlat = lat-py; dlon = lon-px
                    dist_km = math.sqrt((dlat*111)**2 + (dlon*111*math.cos(lat*math.pi/180))**2)
                    if min_water_km is None or dist_km < min_water_km:
                        min_water_km = dist_km
                        closest_water = wf

    if min_water_km is not None and min_water_km <= 5.0:
        if min_water_km < 0.3:
            risks['water_proximity'] = {
                'distance_km': round(min_water_km, 3),
                'name': closest_water['name'] or 'unnamed water body',
                'type': closest_water['type'],
                'severity': 'high' if min_water_km < 0.1 else 'medium',
                'note': f'Property is only {int(min_water_km*1000)}m from a water body.',
            }
        else:
            pros['near_water'] = {
                'distance_km': round(min_water_km, 2),
                'name': closest_water['name'] or 'unnamed water body',
                'type': closest_water['type'],
                'note': f'Within {min_water_km:.1f} km of a water body.',
            }

    # Biodiversity
    min_gbif_km = None
    closest_species = None
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for g in gbif_by_cell.get((gx+dx, gy+dy), []):
                d = haversine_km(lon, lat, g['lon'], g['lat'])
                if min_gbif_km is None or d < min_gbif_km:
                    min_gbif_km = d
                    closest_species = g['species']
    if min_gbif_km is not None and min_gbif_km < 10:
        pros['biodiversity'] = {
            'distance_km': round(min_gbif_km, 1),
            'nearest_species': closest_species,
            'note': f'GBIF observation within {min_gbif_km:.1f} km.',
        }

    # Score
    score = 0
    if risks['flood']:
        score += 30 * (3 if risks['flood']['severity'] == 'high' else 1.5 if risks['flood']['severity'] == 'medium' else 0.5)
    if risks['climate']:
        c = risks['climate']
        for k, w in [('flood_risk', 15), ('drought_risk', 8), ('heatwave_risk', 5), ('wildfire_risk', 10)]:
            v = c.get(k)
            if v is not None:
                if str(v).lower() in ('high', '3', 'alto', 'alta'): score += w * 2
                elif str(v).lower() in ('medium', '2', 'medio', 'media'): score += w
                else: score += w * 0.3
    if risks['indigenous']: score += 50
    if risks['water_proximity']:
        score += 25 * (2 if risks['water_proximity']['severity'] == 'high' else 1)

    pro_score = 0
    if pros['near_water']:
        if pros['near_water']['distance_km'] < 1: pro_score += 20
        elif pros['near_water']['distance_km'] < 2: pro_score += 10
    if pros['biodiversity']:
        if pros['biodiversity']['distance_km'] < 2: pro_score += 15
        elif pros['biodiversity']['distance_km'] < 5: pro_score += 8

    results.append({
        'id': p.get('id', f'prop-{idx}'),
        'source': p.get('source'),
        'lat': lat, 'lon': lon,
        'title': p.get('title'),
        'state_province': p.get('state_province'),
        'city': p.get('city'),
        'property_type': p.get('property_type'),
        'listing_type': p.get('listing_type'),
        'price_usd': p.get('price_usd'),
        'area_ha': p.get('area_ha'),
        'bedrooms': p.get('bedrooms'),
        'source_url': p.get('source_url'),
        'risks': risks, 'pros': pros,
        'risk_score': round(score, 1),
        'pro_score': round(pro_score, 1),
        'net_score': round(pro_score - score, 1),
    })

    if (idx + 1) % 1000 == 0:
        print(f'  {idx+1:,} done ({time.time()-t0:.0f}s)')

elapsed = time.time() - t0
print(f'\nDone in {elapsed:.0f}s')
print(f'Total: {len(results):,}')

# Save
output = {
    'generated_at': '2026-07-13T17:00:00Z',
    'method': 'spatial-join: point-in-polygon + closest-feature for proximity',
    'search_radii': {
        'water_flood': '300 m (risk) / 5 km (pro)',
        'biodiversity': '10 km',
        'indigenous': 'point-in-polygon (exact)',
        'flood_zone': 'point-in-polygon (exact)',
        'climate': 'point-in-polygon (depto)',
    },
    'stats': {
        'total_properties': len(results),
    },
    'analyses': results,
}

out_path = DATA / 'property_risk_analysis.json'
print(f'\nSaving to {out_path}...')
with open(out_path, 'w') as f:
    json.dump(output, f, separators=(',', ':'))
print(f'  Size: {os.path.getsize(out_path)/1024/1024:.2f} MB')