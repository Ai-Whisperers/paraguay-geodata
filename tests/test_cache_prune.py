"""tests/test_cache_prune.py

Tests for tools/cache_prune.py.  Covers the deletion path, the
keep-protect logic, and the size accounting.
"""
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import cache_prune  # noqa: E402


@pytest.fixture
def fake_cache(tmp_path, monkeypatch):
    """Create a fake cache with a few files of known ages."""
    cache = tmp_path / "cache"
    cache.mkdir()
    # 3 files: 1 fresh, 1 just over the cutoff, 1 way old
    fresh = cache / "fresh.txt"
    fresh.write_text("fresh")
    cut = cache / "cut.txt"
    cut.write_text("cut")
    old = cache / "old.txt"
    old.write_text("old")
    # Set mtime to 30 days, 15 days, 1 day ago
    now = time.time()
    os.utime(fresh, (now - 86400, now - 86400))      # 1 day old (kept)
    os.utime(cut, (now - 15 * 86400, now - 15 * 86400))  # 15 days old (deleted)
    os.utime(old, (now - 30 * 86400, now - 30 * 86400))  # 30 days old (deleted)
    return cache


def test_prune_deletes_only_old_files(fake_cache):
    """Files >= 14 days old are deleted.

    With keep_days=14:
      - fresh.txt  = 1 day   → kept
      - cut.txt    = 15 days → deleted (just over cutoff)
      - old.txt    = 30 days → deleted
    """
    summary = cache_prune._prune(fake_cache, keep_days=14, dry_run=False)
    assert summary["deleted"] == 2  # cut.txt + old.txt
    assert summary["kept"] == 1      # fresh.txt only
    assert (fake_cache / "fresh.txt").exists()
    assert not (fake_cache / "cut.txt").exists()
    assert not (fake_cache / "old.txt").exists()


def test_prune_dry_run_keeps_files(fake_cache):
    summary = cache_prune._prune(fake_cache, keep_days=14, dry_run=True)
    assert summary["deleted"] == 2
    assert (fake_cache / "old.txt").exists()  # dry-run doesn't actually delete
    assert (fake_cache / "cut.txt").exists()


def test_prune_protects_canonical_artifacts(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    can = cache / "properties.mbtiles"
    can.write_text("canonical")
    # Even if old, must not be deleted
    ancient = time.time() - 365 * 86400
    os.utime(can, (ancient, ancient))
    summary = cache_prune._prune(cache, keep_days=14, dry_run=False)
    assert summary["deleted"] == 0
    assert (cache / "properties.mbtiles").exists()


def test_prune_reports_savings_bytes(fake_cache):
    summary = cache_prune._prune(fake_cache, keep_days=14, dry_run=False)
    # cut.txt is 3 bytes + old.txt is 3 bytes = 6 bytes total
    assert summary["savings_bytes"] == 6


def test_prune_handles_missing_root(tmp_path):
    summary = cache_prune._prune(tmp_path / "nonexistent", keep_days=14, dry_run=False)
    assert summary["deleted"] == 0
    assert summary["kept"] == 0


def test_prune_returns_errors_dict(tmp_path):
    """The summary always has an errors list."""
    cache = tmp_path / "cache"
    cache.mkdir()
    summary = cache_prune._prune(cache, keep_days=14, dry_run=False)
    assert isinstance(summary["errors"], list)
    assert summary["errors"] == []  # no errors on empty cache

    # Add an old file and verify the error list is still well-formed.
    target = cache / "doomed.txt"
    target.write_text("x")
    ancient = time.time() - 100 * 86400
    os.utime(target, (ancient, ancient))
    summary = cache_prune._prune(cache, keep_days=14, dry_run=False)
    assert isinstance(summary["errors"], list)
    # Either we deleted it (root) or we got an error in the list.
    assert (target.exists() is False) or len(summary["errors"]) > 0
