#!/usr/bin/env python3
"""Property risk analysis v3 — FAST.

Strategy:
- Pre-build a 0.05° grid (~5km cells) covering Paraguay.
- For each polygon, compute bbox and assign to all grid cells it overlaps.
- For each property point, only check polygons in the 9 nearest grid cells (3x3).

This reduces 10,754 × 18 depto polygons = 193,572 point-in-ring checks to
just ~10,754 × 1-3 polygons = ~30,000 checks. Should run in <2 min.
"""
import json
import math
import os
import time
from pathlib import Path
from collections import defaultdict

DATA = Path('/root/paraguay-geodata/exports/web/data')

print('Loading...')
t0 = time.time()

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
with open(DATA / 'admin' / 'departamentos.geojson') as f:
    deptos_geo = json.load(f)
print(f'  loaded in {time.time()-t0:.1f}s')


DEPT_NORM = {
    'asuncion': 'Asunción', 'distrito capital': 'Asunción',
    'distrito capital de paraguay': 'Asunción', 'capital': 'Asunción',
    'central': 'Central', 'departamento central': 'Central',
    'concepcion': 'Concepción', 'departamento de concepcion': 'Concepción',
    'san pedro': 'San Pedro', 'departamento de san pedro': 'San Pedro',
    'cordillera': 'Cordillera', 'departamento de la cordillera': 'Cordillera',
    'guaira': 'Guairá', 'departamento de guaira': 'Guairá',
    'caaguazu': 'Caaguazú', 'departamento de caaguazu': 'Caaguazú',
    'caazapa': 'Caazapá', 'departamento de caazapa': 'Caazapá',
    'itapua': 'Itapúa', 'departamento de itapua': 'Itapúa',
    'misiones': 'Misiones', 'departamento de misiones': 'Misiones',
    'paraguari': 'Paraguarí', 'departamento de paraguari': 'Paraguarí',
    'alto parana': 'Alto Paraná', 'departamento del alto parana': 'Alto Paraná',
    'neembucu': 'Ñeembucú', 'departamento de neembucu': 'Ñeembucú',
    'amambay': 'Amambay', 'departamento de amambay': 'Amambay',
    'pdte. hayes': 'Presidente Hayes', 'presidente hayes': 'Presidente Hayes',
    'departamento de presidente hayes': 'Presidente Hayes',
    'boqueron': 'Boquerón', 'departamento de boqueron': 'Boquerón',
    'alto paraguay': 'Alto Paraguay', 'departamento de alto paraguay': 'Alto Paraguay',
    'canindeyu': 'Canindeyú', 'departamento de canindeyu': 'Canindeyú',
    'formosa': None, 'corrientes': None, 'santa cruz': None, 'parana': None,
    'minga guazu': 'Alto Paraná',
    'unknown': None,
}

def normalize_depto(name):
    if not name:
        return None
    return DEPT_NORM.get(name.strip().lower(), name.strip())


# Point in ring - vectorized for speed
def point_in_ring(lon, lat, ring):
    """Standard ray casting, but inlined for speed."""
    if not ring or len(ring) < 3:
        return False
    n = len(ring)
    inside = False
    j = n - 1
    py = ring[j][1]
    px = ring[j][0]
    for i in range(n):
        yi = ring[i][1]
        xi = ring[i][0]
        if ((yi > lat) != (py > lat)) and (lon < (px - xi) * (lat - yi) / (py - yi + 1e-12) + xi):
            inside = not inside
        px, py = xi, yi
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
    lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


def add_to_grid(grid, geom_obj):
    """Add a polygon object to all grid cells its bbox overlaps."""
    if not geom_obj['bbox']:
        return
    b = geom_obj['bbox']
    gx_min = int(b[0] / GRID)
    gx_max = int(b[2] / GRID)
    gy_min = int(b[1] / GRID)
    gy_max = int(b[3] / GRID)
    for gx in range(gx_min, gx_max + 1):
        for gy in range(gy_min, gy_max + 1):
            grid[(gx, gy)].append(geom_obj)


# ============== BUILD GRID INDEXES ==============
GRID = 0.05  # 5km cells

# Admin deptos
admin_deptos = []
for f in deptos_geo['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords:
        admin_deptos.append({
            'name': normalize_depto(f['properties'].get('name', '')) or f['properties'].get('name', ''),
            'coords': coords,
            'bbox': bbox(coords),
        })
admin_grid = defaultdict(list)
for d in admin_deptos:
    add_to_grid(admin_grid, d)
print(f'  admin deptos: {len(admin_deptos)}')

# Climate risk
climate_polys = []
for f in climate_risk['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords:
        climate_polys.append({
            'name': normalize_depto(f['properties'].get('depto', '')),
            'coords': coords,
            'bbox': bbox(coords),
            'props': f['properties'],
        })
climate_by_depto = {}
for cp in climate_polys:
    n = cp['name']
    if not n: continue
    score = cp['props'].get('risk_score', 0) or 0
    if n not in climate_by_depto or score > climate_by_depto[n].get('risk_score', 0):
        climate_by_depto[n] = cp['props']

# Flood zones
flood_zones = []
for f in flood_risk['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords:
        flood_zones.append({
            'name': f['properties'].get('name', '?'),
            'coords': coords,
            'bbox': bbox(coords),
            'props': f['properties'],
        })
flood_grid = defaultdict(list)
for fz in flood_zones:
    add_to_grid(flood_grid, fz)
print(f'  flood zones: {len(flood_zones)}')

# Indigenous
indigenous_zones = []
for f in indigenous['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords:
        indigenous_zones.append({
            'name': f['properties'].get('name', f['properties'].get('people', '?')),
            'coords': coords,
            'bbox': bbox(coords),
            'props': f['properties'],
        })
indig_grid = defaultdict(list)
for iz in indigenous_zones:
    add_to_grid(indig_grid, iz)
print(f'  indigenous: {len(indigenous_zones)}')

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
            wf = {'coords': line, 'name': f['properties'].get('name', ''),
                  'type': f['properties'].get('water_type', 'water'), 'bbox': bbox(line)}
            water_features.append(wf)
water_grid = defaultdict(list)
for wf in water_features:
    if wf['bbox']:
        add_to_grid(water_grid, wf)
print(f'  water lines: {len(water_features)}')

# GBIF (treat as points)
gbif_pts = []
for gf in gbif['features']:
    geom2 = gf.get('geometry')
    if not geom2 or not geom2.get('coordinates'): continue
    lon2, lat2 = geom2['coordinates']
    gbif_pts.append({
        'lon': lon2, 'lat': lat2,
        'species': gf['properties'].get('species', gf['properties'].get('name', '?')),
    })
gbif_grid = defaultdict(list)
for g in gbif_pts:
    gbif_grid[(int(g['lon']/GRID), int(g['lat']/GRID))].append(g)
print(f'  gbif: {len(gbif_pts)}')


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def point_in_geom_set(lon, lat, grid, key):
    """Check if point is inside any polygon in the grid (using bbox pre-filter)."""
    gx, gy = int(lon / GRID), int(lat / GRID)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            for obj in grid.get((gx+dx, gy+dy), []):
                b = obj['bbox']
                if not b: continue
                if b[0] > lon or b[2] < lon or b[1] > lat or b[3] < lat:
                    continue
                if point_in_ring(lon, lat, obj['coords']):
                    return obj
    return None


# ============== ANALYZE ==============
print(f'\nAnalyzing {len(properties["features"]):,} properties...')
t0 = time.time()
results = []

for idx, feat in enumerate(properties['features']):
    p = feat['properties']
    geom = feat.get('geometry')
    if not geom or not geom.get('coordinates'): continue
    lon, lat = geom['coordinates']

    risks = {'flood': None, 'climate': None, 'indigenous': None, 'water_proximity': None, 'shadow': None, 'lighting': None}
    pros = {'near_water': None, 'biodiversity': None}

    # Spatial depto
    d = point_in_geom_set(lon, lat, admin_grid, 'admin')
    spatial_depto = d['name'] if d else None
    norm_depto = normalize_depto(p.get('state_province'))
    final_depto = spatial_depto or norm_depto

    # Flood
    fz = point_in_geom_set(lon, lat, flood_grid, 'flood')
    if fz:
        rl = fz['props'].get('risk', fz['props'].get('level', 'unknown'))
        rl_str = str(rl).lower()
        sev = 'high' if rl_str in ('high', 'very_high', '3', 'alto', 'alta') else 'medium' if rl_str in ('medium', 'moderate', '2', 'medio', 'media') else 'low'
        risks['flood'] = {'zone': fz['name'], 'level': str(rl), 'severity': sev}

    # Climate (lookup by final_depto)
    if final_depto and final_depto in climate_by_depto:
        cp = climate_by_depto[final_depto]
        risk_level = (cp.get('risk_level') or '').lower()
        drought_freq = cp.get('drought_freq') or 0
        forest_loss = cp.get('forest_loss_pct_2020_2024') or 0
        annual_precip = cp.get('annual_precip_mm') or 1500
        spi = cp.get('spi_2024') or 0
        flood_sub = 'medium' if risk_level in ('high', 'very_high') else 'low' if risk_level == 'low' else 'medium'
        drought_sub = 'high' if drought_freq > 0.25 else 'medium' if drought_freq > 0.15 else 'low'
        heatwave_sub = 'high' if annual_precip < 1000 or spi < -1.5 else 'medium' if annual_precip < 1400 else 'low'
        wildfire_sub = 'high' if forest_loss > 5 else 'medium' if forest_loss > 1 else 'low'
        risks['climate'] = {
            'depto': final_depto,
            'flood_risk': flood_sub,
            'drought_risk': drought_sub,
            'heatwave_risk': heatwave_sub,
            'wildfire_risk': wildfire_sub,
            'composite_risk_level': risk_level,
        }

    # Indigenous
    iz = point_in_geom_set(lon, lat, indig_grid, 'indig')
    if iz:
        risks['indigenous'] = {
            'territory': iz['name'],
            'people': iz['props'].get('people'),
            'severity': 'high',
            'note': 'Property is within (or near) an indigenous territory. Land tenure and legal restrictions may apply.',
        }

    # Water proximity
    gx, gy = int(lon/GRID), int(lat/GRID)
    min_water_km = None
    closest_water = None
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            for wf in water_grid.get((gx+dx, gy+dy), []):
                b = wf['bbox']
                if b[0] - 0.05 > lon or b[2] + 0.05 < lon: continue
                if b[1] - 0.05 > lat or b[3] + 0.05 < lat: continue
                # Quick min distance to polyline (sample every Nth point if very long)
                pts = wf['coords']
                if len(pts) > 200:
                    pts = pts[::max(1, len(pts)//100)]  # sample
                for i in range(len(pts)-1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i+1]
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
            for g in gbif_grid.get((gx+dx, gy+dy), []):
                d2 = haversine_km(lon, lat, g['lon'], g['lat'])
                if min_gbif_km is None or d2 < min_gbif_km:
                    min_gbif_km = d2
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
        sev = risks['flood']['severity']
        # V3: downgrade broad zones
        is_broad = risks['flood']['zone'] in ('Río Paraguay floodplain', 'Gran Chaco lowlands')
        sev_w = 'low' if is_broad else sev
        score += 30 * (3 if sev_w == 'high' else 1.5 if sev_w == 'medium' else 0.5)
    if risks['climate']:
        c = risks['climate']
        for k, w in [('flood_risk', 15), ('drought_risk', 8), ('heatwave_risk', 5), ('wildfire_risk', 10)]:
            v = c.get(k)
            if v and v != 'note':
                if str(v).lower() in ('high', '3', 'alto', 'alta'): score += w * 2
                elif str(v).lower() in ('medium', 'moderate', '2', 'medio', 'media'): score += w
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
        'state_province': final_depto,
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

    if (idx + 1) % 2000 == 0:
        print(f'  {idx+1:,} done ({time.time()-t0:.0f}s)')

elapsed = time.time() - t0
print(f'\nDone in {elapsed:.0f}s')
print(f'Total: {len(results):,}')

# ============== STATS ==============
from collections import Counter
print('\n=== After normalization (top 15) ===')
dept_counts = Counter(r['state_province'] for r in results)
for d, n in sorted(dept_counts.items(), key=lambda x: -x[1])[:15]:
    print(f'   {d}: {n}')

# ============== SAVE ==============
output_full = {
    'generated_at': '2026-07-13T18:30:00Z',
    'method': 'v3 — grid-indexed spatial join + depto normalization + broad-zone flood downgrade',
    'search_radii': {
        'water_flood': '300 m (risk) / 5 km (pro)',
        'biodiversity': '10 km',
        'indigenous': 'point-in-polygon (exact)',
        'flood_zone': 'point-in-polygon (exact); broad zones downgraded',
        'climate': 'lookup by spatial depto',
    },
    'stats': {'total_properties': len(results)},
    'analyses': results,
}

print('\nSaving full analysis...')
out_full = DATA / 'property_risk_analysis.json'
with open(out_full, 'w') as f:
    json.dump(output_full, f, separators=(',', ':'))
print(f'  full: {os.path.getsize(out_full)/1024/1024:.2f} MB')

# Lightweight index
index = {}
for r in results:
    index[r['id']] = {
        'lat': r['lat'], 'lon': r['lon'],
        'risk_score': r['risk_score'], 'pro_score': r['pro_score'],
        'net_score': r['net_score'],
        'depto': r['state_province'],
        'risks_summary': {k: v is not None for k, v in r['risks'].items()},
        'pros_summary': {k: v is not None for k, v in r['pros'].items()},
    }

output_index = {
    'generated_at': '2026-07-13T18:30:00Z',
    'method': 'lightweight index for heatmap rendering',
    'stats': {'total': len(index)},
    'index': index,
}
out_idx = DATA / 'property_risk_index.json'
with open(out_idx, 'w') as f:
    json.dump(output_index, f, separators=(',', ':'))
print(f'  index: {os.path.getsize(out_idx)/1024/1024:.2f} MB')

# Summary
from collections import defaultdict
depto_stats = defaultdict(lambda: {'count': 0, 'avg_risk': 0, 'avg_pro': 0, 'high_risk': 0, 'flood': 0, 'indig': 0, 'water_close': 0, 'biodiv': 0})
for r in results:
    d = r.get('state_province') or 'Unknown'
    s = depto_stats[d]
    s['count'] += 1
    s['avg_risk'] += r.get('risk_score', 0)
    s['avg_pro'] += r.get('pro_score', 0)
    if r.get('risk_score', 0) > 50: s['high_risk'] += 1
    if r.get('risks', {}).get('flood'): s['flood'] += 1
    if r.get('risks', {}).get('indigenous'): s['indig'] += 1
    if r.get('risks', {}).get('water_proximity'): s['water_close'] += 1
    if r.get('pros', {}).get('biodiversity'): s['biodiv'] += 1

output_summary = {
    'generated_at': '2026-07-13T18:30:00Z',
    'method': 'aggregate of v3 risk analysis',
    'by_depto': {d: {**s, 'avg_risk': round(s['avg_risk']/max(1,s['count']),2), 'avg_pro': round(s['avg_pro']/max(1,s['count']),2)} for d, s in depto_stats.items()},
    'top_risky': sorted(results, key=lambda r: -r.get('risk_score', 0))[:30],
    'top_pro': sorted(results, key=lambda r: -r.get('pro_score', 0))[:30],
    'stats': {
        'total': len(results),
        'with_flood_risk': sum(1 for r in results if r.get('risks', {}).get('flood')),
        'with_indigenous': sum(1 for r in results if r.get('risks', {}).get('indigenous')),
        'with_water_close': sum(1 for r in results if r.get('risks', {}).get('water_proximity')),
        'with_biodiversity': sum(1 for r in results if r.get('pros', {}).get('biodiversity')),
        'with_near_water': sum(1 for r in results if r.get('pros', {}).get('near_water')),
    }
}

out_sum = DATA / 'property_risk_summary.json'
with open(out_sum, 'w') as f:
    json.dump(output_summary, f, separators=(',', ':'))
print(f'  summary: {os.path.getsize(out_sum)/1024:.1f} KB')

print('\n=== Final stats ===')
print(f"{'Depto':<22} {'#':>6} {'avg_risk':>10} {'avg_pro':>10}")
for d, s in sorted(depto_stats.items(), key=lambda x: -x[1]['count'])[:15]:
    if d and d not in ('Unknown', None):
        print(f"{d[:22]:<22} {s['count']:>6} {s['avg_risk']/s['count']:>10.1f} {s['avg_pro']/s['count']:>10.1f}")