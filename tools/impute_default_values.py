"""tools/impute_default_values.py — fill missing area/depto from title patterns + type median.

Some listings miss metadata that we can confidently infer:

  1. **area**: 4,450 listings (41.3%) have no area_ha. For most property_types
     we can use the median area of known listings of the same type:
       - apartment: 70 m² / 0.007 ha
       - house: 400 m² / 0.04 ha
       - land: 800 m² / 0.08 ha
       - commercial: 285 m² / 0.0285 ha
       - office: 196 m² / 0.0196 ha
     This is a "statistical middle" — better than empty, but flagged as
     `area_source: imputed_median` so filters can show it as approximate.

  2. **depto**: 1,165 listings (10.8%) have no depto. The depto is usually
     in the title: "Asunción", "Ciudad del Este", "San Lorenzo", "Luque"
     etc. We try to match against the 17 known deptos.

  3. **currency**: 1,157 listings (10.7%) have no currency. If the price
     is huge (>10,000,000) it's probably PYG; otherwise USD.

  4. **barrio**: 1,004 listings have no barrio. We try to extract from the
     title (already done by extract_listing_metadata).

Usage:
  python3 -m tools.impute_default_values
  python3 -m tools.impute_default_values --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON_PATH = REPO / "data" / "properties" / "canonical_properties.geojson"


# Median area per property_type (in ha). Computed from the current 10,780-listing
# dataset. Used when no title-based area extraction is possible.
AREA_MEDIAN_BY_TYPE = {
    "apartment":  0.0070,   # 70 m²
    "house":      0.0400,   # 400 m²
    "land":       0.0800,   # 800 m²
    "commercial": 0.0285,   # 285 m²
    "office":     0.0196,   # 196 m²
}


# Paraguay's 17 departments + Capital District. Used to match against title.
DEPTOS = [
    "Asunción", "Concepción", "San Pedro", "Cordillera", "Guairá",
    "Caaguazú", "Caazapá", "Itapúa", "Misiones", "Paraguarí",
    "Alto Paraná", "Central", "Ñeembucú", "Amambay", "Canindeyú",
    "Presidente Hayes", "Boquerón", "Alto Paraguay",
]


def impute_depto(title: str) -> str | None:
    """Match deptos in title. Returns the first match or None."""
    if not title:
        return None
    for depto in sorted(DEPTOS, key=len, reverse=True):  # longest first
        # Whole-word match (case-insensitive). Allow plurals.
        if re.search(rf"\b{re.escape(depto)}\b", title, re.IGNORECASE):
            return depto
    # Common city aliases (covers ~30 cities mapped to their depto)
    aliases = {
        "CDE": "Alto Paraná",
        "Ciudad del Este": "Alto Paraná",
        "Encarnación": "Itapúa",
        "Villarrica": "Guairá",
        "Coronel Oviedo": "Caaguazú",
        "Pedro Juan Caballero": "Amambay",
        "PJC": "Amambay",
        "Pilcomayo": "Central",
        # Alto Paraná
        "Minga Guazú": "Alto Paraná",
        "Minga Guazu": "Alto Paraná",
        "Hernandarias": "Alto Paraná",
        "Presidente Franco": "Alto Paraná",
        "Los Cedrales": "Alto Paraná",
        "Santa Rita": "Alto Paraná",
        "Monday": "Alto Paraná",
        "Mallorquín": "Alto Paraná",
        "Ka'arendy": "Alto Paraná",
        # Central
        "San Lorenzo": "Central",
        "Luque": "Central",
        "Lambaré": "Central",
        "Fernando de la Mora": "Central",
        "Capiatá": "Central",
        "Mariano Roque Alonso": "Central",
        "Limpio": "Central",
        "Ñemby": "Central",
        "Itauguá": "Central",
        "Areguá": "Central",
        "Villeta": "Central",
        # Cordillera
        "Caacupé": "Cordillera",
        "San Bernardino": "Cordillera",
        "Tobatí": "Cordillera",
        "Atyrá": "Cordillera",
        # Itapúa
        "Hohenau": "Itapúa",
        # Paraguarí
        "Paraguarí": "Paraguarí",
        "Carapeguá": "Paraguarí",
        "Ybycuí": "Paraguarí",
        # Other
        "San Estanislao": "San Pedro",
        "Ayolas": "Misiones",
        "Pilar": "Ñeembucú",
        "Concepción": "Concepción",
        "Salto del Guairá": "Canindeyú",
        "Pozo Colorado": "Presidente Hayes",
        "Filadelfia": "Boquerón",
    }
    for alias, depto in aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", title, re.IGNORECASE):
            return depto
    return None


def impute_currency(price: float | None, title: str) -> str | None:
    """If price is large, it's PYG; otherwise USD."""
    if not price or price <= 0:
        return None
    if price > 10_000_000:
        return "PYG"
    if price < 1_000_000:
        return "USD"
    # Ambiguous range — check title for clue
    if title and ("guaraní" in title.lower() or "guarani" in title.lower()):
        return "PYG"
    return "USD"


def impute_area(props: dict) -> tuple[float, str] | None:
    """Impute area from property_type median if available."""
    area = props.get("area_ha")
    if area and area > 0:
        return None  # already has area
    pt = props.get("property_type")
    if pt and pt in AREA_MEDIAN_BY_TYPE:
        return AREA_MEDIAN_BY_TYPE[pt], "imputed_median"
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Impute default values for missing metadata.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON_PATH.exists():
        print(f"  ERR: {CANON_PATH} not found")
        return 1

    print("=== impute_default_values ===")
    data = json.loads(CANON_PATH.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features")

    n_area = 0
    n_depto = 0
    n_currency = 0

    for f in features:
        p = f["properties"]
        flags = p.get("quality_flags") or []

        # area
        result = impute_area(p)
        if result:
            p["area_ha"] = result[0]
            p["area_source"] = result[1]
            # Drop the missing_area flag now that we've imputed
            p["quality_flags"] = [f for f in flags if f != "missing_area"]
            n_area += 1
        else:
            pass  # keep flags as-is

        # depto
        if not p.get("state_province"):
            d = impute_depto(p.get("title") or "")
            if d:
                p["state_province"] = d
                p["state_province_source"] = "title"
                # Drop any foreign_depto flag now that we've resolved
                p["quality_flags"] = [f for f in p.get("quality_flags", []) if f != "foreign_depto"]
                n_depto += 1

        # currency
        if not p.get("currency"):
            c = impute_currency(p.get("price_usd"), p.get("title") or "")
            if c:
                p["currency"] = c
                p["currency_source"] = "inferred"
                # Drop currency_conflict flag (we picked one)
                p["quality_flags"] = [f for f in p.get("quality_flags", []) if f != "currency_conflict"]
                n_currency += 1

    print(f"  area imputed: {n_area:,}")
    print(f"  depto imputed: {n_depto:,}")
    print(f"  currency imputed: {n_currency:,}")

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
