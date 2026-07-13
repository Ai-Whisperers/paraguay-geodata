#!/usr/bin/env python3
"""Generate sample regulatory zones JSON for Asunción.

This is the data model for Phase 4 (Lucía's municipal ordinances).
For now: synthetic example data showing the schema.
Real data comes from Lucía's collection + municipal websites.
"""
import json
from pathlib import Path

DATA = Path('/root/paraguay-geodata/exports/web/data')

# Synthetic zoning data for Asunción centro
# Real data should come from Catastro urban_zoning + municipal ordinances
zones = [
    {
        "zone_id": "asu-centro-C1",
        "city": "Asunción",
        "category": "commercial",
        "name": "Centro - Comercial intensivo C1",
        "max_height_m": 30,
        "max_floors": 9,
        "max_lot_coverage_pct": 80,
        "max_construction_pct": 600,
        "setback_front_m": 0,
        "setback_side_m": 3,
        "setback_back_m": 3,
        "allowed_use": ["comercio", "oficina", "vivienda", "hotel", "gastronomía"],
        "restricted_use": ["industrial", "taller mecánico", "depósito"],
        "ordinance_ref": "Ord. 246/94 art. 17 - Zona C1 Centro",
        "last_updated": "2024-01-15",
        "approximate_bbox": [-57.585, -25.290, -57.560, -25.265],
    },
    {
        "zone_id": "asu-centro-R2",
        "city": "Asunción",
        "category": "residential",
        "name": "Centro - Residencial R2",
        "max_height_m": 15,
        "max_floors": 5,
        "max_lot_coverage_pct": 60,
        "max_construction_pct": 300,
        "setback_front_m": 3,
        "setback_side_m": 2,
        "setback_back_m": 2,
        "allowed_use": ["vivienda", "comercio menor", "oficina"],
        "restricted_use": ["industrial", "gastronomía con extracción", "estacionamiento > 5 autos"],
        "ordinance_ref": "Ord. 246/94 art. 22 - Zona R2",
        "last_updated": "2024-01-15",
        "approximate_bbox": [-57.610, -25.305, -57.575, -25.275],
    },
    {
        "zone_id": "asu-villa-morra-R3",
        "city": "Asunción",
        "category": "residential",
        "name": "Villa Morra - Residencial R3 (denso)",
        "max_height_m": 25,
        "max_floors": 7,
        "max_lot_coverage_pct": 60,
        "max_construction_pct": 400,
        "setback_front_m": 3,
        "setback_side_m": 3,
        "setback_back_m": 3,
        "allowed_use": ["vivienda", "comercio", "oficina", "hotel boutique"],
        "restricted_use": ["industrial", "depósito", "taller"],
        "ordinance_ref": "Ord. 246/94 art. 24 - Zona R3",
        "last_updated": "2024-01-15",
        "approximate_bbox": [-57.605, -25.310, -57.560, -25.270],
    },
    {
        "zone_id": "asu-carmelitas-R3",
        "city": "Asunción",
        "category": "residential",
        "name": "Carmelitas - Residencial R3",
        "max_height_m": 25,
        "max_floors": 7,
        "max_lot_coverage_pct": 60,
        "max_construction_pct": 400,
        "setback_front_m": 3,
        "setback_side_m": 3,
        "setback_back_m": 3,
        "allowed_use": ["vivienda", "comercio", "oficina"],
        "restricted_use": ["industrial"],
        "ordinance_ref": "Ord. 246/94 art. 24 - Zona R3",
        "last_updated": "2024-01-15",
        "approximate_bbox": [-57.575, -25.290, -57.535, -25.250],
    },
]

# Save
out = DATA / 'construction_zones.json'
out.write_text(json.dumps({'zones': zones, 'version': 1}, indent=2, ensure_ascii=False))
print(f"✓ wrote {out} with {len(zones)} synthetic zones")
print("\nReal data sources needed from Lucía:")
print("  - Asunción: Ord. 246/94 + Plan Regulador 2010")
print("  - CDE, Encarnación, Pilar, Pedro Juan Caballero ordinances")
print("  - Catastro urban_zoning polygons (already in /data/admin/catastro_urba.geojson)")