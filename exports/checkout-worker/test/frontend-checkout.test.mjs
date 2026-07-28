// Static contract tests for the paid-checkout frontend wiring and Pages redirects.

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const workerUrl = 'https://geodata-checkout.weissvanderpol-ivan.workers.dev';
const repoRoot = resolve(import.meta.dirname, '../../..');

async function run() {
    const index = await readFile(resolve(repoRoot, 'exports/web/index.html'), 'utf8');
    const pricing = await readFile(resolve(repoRoot, 'exports/web/pricing.html'), 'utf8');
    const redirects = await readFile(resolve(repoRoot, 'exports/web/_redirects'), 'utf8');

    const checkoutBlock = index.slice(
        index.indexOf('// ========== STRIPE GATED DOWNLOAD =========='),
        index.indexOf('// ========== DOWNLOAD MENU UI =========='),
    );
    assert.ok(checkoutBlock.includes(`window.__STRIPE_CHECKOUT_URL || '${workerUrl}'`));
    assert.ok(checkoutBlock.includes("fetch(window.__STRIPE_CHECKOUT_URL + '/checkout'"));
    assert.ok(checkoutBlock.includes('window.location.assign(payload.url)'));
    assert.ok(!checkoutBlock.includes("window.open(url, '_blank'"));
    console.log('✓ F1 map checkout posts to the real Worker endpoint');

    assert.ok(pricing.includes(`const WORKER_URL = '${workerUrl}'`));
    assert.ok(pricing.includes("fetch(WORKER_URL + '/checkout'"));
    assert.ok(pricing.includes('window.location.assign(data.url)'));
    console.log('✓ F2 pricing checkout posts to the real Worker endpoint');

    assert.ok(!redirects.match(/^\/pricing\s+\/pricing\.html/m));
    assert.ok(redirects.match(/^\/plan\s+\/architect-plan\s+301$/m));
    console.log('✓ F3 Pages redirects cannot loop pricing or plan routes');

    console.log('\nALL FRONTEND CHECKOUT TESTS PASS');
}

run().catch(error => {
    console.error('FAIL', error);
    process.exit(1);
});
