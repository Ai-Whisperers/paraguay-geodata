"""tools/extract_listing_metadata.py — extract area + street from title.

Many listings have area or street info embedded in the title (often the
detail page doesn't expose it as a structured field). This tool:

  1. extracts area from title using Spanish-number regex
  2. extracts street/address from title (common Paraguay prefixes)
  3. extracts bedrooms/bathrooms from title
  4. writes the extracted values as flags on the feature

Currently the data has 4,453 listings with no area (41.3%) and 4,793
listings with no real coords (44.5%). This tool addresses the first.

Area regex patterns handled:
  - "Terreno de 1,000.59m²" → 0.10 ha
  - "Casa 350 m²" / "350 m2" / "350mts2"
  - "5 hectareas" → 5.0 ha
  - "5.5 ha" → 5.5 ha
  - "1.000 x 500 m" → 50.0 ha (rectangular land)

Bedrooms patterns:
  - "3 dormitorios" / "3 dorm" / "3 ambientes" / "3 habitaciones"
  - "Suite principal" → 1
  - "Monoambiente" → 0

Address patterns:
  - "Avda. España" / "Av. España" / "Av España"
  - "Calle Palma"
  - "Casa C/ ..." (con = "with", often an address follows)
  - "km 4.5" (route markers)

Usage:
  python3 -m tools.extract_listing_metadata
  python3 -m tools.extract_listing_metadata --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON_PATH = REPO / "data" / "properties" / "canonical_properties.geojson"


# ------- Area extraction -------

# Spanish/dec numbers: "1.000,59" or "1000.59" or "1,000.59"
_NUMS = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+)"

_AREA_PATTERNS = [
    # explicit "m²" or "m2" or "metros cuadrados"
    (re.compile(rf"{_NUMS}\s*(?:m²|m2|mts2|metros\s*cuadrados|metros\s*2)\b", re.IGNORECASE), "m2"),
    # "5 hectáreas" / "5 ha" / "5 has"
    (re.compile(rf"{_NUMS}\s*(?:hect[áa]reas?|has?)\b", re.IGNORECASE), "ha"),
    # "1,000 x 500 m" — rectangular land
    (re.compile(rf"{_NUMS}\s*[xX]\s*{_NUMS}\s*(?:m²|m2|metros)\b", re.IGNORECASE), "m2_rect"),
]


def parse_decimal(s: str) -> float:
    """Parse '1.000,59' or '1,000.59' or '1000.59' or '5' as float.

    Handles:
      - Spanish: '1.000,59' (thousands-separator=. , decimal-separator=,)
      - English: '1,000.59' (thousands-separator=, , decimal-separator=.)
      - Argentine: '2.200.000' (only thousands-separators=., no decimal)
      - Plain: '1000.59' or '5'
    """
    s = s.strip()
    # Argentine style: only dots, multiple, all 3-digit groups → all thousands
    if "." in s and "," not in s:
        parts = s.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]) and parts[0].isdigit():
            # Like '2.200.000' → '2200000'
            s = s.replace(".", "")
        try:
            return float(s)
        except ValueError:
            pass
    # If both , and . exist, the LAST one is the decimal separator
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # If comma has exactly 3 digits after it, it's a thousands separator
        # else it's a decimal separator (Spanish convention)
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    return float(s)


def extract_area(title: str) -> tuple[float, str] | None:
    """Extract (area_ha, source) from title. Returns None if not found."""
    if not title:
        return None
    for pat, kind in _AREA_PATTERNS:
        m = pat.search(title)
        if not m:
            continue
        if kind == "m2":
            sqm = parse_decimal(m.group(1))
            return round(sqm / 10000, 4), "title_m2"
        elif kind == "ha":
            ha = parse_decimal(m.group(1))
            return round(ha, 4), "title_ha"
        elif kind == "m2_rect":
            # Find the two numbers
            nums = re.findall(r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+", m.group(0))
            if len(nums) >= 2:
                a = parse_decimal(nums[0])
                b = parse_decimal(nums[1])
                return round((a * b) / 10000, 4), "title_m2_rect"
    return None


# ------- Bedrooms extraction -------

_BED_PATTERNS = [
    re.compile(r"(\d+)\s*(?:dormitorios?|dorm\.|dorms|habitaciones?|ambientes?)\b", re.IGNORECASE),
    re.compile(r"\bmonoambiente\b", re.IGNORECASE),  # 0 bedrooms
    re.compile(r"\bsuite\s+principal\b", re.IGNORECASE),  # add 1
]


def extract_bedrooms(title: str) -> int | None:
    if not title:
        return None
    for pat in _BED_PATTERNS:
        m = pat.search(title)
        if m:
            if "monoambiente" in m.group(0).lower():
                return 0
            elif "suite" in m.group(0).lower():
                return 1
            else:
                return int(m.group(1))
    return None


# ------- Address extraction -------

_ADDRESS_PATTERNS = [
    re.compile(r"\b(?:Avda?\.?|Av\.?|Avenida)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)", re.IGNORECASE),
    re.compile(r"\bCalle\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)", re.IGNORECASE),
    re.compile(r"\bkm\s+(\d+(?:\.\d+)?)", re.IGNORECASE),  # route marker
    re.compile(r"\b(?:c/|con)\s+(?:cochera\s+en\s+|acceso\s+a\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", re.IGNORECASE),
]


def extract_address(title: str) -> str | None:
    """Extract street/address from title. Returns the first match or None."""
    if not title:
        return None
    for pat in _ADDRESS_PATTERNS:
        m = pat.search(title)
        if m:
            return m.group(0).strip()
    return None


# ------- Barrio extraction (Py neighborhoods) -------

# Known barrios of Asunción and Central/Cordillera/etc.
_BARRIO_PATTERN = re.compile(
    r"\b(?:barrio|b°)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)",
    re.IGNORECASE,
)


def extract_barrio(title: str) -> str | None:
    if not title:
        return None
    m = _BARRIO_PATTERN.search(title)
    if m:
        return m.group(1).strip()
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract area/street/bedrooms from listing titles.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON_PATH.exists():
        print(f"  ERR: {CANON_PATH} not found — run canonicalize_properties first")
        return 1

    print("=== extract_listing_metadata ===")

    data = json.loads(CANON_PATH.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features")

    n_area = 0
    n_bed = 0
    n_addr = 0
    n_barrio = 0
    n_area_existing = 0
    n_bed_existing = 0

    for f in features:
        p = f["properties"]
        title = p.get("title") or ""
        if not title:
            continue

        # Area
        if not p.get("area_ha") or p["area_ha"] == 0:
            area = extract_area(title)
            if area is not None:
                p["area_ha"] = area[0]
                p["area_source"] = area[1]
                n_area += 1
        else:
            n_area_existing += 1

        # Bedrooms
        if not p.get("bedrooms") or p["bedrooms"] == 0:
            beds = extract_bedrooms(title)
            if beds is not None:
                p["bedrooms"] = beds
                p["bedrooms_source"] = "title"
                n_bed += 1
        else:
            n_bed_existing += 1

        # Address
        addr = extract_address(title)
        if addr:
            p["address"] = addr
            p["address_source"] = "title"
            n_addr += 1

        # Barrio
        b = extract_barrio(title)
        if b:
            p["barrio"] = b
            p["barrio_source"] = "title"
            n_barrio += 1

    print(f"  area extracted: {n_area:,} (was missing {n_area:,} of {n - n_area_existing:,})")
    print(f"  bedrooms extracted: {n_bed:,}")
    print(f"  addresses extracted: {n_addr:,}")
    print(f"  barrios extracted: {n_barrio:,}")

    if args.dry_run:
        print(f"  --dry-run: no writes")
        return 0

    data["features"] = features
    data["generated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    CANON_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  wrote {CANON_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
