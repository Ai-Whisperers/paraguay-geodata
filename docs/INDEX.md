# Paraguay Geodata — Improvement Index

This folder groups the working documents for the Paraguay Geodata platform.

## Strategy

- [`PLAN_v2.md`](PLAN_v2.md) — **Master improvement plan, sequenced and scored.**
  Replaces `PLAN.md` / `ROADMAP.md` as the single source of truth.
- [`PROPERTY_RISK_ANALYSIS.md`](PROPERTY_RISK_ANALYSIS.md) — Property-level
  risk + pro scoring; v2 with depto normalization.
- [`MIGRATION_FROM_LQV.md`](MIGRATION_FROM_LQV.md) — How the national fork
  came out of the La Quebrada Viva (LQV) project.
- [`LUCIA_HANDOFF.md`](LUCIA_HANDOFF.md) — Architect export handoff notes.
- [`ROADMAP.md`](ROADMAP.md) — Original 2,500-item brainstorm; kept for
  reference; do **not** edit.

## Reference (per-source)

- [`sources/administrative.md`](sources/administrative.md) — INE, admin
  boundaries.
- [`sources/agriculture.md`](sources/agriculture.md) — INBIO zafra PDFs.
- [`sources/businesses.md`](sources/businesses.md) — DNCP public tenders.
- [`sources/cadastre.md`](sources/cadastre.md) — Catastro Nacional WFS.
- [`sources/environment.md`](sources/environment.md) — MADES, climate risk.
- [`sources/finance.md`](sources/finance.md) — BCP macro / rates.
- [`sources/infrastructure.md`](sources/infrastructure.md) — MOPC, ANDE.
- [`sources/satellite.md`](sources/satellite.md) — Copernicus, Hansen, etc.
- [`sources/socioeconomic.md`](sources/socioeconomic.md) — DGEEC census.

## Operations

- [`operations/national-tile-fabric.md`](operations/national-tile-fabric.md)
- [`operations/properties-pipeline.md`](operations/properties-pipeline.md)
- [`operations/price-model.md`](operations/price-model.md)
- [`operations/api-key-checklist.md`](operations/api-key-checklist.md)

## API

- [`api/openapi.yaml`](api/openapi.yaml) — OpenAPI 3.0 spec.

## Ethics

- [`ethics/scraper-policy.md`](ethics/scraper-policy.md) — Per-source
  rate limits + PII handling.

---

**Quick links**

| Where to look | Path |
|---|---|
| What just shipped | `STATUS.md` |
| Live at | https://geodata.paragu-ai.com/ |
| Repo | https://github.com/Ai-Whisperers/paraguay-geodata |
| Tests | `tests/` · run with `pytest -q` |
| Canonicalize | `python3 -m tools.canonicalize_properties` |
| Build facets | `python3 -m tools.build_facets` |
| Weekly refresh | `bash scripts/refresh_properties.sh` |