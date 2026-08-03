# Paraguay Geodata — Makefile
# Common dev workflows.  Run `make` for a list of targets.

SHELL := /bin/bash
PY ?= python3
PIP ?= pip3

.PHONY: help install install-dev lint format test test-cover build clean \
        deploy-preview deploy-prod scrub canonicalize merge build-all \
        package-extension data-freshness tile-index lint-ruff format-check

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' Makefile

install:  ## Install the package (runtime only).
	$(PIP) install -e .

install-dev:  ## Install dev + lint + test deps.
	$(PIP) install -e ".[dev]"
	$(PY) -m playwright install --with-deps chromium || true

lint:  ## Run ruff on tools/ + tests/.
	ruff check tools/ tests/
	ruff format --check tools/ tests/

format:  ## Auto-format tools/ + tests/.
	ruff format tools/ tests/

format-check:  ## Verify formatting.
	ruff format --check tools/ tests/

test:  ## Run pytest.
	$(PY) -m pytest tests/ -q --no-header

test-cover:  ## Run pytest with coverage.
	$(PY) -m pytest tests/ -q --no-header --cov=tools --cov-report=term-missing --cov-fail-under=20

canonicalize:  ## Re-run canonicalize on the live geojson.
	$(PY) -m tools.canonicalize_properties \
		--input exports/web/data/properties_latest.geojson \
		--output data/properties

merge:  ## Re-merge sources into properties_latest.geojson.
	$(PY) -m tools.merge_fresh_sources

facets:  ## Rebuild facets.json.
	$(PY) -m tools.build_facets

data-freshness:  ## Rebuild data_freshness.json.
	$(PY) -m tools.build_data_freshness

days-on-market:  ## Rebuild days_on_market.json.
	$(PY) -m tools.build_days_on_market

pmtiles:  ## Convert canonical_properties.geojson → .pmtiles (411 KB vs 11 MB raw).
	$(PY) -m tools.build_pmtiles

build-all: canonicalize merge facets data-freshness days-on-market pmtiles  ## Rebuild all derived artifacts.

scrub:  ## Apply PII scrub to a single file (use carefully).
	$(PY) -m tools.scrub_pii $(INPUT) $(OUTPUT)

deploy-preview:  ## Deploy to Cloudflare Pages preview (alias of prod).
	CLOUDFLARE_API_TOKEN=$$CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID=$$CLOUDFLARE_ACCOUNT_ID \
		npx --yes wrangler@latest pages deploy exports/web --project-name paraguay-geodata --branch main --commit-dirty=true

deploy-prod: build-all  ## Build all and deploy to prod.
	CLOUDFLARE_API_TOKEN=$$CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID=$$CLOUDFLARE_ACCOUNT_ID \
		npx --yes wrangler@latest pages deploy exports/web --project-name paraguay-geodata --branch main --commit-dirty=true

fetch-infocasas:  ## Run InfoCasas fetcher.
	$(PY) -m tools.fetch_properties --portal infocasas --output-dir data/properties/snapshots

fetch-tulugar:  ## Run TuLugar fetcher.
	$(PY) -m tools.fetch_tulugar --output-dir data/properties/snapshots

fetch-asuncion:  ## Run Asunción.estate fetcher.
	$(PY) -m tools.fetch_asuncion_estate --output-dir data/properties/snapshots

fetch-all: fetch-tulugar fetch-asuncion fetch-infocasas  ## Run all fetchers.

audit-links:  ## HEAD-check every source URL.
	$(PY) -m tools.check_property_links

clean:  ## Remove __pycache__ + .coverage + ephemeral outputs.
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
	rm -f .coverage coverage.json
