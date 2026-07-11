// Playwright headless E2E test
// Run: npx playwright test (after npm init playwright)
// Or use the bundled chromium-headless-shell via raw DevTools Protocol

const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();

    const errors = [];
    const warnings = [];
    page.on('console', m => {
        if (m.type() === 'error') errors.push(m.text());
        if (m.type() === 'warning') warnings.push(m.text());
    });
    page.on('pageerror', e => errors.push(`PAGE ERROR: ${e.message}`));

    console.log('=== Loading https://geodata.paragu-ai.com/ ===');
    await page.goto('https://geodata.paragu-ai.com/', { waitUntil: 'networkidle', timeout: 60000 });
    console.log('Title:', await page.title());

    await page.waitForTimeout(8000);

    // 1. Stats panel populated
    const tilesStat = await page.locator('#statTiles').textContent();
    const listingsStat = await page.locator('#statListings').textContent();
    console.log(`Tiles stat: ${tilesStat}, Listings stat: ${listingsStat}`);
    if (tilesStat === '—' || listingsStat === '—') {
        errors.push(`Stats not populated: tiles=${tilesStat}, listings=${listingsStat}`);
    }

    // 2. Layer grid populated
    const layerCount = await page.locator('#layerGrid .layer').count();
    console.log(`Layers rendered: ${layerCount}`);
    if (layerCount < 17) errors.push(`Only ${layerCount} layers rendered (expected ≥17)`);

    // 3. Market signals populated
    const marketSignals = await page.locator('#marketSignals').textContent();
    console.log(`Market signals length: ${marketSignals.length} chars`);
    if (marketSignals.length < 50) errors.push(`Market signals empty/short`);

    // 4. Charts rendered
    const priceChart = await page.locator('#chartPriceByDepto').isVisible();
    const typeChart = await page.locator('#chartPropertyTypes').isVisible();
    const deptoChart = await page.locator('#chartDeptos').isVisible();
    console.log(`Charts visible: price=${priceChart}, type=${typeChart}, depto=${deptoChart}`);
    if (!priceChart || !typeChart || !deptoChart) errors.push('Some charts not visible');

    // 5. Lang switcher visible
    const langOptions = await page.locator('#langSwitcher option').count();
    console.log(`Lang options: ${langOptions}`);
    if (langOptions !== 3) errors.push(`Lang switcher wrong: ${langOptions} options (expected 3)`);

    // 6. Geocoder works
    await page.fill('#geoSearch', 'Asuncion');
    await page.waitForTimeout(2500);
    const geocoderResults = await page.locator('#geoSearchResults .geo-result').count();
    console.log(`Geocoder results for "Asuncion": ${geocoderResults}`);
    if (geocoderResults === 0) errors.push('Geocoder returned 0 results');

    // 7. Map controls visible
    const shareBtn = await page.locator('button:has-text("Share view")').isVisible();
    const embedBtn = await page.locator('button:has-text("Embed")').isVisible();
    const locateBtn = await page.locator('button:has-text("Locate")').isVisible();
    const csvBtn = await page.locator('button:has-text("CSV")').isVisible();
    console.log(`Map buttons: share=${shareBtn}, embed=${embedBtn}, locate=${locateBtn}, csv=${csvBtn}`);

    // 8. Property popup on marker click
    // First need to enable property layer and zoom
    // Skip - requires complex interaction

    // 9. Mobile view
    const mobileCtx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const mobilePage = await mobileCtx.newPage();
    await mobilePage.goto('https://geodata.paragu-ai.com/', { waitUntil: 'networkidle', timeout: 30000 });
    await mobilePage.waitForTimeout(5000);
    const menuBtn = await mobilePage.locator('#sidebarToggle').isVisible();
    const filterBtn = await mobilePage.locator('#filterSheetToggle').isVisible();
    console.log(`Mobile: menuBtn=${menuBtn}, filterBtn=${filterBtn}`);
    if (!menuBtn) errors.push('Mobile menu button not visible');
    if (!filterBtn) errors.push('Mobile filter button not visible');

    // 10. SW registered
    const swRegistered = await page.evaluate(async () => {
        if (!('serviceWorker' in navigator)) return false;
        const reg = await navigator.serviceWorker.getRegistration();
        return !!reg;
    });
    console.log(`SW registered: ${swRegistered}`);
    if (!swRegistered) errors.push('Service Worker not registered');

    // 11. Errors check
    console.log(`\n=== ERRORS: ${errors.length} ===`);
    for (const e of errors) console.log(`  ✗ ${e}`);

    console.log(`\n=== WARNINGS: ${warnings.length} ===`);
    for (const w of warnings.slice(0, 5)) console.log(`  ⚠ ${w}`);

    await browser.close();

    if (errors.length > 0) {
        console.log('\nFAIL');
        process.exit(1);
    }
    console.log('\nPASS');
})();