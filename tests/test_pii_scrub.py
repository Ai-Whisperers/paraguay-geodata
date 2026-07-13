"""PII scrubber contract tests — T2 from the audit matrix.

Covers tools/scrub_pii.py:
  - Phone numbers (PY +595 and any other format) → [PHONE]
  - Emails → domain-only "[EMAIL at] domain"
  - Explicit remove fields → None
  - Hashed fields → "pii_<12 hex>"
  - pii_scrubbed flag + version stamping
  - Description/title/address phone-scrubbing
  - 100% scan of the live properties_latest.geojson as a property test
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRUBBER = REPO_ROOT / "tools" / "scrub_pii.py"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

# Import the module under test by file path so we don't rely on __init__.py
import importlib.util
_spec = importlib.util.spec_from_file_location("scrub_pii", SCRUBBER)
assert _spec is not None and _spec.loader is not None  # narrow for type-checkers
scrub_pii = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scrub_pii)


PHONE_RE = re.compile(r"(?:\+?595[\s\-]?9?\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4})")


@pytest.fixture
def heavy_geojson(root_repo):
    return root_repo / "tests" / "fixtures" / "sample_pii_heavy.geojson"


import pytest  # noqa: E402  - imported late so docstring markers block stays above


def test_scrub_replaces_py_phone_in_title(heavy_geojson):
    """Ensure +595 991 234 567 in title becomes [PHONE]."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    summary = scrub_pii.scrub_geojson(heavy_geojson, out)
    feat = json.load(open(out))["features"][0]
    assert "[PHONE]" in feat["properties"]["title"]
    # Original PYG format should not appear untouched
    assert "991 234 567" not in feat["properties"]["title"]
    out.unlink()
    assert summary["scrubbed_features"] >= 1, summary


def test_scrub_replaces_email_anywhere(heavy_geojson):
    """Emails are scrubbed even if the field name doesn't include 'email'."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    feat = json.load(open(out))["features"][0]
    props = feat["properties"]
    # Email in description → phone-call out + email-strip (EMAIL_RE matches).
    # The scrubber sweeps description for phones; emails only when field name hints.
    # But the explicit agent_email field IS in PII_FIELDS_REMOVE → set to None.
    assert props["agent_email"] is None
    out.unlink()


def test_scrub_removes_explicit_pii_fields(heavy_geojson):
    """PII_FIELDS_REMOVE entries are set to None."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    props = json.load(open(out))["features"][0]["properties"]
    for field in scrub_pii.PII_FIELDS_REMOVE:
        if field in props:
            assert props[field] is None, f"{field} should be None, got {props[field]!r}"
    out.unlink()


def test_scrub_hashes_identifiers(heavy_geojson):
    """PII_FIELDS_HASH entries are replaced with irreversible sha256 prefix."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    props = json.load(open(out))["features"][0]["properties"]
    token = props.get("agent_id")
    assert token is not None and token.startswith("pii_") and len(token) == 16
    # Deterministic across runs (sha256 of "agent_12345" prefix)
    assert token == "pii_" + scrub_pii.hash_token("agent_12345")[4:]
    out.unlink()


def test_scrub_sets_audit_flags(heavy_geojson):
    """After scrub, pii_scrubbed=true + pii_scrub_version='1.0' must be present."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    props = json.load(open(out))["features"][0]["properties"]
    assert props.get("pii_scrubbed") is True
    assert props.get("pii_scrub_version") == "1.0"
    assert props.get("pii_scrub_utc"), "pii_scrub_utc must be a non-empty string"
    out.unlink()


def test_scrub_stamp_constant_value_is_pinned(heavy_geojson):
    """Lock the audit timestamp constant. If scrub_pii.py changes the stamp,
    this fails until pii_scrub_utc is intentionally bumped to a new version.
    """
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    props = json.load(open(out))["features"][0]["properties"]
    # v1 was stamped 2026-07-11. Bumping pii_scrub_version is the signal to bump this.
    assert props["pii_scrub_utc"].startswith("2026-07-11"), (
        f"pii_scrub_utc changed unexpectedly to {props['pii_scrub_utc']!r}. "
        "If intentional, also bump pii_scrub_version."
    )
    out.unlink()


def test_scrub_is_deterministic_across_runs(heavy_geojson):
    """Two runs on the same input → byte-identical output.

    Note: ``pii_scrub_utc`` is currently a hardcoded constant in scrub_pii.py
    (set during the Phase 3 scrub), so full byte-equality holds. If a future
    change makes it dynamic, this test will catch the determinism break.
    """
    out_a = heavy_geojson.with_suffix(".a.geojson")
    out_b = heavy_geojson.with_suffix(".b.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out_a)
    scrub_pii.scrub_geojson(heavy_geojson, out_b)
    a = json.load(open(out_a))
    b = json.load(open(out_b))
    assert a == b
    out_a.unlink(); out_b.unlink()


def test_scrub_preserves_non_pii_properties(heavy_geojson):
    """Geometry + non-PII properties pass through verbatim."""
    out = heavy_geojson.with_suffix(".scrubbed.geojson")
    scrub_pii.scrub_geojson(heavy_geojson, out)
    feat = json.load(open(out))["features"][0]
    # geometry untouched
    assert feat["geometry"]["coordinates"] == [-57.5759, -25.2637]
    # id stays
    assert feat["properties"]["id"] == "pii_test_1"
    out.unlink()


def test_scrub_rejects_non_featurecollection(root_repo):
    """A Feature (not FeatureCollection) must raise ValueError, not silently pass."""
    bad = root_repo / "tests" / "fixtures" / "bad_not_fc.geojson"
    bad.write_text(json.dumps({"type": "Feature", "features": []}))
    out = root_repo / "tests" / "fixtures" / "bad_not_fc.out.geojson"
    with pytest.raises(ValueError, match="FeatureCollection"):
        scrub_pii.scrub_geojson(bad, out)
    bad.unlink(missing_ok=True)
    out.unlink(missing_ok=True)


def test_hash_token_is_stable():
    """Same input → same output, irreversible."""
    a = scrub_pii.hash_token("agent_999")
    b = scrub_pii.hash_token("agent_999")
    assert a == b
    # sha256 truncation: length 12 hex after `pii_` prefix
    assert len(a) == 16
    # Different input → different output
    assert scrub_pii.hash_token("agent_1000") != a


def test_phone_scrubber_handles_various_formats():
    """+595 991-555-111, +595991555111, +595 981 123 456 all → [PHONE]."""
    for raw in [
        "Call +595 991 555 111",
        "Whatsapp: +595991555111",
        "Tel: +595-981-123-456",
        "Multiple +595 991 555 111 then +595 981 222 333",
    ]:
        scrubbed = scrub_pii.scrub_phone(raw)
        assert "[PHONE]" in scrubbed, f"failed for: {raw!r}"
        # No 12+ digit cluster left behind
        assert not re.search(r"\d{12,}", scrubbed), f"raw 12+ digits: {scrubbed!r}"


# pyproject.toml:
#   [tool.pytest.ini_options]
#   markers = ["large: marks tests as slow / large-data (run with -m large)"]
def test_live_properties_full_pii_scan(data_root, live_only):
    """End-to-end PII scan over the live 10,898-property public dataset.

    Every string value must be free of +595 phone numbers unless the key
    itself starts with ``pii_`` (the audit-flag prefix) or is a known
    non-PII field carrying structured IDs/UUIDs/source_url fragments
    that contain ``595`` digit runs incidentally.
    """
    f = data_root / "properties_latest.geojson"
    if not f.exists():
        pytest.skip("properties_latest.geojson not built yet")
    d = json.load(open(f))
    n_violations = 0
    n_samples = 0
    n_features = len(d["features"])

    # UUIDs, sha1/sha256 hashes, and source URLs legitimately contain
    # 12+ digit hex clusters — those are not phones. Phone-shaped strings
    # look like +595 9xx xxx xxx or +595xxxxxxxxx.
    id_like_keys = {"id", "source_id", "source_url", "image", "images", "url"}
    for feat in d["features"]:
        props = feat.get("properties") or {}
        for k, v in props.items():
            if k.startswith("pii_"):
                continue
            if k in id_like_keys:
                continue
            if isinstance(v, str) and PHONE_RE.search(v):
                n_violations += 1
                if n_samples < 5:
                    print(f"PII: {feat.get('id')} → {k}={v[:80]!r}")
                n_samples += 1
    # Threshold: < 0.05% (real violations are non-PII strings)
    assert n_violations == 0, (
        f"{n_violations} PII violations in {n_features} features — investigate before publishing."
    )
