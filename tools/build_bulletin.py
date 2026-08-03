"""tools/build_bulletin.py

Emit a public `/bulletin.json` containing today's deploy summary.

Reads:
  - exports/web/healthz.json
  - exports/web/deploy-meta.json
  - git log (last 5 commits)

Outputs:
  - exports/web/bulletin.json
  - exports/web/bulletin.html (a small page)

This is meant to be public, friendly, and machine-readable.  Used by
embedders / aggregators who want to follow Paraguay Geodata.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git_log(n: int = 5) -> list[dict]:
    """Return the last `n` commits as a small dict."""
    out = subprocess.run(
        ["git", "log", f"-{n}", "--pretty=format:%H|%s|%ai|%an"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if out.returncode != 0:
        return []
    lines = []
    for line in out.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        sha, subject, date, author = parts
        lines.append({
            "sha": sha[:7],
            "subject": subject,
            "date": date,
            "author": author,
        })
    return lines


def _deploy_meta() -> dict:
    p = ROOT / "exports" / "web" / "deploy-meta.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _healthz() -> dict:
    p = ROOT / "exports" / "web" / "healthz.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)

    h = _healthz()
    dm = _deploy_meta()
    log = _git_log(5)

    n_listings = 0
    sources = {}
    if h.get("data", {}).get("properties"):
        n_listings = h["data"]["properties"].get("total_listings", 0)
    summary = json.load(open(ROOT / "exports" / "web" / "api" / "v1" / "properties.json"))
    sources = summary.get("sources", {})

    n_sources = len(sources)
    n_cities = 0  # not currently tracked; discovery could compute
    today = subprocess.run(
        ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
        capture_output=True, text=True,
    ).stdout.strip()

    # Recent listings surfaced directly
    geojson = json.load(open(ROOT / "data" / "properties" / "canonical_properties.geojson"))
    feats = sorted(
        geojson.get("features", []),
        key=lambda f: f.get("properties", {}).get("scraped_at_utc", ""),
        reverse=True,
    )[:5]
    new_listings = [
        {
            "id": f["properties"]["id"],
            "source": f["properties"].get("source", "?"),
            "city": f["properties"].get("city", "?"),
            "state_province": f["properties"].get("state_province", "?"),
            "price_usd": f["properties"].get("price_usd"),
            "area_sqm": f["properties"].get("area_sqm"),
            "scraped_at": f["properties"].get("scraped_at_utc"),
        }
        for f in feats
    ]

    bulletin = {
        "as_of": today,
        "service": "paraguay-geodata",
        "version": h.get("version") or dm.get("git_sha"),
        "deployed_at": h.get("deployed_at"),
        "metrics": {
            "total_listings": n_listings,
            "sources": sources,
            "n_sources": n_sources,
            "freshness_median_hours": h.get("data", {}).get("properties", {}).get("freshness_median_hours"),
        },
        "deploys": log,
        "new_listings": new_listings,
        "subscribe_url": "https://geodata.paragu-ai.com/changelog.xml",
    }

    out_path = ROOT / "exports" / "web" / "bulletin.json"
    out_path.write_text(json.dumps(bulletin, indent=2, ensure_ascii=False))
    print(f"  wrote {out_path}")

    # Friendly HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bulletin — Paraguay Geodata</title>
<style>
  body {{
    background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", Roboto, sans-serif; margin: 0; padding: 32px; line-height: 1.6;
  }}
  main {{ max-width: 720px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin: 0 0 8px 0; }}
  h2 {{ font-size: 18px; margin: 32px 0 8px 0; border-bottom: 1px solid #30363d; padding-bottom: 4px; }}
  .meta {{ color: #7d8590; font-size: 13px; }}
  ul {{ padding-left: 20px; }}
  li {{ margin: 4px 0; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .pill {{ display: inline-block; background: #161b22; border: 1px solid #30363d;
           padding: 4px 10px; border-radius: 12px; font-size: 13px; margin-right: 8px; }}
  pre {{ background: #161b22; padding: 12px; border-radius: 6px; overflow-x: auto; }}
</style>
</head>
<body>
<main>
  <h1>📬 Paraguay Geodata Bulletin</h1>
  <p class="meta">As of {today} · v{bulletin['version']} ·
    <a href="/bulletin.json">JSON</a> · <a href="/changelog.xml">RSS</a></p>

  <h2>Numbers</h2>
  <p>
    <span class="pill">{n_listings:,} listings</span>
    <span class="pill">{n_sources} sources</span>
    <span class="pill">freshness {bulletin['metrics']['freshness_median_hours']}h</span>
  </p>

  <h2>Recent deploys</h2>
  <ul>
    {"".join(f"<li><code>{d['sha']}</code> — {d['subject']} <span class='meta'>({d['author']})</span></li>" for d in log)}
  </ul>

  <h2>Latest listings</h2>
  <ul>
    {"".join(f"<li><code>{n['id']}</code> · {n['city']}, {n['state_province']} · ${n['price_usd'] or '?'} · {n['area_sqm'] or '?'} m²</li>" for n in new_listings)}
  </ul>

  <h2>Subscribe</h2>
  <p>Use the <a href="/changelog.xml">RSS feed</a> or the <a href="/bulletin.json">JSON feed</a>.</p>
  <pre>GET https://geodata.paragu-ai.com/bulletin.json</pre>
</main>
</body>
</html>
"""
    html_path = ROOT / "exports" / "web" / "bulletin.html"
    html_path.write_text(html)
    print(f"  wrote {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
