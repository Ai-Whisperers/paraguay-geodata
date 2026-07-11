#!/usr/bin/env python3
"""tools/convert_to_pmtiles.py

Convert large GeoJSON files to PMTiles (single-file vector tiles).
100× faster loading than GeoJSON. Industry standard.

PMTiles spec: https://github.com/protomaps/PMTiles
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
DATA_DIR = ROOT / 'exports/web/data'

# Files to convert (large ones that benefit most)
TARGETS = [
    'roads.geojson',
    'water.geojson',
    'buildings_asuncion.geojson',
    'properties_latest.geojson',
]

def check_tools():
    """Check if tippecanoe + pmtiles tools are installed."""
    for cmd in ['tippecanoe', 'pmtiles']:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
        except FileNotFoundError:
            print(f'⚠ {cmd} not installed. Install:')
            print('  sudo apt install tippecanoe')
            print('  pip install pmtiles')
            return False
    return True


def convert_to_pmtiles(input_file, output_file, layer_name, min_zoom=4, max_zoom=14):
    """Convert GeoJSON to PMTiles using tippecanoe + pmtiles CLI."""
    print(f'Converting {input_file.name} → {output_file.name}...')

    # Step 1: tippecanoe → MBTiles
    mbtiles_path = output_file.with_suffix('.mbtiles')
    subprocess.run([
        'tippecanoe',
        '-o', str(mbtiles_path),
        '-l', layer_name,
        '-z', str(max_zoom),
        '-Z', str(min_zoom),
        '--drop-rate=0.5',
        '--extend-zooms-if-still-dropping',
        '--force',
        '--read-parallel',
        str(input_file),
    ], check=True)

    # Step 2: pmtiles → PMTiles
    subprocess.run([
        'pmtiles', 'convert',
        str(mbtiles_path),
        str(output_file),
    ], check=True)

    # Cleanup
    mbtiles_path.unlink()

    print(f'  ✓ {output_file.name}: {output_file.stat().st_size / 1e6:.1f} MB')


def main():
    if not check_tools():
        return 1

    for target_name in TARGETS:
        input_path = DATA_DIR / target_name
        if not input_path.exists():
            print(f'  Skipping {target_name} (not found)')
            continue

        # Layer name = filename without extension
        layer_name = target_name.replace('.geojson', '').replace('.json', '')
        output_path = DATA_DIR / f'{layer_name}.pmtiles'

        # Determine zoom range based on data type
        if 'buildings' in target_name:
            min_zoom, max_zoom = 12, 18
        elif 'roads' in target_name:
            min_zoom, max_zoom = 6, 16
        elif 'water' in target_name:
            min_zoom, max_zoom = 4, 14
        else:
            min_zoom, max_zoom = 4, 14

        try:
            convert_to_pmtiles(input_path, output_path, layer_name, min_zoom, max_zoom)
        except Exception as e:
            print(f'  ✗ Failed: {e}')

    # Generate index.json pointing to all PMTiles
    index = {'pmtiles': []}
    for pmt in DATA_DIR.glob('*.pmtiles'):
        index['pmtiles'].append({
            'name': pmt.stem,
            'url': f'./{pmtiles.name(pmt).replace(DATA_DIR.name + "/", "")}',
            'size_mb': round(pmt.stat().st_size / 1e6, 1),
        })
    (DATA_DIR / 'pmtiles_index.json').write_text(json.dumps(index, indent=2))
    print(f'\nGenerated pmtiles_index.json with {len(index["pmtiles"])} files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())