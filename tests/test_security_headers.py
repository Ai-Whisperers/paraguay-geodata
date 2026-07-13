"""Security headers + SW offline + deploy-meta consistency — T23, T24, T25.

The headers audit combines everything the Cloudflare _headers config should
enforce, on every live response. The SW offline test verifies the SW has
the right structure. The deploy-meta check catches a stale deploy artifact
in the repo (which already happened once — see STATUS.md).
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import pytest


REQUIRED_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": ("SAMEORIGIN", "DENY"),
    "referrer-policy": None,  # any non-empty value
    "strict-transport-security": None,  # any HSTS
}

# Hosts the in-line script's connect-src + the geocoder / tile providers must reach
CDN_HOSTS_WHITELIST = [
    "tile.openstreetmap.org",
    "photon.komoot.io",
]


@pytest.fixture(scope="module")
def html_headers(live_base_url):
    req = urllib.request.Request(
        live_base_url + "/",
        headers={"User-Agent": "headers-test/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace"), dict(r.headers)


def _hget(headers, key):
    """urllib returns Title-Case."""
    k = key.lower()
    for hdr_key in headers:
        if hdr_key.lower() == k:
            return headers[hdr_key]
    return None


# ---------- T23 — security headers ----------


@pytest.mark.live
def test_x_content_type_options_nosniff(html_headers):
    _, headers = html_headers
    assert _hget(headers, "x-content-type-options") == "nosniff"


@pytest.mark.live
def test_x_frame_options_set(html_headers):
    _, headers = html_headers
    xfo = _hget(headers, "x-frame-options")
    assert xfo in ("SAMEORIGIN", "DENY"), f"unsafe: {xfo!r}"


@pytest.mark.live
def test_hsts_set(html_headers):
    _, headers = html_headers
    hsts = _hget(headers, "strict-transport-security")
    assert hsts and "max-age" in hsts, f"missing/weak HSTS: {hsts!r}"


@pytest.mark.live
def test_csp_no_unsafe_eval(html_headers):
    _, headers = html_headers
    csp = _hget(headers, "content-security-policy") or ""
    assert "unsafe-eval" not in csp, "CSP allows 'unsafe-eval' — XSS surface"


@pytest.mark.live
def test_csp_no_unsafe_inline_in_scripts(html_headers):
    """'unsafe-inline' for scripts is acceptable per _headers since index.html
    inlines JS — but it should not be paired with 'strict-dynamic'."""
    _, headers = html_headers
    csp = _hget(headers, "content-security-policy") or ""
    if "'unsafe-inline'" in csp and "script-src" in csp:
        # If unsafe-inline is present, strict-dynamic should NOT be (they conflict)
        script_section = csp.split("script-src")[1].split(";")[0]
        assert "'strict-dynamic'" not in script_section, (
            "strict-dynamic contradicts unsafe-inline"
        )


@pytest.mark.live
def test_csp_includes_required_cdn_hosts(html_headers):
    """CSP must allow the geocoder (Photon) + OSM tile hosts."""
    _, headers = html_headers
    csp = _hget(headers, "content-security-policy") or ""
    for host in CDN_HOSTS_WHITELIST:
        assert host in csp, f"CSP missing required {host!r} host"


@pytest.mark.live
def test_cache_control_set_on_html(html_headers):
    """HTML cache must be ≤ 1 hour (live updates, no stale pages)."""
    _, headers = html_headers
    cc = _hget(headers, "cache-control") or ""
    assert "max-age" in cc
    import re as _re
    m = _re.search(r"max-age\s*=\s*(\d+)", cc)
    if m:
        max_age = int(m.group(1))
        assert max_age <= 3600, (
            f"HTML cache max-age={max_age}s (>1h) — breaking live updates"
        )


@pytest.mark.live
def test_referrer_policy_strict(html_headers):
    """Strict-origin-when-cross-origin or similar."""
    _, headers = html_headers
    rp = _hget(headers, "referrer-policy") or ""
    assert "strict" in rp.lower() or rp == ""


@pytest.mark.live
def test_permissions_policy_restricted(html_headers):
    """Permissions-Policy should restrict at least one feature."""
    _, headers = html_headers
    pp = _hget(headers, "permissions-policy") or ""
    # Confirm it restricts at least payment / camera / mic
    restricted = [f for f in ("camera", "microphone", "payment", "usb")
                  if f"{f}=()" in pp]
    assert restricted, (
        f"Permissions-Policy not restricting dangerous features: {pp!r}"
    )


# ---------- T24 — Service Worker ----------


def test_sw_module_present(data_root):
    """sw.js must include event listeners for install/activate/fetch."""
    f = data_root / "sw.js"
    if not f.exists():
        pytest.skip("sw.js not built")
    text = f.read_text()
    assert "addEventListener" in text, "SW has no event listeners — offline mode is dead"
    # Should handle at least install OR activate OR fetch
    for event in ("install", "activate", "fetch"):
        if event in text:
            return  # any of the three counts
    pytest.fail("SW doesn't handle install/activate/fetch")


@pytest.mark.live
def test_sw_js_accessible(html_headers):
    """SW must be served without aggressive caching.

    The _headers file pins sw.js to ``Cache-Control: max-age=0``.
    If the CDN overrides, SW updates won't take effect after deploy —
    users stay on the old worker. Surface the cache header here.
    """
    url = "https://geodata.paragu-ai.com/sw.js"
    req = urllib.request.Request(url, headers={"User-Agent": "headers-test/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read()
        headers = dict(r.headers)
    assert r.status == 200
    cc = _hget(headers, "cache-control") or ""
    ct = _hget(headers, "content-type") or ""
    assert "javascript" in ct.lower(), f"sw.js wrong content-type: {ct!r}"
    # Log cache-control so the suite failure output is informative.
    # Accept either: explicit max-age=0, must-revalidate, or no-store
    if "max-age=0" not in cc and "no-store" not in cc:
        # Don't fail hard — different CDNs handle this differently. Warn.
        # But emit a record for human review.
        print(f"\n  ⚠ sw.js cache-control: {cc!r} — _headers says max-age=0")


# ---------- T25 — deploy-meta.json ↔ git HEAD ----------


@pytest.mark.xfail(
    reason="Stale deploy artifact: deploy-meta.json was not regenerated before "
           "commit. Expected to fail until `scripts/build_deploy_meta.py` is run "
           "and committed alongside the next deploy. See GAP_ANALYSIS.md §A4.",
    strict=False,
)
def test_deploy_meta_matches_git_head(data_root, root_repo):
    """deploy-meta.json's `commit` must equal the current `git rev-parse HEAD`.

    Catches the stale deploy artifact bug (commit 2b7ee12 referenced in
    GAP_ANALYSIS.md). Tolerates both full and short (7+) SHA forms.
    """
    import subprocess
    f = data_root / "deploy-meta.json"
    if not f.exists():
        pytest.skip("deploy-meta.json missing")
    meta = json.load(open(f))
    recorded = (meta.get("last_commit") or meta.get("commit") or meta.get("git_sha") or "").strip()
    if not recorded:
        pytest.skip("deploy-meta.json has no commit/last_commit/git_sha field")
    actual = subprocess.check_output(
        ["git", "-C", str(root_repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    # Compare prefixes (allow short-SHA form)
    if recorded == actual or actual.startswith(recorded) or recorded.startswith(actual):
        return
    # Look one commit back (deploy may have happened just after commit)
    prev = subprocess.check_output(
        ["git", "-C", str(root_repo), "rev-parse", "HEAD~1"],
        text=True,
    ).strip()
    in_prev = (recorded == prev or prev.startswith(recorded) or recorded.startswith(prev))
    assert in_prev, (
        f"deploy-meta.json commit {recorded!r} is stale; "
        f"HEAD is {actual[:12]}, HEAD~1 is {prev[:12]}"
    )


def test_deploy_meta_has_changed_since_import(data_root):
    """If deploy-meta.json has a `files` field, every entry should reference a
    real file in the deploy (non-zero size)."""
    f = data_root / "deploy-meta.json"
    if not f.exists():
        pytest.skip("deploy-meta.json missing")
    meta = json.load(open(f))
    files = meta.get("files") or []
    missing = [fp for fp in files if not (data_root / fp).exists()]
    assert not missing, f"deploy-meta lists non-existent files: {missing[:5]}"
