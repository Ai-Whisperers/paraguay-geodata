#!/usr/bin/env python3
"""scripts/probe_datos_gov.py — find every PY geo dataset on datos.gov.py."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with open("/tmp/locales_search.json") as f:
    d = json.load(f)
results = d.get("result", {}).get("results", [])
print(f"total results: {len(results)}")
for r in results[:12]:
    title = r.get("title", "?")
    print(f"  {title[:90]}")
    for res in r.get("resources", [])[:2]:
        fmt = res.get("format", "?")
        name = res.get("name", "?")
        url = res.get("url", "")
        print(f"      [{fmt:10s}] {name[:50]:50s}  {url[:80]}")
    print()