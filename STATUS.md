# STATUS — Paraguay Geodata

Live state of the repo. Updated before every commit.

Last update: 2026-07-10 (Phase 0 + 0.5 expansion shipped — commit `73a96bb` + new data-inventory expansion)

## Phase Tracker

| Phase | Name | Status | Deliverables |
|---|---|---|---|
| **0** | Skeleton + ethics gate | 🟡 In progress | Repo + 4-doc skeleton + tile index + scrapping policy drafted |
| **1** | National satellite + topographic coverage | ⏳ Queued | DEM + Esri + OSM + S2 + MapBiomas + Hansen + JRC across the grid |
| **2** | Properties + price surfaces | ⏳ Queued | Listings scraper + escritura cross-ref + hedonic kriging |
| **3** | Interactive + 3D national | ⏳ Queued | Cesium globe + per-tile Three.js planning world |

## Track Trackers

### Track A — Code/Data (this repo)

- **Visibility**: PRIVATE GitHub (`gh repo view Ai-Whisperers/paraguay-geodata`)
- **Branch**: `main`
- **Last commit**: (this is the first commit, see `git log` once pushed)
- **Last push**: TBD

### Track B — Live deploy (Phase 1+)

- **CF Pages project**: TBD (Phase 1 milestone)
- **R2 bucket**: TBD (Phase 0 milestone)
- **Live URL**: not yet live (no deploy exists)

## Live deploy probes (Phase 1+, runnable)

```bash
# 1. Repo state
gh repo view Ai-Whisperers/paraguay-geodata --json visibility,name,pushedAt,defaultBranchRef

# 2. Local vs remote parity
git fetch origin && git log @{u}..HEAD

# 3. R2 / Pages asset probes (post-Phase 1)
# (filled in when the R2 bucket is provisioned)
```

## Phase 0 — In Progress

> **Status (2026-07-10)**: SHIPPED ✅ — commit `73a96bb` on `origin/main`, byte-perfect verified.

### Shipped

- [x] Create `Ai-Whisperers/paraguay-geodata` (private)
- [x] 4-doc canonical skeleton (README / ARCHITECTURE / CLAUDE / STATUS)
- [x] Tile index script (`tools/national_tile_index.py`) → 7,912 tiles confirmed
- [x] Per-tile fetch orchestrator (`tools/fetch_tile.py` — stub for Phase 1 to fill in)
- [x] Scraper spec + ethics gate (`docs/operations/properties-pipeline.md` + `docs/ethics/scraper-policy.md`)
- [x] First end-to-end smoke (`6/6 tests pass`, dry-run completes in <1s)
- [x] Phase 0 commit + push + raw URLs

### Blocked on / awaiting

- (none — Phase 0 was self-contained)

### Decisions made (this phase)

- **Repo structure**: sibling of `la-quebrada-viva`, not a parent. LQV stays frozen at escritura; this is a fresh start.
- **License**: MIT (code) + CC0 (data) — same as LQV.
- **Listings source**: Public portals (infocasas + propiedades.com.py + baiker) cross-referenced against escritura anchors. Most ambitious option, best trust signal.
- **Storage**: Cloudflare R2 for heavy rasters, Pages for HTML + small JSON. R2 free tier covers ~100-500 GB/year.
- **Tile size**: 10×10 km, EPSG:4326. ~7,900 tiles covering Paraguay (corrected from early "~1,000" estimate).
- **Viewer pattern**: ONE `/mapa.html` with `?tile=<id>&r=<km>` + UI picker (LQV single-source-of-truth pattern).

## Phase 1 — Queued

(Will be filled in once Phase 0 ships — pull from `docs/operations/national-tile-fabric.md` §Phase 1.)

## Phase 2 — Queued

(Will be filled in once Phase 1 ships — pull from `docs/operations/properties-pipeline.md` + `docs/operations/price-model.md`.)

## Phase 3 — Queued

(Cesium globe + Three.js planning world — see `ARCHITECTURE.md`.)

## Cross-references

- Design: `ARCHITECTURE.md`
- Action items: `splats/TODO.md`
- Umbrella skill (technique): `~/.hermes/skills/lqv-bundle/SKILL.md`
- Class skill: `~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md`
- Source catalogue skill: `~/.hermes/skills/paraguay-open-data-fetch/SKILL.md`

## How to update this file

Before every commit that changes repo state, update:
1. The "Last update" date at the top
2. The affected phase's "Open work" checklist (✓ what shipped, ☐ what didn't)
3. The "Decisions made" section if you made a structural call

The triangle of authority: `STATUS.md` (this, live state) ↔ `ARCHITECTURE.md` (design, mostly stable) ↔ `CLAUDE.md` (agent ops). When any one changes, check the other two for stale references.
