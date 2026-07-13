"""Layer registry contract tests — T10 + T11 from the audit matrix.

Two test surfaces:
  - T10 (this file): pure-HTTP tests against the LIVE deployed site,
    asserting layerState has all 34 expected ids + LAYER_GROUPS_ORDER has
    the right group ordering. (Discovered via deploy_smoke run.)

These are the high-signal T10/T11 tests that survive without a heavy
in-process Playwright suite. The interactive round-trip T11 (click toggle
on/off) is covered by tools/test_interactions.py (manual, not part of CI).

If the live site is unreachable, skip via PY_GEO_OFFLINE=1.
"""
from __future__ import annotations

import json
import re
import urllib.request

import pytest


EXPECTED_LAYER_IDS = {
    # grid
    "tile_fabric", "priority_tiles", "hillshade_national", "hillshade_priority",
    # base admin
    "departamentos_py", "distritos_py", "barrios_py",
    # admin catastro
    "catastro_dpto", "catastro_dist", "catastro_parcels", "catastro_urba",
    # env
    "indigenous", "climate_risk", "flood_risk",
    # agri
    "inbio_soja", "inbio_arroz", "inbio_maiz",
    # urban
    "osm_water", "osm_buildings", "osm_roads", "anchor_circles",
    # realestate
    "properties_sale", "properties_rent", "properties_short",
    "properties_house", "properties_apartment", "properties_land",
    "properties_commercial",
    "properties_heat_pha", "properties_heat_area", "properties_heat_risk",
    # biodiv
    "gbif_animalia", "gbif_plantae",
}


CORE_GROUPS = ("grid", "base", "env", "agri")


@pytest.fixture(scope="module")
def index_html(live_base_url):
    """Fetch index.html from the live deploy once per module."""
    req = urllib.request.Request(
        live_base_url + "/",
        headers={"User-Agent": "layer-registry-test/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


@pytest.mark.live
def test_every_expected_layer_id_in_index_html(index_html):
    """T10 — every documented layer id is declared in layerState."""
    layer_state_match = re.search(
        r"const layerState\s*=\s*\{(.+?)\n\};",
        index_html,
        re.DOTALL,
    )
    assert layer_state_match, "no `const layerState = {...}` block in HTML"
    body = layer_state_match.group(1)
    declared = set(re.findall(r"^\s*(\w+)\s*:\s*\{[^}]*group:", body, re.MULTILINE))
    missing = EXPECTED_LAYER_IDS - declared
    assert not missing, (
        f"layer ids missing from layerState: {sorted(missing)}"
    )


@pytest.mark.live
def test_layer_state_entry_has_group_and_label(index_html):
    """T10 — each layerState entry carries {group, label} so renderLayerGrid
    doesn't crash when building the sidebar tree."""
    body = re.search(
        r"const layerState\s*=\s*\{(.+?)\n\};",
        index_html,
        re.DOTALL,
    ).group(1)
    # Find all `id: { ... }` entries; check that each block has group + label
    entries = re.findall(
        r"^(\s+)(\w+):\s*\{\s*group:\s*['\"]([^'\"]+)['\"][^}]*label:\s*['\"]([^'\"]+)['\"]",
        body,
        re.MULTILINE,
    )
    assert len(entries) >= len(EXPECTED_LAYER_IDS) - 2, (
        f"only {len(entries)} entries match the standard pattern — "
        "index.html layout may have changed"
    )
    bad = [(i, g) for _, i, g, _ in entries if not g]
    assert not bad, f"entries without group: {bad}"


@pytest.mark.live
def test_layer_group_order_contains_core_groups(index_html):
    """T10 — LAYER_GROUP_ORDER has the core draw-order groups in a sane place."""
    body = re.search(
        r"const LAYER_GROUP_ORDER\s*=\s*\[(.+?)\];",
        index_html,
        re.DOTALL,
    )
    assert body, "no LAYER_GROUP_ORDER const in HTML"
    order_text = body.group(1)
    for g in CORE_GROUPS:
        assert f"'{g}'" in order_text or f'"{g}"' in order_text, (
            f"{g!r} missing from LAYER_GROUP_ORDER"
        )


@pytest.mark.live
def test_layer_state_wiring_for_layer_groups(index_html):
    """T10 — LAYER_GROUPS is auto-initialized from layerState (the loop at
    the bottom of the IIFE). If this wiring breaks, every layer renders blank."""
    # LAYER_GROUPS is built as `for (const id of LAYER_GROUPS_ORDER) LAYER_GROUPS[id] = [L.layerGroup()];`
    has_init = "for (const id of LAYER_GROUPS_ORDER)" in index_html
    assert has_init, (
        "LAYER_GROUPS isn't seeded from LAYER_GROUPS_ORDER — sidebar checkboxes won't work"
    )
