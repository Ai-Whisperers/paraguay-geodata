# Paraguay Geodata — API v1 · GDPR / LGPD data-deletion endpoint

POST https://geodata.paragu-ai.com/api/v1/delete
Content-Type: application/json

```
{
  "email": "owner@example.com",
  "listing_url": "https://www.infocasas.com.py/casa-en-venta-...",  // OR
  "listing_id": "ic_abc123",
  "reason": "I am the owner and want this listing removed (GDPR Art. 17 / LGPD Art. 18)",
  "signature": "..."  // optional: SHA256(email + listing_url) proves you control the email
}
```

Submission opens a mailto to legal@ai-whisperers.org with the request.
A human reviews within 5 business days.

## Note

We can't process deletions directly from the static site (no backend).
This endpoint is a convention for clients + an automated form-submission
bridge.  The actual removal happens in the canonicalize_properties pipeline
via a `deleted_listings` exclusion list.

## How to implement

1. Copy the body into an email to legal@ai-whisperers.org.
2. Or use the in-page form at /contact.html (selects "DMCA / takedown").
3. We add the listing to `data/properties/deleted_listings.json` (gitignored).
4. canonicalize_properties.py filters out anything in that list.
5. The next deploy removes it from the live geojson.

## Why no automation yet

We have no backend. A Cloudflare Worker (in `exports/checkout-worker/`)
could implement this but it's not deployed.  Until then, the mailto
flow is the contract.
