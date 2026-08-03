#!/usr/bin/env bash
# Wrangler deploy shim — uses the CF API token already in the env.
set -euo pipefail
ROOT="${ROOT:-/root/paraguay-geodata}"
TOK="${CLOUDFLARE_API_TOKEN:-}"
ACCT="${CLOUDFLARE_ACCOUNT_ID:-9eb1832f3e42a1dbd6ba854f8d6a1cb2}"
export CF_API_TOKEN="$TOK" CLOUDFLARE_API_TOKEN="$TOK" CLOUDFLARE_ACCOUNT_ID="$ACCT"
cd "$ROOT/exports/web"
exec npx --yes wrangler@latest pages deploy . --project-name paraguay-geodata --branch main --commit-dirty=true
