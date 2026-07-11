#!/usr/bin/env python3
"""scripts/show_listings_sample.py — print a few listings we scraped."""
import json
import sys

g = json.load(open(sys.argv[1]))
print("features:", len(g["features"]))
print("----first 3 features----")
for f in g["features"][:3]:
    p = f["properties"]
    print(json.dumps(p, indent=2))
    print("---")