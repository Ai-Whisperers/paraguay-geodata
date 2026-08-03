"""tools/cache_prune.py

Prune stale cache files older than `keep_days` from the data/properties/
cache/ tree.  Used by `scripts/refresh_properties.sh` and the standalone
Hermes cron.

What it does:
  1. Walks the cache root (default: data/properties/cache).
  2. Deletes any file older than `keep_days` (default 14).
  3. Removes empty subdirectories after the file sweep.
  4. Writes a log to data/properties/cache_prune.log (rotated daily).
  5. Always preserves the canonical mbtiles + pmtiles (they're expensive
     to rebuild and we want a 14-day history of canonical tile artifacts).

Usage:
  python3 -m tools.cache_prune
  python3 -m tools.cache_prune --keep-days 7
  python3 -m tools.cache_prune --root /tmp/other-cache --dry-run
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / "data" / "properties" / "cache"
LOG_PATH = ROOT / "data" / "properties" / "cache_prune.log"

# Paths we never prune (canonical artifacts we want to keep).
PROTECTED_PATTERNS = (
    "properties.mbtiles",
    "properties.pmtiles",
    "pymtiles_input.ndjson",
)


def _is_protected(path: Path) -> bool:
    return any(path.name == p for p in PROTECTED_PATTERNS)


def _format_age_days(path: Path) -> float:
    """Return the age of the file in days, as a float."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return 0.0
    age = (_dt.datetime.now().timestamp() - mtime) / 86400.0
    return age


def _walk(cache_root: Path):
    """Yield (file, mtime_days) for every regular file under cache_root."""
    for path in cache_root.rglob("*"):
        if path.is_file():
            yield path, _format_age_days(path)


def _prune(cache_root: Path, keep_days: int, dry_run: bool) -> dict:
    """Delete files older than keep_days.  Returns a summary."""
    if not cache_root.exists():
        return {"deleted": 0, "kept": 0, "savings_bytes": 0, "errors": []}

    cutoff = float(keep_days)
    deleted = 0
    kept = 0
    savings = 0
    errors = []

    for path, age in _walk(cache_root):
        if _is_protected(path):
            kept += 1
            continue
        if age < cutoff:
            kept += 1
            continue
        try:
            size = path.stat().st_size
            if not dry_run:
                path.unlink()
            deleted += 1
            savings += size
        except OSError as e:
            errors.append(f"{path}: {e}")

    # Clean up empty directories.
    if not dry_run:
        for d in sorted(cache_root.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except OSError:
                    pass

    return {
        "deleted": deleted,
        "kept": kept,
        "savings_bytes": savings,
        "errors": errors,
    }


def _format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.2f} GB"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_CACHE,
                        help="Cache root (default: %(default)s).")
    parser.add_argument("--keep-days", type=int, default=14,
                        help="Delete files older than this (default: 14).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be deleted without doing it.")
    parser.add_argument("--no-log", action="store_true",
                        help="Skip writing the log file (CI mode).")
    args = parser.parse_args(argv)

    summary = _prune(args.root, args.keep_days, args.dry_run)
    summary["as_of"] = _dt.datetime.now().isoformat() + "Z"
    summary["root"] = str(args.root)
    summary["keep_days"] = args.keep_days
    summary["dry_run"] = args.dry_run

    print(f"  cache root:  {args.root}")
    print(f"  keep_days:   {args.keep_days}")
    print(f"  mode:        {'dry-run' if args.dry_run else 'live'}")
    print(f"  deleted:     {summary['deleted']:,} files")
    print(f"  kept:        {summary['kept']:,} files")
    print(f"  savings:     {_format_bytes(summary['savings_bytes'])}")
    if summary["errors"]:
        print(f"  errors:      {len(summary['errors'])}")
        for e in summary["errors"][:5]:
            print(f"    - {e}")

    if not args.no_log:
        # Rotate log: keep only the last 30 days.
        log_path = LOG_PATH
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_lines = open(log_path).readlines() if log_path.exists() else []
        log_line = json.dumps(summary) + "\n"
        log_lines.append(log_line)
        cutoff = _dt.datetime.now() - _dt.timedelta(days=30)
        new = []
        for line in log_lines:
            try:
                d = json.loads(line)
                if d.get("as_of", "") >= cutoff.isoformat() + "Z":
                    new.append(line)
            except Exception:
                continue
        log_path.write_text("".join(new))
        print(f"  log:         {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
