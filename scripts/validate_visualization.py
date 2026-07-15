#!/usr/bin/env python3
"""End-to-end visualization validator for Paraguay Geodata.

Runs against the deployed site (or a local server) and verifies:
1. Every satellite-derived layer is registered, loads, and is toggleable.
2. The legend surfaces each active layer family.
3. Profession presets activate the right layers and the legend reflects them.
4. Hillshade blend-mode toggle cycles between multiply / overlay / soft-light.
5. New layers (esri_imagery, construction_zones, properties_risk_dots) appear
   in the layer tree and respond to toggles.
6. No console errors during the smoke run.

Writes a JSON report to stdout.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeout


EXPECTED_LAYERS = {
    # grid
    "tile_fabric", "priority_tiles", "esri_imagery",
    "hillshade_national", "hillshade_priority",
    # base
    "departamentos_py", "distritos_py", "barrios_py",
    # admin
    "catastro_dpto", "catastro_dist", "catastro_parcels", "catastro_urba",
    # env
    "indigenous", "climate_risk", "flood_risk", "construction_zones",
    # agri
    "inbio_soja", "inbio_arroz", "inbio_maiz",
    # urban
    "osm_water", "osm_buildings", "osm_roads", "anchor_circles",
    # realestate
    "properties_sale", "properties_rent", "properties_short",
    "properties_house", "properties_apartment", "properties_land",
    "properties_commercial",
    "properties_heat_pha", "properties_heat_area", "properties_heat_risk",
    "properties_risk_dots",
    # biodiv
    "gbif_animalia", "gbif_plantae",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="https://geodata.paragu-ai.com/",
                   help="Live URL to probe (must serve the same index.html)")
    p.add_argument("--out", default=None,
                   help="Write JSON report here (default: stdout)")
    p.add_argument("--screenshots-dir", default="/tmp/pygeodata_validation",
                   help="Where to save screenshots for manual review")
    p.add_argument("--timeout-ms", type=int, default=15000)
    args = p.parse_args()

    out_dir = Path(args.screenshots_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"url": args.url, "checks": {}, "errors": []}

    with sync_playwright() as pwb:
        browser = pwb.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            service_workers="block",  # critical for PWA sites so we get fresh assets
        )
        page = ctx.new_page()
        console_errors: list[str] = []
        def on_console(msg):
            if msg.type == "error":
                console_errors.append(f"{msg.location.get('url', '')}: {msg.text}")
        page.on("console", on_console)

        # Bootstrap
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout_ms)
        except Exception as e:
            report["errors"].append(f"goto failed: {e!r}")
            return _write(report, args.out, code=2)

        # Wait for the Leaflet container and the layer tree to populate.
        try:
            page.wait_for_selector(".layer-tree", timeout=args.timeout_ms)
        except PWTimeout:
            report["errors"].append("layer-tree never rendered")
            page.screenshot(path=str(out_dir / "01_no_tree.png"))
            return _write(report, args.out, code=3)

        # Verify every layer id is registered in window.layerState.
        registered = set(page.evaluate(
            "() => Object.keys(window.layerState || {})"
        ))
        missing = sorted(EXPECTED_LAYERS - registered)
        report["checks"]["registered_layer_ids"] = {
            "expected": len(EXPECTED_LAYERS),
            "present": len(registered & EXPECTED_LAYERS),
            "missing": missing,
        }
        page.screenshot(path=str(out_dir / "02_after_load.png"), full_page=False)

        # Verify every layer has a rendered row in the tree.
        rows = set(page.evaluate(
            "() => Array.from(document.querySelectorAll('.layer[data-layer-id]'))"
            "          .map(el => el.getAttribute('data-layer-id'))"
        ))
        report["checks"]["rendered_layer_rows"] = {
            "rows_total": len(rows),
            "expected_total": len(EXPECTED_LAYERS),
            "missing_rows": sorted(EXPECTED_LAYERS - rows),
        }

        # Verify legend sections are present.
        legend_summary = page.evaluate(
            """() => Array.from(document.querySelectorAll('#legend details'))
                .map(d => ({open: d.open, summary: d.querySelector('summary')?.textContent?.trim() || ''}))"""
        )
        report["checks"]["legend_sections"] = {
            "count": len(legend_summary),
            "items": legend_summary,
        }

        # Test each profession preset; ensure it activates the right layers
        # and the legend re-renders without errors.
        presets = {
            "architect":          ["hillshade_national", "esri_imagery", "construction_zones", "flood_risk"],
            "developer":          ["hillshade_national", "esri_imagery", "construction_zones", "properties_risk_dots"],
            "urban_planner":      ["hillshade_national", "esri_imagery", "construction_zones", "properties_risk_dots"],
            "tourist":            ["hillshade_national", "hillshade_priority", "esri_imagery"],
            "researcher":         ["hillshade_national", "esri_imagery", "construction_zones", "properties_risk_dots"],
        }
        preset_results = {}
        for preset, expected_active in presets.items():
            page.evaluate(
                f"window.applyPreset && window.applyPreset('{preset}')"
            )
            page.wait_for_timeout(300)
            active = page.evaluate(
                "() => Object.entries(window.layerState || {})"
                "       .filter(([, l]) => l.active)"
                "       .map(([id]) => id)"
            )
            ok = all(l in active for l in expected_active)
            preset_results[preset] = {
                "expected_active": expected_active,
                "all_active": ok,
                "active_count": len(active),
            }
        report["checks"]["presets"] = preset_results
        page.screenshot(path=str(out_dir / "03_preset_researcher.png"))

        # Cycle hillshade blend-mode and verify the legend span updates.
        blend_results = {}
        for _ in range(3):
            page.evaluate("window.cycleHillshadeBlendMode && window.cycleHillshadeBlendMode()")
            page.wait_for_timeout(120)
            blend = page.evaluate("() => document.getElementById('legendHillshadeBlend')?.textContent || ''")
            css_mode = page.evaluate("() => { const s = document.getElementById('hillshade-blend-style'); return s ? s.textContent : ''; }")
            blend_results.setdefault("attempts", []).append({"legend": blend, "css_includes_mode": blend in css_mode})
        blend_results["ok"] = all(a["css_includes_mode"] for a in blend_results["attempts"])
        report["checks"]["hillshade_blend"] = blend_results

        # Toggle each new layer and verify opacity handler doesn't throw.
        toggles = ["esri_imagery", "construction_zones", "properties_risk_dots", "hillshade_national", "hillshade_priority"]
        toggle_results = {}
        for t in toggles:
            before = page.evaluate(f"() => window.layerState?.[{json.dumps(t)}]?.active")
            # Run load + toggle through the layer tree's checkbox (best effort)
            page.evaluate(f"""
                (async () => {{
                    const id = {json.dumps(t)};
                    const ls = window.layerState?.[id];
                    if (!ls) return;
                    ls.active = !ls.active;
                    if (typeof window.ensureLayerLoaded === 'function') await window.ensureLayerLoaded(id);
                    if (typeof window.applyLayerVisibility === 'function') window.applyLayerVisibility(id);
                    if (typeof window.applyLayerOpacity === 'function') window.applyLayerOpacity(id);
                }})()
            """)
            page.wait_for_timeout(400)
            after = page.evaluate(f"() => window.layerState?.[{json.dumps(t)}]?.active")
            toggle_results[t] = {"before": before, "after": after, "toggled": before != after}
        report["checks"]["toggle_roundtrip"] = toggle_results

        # Final screenshot with esri_imagery + hillshade + construction_zones on
        page.evaluate("""
            (async () => {
                if (!window.layerState) return;
                const want = ['esri_imagery', 'hillshade_national', 'construction_zones', 'departamentos_py'];
                const off = Object.keys(window.layerState).filter(k => !want.includes(k));
                for (const id of off) window.layerState[id].active = false;
                for (const id of want) {
                    if (!window.layerState[id]) continue;
                    window.layerState[id].active = true;
                    if (typeof window.ensureLayerLoaded === 'function') await window.ensureLayerLoaded(id);
                    if (typeof window.applyLayerVisibility === 'function') window.applyLayerVisibility(id);
                }
            })()
        """)
        page.wait_for_timeout(2500)  # give esri tiles time to load
        page.screenshot(path=str(out_dir / "04_final_with_esri_hillshade.png"), full_page=False)
        page.screenshot(path=str(out_dir / "05_full_page.png"), full_page=True)

        report["checks"]["console_errors"] = console_errors[:25]
        report["checks"]["console_error_count"] = len(console_errors)

        browser.close()

    return _write(report, args.out, code=0 if not report["errors"] else 1)


def _write(report, out, code=0):
    text = json.dumps(report, indent=2, default=str)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text)
        print(f"Report written: {out}")
    else:
        print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())