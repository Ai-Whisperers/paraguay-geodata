// Self-contained Node test for the worker's HMAC sign/verify + handlers.
// We extract the relevant pure-function code (no stripe import) so we can test
// it without bundling wrangler / wrangler's edge-runtime stubs.
//
// Run: node test/handler.test.mjs

import assert from 'node:assert/strict';

// ---- copy of signToken / verifyToken from worker.js (kept identical) ----
async function importHmacKey(secret) {
    const enc = new TextEncoder();
    return crypto.subtle.importKey(
        'raw', enc.encode(secret),
        { name: 'HMAC', hash: 'SHA-256' },
        false, ['sign', 'verify']
    );
}
async function signToken(secret, payload) {
    const key = await importHmacKey(secret);
    const enc = new TextEncoder();
    const json = JSON.stringify(payload);
    const sig = await crypto.subtle.sign('HMAC', key, enc.encode(json));
    const b64 = btoa(String.fromCharCode(...new Uint8Array(sig)));
    const b64url = b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    return b64url + '.' + btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
async function verifyToken(secret, token) {
    if (!token || typeof token !== 'string') return null;
    const [sigB64, payloadB64] = token.split('.');
    if (!sigB64 || !payloadB64) return null;
    try {
        const json = atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/'));
        const key = await importHmacKey(secret);
        const enc = new TextEncoder();
        const sigBytes = Uint8Array.from(
            atob(sigB64.replace(/-/g, '+').replace(/_/g, '/')),
            c => c.charCodeAt(0)
        );
        const ok = await crypto.subtle.verify('HMAC', key, sigBytes, enc.encode(json));
        if (!ok) return null;
        const payload = JSON.parse(json);
        if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
        return payload;
    } catch { return null; }
}

// ---- copy of CATALOG + json helpers ----
const CATALOG = {
    geojson_all: { priceEnv: 'STRIPE_PRICE_GEOJSON_ONE_TIME', name: 'g', format: 'geojson', downloadKey: 'properties_latest.geojson' },
    dxf_all:     { priceEnv: 'STRIPE_PRICE_DXF_ONE_TIME',     name: 'd', format: 'dxf',     downloadKey: 'properties_latest.dxf' },
    sub_yearly:  { priceEnv: 'STRIPE_PRICE_SUB_YEARLY',        name: 's', format: 'both',    downloadKey: 'subscription' },
};

// ---- tests ----
async function run() {
    const SECRET = 'test-secret-please-rotate-in-prod-' + 'x'.repeat(20);

    // T1: round-trip
    {
        const tok = await signToken(SECRET, { sid: 'cs_123', product: 'geojson_all', exp: Math.floor(Date.now()/1000) + 60, email: 'a@b.co' });
        const got = await verifyToken(SECRET, tok);
        assert.equal(got.sid, 'cs_123');
        assert.equal(got.product, 'geojson_all');
        console.log('✓ T1 sign/verify round-trip');
    }

    // T2: tampered signature rejected
    {
        const tok = await signToken(SECRET, { sid: 'x', product: 'dxf_all', exp: 0 });
        const tampered = tok.replace(/^[^.]+/, 'AAAA' + tok.slice(4));
        const got = await verifyToken(SECRET, tampered);
        assert.equal(got, null);
        console.log('✓ T2 tampered signature rejected');
    }

    // T3: wrong key rejected
    {
        const tok = await signToken(SECRET, { sid: 'x', product: 'dxf_all', exp: 0 });
        const got = await verifyToken('other-secret-' + 'x'.repeat(20), tok);
        assert.equal(got, null);
        console.log('✓ T3 wrong key rejected');
    }

    // T4: expired token rejected
    {
        const tok = await signToken(SECRET, { sid: 'x', product: 'geojson_all', exp: 1 });  // 1970
        const got = await verifyToken(SECRET, tok);
        assert.equal(got, null);
        console.log('✓ T4 expired token rejected');
    }

    // T5: malformed token rejected
    {
        for (const bad of ['', null, undefined, 'no-dot-here', 'a.b.c', '.', 'a.']) {
            const got = await verifyToken(SECRET, bad);
            assert.equal(got, null, `bad token should reject: ${bad}`);
        }
        console.log('✓ T5 malformed tokens rejected');
    }

    // T6: catalog contains expected products
    {
        for (const p of ['geojson_all', 'dxf_all', 'sub_yearly']) {
            assert.ok(CATALOG[p], `missing ${p}`);
            assert.ok(CATALOG[p].priceEnv, `missing priceEnv for ${p}`);
            assert.ok(CATALOG[p].downloadKey, `missing downloadKey for ${p}`);
        }
        console.log('✓ T6 catalog complete');
    }

    console.log('\nALL TESTS PASS');
}

run().catch(e => { console.error('FAIL', e); process.exit(1); });