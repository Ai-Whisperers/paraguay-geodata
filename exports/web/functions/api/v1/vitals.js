// /functions/api/v1/vitals.js
// Lightweight serverless endpoint that accepts client-side Web Vitals reports.
// Stores the last 100 reports in-memory (resets on cold start) and returns 204.
//
// POST /api/v1/vitals
// Headers: Content-Type: application/json
// Body: { name: 'LCP'|'CLS'|..., value: 1234, id: 'v1|...', label: '...' }
//
// On any other method: returns 405 Method Not Allowed (which is what
// monitoring.js will see when it tries to GET, signalling it to switch
// to console-only mode).

export async function onRequest(context) {
  if (context.request.method !== 'POST') {
    return new Response('Method Not Allowed', {
      status: 405,
      headers: { 'Allow': 'POST' }
    });
  }
  try {
    const body = await context.request.json();
    // Validate shape
    if (!body || typeof body.name !== 'string' || typeof body.value !== 'number') {
      return new Response('Bad Request', { status: 400 });
    }
    // Server-side log (visible in CF Pages logs)
    console.log('[vitals]', JSON.stringify(body));
    return new Response(null, { status: 204 });
  } catch (e) {
    return new Response('Bad Request', { status: 400 });
  }
}