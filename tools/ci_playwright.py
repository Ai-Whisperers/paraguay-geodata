#!/usr/bin/env python3
"""tools/ci_playwright.py

Playwright-based end-to-end test for CI.
Verifies critical user flows work on the live site.

Requires: playwright + chromium browser installed
  pip install playwright
  playwright install chromium
"""
import sys
import asyncio
from playwright.async_api import async_playwright


async def run_tests():
    errors = []
    warnings = []
    console_logs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await ctx.new_page()

        page.on('console', lambda m: (
            console_logs.append(f'[{m.type}] {m.text[:200]}'),
            errors.append(m.text) if m.type == 'error' else None,
        ))
        page.on('pageerror', lambda e: errors.append(f'PAGE ERROR: {str(e)[:300]}'))

        URL = 'https://geodata.paragu-ai.com/'
        print(f'=== Loading {URL} ===')
        try:
            await page.goto(URL, wait_until='domcontentloaded', timeout=30000)
            print('  ✓ Loaded')
        except Exception as e:
            print(f'  ✗ Load failed: {e}')
            return 1

        # Wait for JS to bootstrap (8s for our slowest loaders)
        await page.wait_for_timeout(8000)

        # Test 1: No console errors
        print(f'\n=== ERRORS ({len(errors)}) ===')
        for e in errors[:10]:
            print(f'  ✗ {e[:200]}')
        if errors:
            print('  FAIL: console errors present')

        # Test 2: Stats panel populated
        tiles_stat = await page.locator('#statTiles').text_content()
        listings_stat = await page.locator('#statListings').text_content()
        print(f'\n=== Stats ===')
        print(f'  Tiles: {tiles_stat}, Listings: {listings_stat}')
        if tiles_stat == '—' or listings_stat == '—':
            errors.append('Stats not populated')

        # Test 3: Layer grid populated
        layers = await page.locator('#layerGrid .layer').count()
        print(f'  Layers: {layers}')
        if layers < 17:
            errors.append(f'Only {layers} layers rendered')

        # Test 4: Charts rendered
        for cid in ['chartPriceByDepto', 'chartPropertyTypes', 'chartDeptos']:
            visible = await page.locator(f'#{cid}').is_visible()
            print(f'  Chart {cid}: {"✓" if visible else "✗"}')

        # Test 5: Lang switcher
        lang_count = await page.locator('#langSwitcher option').count()
        print(f'  Lang options: {lang_count}')
        if lang_count != 3:
            errors.append('Lang switcher missing')

        # Test 6: Geocoder
        await page.fill('#geoSearch', 'Asuncion')
        await page.wait_for_timeout(2500)
        geocoder_results = await page.locator('#geoSearchResults .geo-result').count()
        print(f'  Geocoder "Asuncion": {geocoder_results} results')
        if geocoder_results == 0:
            warnings.append('Geocoder returned 0 results')

        # Test 7: Mortgage calc
        await page.fill('#mortValue', '100000')
        await page.wait_for_timeout(500)
        mort_text = await page.locator('#mortResult').text_content()
        print(f'  Mortgage calc: {mort_text[:100]}')

        # Test 8: Mobile view
        mobile_ctx = await browser.new_context(viewport={'width': 375, 'height': 812})
        mobile_page = await mobile_ctx.new_page()
        await mobile_page.goto(URL, wait_until='domcontentloaded', timeout=30000)
        await mobile_page.wait_for_timeout(5000)
        menu_btn = await mobile_page.locator('#sidebarToggle').is_visible()
        filter_btn = await mobile_page.locator('#filterSheetToggle').is_visible()
        print(f'\n=== Mobile ===')
        print(f'  Menu button: {"✓" if menu_btn else "✗"}')
        print(f'  Filter button: {"✓" if filter_btn else "✗"}')
        if not menu_btn or not filter_btn:
            errors.append('Mobile UI broken')

        # Test 9: SW registered
        sw_registered = await page.evaluate('''
            async () => {
                if (!('serviceWorker' in navigator)) return false;
                const reg = await navigator.serviceWorker.getRegistration();
                return !!reg;
            }
        ''')
        print(f'\n=== PWA ===')
        print(f'  SW registered: {sw_registered}')

        # Test 10: Security headers
        r = await ctx.request.get(URL)
        sec_headers = {
            'Content-Security-Policy': r.headers.get('content-security-policy'),
            'Strict-Transport-Security': r.headers.get('strict-transport-security'),
            'X-Frame-Options': r.headers.get('x-frame-options'),
            'X-Content-Type-Options': r.headers.get('x-content-type-options'),
        }
        print(f'\n=== Security Headers ===')
        for k, v in sec_headers.items():
            print(f'  {k}: {"✓ " + v[:60] if v else "✗ MISSING"}')
            if not v:
                errors.append(f'Security header missing: {k}')

        await browser.close()

        # Result
        print(f'\n{"="*60}')
        if errors:
            print(f'FAIL: {len(errors)} errors')
            for e in errors:
                print(f'  - {e[:200]}')
            return 1
        else:
            print(f'PASS ({len(warnings)} warnings)')
            for w in warnings:
                print(f'  ⚠ {w[:200]}')
            return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(run_tests()))