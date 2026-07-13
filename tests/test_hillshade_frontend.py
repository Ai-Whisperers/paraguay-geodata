"""Browser regression tests for national and priority hillshade integration."""

import contextlib
import http.server
import threading
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


WEB_ROOT = Path(__file__).resolve().parents[1] / "exports" / "web"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class HillshadeFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(WEB_ROOT), **kwargs
        )
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)
        self.page.wait_for_function(
            "() => window.PROFESSION_PRESETS && window._paraguayPriorityHillshades",
            timeout=60_000,
        )

    def tearDown(self):
        with contextlib.suppress(Exception):
            self.page.close()

    def test_every_profession_preset_references_real_layers(self):
        invalid = self.page.evaluate(
            """() => Object.entries(window.PROFESSION_PRESETS)
                .flatMap(([preset, cfg]) => Array.isArray(cfg.layers)
                    ? cfg.layers.filter(id => !(id in layerState)).map(id => `${preset}:${id}`)
                    : [])"""
        )
        self.assertEqual([], invalid)

    def test_tourist_preset_loads_priority_hillshade_at_city_zoom(self):
        self.page.evaluate(
            """() => {
                window.applyPreset('tourist');
                map.setView([-25.28, -57.63], 13, { animate: false });
            }"""
        )
        self.page.wait_for_function(
            "() => Object.hasOwn(window._paraguayPriorityHillshades, 'asu_centro')",
            timeout=15_000,
        )
        state = self.page.evaluate(
            """() => ({
                active: layerState.hillshade_priority.active,
                inMap: map.hasLayer(LAYER_GROUPS.hillshade_priority[0]),
                count: LAYER_GROUPS.hillshade_priority[0].getLayers().length,
            })"""
        )
        self.assertTrue(state["active"])
        self.assertTrue(state["inMap"])
        self.assertGreaterEqual(state["count"], 1)

    def test_national_hillshade_registers_four_regional_overlays(self):
        self.page.wait_for_function(
            "() => window.__hillshadeGroup && window.__hillshadeGroup.getLayers().length === 4",
            timeout=15_000,
        )
        self.assertEqual(
            4,
            self.page.evaluate("() => window.__hillshadeGroup.getLayers().length"),
        )


if __name__ == "__main__":
    unittest.main()
