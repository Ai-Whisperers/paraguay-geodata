# CLAUDE.md — Paraguay Geodata

Instructions for AI agents (Claude Code / Codex / Cursor / etc.) running this repo.

## If you're a fresh agent, read these first (in order)

1. `README.md` — project one-page
2. `STATUS.md` — current phase + active blockers + last commit
3. `docs/INDEX.md` — map of every doc
4. `ARCHITECTURE.md` — pipeline + storage layout
5. The single most relevant operational doc for the user's request (e.g. `docs/operations/national-tile-fabric.md` if the user mentions tiles, `docs/operations/properties-pipeline.md` if listings, etc.)

Do NOT re-read the entire repo for context. Use `git log --oneline -50` + `STATUS.md` for orientation.

## Repo conventions

### Branches

- `main` is the source of truth. All work happens here. No `develop`, no long-lived feature branches.
- Commit often. The convention is WIP-then-clean: if a phase has 5 sub-deliverables, ship 5 commits.
- Tags: `phase0`, `phase1`, `phase2`, `phase3` mark end-of-phase checkpoints. Don't tag mid-phase.
- We follow the same triangle-of-authority pattern as LQV: `STATUS.md` (live state) ↔ `ARCHITECTURE.md` (design) ↔ `CLAUDE.md` (this file, agent instructions). When any one changes, check the other two.

### Naming

- Tool files: `tools/<verb>_<noun>.py` — `fetch_tile.py`, `build_peaks_geojson.py`, `build_price_surface.py`.
- Doc files: `docs/<category>/<title-in-kebab-case>.md`.
- Schema files: `docs/specs/<noun>-schema.json` (JSON Schema 2020-12).
- Cron-named shell scripts: `scripts/<cron-name>.sh` — registered in `~/.hermes/cron/jobs.json` (Hermes cron), not in this repo.

### Where do big files go?

| File size | Where |
|---|---|
| < 1 MB (small GeoJSONs, raw HTML) | `exports/web/` — gitignored-but-tracked-as-needed |
| < 25 MiB (single .png, .tif, .geojson) | `exports/web/data/` — Cloudsflare Pages can host |
| > 25 MiB or raster-heavy tile outputs | `exports/big_data_excluded_from_deploy/` — gitignored, R2-backed |
| Source-of-truth tile data (raw S2 bands, original DEM) | `data/tiles/<lon>_<lat>/` — gitignored |

### NEVER do

- **NEVER add a hostname with backtick-in-shell-hell heredocs.** Use `shell_quote()` or `python3 -c "import subprocess; subprocess.run([...])"`.
- **NEVER leave a `git push` for "later".** Push before reporting done. The cron `paraguay-geodata-sync` will catch drift, but you shouldn't create it.
- **NEVER scrape a portal without first running the ethics gate** (`docs/ethics/scraper-policy.md`).
- **NEVER push raw S2 or DEM tiles to GitHub.** They go to R2 or stay local, period. `.gitignore` covers this; don't override.
- **NEVER claim a deploy is live without probing it.** Use the 4-probe pattern at end of `STATUS.md`.
- **NEVER write a `python -c "import hermes_tools; …"` heredoc with `$VARIABLE` substitution** — the shell hooks swallow variables. Use `write_file` + `terminal` separately.
- **NEVER edit a tool script that has a `.py.bak` next to it.** That means it's the canonical LQV original we never want to break; the new file is the national variant.

### ALWAYS do

- **ALWAYS update `STATUS.md` before the final commit.** This is the only doc the user opens to "what's the live state".
- **ALWAYS add a reference to the relevant skill or umbrella when you write a new tool.** Every `tools/*.py` file gets a top-level docstring pointing at the class-level skill.
- **ALWAYS run tools through `python3 -m tools.<name>`** (or whatever the runner is in `pyproject.toml`) so imports resolve consistently. Avoid running direct paths.
- **ALWAYS keep `STATUS.md`'s "Live deploy probes" section runnable.** When you change a URL or surface, update the probe.
- **ALWAYS prefer the cheapest path that satisfies the requirement.** Don't spin up a GPU server to run a 2-D raster overlay. Don't reach for Three.js when Leaflet does it.

## When you're stuck

Run the 4-probe audit:

```bash
# 1. Repo state
gh repo view Ai-Whisperers/paraguay-geodata --json visibility,name,pushedAt,defaultBranchRef

# 2. Local vs remote parity
cd /root/paraguay-geodata && git fetch origin && git log @{u}..HEAD

# 3. Last commit per phase
git log --oneline | head -20

# 4. Deploy health (if a deploy exists yet — Phase 1+)
curl -sI https://paraguay-geodata.pages.dev | head -3
```

If 1-3 work but 4 fails: it's a deploy problem, not a code problem.
If 1 fails: you lost the repo, recreate from `ARCHITECTURE.md`.
If 2 fails behind/ahead by > 2 commits: someone (probably you) forgot to push.

## Phase tracking

See `splats/TODO.md` for the current phase's task list. Update it before each commit. Don't use the GitHub project board — keep it repo-local.

## Skill firing

When the user mentions any of these, load the named skill **before** writing code:

| User mention | Load skill |
|---|---|
| "tile", "tile index", "national", "all of Paraguay", "10×10" | `paraguay-open-data-fetch` + `lqv-bundle` (for technique) |
| "properties", "listings", "for sale", "precio", "infocasas", "propiedades.com.py" | `ethical-web-scraping-decision` first |
| "DEM", "elevation", "topography", "cerros" | `satellite-to-blender-pipeline` |
| "3D", "Cesium", "Three.js", "game world" | `satellite-to-blender-pipeline` |
| "deploy", "Pages", "wrangler", "R2" | `cloudflare-pages-deployment` |
| "LSV", "LQV", "Escobar", "Paraguarí" | `lqv-bundle` (umbrella), then this repo's `docs/operations/national-tile-fabric.md` |
| "audit", "roast", "what's broken" | `roast-audit-then-implement` |

## When the user says "do all of this"

That means every todo item in the current phase. Stop reading. Ship them. End with a single paragraph linking the live commits.
