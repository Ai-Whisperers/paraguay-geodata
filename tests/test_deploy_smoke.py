"""Deploy smoke test — T5 from the audit matrix.

After a wrangler deploy, this is the test that proves the site is live.
Run with::

    PY_GEO_BASE_URL=https://afe4b2a3.paraguay-geodata.pages.dev \
      python3 -m pytest tests/test_deploy_smoke.py -v

Or against the production base URL by default. Each test gates the
deploy with minimum size + content checks, so a broken Cloudflare
deployment is caught within ~10 seconds instead of "wait for the user
to ping us".
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

# Min sizes for "the deploy is alive" check:
MIN_HTML_BYTES = 50_000      # the index.html ships ~264 KB
MIN_PROPS_BYTES = 1_000_000  # properties_latest.geojson ~14 MB
MIN_GBIF_BYTES = 5_000       # gbif_paraguay.geojson ~94 KB
SW_MIN_BYTES = 500           # service worker


def _fetch(url, timeout=10):
    """HEAD-style probe but always GET so we can size-check the body."""
    req = urllib.request.Request(url, headers={"User-Agent": "deploy-smoke/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""


def _hget(headers, key):
    """Case-insensitive header lookup (urllib returns Title-Case)."""
    k = key.lower()
    for hdr_key in headers:
        if hdr_key.lower() == k:
            return headers[hdr_key]
    return None


@pytest.fixture(scope="module")
def base_url(live_base_url):
    return live_base_url


# ---------- HTML ----------


@pytest.mark.live
def test_index_html_returns_200_with_min_size(base_url, live_only):
    """The HTML is the most user-facing artifact. If this is broken, the
    whole deploy is a no-go."""
    status, _, body = _fetch(base_url + "/")
    assert status == 200, f"GET / → {status}"
    assert len(body) >= MIN_HTML_BYTES, f"only {len(body)} bytes (expected ≥{MIN_HTML_BYTES})"
    text = body.decode("utf-8", errors="replace")
    assert "<div id=\"map\"" in text, "no #map div in HTML"


@pytest.mark.live
def test_index_html_has_layer_state_keys(base_url, live_only):
    """index.html must declare layerState with at least 21 unique layer ids."""
    status, _, body = _fetch(base_url + "/")
    assert status == 200
    text = body.decode("utf-8", errors="replace")
    required_layers = {
        "tile_fabric", "priority_tiles", "hillshade_national",
        "departamentos_py", "catastro_dpto", "inbio_soja",
        "properties_sale", "properties_rent",
        "osm_roads", "osm_water", "gbif_animalia",
    }
    missing = required_layers - set(_extract_layer_ids(text))
    assert not missing, f"layer state missing in HTML: {missing}"


def _extract_layer_ids(html):
    """Extract layer ids from the layerState const inside index.html."""
    import re
    return re.findall(r"^\s+(\w+):\s*\{", html, re.MULTILINE)


# ---------- GeoJSON data ----------

@pytest.mark.live
def test_properties_latest_is_featurecollection_with_min_count(base_url, live_only):
    status, _, body = _fetch(base_url + "/data/properties_latest.geojson")
    assert status == 200
    assert len(body) >= MIN_PROPS_BYTES, f"only {len(body)} bytes (expected ≥{MIN_PROPS_BYTES})"
    d = json.loads(body)
    assert d.get("type") == "FeatureCollection"
    assert len(d["features"]) >= 1000


@pytest.mark.live
def test_gbif_geojson_nonempty(base_url, live_only):
    status, _, body = _fetch(base_url + "/data/gbif_paraguay.geojson")
    assert status == 200
    assert len(body) >= MIN_GBIF_BYTES
    d = json.loads(body)
    assert len(d["features"]) >= 100


@pytest.mark.live
def test_priority_tiles_json_nonempty(base_url, live_only):
    status, _, body = _fetch(base_url + "/data/priority_tiles.json")
    assert status == 200
    d = json.loads(body)
    tiles = d.get("tiles") or d.get("priority_tiles") or d
    if isinstance(tiles, list):
        assert len(tiles) >= 30, f"only {len(tiles)} priority tiles"


@pytest.mark.live
def test_tile_index_present_and_has_thousands(base_url, live_only):
    status, _, body = _fetch(base_url + "/data/tile_index.json")
    assert status == 200
    d = json.loads(body)
    tiles = d.get("tiles") or d
    if isinstance(tiles, list):
        assert 1000 <= len(tiles) <= 10000, f"unexpected tile count {len(tiles)}"


# ---------- Service worker ----------

@pytest.mark.live
def test_sw_accessible(base_url, live_only):
    status, _, body = _fetch(base_url + "/sw.js")
    assert status == 200, f"GET /sw.js → {status}"
    assert len(body) >= SW_MIN_BYTES


# ---------- Security headers ----------

@pytest.mark.live
def test_x_content_type_options_nosniff(base_url, live_only):
    status, headers, _ = _fetch(base_url + "/")
    assert status == 200
    assert _hget(headers, "x-content-type-options") == "nosniff", (
        f"missing/wrong: {_hget(headers, 'x-content-type-options')!r}"
    )


@pytest.mark.live
def test_x_frame_options_set(base_url, live_only):
    status, headers, _ = _fetch(base_url + "/")
    assert status == 200
    xfo = _hget(headers, "x-frame-options")
    assert xfo in ("SAMEORIGIN", "DENY"), f"unsafe: {xfo!r}"


@pytest.mark.live
def test_no_unsafe_eval_in_csp(base_url, live_only):
    """`unsafe-eval` allows arbitrary JS execution. Reject it."""
    status, headers, _ = _fetch(base_url + "/")
    assert status == 200
    csp = _hget(headers, "content-security-policy") or ""
    assert "unsafe-eval" not in csp, "CSP allows 'unsafe-eval'"


# ---------- Static helpers ----------

@pytest.mark.live
def test_favicon_exists(base_url, live_only):
    status, _, _ = _fetch(base_url + "/favicon.svg")
    assert status == 200


@pytest.mark.live
def test_mapa_html_exists(base_url, live_only):
    status, _, _ = _fetch(base_url + "/mapa.html")
    assert status == 200


@pytest.mark.live
def test_datos_html_exists(base_url, live_only):
    status, _, _ = _fetch(base_url + "/datos.html")
    assert status == 200


# ---------- Aggregate ----------

@pytest.mark.live
def test_every_documented_endpoint_at_least_alive(base_url, live_only):
    """Endpoints that PROVENANCE.md / STATUS.md say are live must be live.
    A missing endpoint = a broken deploy.
    """
    endpoints = [
        "/",
        "/manifest.webmanifest",
        "/sw.js",
        "/data/properties_latest.geojson",
        "/data/priority_tiles.json",
        "/data/tile_index.json",
        "/data/gbif_paraguay.geojson",
        "/data/bcp_snapshot.json",
        "/data/nasa_power_asuncion.json",
        "/data/inbio_zafra_2025_2026.json",
        "/data/data_freshness.json",
        "/data/environment_meta.json",
        "/data/admin/catastro_dpto.geojson",
        "/data/admin/catastro_dist.geojson",
        "/data/water.geojson",
        "/data/buildings_asuncion.geojson",
        "/data/roads.geojson",
        "/data/ml/fair_price_model.json",
    ]
    dead = []
    for ep in endpoints:
        status, _, _ = _fetch(base_url + ep)
        if status != 200:
            dead.append((ep, status))
    assert not dead, f"dead endpoints: {dead}"
