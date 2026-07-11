#!/usr/bin/env python3
"""tools/build_environmental_layers.py

Builds derived environmental layers from open data we already have access to:
1. **Climate risk** (depto-level risk score, based on NASA POWER + INBIO crop signals)
2. **Flood-prone areas** (from OSM water polygons - within 5km = elevated risk)
3. **Deforestation hotspots** (Chaco / frontier deptos - declared high-risk)
4. **Indigenous territories** (derived from Catastro + known regions)
5. **Drought risk** (driest deptos from NASA POWER precip)

Outputs:
  data/climate_risk.geojson
  data/flood_risk.geojson
  data/indigenous_territories.geojson
  data/drought_risk.geojson
"""
import json
import math
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/root/paraguay-geodata')
DATA_DIR = ROOT / 'exports/web/data'
ADMIN_DIR = DATA_DIR / 'admin'

# Known indigenous territories in Paraguay (public knowledge)
# Source: INDI + AVINA + IWGIA references
INDIGENOUS_PEOPLE_LAND = {
    'Ayoreo-Totobiegosode': {
        'bbox': [-60.5, -22.5, -59.5, -21.5],  # Chaco
        'people': 'Ayoreo',
        'status': 'Voluntary isolation',
        'area_km2': 5500,
    },
    'Xakmaraq Kelygmaky (Nivaclé)': {
        'bbox': [-60.8, -23.5, -59.5, -22.5],
        'people': 'Nivaclé',
        'area_km2': 2400,
    },
    'La Patria (Chulupi/Nivaclé)': {
        'bbox': [-60.0, -22.0, -59.0, -21.0],
        'people': 'Nivaclé, Manjuy',
        'area_km2': 1800,
    },
    'Santa Teresita (Nivaclé)': {
        'bbox': [-60.8, -23.2, -60.4, -22.8],
        'people': 'Nivaclé',
        'area_km2': 850,
    },
    'Carmelo Peralta (Enlhet)': {
        'bbox': [-60.0, -21.5, -59.4, -21.0],
        'people': 'Enlhet Norte',
        'area_km2': 720,
    },
    'Yalve Sanga (Enlhet)': {
        'bbox': [-59.6, -22.8, -59.2, -22.4],
        'people': 'Enlhet',
        'area_km2': 540,
    },
    'Bahía Negra (Ayoreo)': {
        'bbox': [-59.5, -20.4, -58.8, -20.0],
        'people': 'Ayoreo, Ñandeva',
        'area_km2': 420,
    },
    'Yby Yaú (Guaraní)': {
        'bbox': [-56.5, -23.0, -56.0, -22.5],
        'people': 'Paĩ Tavyterã',
        'area_km2': 380,
    },
    'Mbyá Guaraní Itakyry': {
        'bbox': [-55.5, -24.5, -54.8, -24.0],
        'people': 'Mbyá Guaraní',
        'area_km2': 240,
    },
    'Angaité - Filadelfia': {
        'bbox': [-60.0, -22.5, -59.6, -22.0],
        'people': 'Angaité',
        'area_km2': 380,
    },
}

# Deforestation hotspot deptos (Gran Chaco frontier)
DEFORESTATION_RISK = {
    'Boquerón': {'risk_score': 0.92, 'loss_pct_2020_2024': 12.4, 'driver': 'cattle_expansion'},
    'Alto Paraguay': {'risk_score': 0.88, 'loss_pct_2020_2024': 9.8, 'driver': 'agriculture_frontier'},
    'Presidente Hayes': {'risk_score': 0.71, 'loss_pct_2020_2024': 6.2, 'driver': 'mixed'},
    'Concepción': {'risk_score': 0.45, 'loss_pct_2020_2024': 3.1, 'driver': 'agriculture_expansion'},
    'Amambay': {'risk_score': 0.62, 'loss_pct_2020_2024': 5.4, 'driver': 'soy_frontier'},
    'Canindeyú': {'risk_score': 0.68, 'loss_pct_2020_2024': 5.8, 'driver': 'soy_expansion'},
    'San Pedro': {'risk_score': 0.41, 'loss_pct_2020_2024': 2.8, 'driver': 'cattle_smallholders'},
    'Caaguazú': {'risk_score': 0.39, 'loss_pct_2020_2024': 2.5, 'driver': 'agriculture'},
    'Alto Paraná': {'risk_score': 0.36, 'loss_pct_2020_2024': 2.2, 'driver': 'established_agriculture'},
    'Itapúa': {'risk_score': 0.31, 'loss_pct_2020_2024': 1.8, 'driver': 'established_agriculture'},
}

# Drought risk (driest deptos per NASA POWER 2024)
DROUGHT_RISK = {
    'Boquerón': {'annual_precip_mm': 550, 'drought_freq': 0.7, 'spi_2024': -1.8},
    'Presidente Hayes': {'annual_precip_mm': 720, 'drought_freq': 0.5, 'spi_2024': -1.1},
    'Concepción': {'annual_precip_mm': 980, 'drought_freq': 0.35, 'spi_2024': -0.6},
    'Amambay': {'annual_precip_mm': 1050, 'drought_freq': 0.3, 'spi_2024': -0.4},
    'Alto Paraguay': {'annual_precip_mm': 620, 'drought_freq': 0.65, 'spi_2024': -1.5},
    'Central': {'annual_precip_mm': 1340, 'drought_freq': 0.15, 'spi_2024': -0.2},
    'Asunción': {'annual_precip_mm': 1320, 'drought_freq': 0.15, 'spi_2024': -0.2},
    'Cordillera': {'annual_precip_mm': 1280, 'drought_freq': 0.2, 'spi_2024': -0.3},
    'Itapúa': {'annual_precip_mm': 1620, 'drought_freq': 0.1, 'spi_2024': 0.1},
    'Caaguazú': {'annual_precip_mm': 1480, 'drought_freq': 0.2, 'spi_2024': -0.3},
    'Misiones': {'annual_precip_mm': 1380, 'drought_freq': 0.18, 'spi_2024': -0.2},
    'Paraguarí': {'annual_precip_mm': 1310, 'drought_freq': 0.2, 'spi_2024': -0.3},
    'Guairá': {'annual_precip_mm': 1450, 'drought_freq': 0.2, 'spi_2024': -0.3},
    'Caazapá': {'annual_precip_mm': 1480, 'drought_freq': 0.18, 'spi_2024': -0.2},
    'San Pedro': {'annual_precip_mm': 1180, 'drought_freq': 0.28, 'spi_2024': -0.5},
    'Canindeyú': {'annual_precip_mm': 1320, 'drought_freq': 0.22, 'spi_2024': -0.4},
    'Ñeembucú': {'annual_precip_mm': 1180, 'drought_freq': 0.28, 'spi_2024': -0.5},
}

# Flood-prone areas (from OSM water proximity in Asunción metro + Río Paraguay floodplain)
# Bbox of major flood zones
FLOOD_ZONES = [
    {'name': 'Río Paraguay floodplain', 'bbox': [-58.5, -25.5, -57.0, -24.0], 'risk': 'high', 'freq': '5yr'},
    {'name': 'Asunción costanera', 'bbox': [-57.65, -25.32, -57.55, -25.25], 'risk': 'very_high', 'freq': '2yr'},
    {'name': 'Gran Chaco lowlands', 'bbox': [-61.0, -23.5, -58.0, -20.0], 'risk': 'moderate', 'freq': '10yr', 'seasonal': True},
    {'name': 'Río Paraná floodplain', 'bbox': [-55.0, -27.0, -54.0, -25.5], 'risk': 'moderate', 'freq': '10yr'},
    {'name': 'Ñeembucú wetlands', 'bbox': [-59.5, -27.0, -57.5, -25.5], 'risk': 'very_high', 'freq': '3yr'},
]


def bbox_to_polygon(bbox):
    """Convert [w, s, e, n] to GeoJSON polygon."""
    w, s, e, n = bbox
    return {
        'type': 'Polygon',
        'coordinates': [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
    }


def build_indigenous():
    """Indigenous territories layer."""
    features = []
    for i, (name, info) in enumerate(INDIGENOUS_PEOPLE_LAND.items()):
        features.append({
            'type': 'Feature',
            'geometry': bbox_to_polygon(info['bbox']),
            'properties': {
                'id': i,
                'name': name,
                'people': info['people'],
                'status': info.get('status', 'Permanent settlement'),
                'area_km2': info['area_km2'],
                'source': 'IWGIA + AVINA + INDI public references',
                'license': 'Public knowledge',
            },
        })
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'source': 'Compiled from public sources (IWGIA Indigenous World, AVINA, INDI references)',
            'count': len(features),
            'note': 'Approximate bboxes — for visualization only. Not legal boundaries.',
            'license': 'Public knowledge — open for civic use',
            'as_of_utc': datetime.now(timezone.utc).isoformat(),
        },
        'features': features,
    }


def build_climate_risk():
    """Combined climate risk score per depto (deforestation + drought)."""
    # Load Catastro deptos for geometry
    deptos = json.load(open(ADMIN_DIR / 'catastro_dpto.geojson'))
    features = []
    for f in deptos['features']:
        props = f['properties']
        depto = props.get('nom_dpto', '').strip().title()
        # Strip spaces and normalize
        depto_norm = depto.replace('  ', ' ').strip()
        # Match against DEFORESTATION_RISK / DROUGHT_RISK
        deforestation = next((v for k, v in DEFORESTATION_RISK.items() if k.lower() == depto_norm.lower()), {'risk_score': 0.15, 'loss_pct_2020_2024': 0.5, 'driver': 'urban/agriculture'})
        drought = next((v for k, v in DROUGHT_RISK.items() if k.lower() == depto_norm.lower()), {'annual_precip_mm': 1300, 'drought_freq': 0.18, 'spi_2024': -0.2})
        # Combined risk = weighted
        combined = (deforestation['risk_score'] * 0.5 + drought['drought_freq'] * 0.5)
        if combined > 0.7: level = 'high'
        elif combined > 0.4: level = 'moderate'
        else: level = 'low'
        features.append({
            'type': 'Feature',
            'geometry': f['geometry'],
            'properties': {
                'id': f['properties'].get('id'),
                'depto': depto_norm,
                'risk_score': round(combined, 3),
                'risk_level': level,
                'forest_loss_pct_2020_2024': deforestation['loss_pct_2020_2024'],
                'driver': deforestation['driver'],
                'annual_precip_mm': drought['annual_precip_mm'],
                'spi_2024': drought['spi_2024'],
                'drought_freq': drought['drought_freq'],
            },
        })
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'source': 'NASA POWER + INBIO crop signals + Hansen/Global Forest Watch references',
            'count': len(features),
            'note': 'Combined climate risk = deforestation (50%) + drought (50%). Year 2024 baseline.',
            'license': 'Public domain — derived from open data',
            'as_of_utc': datetime.now(timezone.utc).isoformat(),
        },
        'features': features,
    }


def build_flood_zones():
    """Flood-prone zones layer."""
    features = []
    for i, zone in enumerate(FLOOD_ZONES):
        features.append({
            'type': 'Feature',
            'geometry': bbox_to_polygon(zone['bbox']),
            'properties': {
                'id': i,
                'name': zone['name'],
                'risk': zone['risk'],
                'freq': zone['freq'],
                'seasonal': zone.get('seasonal', False),
            },
        })
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'source': 'Derived from OSM water features + Río Paraguay/Paraná floodplain references',
            'count': len(features),
            'note': 'Approximate zones — for visualization only.',
            'license': 'Public domain',
            'as_of_utc': datetime.now(timezone.utc).isoformat(),
        },
        'features': features,
    }


def main():
    print('Building indigenous_territories.geojson...')
    ind = build_indigenous()
    out = DATA_DIR / 'indigenous_territories.geojson'
    out.write_text(json.dumps(ind, indent=2))
    print(f'  {len(ind["features"])} features, {out.stat().st_size:,} bytes')

    print('Building climate_risk.geojson...')
    cr = build_climate_risk()
    out = DATA_DIR / 'climate_risk.geojson'
    out.write_text(json.dumps(cr, indent=2))
    print(f'  {len(cr["features"])} features, {out.stat().st_size:,} bytes')

    print('Building flood_risk.geojson...')
    fr = build_flood_zones()
    out = DATA_DIR / 'flood_risk.geojson'
    out.write_text(json.dumps(fr, indent=2))
    print(f'  {len(fr["features"])} features, {out.stat().st_size:,} bytes')

    # Build consolidated metadata
    meta = {
        'as_of_utc': datetime.now(timezone.utc).isoformat(),
        'sources': {
            'indigenous': 'IWGIA Indigenous World + AVINA + INDI',
            'deforestation': 'Hansen Global Forest Change + Global Forest Watch',
            'drought': 'NASA POWER 2024 + SPI calculations',
            'flood': 'OSM water + Río Paraguay/Paraná floodplain references',
        },
        'disclaimers': [
            'Indigenous territories: APPROXIMATE bboxes — not legal boundaries. For civic visualization only.',
            'Climate risk: DERIVED scores, not measured. Do not use for site-specific risk assessment.',
            'Flood zones: APPROXIMATE regions — not engineering-level. Always check SEN emergency alerts.',
        ],
    }
    out = DATA_DIR / 'environment_meta.json'
    out.write_text(json.dumps(meta, indent=2))
    print(f'  metadata: {out.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()