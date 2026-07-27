// =============================================================================
// geodata-checkout Worker
//
// Cloudflare Worker that gates full-dataset GeoJSON / DXF downloads behind a
// Stripe checkout. Free preview (viewport / filtered / selection) is served
// directly from the static site; this worker handles ONLY the paid flow.
//
// Endpoints
//   POST /checkout        {product: 'geojson_all'|'dxf_all'} -> redirect to Stripe Checkout
//   GET  /success         Stripe redirects here on payment; issues one-time download token
//   GET  /download/:token Verifies HMAC; serves dataset from R2 (or redirects to signed URL)
//
// Pricing (configurable via env STRIPE_PRICE_*)
//   STRIPE_PRICE_GEOJSON_ONE_TIME  = 'price_...'  (default $29 one-time)
//   STRIPE_PRICE_DXF_ONE_TIME      = 'price_...'  (default $99 one-time — heavier dataset prep)
//   STRIPE_PRICE_SUB_YEARLY        = 'price_...'  (default $299/year — all formats, refresh monthly)
//
// Dependencies: stripe (npm). Deployed via wrangler deploy.
// =============================================================================

import Stripe from 'stripe';

const CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
};

// Catalog: product id -> Stripe price env var + display name
const CATALOG = {
    geojson_all: {
        priceEnv: 'STRIPE_PRICE_GEOJSON_ONE_TIME',
        name: 'Paraguay Geodata — full national GeoJSON export',
        format: 'geojson',
        downloadKey: 'properties_latest.geojson',
    },
    dxf_all: {
        priceEnv: 'STRIPE_PRICE_DXF_ONE_TIME',
        name: 'Paraguay Geodata — full national DXF (CAD) export',
        format: 'dxf',
        // DXF is generated server-side from the GeoJSON on demand; cached in R2.
        downloadKey: 'properties_latest.dxf',
    },
    sub_yearly: {
        priceEnv: 'STRIPE_PRICE_SUB_YEARLY',
        name: 'Paraguay Geodata — Pro subscription (1 year)',
        format: 'both',
        downloadKey: 'subscription',
    },
};

const TOKEN_TTL_SECONDS = 3600; // 1 hour

// ----- HMAC token sign/verify -----
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
    } catch {
        return null;
    }
}

// ----- CORS helper -----
function withCors(resp) {
    const r = new Response(resp.body, resp);
    for (const [k, v] of Object.entries(CORS)) r.headers.set(k, v);
    return r;
}

// ----- POST /checkout -----
async function handleCheckout(request, env, ctx) {
    if (request.method !== 'POST') {
        return withCors(new Response('Method not allowed', { status: 405 }));
    }
    let body;
    try { body = await request.json(); }
    catch { return withCors(jsonError('Invalid JSON body', 400)); }

    const product = body.product;
    const productDef = CATALOG[product];
    if (!productDef) return withCors(jsonError('Unknown product', 400));

    const priceId = env[productDef.priceEnv];
    if (!priceId) return withCors(jsonError(`Price not configured for ${product}`, 500));

    const stripe = new Stripe(env.STRIPE_SECRET_KEY, { apiVersion: '2024-06-20' });
    const origin = new URL(request.url).origin;
    const successUrl = `${origin}/success?session_id={CHECKOUT_SESSION_ID}&product=${encodeURIComponent(product)}`;
    const cancelUrl  = `${origin}/cancel`;

    const session = await stripe.checkout.sessions.create({
        mode: product === 'sub_yearly' ? 'subscription' : 'payment',
        line_items: [{ price: priceId, quantity: 1 }],
        success_url: successUrl,
        cancel_url: cancelUrl,
        metadata: { product, download_key: productDef.downloadKey },
        // Allow promotion codes, collect billing address for receipts.
        allow_promotion_codes: true,
        billing_address_collection: 'auto',
    });

    return withCors(jsonResponse({ url: session.url, id: session.id }));
}

// ----- GET /success?session_id=...&product=... -----
// Verifies the Stripe session, then issues a one-time signed token.
// The static site reads ?token= from the URL and hits /download/:token.
async function handleSuccess(request, env) {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get('session_id');
    const product = url.searchParams.get('product');
    if (!sessionId || !product || !CATALOG[product]) {
        return new Response('Invalid success link', { status: 400 });
    }

    const stripe = new Stripe(env.STRIPE_SECRET_KEY, { apiVersion: '2024-06-20' });
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    if (session.payment_status !== 'paid' && session.status !== 'complete') {
        return new Response('Payment not confirmed', { status: 402 });
    }

    const exp = Math.floor(Date.now() / 1000) + TOKEN_TTL_SECONDS;
    const token = await signToken(env.DOWNLOAD_TOKEN_SIGNING_KEY, {
        sid: sessionId,
        product,
        exp,
        email: session.customer_details?.email || '',
    });

    // Redirect the browser to the static site's download landing page with the token.
    const dest = `${url.origin}/download?token=${encodeURIComponent(token)}&product=${encodeURIComponent(product)}`;
    return Response.redirect(dest, 302);
}

// ----- GET /download?token=...&product=... -----
// Verifies the signed token, then streams the dataset.
// In production, EXPORTS R2 bucket should hold the artifacts; for now
// we proxy from the public R2 / CDN URL stored in env.
async function handleDownload(request, env, ctx) {
    const url = new URL(request.url);
    const token = url.searchParams.get('token');
    const payload = await verifyToken(env.DOWNLOAD_TOKEN_SIGNING_KEY, token);
    if (!payload) return withCors(jsonError('Invalid or expired token', 401));

    const product = payload.product;
    const productDef = CATALOG[product];
    if (!productDef) return withCors(jsonError('Unknown product', 400));

    // Resolve the artifact. If R2 binding is configured, fetch from there; else
    // proxy from env.DATASET_BASE_URL (Cloudflare R2 public bucket or Pages deploy).
    let artifact = null;
    if (env.EXPORTS && typeof env.EXPORTS.get === 'function') {
        const obj = await env.EXPORTS.get(productDef.downloadKey);
        if (obj) {
            artifact = {
                body: obj.body,
                contentType: productDef.format === 'dxf' ? 'application/dxf' : 'application/geo+json',
                filename: `paraguay-properties-all-${new Date().toISOString().slice(0,10)}.${productDef.format}`,
            };
        }
    }
    if (!artifact && env.DATASET_BASE_URL) {
        const upstream = await fetch(`${env.DATASET_BASE_URL}/${productDef.downloadKey}`);
        if (upstream.ok) {
            artifact = {
                body: upstream.body,
                contentType: upstream.headers.get('Content-Type') || (productDef.format === 'dxf' ? 'application/dxf' : 'application/geo+json'),
                filename: `paraguay-properties-all-${new Date().toISOString().slice(0,10)}.${productDef.format}`,
            };
        }
    }
    if (!artifact) return withCors(jsonError('Dataset not yet uploaded — contact erebus@ai-whisperers.org', 503));

    return new Response(artifact.body, {
        status: 200,
        headers: {
            'Content-Type': artifact.contentType,
            'Content-Disposition': `attachment; filename="${artifact.filename}"`,
            'Cache-Control': 'no-store',
            ...CORS,
        },
    });
}

// ----- helpers -----
function jsonResponse(obj, status = 200) {
    return new Response(JSON.stringify(obj), {
        status,
        headers: { 'Content-Type': 'application/json' },
    });
}
function jsonError(msg, status) { return jsonResponse({ error: msg }, status); }

// ----- router -----
export default {
    async fetch(request, env, ctx) {
        if (request.method === 'OPTIONS') return withCors(new Response(null, { status: 204 }));
        const url = new URL(request.url);
        const path = url.pathname;
        try {
            if (path === '/checkout' || path === '/api/checkout') return await handleCheckout(request, env, ctx);
            if (path === '/success'  || path === '/api/success')  return await handleSuccess(request, env);
            if (path === '/download' || path === '/api/download') return await handleDownload(request, env, ctx);
            if (path === '/' || path === '/health') {
                return withCors(jsonResponse({ ok: true, service: 'geodata-checkout' }));
            }
            return withCors(jsonError('Not found', 404));
        } catch (err) {
            console.error('worker error', err);
            return withCors(jsonError(err.message || 'Internal error', 500));
        }
    },
};