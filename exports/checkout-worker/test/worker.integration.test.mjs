// Integration tests for the production worker module.
// These intentionally import the real worker instead of copying implementation.

import assert from 'node:assert/strict';
import worker from '../src/worker.js';

const TEST_ENV = {
    STRIPE_SECRET_KEY: 'sk_test_placeholder',
    DOWNLOAD_TOKEN_SIGNING_KEY: 'test-signing-key-' + 'x'.repeat(32),
    STRIPE_PRICE_GEOJSON_ONE_TIME: 'price_geojson',
    STRIPE_PRICE_DXF_ONE_TIME: 'price_dxf',
    STRIPE_PRICE_SUB_YEARLY: 'price_sub',
};

async function body(response) {
    const text = await response.text();
    try { return JSON.parse(text); } catch { return text; }
}

async function run() {
    const checkoutCalls = [];
    const paidSession = {
        payment_status: 'paid',
        status: 'complete',
        metadata: { product: 'geojson_all' },
        customer_details: { email: 'architect@example.com' },
    };
    const stripeClient = {
        checkout: {
            sessions: {
                async create(options) {
                    checkoutCalls.push(options);
                    return { id: 'cs_test_123', url: 'https://checkout.stripe.com/c/pay/cs_test_123' };
                },
                async retrieve() { return paidSession; },
            },
        },
    };
    const env = { ...TEST_ENV, STRIPE_CLIENT: stripeClient };

    {
        const response = await worker.fetch(new Request('https://checkout.example/health'), env, {});
        assert.equal(response.status, 200);
        const payload = await body(response);
        assert.equal(payload.ok, true);
        assert.equal(payload.ready, false);
        assert.equal(payload.mode, 'test');
        assert.deepEqual(payload.products.sort(), ['dxf_all', 'geojson_all', 'sub_yearly']);
        assert.equal(payload.artifacts.geojson_all, false);
        assert.equal(payload.artifacts.dxf_all, false);
        console.log('✓ I1 health exposes configuration readiness without secrets');
    }

    {
        const response = await worker.fetch(
            new Request('https://checkout.example/checkout', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ product: 'unknown' }),
            }),
            TEST_ENV,
            {},
        );
        assert.equal(response.status, 400);
        assert.deepEqual(await body(response), { error: 'Unknown product' });
        console.log('✓ I2 unknown checkout product rejected');
    }

    {
        const response = await worker.fetch(
            new Request('https://checkout.example/checkout', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ product: 'geojson_all' }),
            }),
            { ...TEST_ENV, STRIPE_SECRET_KEY: '' },
            {},
        );
        assert.equal(response.status, 503);
        assert.deepEqual(await body(response), { error: 'Checkout is not configured' });
        console.log('✓ I3 checkout fails closed when Stripe is not configured');
    }

    {
        const response = await worker.fetch(
            new Request('https://checkout.example/download?token=not-a-token'),
            TEST_ENV,
            {},
        );
        assert.equal(response.status, 401);
        assert.deepEqual(await body(response), { error: 'Invalid or expired token' });
        console.log('✓ I4 invalid download token rejected');
    }

    {
        const response = await worker.fetch(
            new Request('https://checkout.example/checkout', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ product: 'geojson_all' }),
            }),
            env,
            {},
        );
        assert.equal(response.status, 200);
        assert.deepEqual(await body(response), {
            url: 'https://checkout.stripe.com/c/pay/cs_test_123',
            id: 'cs_test_123',
        });
        assert.equal(checkoutCalls.length, 1);
        assert.equal(checkoutCalls[0].mode, 'payment');
        assert.deepEqual(checkoutCalls[0].line_items, [{ price: 'price_geojson', quantity: 1 }]);
        assert.equal(checkoutCalls[0].metadata.product, 'geojson_all');
        assert.equal(checkoutCalls[0].billing_address_collection, 'required');
        assert.equal(checkoutCalls[0].automatic_tax, undefined);
        console.log('✓ I5 checkout creates a Stripe hosted payment session');
    }

    {
        const response = await worker.fetch(new Request('https://checkout.example/cancel'), env, {});
        assert.equal(response.status, 303);
        assert.equal(response.headers.get('location'), 'https://geodata.paragu-ai.com/pricing?checkout=cancelled');
        console.log('✓ I6 cancel returns buyer to pricing page');
    }

    {
        const response = await worker.fetch(
            new Request('https://checkout.example/success?session_id=cs_test_123&product=geojson_all'),
            env,
            {},
        );
        assert.equal(response.status, 302);
        const location = new URL(response.headers.get('location'));
        assert.equal(location.pathname, '/download');
        assert.equal(location.searchParams.get('product'), 'geojson_all');
        assert.ok(location.searchParams.get('token'));

        const download = await worker.fetch(new Request(location), {
            ...env,
            EXPORTS: {
                async get(key) {
                    assert.equal(key, 'properties_latest.geojson');
                    return { body: '{"type":"FeatureCollection","features":[]}' };
                },
            },
        }, {});
        assert.equal(download.status, 200);
        assert.equal(download.headers.get('content-type'), 'application/geo+json');
        assert.match(download.headers.get('content-disposition'), /attachment; filename="paraguay-properties-all-/);
        console.log('✓ I7 paid session issues a signed token and downloads its artifact');
    }

    console.log('\nALL INTEGRATION TESTS PASS');
}

run().catch(error => {
    console.error('FAIL', error);
    process.exit(1);
});
