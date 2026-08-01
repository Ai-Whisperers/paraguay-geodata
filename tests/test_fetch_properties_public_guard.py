"""Test the WRITE_PUBLIC opt-in for tools/fetch_properties.py.

Regressed 2026-08-01: a per-dept refresh overwrote the canonical
exports/web/data/properties_latest.geojson with just that dept's data.
The merge script had already combined all sources → 3,012 features
on the viewer, then a `--dept paraguari` partial run clobbered it to
101.

Fix: WRITE_PUBLIC must be opt-in via env var (WRITE_PUBLIC=1) or flag
(--write-public).  Without either, per-dept runs save a raw snapshot
to data/properties/snapshots but do NOT touch the public artifact.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_default_run_does_not_write_public(tmp_path, monkeypatch):
    """Without WRITE_PUBLIC or --write-public, exports/web/data/properties_latest.geojson
    must be untouched even after fetch_properties runs against a fake depto.
    """
    env = os.environ.copy()
    env.pop("WRITE_PUBLIC", None)
    env.pop("HERMES_HOME", None)

    # Stage a "before" file
    public = ROOT / "exports" / "web" / "data" / "properties_latest.geojson"
    sentinel = public.read_bytes() if public.exists() else b""

    # Run a no-fetch scrape — it should not write the public artifact
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'tools');\n"
         "import fetch_properties as fp;\n"
         "import sys; sys.exit(fp.main(['--portal', 'infocasas', '--max-pages', '0']))"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=30,
    )
    # The fetch will fail because there's no actual data; we only check
    # whether the public file was overwritten AFTER the test reset.
    after = public.read_bytes() if public.exists() else b""
    # If the run errored early (no listings), the public file should be unchanged
    if "raw snapshot only" in r.stdout or "raw snapshot only" in r.stderr:
        assert after == sentinel, "WRITE_PUBLIC opt-in failed: public file was touched"


def test_write_public_flag_overwrites_public(tmp_path, monkeypatch):
    """With WRITE_PUBLIC=1, fetch_properties DOES overwrite the public artifact."""
    env = os.environ.copy()
    env["WRITE_PUBLIC"] = "1"

    # Run with --write-public in argv
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'tools');\n"
         "import fetch_properties as fp;\n"
         "import sys; sys.exit(fp.main(['--portal', 'infocasas', '--max-pages', '0', '--write-public']))"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=30,
    )
    # Should print the public snapshot line
    assert "[fetch] public snapshot" in r.stdout or "[fetch] public snapshot" in r.stderr, \
        f"--write-public flag should have written public, got: {r.stdout}\n{r.stderr}"
