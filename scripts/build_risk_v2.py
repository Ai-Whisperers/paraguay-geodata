#!/usr/bin/env python3
"""Property risk analysis v2 — fixed.

Fixes over v1:
1. climate_risk.geojson uses 'risk_level' (single composite), 'drought_freq' (numeric)
   — derive flood/heat/fire sub-risks from risk_level + depto-specific factors
2. Depto name normalization: Asunción ↔ Asuncion, Itapúa ↔ Itapua, etc.
3. Flood risk: keep as-is (Asunción costanera is real)
4. Reduce file size: index by id, drop redundant fields
"""
import json
import math
import os
import re
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


# ============== NORMALIZATION ==============
DEPT_NORM = {
    # variations found in properties
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
    # Brazilian/Argentine provinces (data contamination)
    'formosa': None, 'corrientes': None, 'santa cruz': None, 'parana': None,
    'minga guazu': 'Alto Paraná',  # Minga Guazú is a city in Alto Paraná
    'unknown': None,
}

def normalize_depto(name):
    if not name:
        return None
    k = name.strip().lower()
    return DEPT_NORM.get(k, name.strip())


# ============== GEOMETRY HELPERS ==============
def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def point_in_ring(lon, lat, ring):
    if not ring or len(ring) < 3: return False
    n = len(ring); inside = False; j = n - 1
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
    lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


# ============== INDEX ==============
# Use OSM admin/departamentos.geojson for canonical depto polygons
# (more reliable than climate_risk.geojson which has name-only)

deptos_admin = []
for f in deptos_geo['features']:
    coords = get_outer_ring(f.get('geometry'))
    if coords:
        deptos_admin.append({
            'name': normalize_depto(f['properties'].get('name', '')) or f['properties'].get('name', ''),
            'coords': coords,
            'bbox': bbox(coords),
        })
print(f'  admin deptos: {len(deptos_admin)}')

# Climate risk polygons (for risk_level only)
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
print(f'  climate polys: {len(climate_polys)}')

# Map: normalized depto name -> climate risk properties
# But climate_polys may have multiple polys per depto; pick highest risk
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
            water_features.append({
                'coords': line, 'name': f['properties'].get('name', ''),
                'type': f['properties'].get('water_type', 'water'),
                'bbox': bbox(line),
            })
print(f'  water: {len(water_features)}')

# Water grid
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
    gbif_by_cell[(gx, gy)].append({'lon': lon2, 'lat': lat2, 'species': gf['properties'].get('species', '?')})


# ============== ANALYZE ==============
print(f'\nAnalyzing {len(properties["features"]):,} properties...')
t0 = time.time()
results = []

# Pre-compute dept name from coords (admin polygon) — for normalization
def find_depto(lon, lat):
    """Find which admin depto the point is in."""
    for d in deptos_admin:
        if d['bbox'] and d['bbox'][0] <= lon <= d['bbox'][2] and d['bbox'][1] <= lat <= d['bbox'][3]:
            if point_in_ring(lon, lat, d['coords']):
                return d['name']
    return None

# Pre-build climate lookup by normalized depto name
# Re-key climate_by_depto to be keyed on canonical names
climate_lookup = climate_by_depto

for idx, feat in enumerate(properties['features']):
    p = feat['properties']
    geom = feat.get('geometry')
    if not geom or not geom.get('coordinates'): continue
    lon, lat = geom['coordinates']

    risks = {'flood': None, 'climate': None, 'indigenous': None, 'water_proximity': None, 'shadow': None, 'lighting': None}
    pros = {'near_water': None, 'biodiversity': None}

    # Normalize depto from properties
    raw_depto = p.get('state_province')
    norm_depto = normalize_depto(raw_depto)

    # Find canonical depto by spatial join (admin polygons)
    spatial_depto = find_depto(lon, lat)

    # Use spatial depto if available; otherwise normalized
    final_depto = spatial_depto or norm_depto

    # Flood
    for fz in flood_zones:
        if fz['bbox'] and fz['bbox'][0] <= lon <= fz['bbox'][2] and fz['bbox'][1] <= lat <= fz['bbox'][3]:
            if point_in_ring(lon, lat, fz['coords']):
                rl = fz['props'].get('risk', fz['props'].get('level', 'unknown'))
                rl_str = str(rl).lower()
                sev = 'high' if rl_str in ('high', 'very_high', '3', 'alto', 'alta') else 'medium' if rl_str in ('medium', 'moderate', '2', 'medio', 'media') else 'low'
                risks['flood'] = {'zone': fz['name'], 'level': str(rl), 'severity': sev}
                break

    # Climate risk: use climate_lookup by final_depto
    if final_depto and final_depto in climate_lookup:
        cp = climate_lookup[final_depto]
        # Derive sub-risks from climate properties
        risk_level = (cp.get('risk_level') or '').lower()
        drought_freq = cp.get('drought_freq') or 0
        forest_loss = cp.get('forest_loss_pct_2020_2024') or 0
        annual_precip = cp.get('annual_precip_mm') or 1500
        spi = cp.get('spi_2024') or 0
        # Map risk_level to sub-risks:
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
    elif final_depto:
        # Depto not in climate_lookup — note but don't fabricate
        risks['climate'] = {
            'depto': final_depto,
            'note': 'Climate data not available for this depto',
        }

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
            if v and v != 'note':  # skip if just a 'note'
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
        'state_province': final_depto,  # normalized
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

# ============== STATS ==============
from collections import Counter
dept_counts = Counter(r['state_province'] for r in results)
print('\n=== After normalization ===')
for d, n in sorted(dept_counts.items(), key=lambda x: -x[1]):
    print(f'   {d}: {n}')

# Save — split into TWO files for fast loading
# 1. property_risk_analysis.json: full data (heavy)
# 2. property_risk_index.json: just id -> {lat, lon, score} (lightweight)

output_full = {
    'generated_at': '2026-07-13T18:00:00Z',
    'method': 'spatial-join v2: point-in-polygon + closest-feature, normalized depto names',
    'search_radii': {
        'water_flood': '300 m (risk) / 5 km (pro)',
        'biodiversity': '10 km',
        'indigenous': 'point-in-polygon (exact)',
        'flood_zone': 'point-in-polygon (exact)',
        'climate': 'lookup by spatial depto (admin/departamentos.geojson)',
    },
    'stats': {
        'total_properties': len(results),
    },
    'analyses': results,
}

print('\nSaving full analysis...')
out_full = DATA / 'property_risk_analysis.json'
with open(out_full, 'w') as f:
    json.dump(output_full, f, separators=(',', ':'))
print(f'  full: {os.path.getsize(out_full)/1024/1024:.2f} MB')

# Lightweight index (just id -> coords + score + depto)
index = {}
for r in results:
    index[r['id']] = {
        'lat': r['lat'],
        'lon': r['lon'],
        'risk_score': r['risk_score'],
        'pro_score': r['pro_score'],
        'net_score': r['net_score'],
        'depto': r['state_province'],
        'risks_summary': {k: v is not None for k, v in r['risks'].items()},
        'pros_summary': {k: v is not None for k, v in r['pros'].items()},
    }

output_index = {
    'generated_at': '2026-07-13T18:00:00Z',
    'method': 'lightweight index for heatmap rendering',
    'stats': {'total': len(index)},
    'index': index,
}

out_idx = DATA / 'property_risk_index.json'
with open(out_idx, 'w') as f:
    json.dump(output_index, f, separators=(',', ':'))
print(f'  index: {os.path.getsize(out_idx)/1024/1024:.2f} MB')

# Summary (depto aggregate + top risky)
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
    'generated_at': '2026-07-13T18:00:00Z',
    'method': 'aggregate of v2 risk analysis',
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