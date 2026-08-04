"""tools/build_home_stats.py — read live stats and embed into home page.

The home page used to hardcode "5,784 properties" but the live count is
10,780. The JSON-LD, og:description, twitter:description, and i18n.js
home.* keys all had drifted.

This tool:
  1. Reads data/properties/data_freshness.json → live feature_count, sources
  2. Reads data/properties/canonical_summary.json → unique deptos, facets
  3. Writes:
     - exports/web/data/home_stats.json (data island for the home page JS)
     - Patches exports/web/index.html (meta description, og:description,
       twitter:description, JSON-LD)
     - Patches exports/web/i18n.js (home.title, home.investors.body,
       home.cta.investors, site.tagline, onboarding.step1.body) — all 4
       locales (es, en, pt, gn)

Result: the home page never lies about itself again. The cron rebuilds
home_stats.json every cycle.

Usage:
  python3 -m tools.build_home_stats
  python3 -m tools.build_home_stats --dry-run  # preview only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
# freshness is built into exports/web/data/ — the data island is the live
# truth, the tool regenerates it daily. canonical_summary lives in
# data/properties/ because it's the source-of-truth tile metadata.
FRESHNESS = REPO / "exports" / "web" / "data" / "data_freshness.json"
SUMMARY = REPO / "data" / "properties" / "canonical_summary.json"
INDEX_HTML = REPO / "exports" / "web" / "index.html"
I18N_JS = REPO / "exports" / "web" / "i18n.js"
HOME_STATS_JSON = REPO / "exports" / "web" / "data" / "home_stats.json"


def load_stats() -> dict:
    """Pull live numbers from freshness + summary."""
    out = {
        "as_of_utc": "",
        "feature_count": 0,
        "median_days": 0,
        "deptos_count": 0,
        "deptos": [],
        "sources": [],
        "sources_count": 0,
    }

    if FRESHNESS.exists():
        f = json.loads(FRESHNESS.read_text())
        out["as_of_utc"] = f.get("as_of_utc", "")
        out["feature_count"] = f.get("feature_count", 0)
        out["median_days"] = f.get("median_days", 0)
        sources = f.get("sources", {})
        if isinstance(sources, dict):
            out["sources"] = [
                {"name": k, "count": v.get("count", 0)}
                for k, v in sources.items()
            ]
            out["sources_count"] = len(sources)

    if SUMMARY.exists():
        s = json.loads(SUMMARY.read_text())
        # deptos count — canonical_summary.json stores it at facets.depto
        facets = s.get("facets", {})
        if isinstance(facets, dict):
            by_depto = facets.get("depto", {})
            if isinstance(by_depto, dict):
                out["deptos_count"] = len(by_depto)
                out["deptos"] = sorted(by_depto.keys())
            elif isinstance(by_depto, list):
                out["deptos_count"] = len(by_depto)
                out["deptos"] = sorted(by_depto)
        elif isinstance(s.get("by_depto"), dict):
            by_depto = s["by_depto"]
            out["deptos_count"] = len(by_depto)
            out["deptos"] = sorted(by_depto.keys())

    return out


def fmt_int(n: int) -> str:
    """Format like 10,780 (en-US style, used in ES/EN/PT/Guarani all)."""
    return f"{n:,}"


def render_i18n_values(stats: dict) -> dict:
    """Return {key: {'es': ..., 'en': ..., 'pt': ..., 'gn': ...}}."""
    n = fmt_int(stats["feature_count"])
    src_n = stats["sources_count"]
    depto_n = stats["deptos_count"]
    src_list = ", ".join(s["name"] for s in stats["sources"])
    return {
        "home.title": {
            "es": f"{n} propiedades en Paraguay",
            "en": f"{n} properties in Paraguay",
            "pt": f"{n} imóveis no Paraguai",
            "gn": f"{n} óga Paraguay retâme",
        },
        "home.tagline": {
            "es": f"{n} propiedades · {depto_n} departamentos · {src_n} fuentes",
            "en": f"{n} properties · {depto_n} departments · {src_n} sources",
            "pt": f"{n} imóveis · {depto_n} departamentos · {src_n} fontes",
            "gn": f"{n} óga · {depto_n} tetãvore · {src_n} fuente",
        },
        "site.tagline": {
            "es": f"{n} propiedades · {depto_n} departamentos · Cobertura nacional",
            "en": f"{n} properties · {depto_n} departments · National coverage",
            "pt": f"{n} imóveis · {depto_n} departamentos · Cobertura nacional",
            "gn": f"{n} óga · {depto_n} tetãvore · Oñemobyta hína",
        },
        "onboarding.step1.body": {
            "es": f"{n} propiedades en Paraguay, en una sola vista.",
            "en": f"{n} properties across Paraguay, in one view.",
            "pt": f"{n} imóveis pelo Paraguai, em uma única vista.",
            "gn": f"{n} óga Paraguay retâme, peteĩ vista rehe.",
        },
        "home.investors.body": {
            "es": f"{n} avisos · {src_n} fuentes ({src_list}) · USD + PYG en cada listing.",
            "en": f"{n} listings · {src_n} sources ({src_list}) · USD + PYG on every listing.",
            "pt": f"{n} anúncios · {src_n} fontes ({src_list}) · USD + PYG em cada listing.",
            "gn": f"{n} ñemobyta · {src_n} fuente ({src_list}) · USD + PYG óga rehegua.",
        },
        "home.cta.investors": {
            "es": f"Ver {n} propiedades →",
            "en": f"View {n} properties →",
            "pt": f"Ver {n} imóveis →",
            "gn": f"Echa {n} óga →",
        },
    }


def patch_i18n_js(stats: dict, dry_run: bool = False) -> int:
    """Replace the home/site/onboarding keys in i18n.js with live values."""
    if not I18N_JS.exists():
        return 0
    content = I18N_JS.read_text()
    new_values = render_i18n_values(stats)
    n_patched = 0

    for key, by_locale in new_values.items():
        for loc, value in by_locale.items():
            # Match inside the "loc" block: "key": "value"
            pattern = re.compile(
                r'("' + re.escape(loc) + r'"\s*:\s*\{[^}]*?"'
                + re.escape(key)
                + r'"\s*:\s*)"[^"]*"',
                re.DOTALL,
            )
            new_content, n = pattern.subn(
                r'\g<1>' + json.dumps(value, ensure_ascii=False),
                content,
            )
            if n > 0:
                content = new_content
                n_patched += n

    if not dry_run:
        I18N_JS.write_text(content)
    return n_patched


def patch_index_html(stats: dict, dry_run: bool = False) -> int:
    """Replace meta description, og:description, twitter:description, JSON-LD."""
    if not INDEX_HTML.exists():
        return 0
    content = INDEX_HTML.read_text()
    n = fmt_int(stats["feature_count"])
    depto_n = stats["deptos_count"]
    src_list_en = ", ".join(s["name"] for s in stats["sources"])
    n_patched = 0

    # 1. meta name="description"
    content, c = re.subn(
        r'(<meta name="description" content=")[^"]+(")',
        lambda m: (
            m.group(1)
            + f"Paraguay national geodata viewer: {n} properties "
            + f"({src_list_en}), {depto_n} deptos, INBIO zafra 2025-2026, "
            + "BCP macro snapshot, climate risk, biodiversity. "
            + "Built by Ai-Whisperers."
            + m.group(2)
        ),
        content,
    )
    n_patched += c

    # 2. meta property="og:description"
    content, c = re.subn(
        r'(<meta property="og:description" content=")[^"]+(")',
        lambda m: (
            m.group(1)
            + f"Interactive Paraguay map: 7,912 tiles, {n} properties, "
            + f"{depto_n} deptos, INBIO crops, BCP macro. Live data."
            + m.group(2)
        ),
        content,
    )
    n_patched += c

    # 3. meta name="twitter:description"
    content, c = re.subn(
        r'(<meta name="twitter:description" content=")[^"]+(")',
        lambda m: (
            m.group(1)
            + f"Interactive Paraguay map: 7,912 tiles, {n} properties, "
            + f"{depto_n} deptos. Live data."
            + m.group(2)
        ),
        content,
    )
    n_patched += c

    # 4. JSON-LD organization description
    content, c = re.subn(
        r'("description":\s*")[^"]+(")',
        r'\g<1>' + f"{n} propiedades en Paraguay. Mapa interactivo construido con datos públicos abiertos." + r'\g<2>',
        content,
    )
    n_patched += c

    if not dry_run:
        INDEX_HTML.write_text(content)
    return n_patched


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Refresh home page stats from live data.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not FRESHNESS.exists():
        print(f"  ERR: {FRESHNESS} not found — run refresh_properties.sh first")
        return 1

    print("=== build_home_stats ===")
    stats = load_stats()
    print(f"  feature_count: {stats['feature_count']:,}")
    print(f"  deptos: {stats['deptos_count']}")
    print(f"  sources: {stats['sources_count']} ({[s['name'] for s in stats['sources']]})")

    # Write data island for client-side rendering
    if not args.dry_run:
        HOME_STATS_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "as_of_utc": stats["as_of_utc"],
            "feature_count": stats["feature_count"],
            "median_days": stats["median_days"],
            "deptos_count": stats["deptos_count"],
            "sources_count": stats["sources_count"],
            "sources": stats["sources"],
        }
        HOME_STATS_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"  wrote {HOME_STATS_JSON.relative_to(REPO)}")

    n_html = patch_index_html(stats, dry_run=args.dry_run)
    print(f"  index.html: {n_html} meta/JSON-LD {'would patch' if args.dry_run else 'patched'}")

    n_i18n = patch_i18n_js(stats, dry_run=args.dry_run)
    print(f"  i18n.js: {n_i18n} home/site/onboarding keys {'would patch' if args.dry_run else 'patched'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
