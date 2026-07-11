#!/usr/bin/env python3
"""scripts/simplify_geojson.py — Douglas-Peucker polygon simplifier.

Reduces coordinate density by 10-50x with ~0.001° tolerance (≈110 m).

Run: python3 scripts/simplify_geojson.py <input> <output> [tolerance_deg]
"""
import json
import math
import sys
from pathlib import Path


def perp_distance(point, line_start, line_end):
    """Perpendicular distance from point to the segment."""
    if line_start == line_end:
        return math.hypot(point[0] - line_start[0], point[1] - line_start[1])
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    den = math.hypot(y2 - y1, x2 - x1)
    return num / den


def douglas_peucker(points, tol):
    if len(points) < 3:
        return points
    # keep first and last
    keep = [False] * len(points)
    keep[0] = True
    keep[-1] = True
    _dp_iter(points, 0, len(points) - 1, tol, keep)
    return [p for p, k in zip(points, keep) if k]


def _dp_iter(points, lo, hi, tol, keep):
    if hi <= lo + 1:
        return
    max_d = 0
    max_i = lo
    for i in range(lo + 1, hi):
        d = perp_distance(points[i], points[lo], points[hi])
        if d > max_d:
            max_d = d
            max_i = i
    if max_d > tol:
        keep[max_i] = True
        _dp_iter(points, lo, max_i, tol, keep)
        _dp_iter(points, max_i, hi, tol, keep)


def simplify_ring(ring, tol):
    if len(ring) < 4:
        return ring
    # Preserve first == last closure
    closed = ring[0] == ring[-1]
    pts = ring[:-1] if closed else ring
    simp = douglas_peucker(pts, tol)
    if closed and simp and simp[0] != simp[-1]:
        simp.append(simp[0])
    return simp


def simplify_geom(geom, tol):
    t = geom["type"]
    if t == "Polygon":
        coords = geom["coordinates"]
        return {
            "type": "Polygon",
            "coordinates": [[simplify_ring(r, tol) for r in poly] for poly in coords],
        }
    if t == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [
                [[simplify_ring(r, tol) for r in poly] for poly in mp]
                for mp in geom["coordinates"]
            ],
        }
    return geom


def main() -> int:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.001  # ~110 m

    fc = json.loads(src.read_text())
    before = src.stat().st_size
    for feat in fc["features"]:
        if feat.get("geometry"):
            feat["geometry"] = simplify_geom(feat["geometry"], tol)
    dst.write_text(json.dumps(fc))
    after = dst.stat().st_size
    print(f"{src.name}: {before:,} → {after:,} bytes ({100*after/before:.1f}%), tol={tol}°")
    return 0


if __name__ == "__main__":
    sys.exit(main())