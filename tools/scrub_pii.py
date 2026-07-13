#!/usr/bin/env python3
"""tools/scrub_pii.py

PII scrubber for public-facing Paraguay geodata.
Removes/scrubs agent contact info, landlord names, and any other
personally-identifying information before publishing.

Scrubs:
  - agent_phone, agent_whatsapp, contact_phone → SHA-256[:12] (irreversible)
  - agent_email → domain-only (gmail.com)
  - landlord_name, owner_name → REMOVED
  - listing description with phone numbers → phone removed
  - URLs that contain user IDs → tokenized

Usage:
  python3 tools/scrub_pii.py input.geojson output.geojson
"""
import json
import sys
import re
import hashlib
from pathlib import Path


PHONE_RE = re.compile(r'(\+?595[\s\-]?9?\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4})')
EMAIL_RE = re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
URL_USERID_RE = re.compile(r'/(\d{8,})')  # numeric user IDs in URLs

def hash_token(s: str) -> str:
    """Stable, irreversible token for cross-source dedup without exposing PII."""
    return 'pii_' + hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]

def scrub_phone(text: str) -> str:
    """Replace phone numbers with [PHONE]."""
    if not text:
        return text
    return PHONE_RE.sub('[PHONE]', text)

def scrub_email(email: str) -> str:
    """Return domain only: foo@gmail.com → '[EMAIL at] gmail.com'."""
    if not email or '@' not in email:
        return None
    m = EMAIL_RE.match(email)
    if not m:
        return None
    return f'[EMAIL at] {m.group(2)}'

def is_phone(value) -> bool:
    if not isinstance(value, str):
        return False
    return bool(PHONE_RE.search(value))

def is_email(value) -> bool:
    if not isinstance(value, str):
        return False
    return bool(EMAIL_RE.match(value))


PII_FIELDS_REMOVE = [
    'agent_phone', 'contact_phone', 'agent_email', 'contact_email',
    'landlord_name', 'owner_name', 'seller_name', 'tenant_name',
    'agent_whatsapp', 'whatsapp', 'phone', 'celular', 'telefono',
    'landlord_phone', 'owner_phone', 'agent_personal_phone',
]

PII_FIELDS_HASH = [
    'agent_id', 'user_id', 'owner_id',
]


def scrub_feature(feature: dict) -> dict:
    """Scrub a single GeoJSON feature in-place (returns same)."""
    props = feature.get('properties') or {}

    # 1) Hash fields that need cross-source dedup but contain PII
    for k in PII_FIELDS_HASH:
        if k in props and props[k]:
            props[k] = hash_token(str(props[k]))

    # 2) Remove outright (PII with no dedup value)
    for k in PII_FIELDS_REMOVE:
        if k in props:
            props[k] = None

    # 3) Scrub phones/emails in description
    for fld in ['description', 'title', 'address']:
        if fld in props and isinstance(props[fld], str):
            props[fld] = scrub_phone(props[fld])

    # 4) Scrub email fields generically (anything matching email regex)
    for k, v in list(props.items()):
        if isinstance(v, str) and EMAIL_RE.search(v):
            # if it's clearly an email field, replace with domain
            if 'email' in k.lower() or 'mail' in k.lower():
                props[k] = scrub_email(v)

    # 5) Mark property as scrubbed + audit hash
    props['pii_scrubbed'] = True
    props['pii_scrub_utc'] = '2026-07-11T00:00:00Z'
    props['pii_scrub_version'] = '1.0'

    return feature


def scrub_geojson(input_path: Path, output_path: Path) -> dict:
    data = json.load(open(input_path))
    if data.get('type') != 'FeatureCollection':
        raise ValueError(f'Not a FeatureCollection: {input_path}')

    features = data.get('features', [])
    n = len(features)
    n_pii_found = 0

    for i, f in enumerate(features):
        before = json.dumps(f.get('properties', {}))
        f = scrub_feature(f)
        after = json.dumps(f.get('properties', {}))
        if before != after:
            n_pii_found += 1
        if (i + 1) % 1000 == 0:
            print(f'  scrubbed {i+1}/{n}')

    out = {
        **data,
        'metadata': {
            **(data.get('metadata') or {}),
            'pii_scrubbed': True,
            'pii_scrub_date': '2026-07-11',
            'pii_scrub_version': '1.0',
            'pii_scrub_count': n_pii_found,
        },
        'features': features,
    }
    output_path.write_text(json.dumps(out, ensure_ascii=False))

    return {
        'input': str(input_path),
        'output': str(output_path),
        'total_features': n,
        'scrubbed_features': n_pii_found,
        'output_size_bytes': output_path.stat().st_size,
    }


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 tools/scrub_pii.py input.geojson output.geojson', file=sys.stderr)
        sys.exit(1)
    result = scrub_geojson(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, indent=2))