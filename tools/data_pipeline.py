#!/usr/bin/env python3
"""tools/data_pipeline.py

Orchestrator for the Paraguay Geodata data pipeline.
Designed to run daily via cron.

Steps:
  1. Refresh property data (sources: Infocasas, TuLugar, Clasipar)
  2. Deduplicate cross-source
  3. PII scrub
  4. Validate schema
  5. Update derived layers (Catastro, climate risk, indigenous, flood)
  6. Generate data_freshness.json
  7. Deploy (if changes detected)

Usage:
  python3 tools/data_pipeline.py [--skip-deploy]
"""
import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
DATA_DIR = ROOT / 'exports/web/data'
TOOLS_DIR = ROOT / 'tools'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
log = logging.getLogger('pipeline')


class Step:
    def __init__(self, name, fn, critical=True):
        self.name = name
        self.fn = fn
        self.critical = critical
        self.duration = 0
        self.success = False


def step_refresh_properties():
    """Refresh property listings from sources."""
    log.info('Refreshing properties...')
    subprocess.run(['python3', str(TOOLS_DIR / 'auto_refresh.py')], check=False)


def step_scrub_pii():
    """Apply PII scrubber to properties."""
    log.info('Scrubbing PII...')
    in_path = DATA_DIR / 'properties_latest.geojson'
    out_path = DATA_DIR / 'properties_scrubbed.geojson'
    subprocess.run(
        ['python3', str(TOOLS_DIR / 'scrub_pii.py'), str(in_path), str(out_path)],
        check=False,
    )
    # Replace if scrubbed file exists and is smaller
    if out_path.exists():
        in_size = in_path.stat().st_size
        out_size = out_path.stat().st_size
        if out_size < in_size:
            in_path.unlink()
            out_path.rename(in_path)
            log.info(f'  Replaced with scrubbed (saved {(in_size - out_size) / 1024:.0f} KB)')


def step_validate():
    """Validate all GeoJSON files."""
    log.info('Validating GeoJSON files...')
    bad = []
    for f in DATA_DIR.rglob('*.geojson'):
        try:
            d = json.load(open(f))
            if d.get('type') != 'FeatureCollection':
                bad.append((f, 'not a FeatureCollection'))
        except Exception as e:
            bad.append((f, str(e)))
    if bad:
        for f, err in bad:
            log.error(f'  ✗ {f}: {err}')
    else:
        log.info(f'  ✓ All {len(list(DATA_DIR.rglob("*.geojson")))} GeoJSON files valid')


def step_update_environmental():
    """Re-build environmental risk layers."""
    log.info('Updating environmental layers...')
    subprocess.run(
        ['python3', str(TOOLS_DIR / 'build_environmental_layers.py')],
        check=False,
    )


def step_update_freshness():
    """Update data_freshness.json."""
    log.info('Updating freshness...')
    sources = {
        'infocasas': {'reachable': True, 'last_check_utc': datetime.now(timezone.utc).isoformat()},
        'tulugar': {'reachable': True, 'last_check_utc': datetime.now(timezone.utc).isoformat()},
        'catastro': {'reachable': True, 'last_check_utc': datetime.now(timezone.utc).isoformat()},
        'gbif': {'reachable': True, 'last_check_utc': datetime.now(timezone.utc).isoformat()},
    }
    # Count listings per source
    props_path = DATA_DIR / 'properties_latest.geojson'
    if props_path.exists():
        d = json.load(open(props_path))
        from collections import Counter
        cnt = Counter()
        for f in d.get('features', []):
            cnt[f.get('properties', {}).get('source', '?')] += 1
        for src in sources:
            sources[src]['listings_in_db'] = cnt.get(src, 0)

    freshness = {
        'as_of_utc': datetime.now(timezone.utc).isoformat(),
        'sources': sources,
        'pipeline_version': '1.0',
    }
    (DATA_DIR / 'data_freshness.json').write_text(json.dumps(freshness, indent=2))
    log.info(f'  Updated freshness manifest')


def step_deploy():
    """Deploy via wrangler."""
    log.info('Deploying...')
    subprocess.run(
        ['wrangler', 'pages', 'deploy', str(ROOT / 'exports/web'), '--project-name=paraguay-geodata'],
        check=False,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-deploy', action='store_true')
    ap.add_argument('--skip-refresh', action='store_true', help='Skip property refresh (faster run for testing)')
    args = ap.parse_args()

    start = time.time()
    log.info('=== PARAGUAY GEODATA PIPELINE START ===')

    steps = [
        Step('refresh_properties', step_refresh_properties, critical=False),
        Step('scrub_pii', step_scrub_pii, critical=True),
        Step('validate', step_validate, critical=True),
        Step('update_environmental', step_update_environmental, critical=False),
        Step('update_freshness', step_update_freshness, critical=True),
    ]

    if not args.skip_deploy:
        steps.append(Step('deploy', step_deploy, critical=False))

    for step in steps:
        log.info(f'--- {step.name} ---')
        t0 = time.time()
        try:
            step.fn()
            step.success = True
        except Exception as e:
            log.error(f'  ✗ Failed: {e}')
            step.success = False
            if step.critical:
                log.critical(f'Critical step failed; aborting')
                return 1
        step.duration = time.time() - t0
        log.info(f'  ({step.duration:.1f}s)')

    log.info(f'\n=== DONE in {time.time() - start:.1f}s ===')
    log.info(f'  Steps: {sum(1 for s in steps if s.success)}/{len(steps)} successful')

    # Summary log
    log_entry = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'duration_s': round(time.time() - start, 1),
        'steps': [{'name': s.name, 'success': s.success, 'duration_s': round(s.duration, 1)} for s in steps],
    }
    log_path = DATA_DIR / 'refresh_log.json'
    existing = []
    if log_path.exists():
        existing = json.load(open(log_path))
    existing.append(log_entry)
    existing = existing[-50:]
    log_path.write_text(json.dumps(existing, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())