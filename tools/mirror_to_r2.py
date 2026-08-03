"""tools/mirror_to_r2.py

Daily R2 mirror of the canonical Paraguay Geodata artifacts.

What it does:
  1. Reads R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
     from the environment.
  2. Uploads the canonical geojson, PMTiles, MBTiles, and the API JSON files
     to the bucket under a date-stamped path.
  3. Always updates the 'latest' copy.
  4. Logs every upload to data/properties/mirror_log.json.

If env vars are unset, the script is a no-op (CI + local dev can run it
without paying for R2).

Usage:
  python3 -m tools.mirror_to_r2
  python3 -m tools.mirror_to_r2 --dry-run         # show what would upload
  python3 -m tools.mirror_to_r2 --keep-days 30    # prune old date-stamped copies
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

import boto3  # type: ignore  # noqa: F401  (declared in pyproject.toml)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINT = os.environ.get("R2_ENDPOINT_URL", "")
DEFAULT_KEY = os.environ.get("R2_ACCESS_KEY_ID", "")
DEFAULT_SECRET = os.environ.get("R2_SECRET_ACCESS_KEY", "")
DEFAULT_BUCKET = os.environ.get("R2_BUCKET", "paraguay-geodata-mirror")

# Files to mirror, relative to REPO_ROOT.
MIRROR_FILES = [
    "exports/web/data/properties_latest.geojson",
    "exports/web/data/properties.pmtiles",
    "exports/web/data/properties.mbtiles",
    "exports/web/data/properties.pmtiles.json",
    "exports/web/api/v1/properties.json",
    "exports/web/api/v1/facets.json",
    "exports/web/healthz.json",
    "exports/web/data/data_freshness.json",
    "exports/web/data/days_on_market.json",
    "exports/web/data/tile_index.json",
]


def _build_client(endpoint: str, key: str, secret: str):
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key,
        aws_secret_access_key=secret,
    )


def _today_prefix() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%d")


def _upload(client, bucket: str, src: Path, key: str) -> dict:
    """Upload `src` to `bucket` at `key`, return summary."""
    if not src.exists():
        return {"src": str(src), "key": key, "status": "missing"}
    size = src.stat().st_size
    with src.open("rb") as f:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=f,
            ContentType=_content_type(src),
            Metadata={"uploaded_at": _dt.datetime.utcnow().isoformat() + "Z"},
        )
    return {"src": str(src), "key": key, "size": size, "status": "ok"}


def _content_type(p: Path) -> str:
    if p.suffix == ".geojson":
        return "application/geo+json"
    if p.suffix == ".pmtiles":
        return "application/octet-stream"
    if p.suffix == ".mbtiles":
        return "application/octet-stream"
    if p.suffix == ".json":
        return "application/json"
    if p.suffix == ".md":
        return "text/markdown"
    return "application/octet-stream"


def _prune_old(client, bucket: str, keep_days: int) -> list[str]:
    """Delete date-stamped copies older than `keep_days`."""
    deleted = []
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(days=keep_days)
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="snapshots/"):
        for obj in page.get("Contents", []):
            if obj["Key"] < f"snapshots/{cutoff.strftime('%Y-%m-%d')}" and obj["Key"] != "snapshots/latest/":
                client.delete_object(Bucket=bucket, Key=obj["Key"])
                deleted.append(obj["Key"])
    return deleted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-days", type=int, default=30)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    args = parser.parse_args(argv)

    log = []
    if not (args.endpoint and DEFAULT_KEY and DEFAULT_SECRET):
        print("  R2 not configured (R2_* env vars unset).  Skipping.")
        print("  Mirror target files:")
        for f in MIRROR_FILES:
            p = ROOT / f
            print(f"    {f}  ({'OK' if p.exists() else 'MISSING'})")
        return 0

    print(f"  mirror target: {args.bucket} @ {args.endpoint}")
    client = _build_client(args.endpoint, DEFAULT_KEY, DEFAULT_SECRET)

    today = _today_prefix()
    for rel in MIRROR_FILES:
        src = ROOT / rel
        if not src.exists():
            print(f"  SKIP: {rel} (missing)")
            log.append({"src": rel, "status": "missing"})
            continue
        # Two copies: date-stamped + 'latest' alias
        date_key = f"snapshots/{today}/{rel}"
        latest_key = f"snapshots/latest/{rel}"
        if args.dry_run:
            print(f"  DRY: {rel} → {date_key} + {latest_key}")
            log.append({"src": rel, "key": date_key, "status": "dryrun"})
        else:
            log.append(_upload(client, args.bucket, src, date_key))
            log.append(_upload(client, args.bucket, src, latest_key))
            print(f"  OK: {rel} → {date_key} + {latest_key}")

    if not args.dry_run and args.keep_days > 0:
        deleted = _prune_old(client, args.bucket, args.keep_days)
        for k in deleted:
            print(f"  DELETE: {k}")
        log.append({"action": "prune", "deleted": deleted})

    # Write a local log
    log_path = ROOT / "data" / "properties" / "mirror_log.json"
    log_path.write_text(json.dumps({
        "as_of": _dt.datetime.utcnow().isoformat() + "Z",
        "bucket": args.bucket,
        "endpoint": args.endpoint,
        "entries": log,
    }, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
