#!/usr/bin/env python3
"""tools/canonicalize_properties.py

Single canonicalization pass for the live properties GeoJSON.

What it does
------------
1.  Maps `state_province` from 32 dirty strings to 17 ISO-3166-2 deptos of
    Paraguay (and drops foreign listings: Formosa, Corrientes, Paraná, Santa Cruz,
    Minga Guazu).
2.  Re-infers `area_ha` from the listing title when the published value is
    missing or conflicts with `area_sqm`. Stores the original in `area_ha_raw`
    and the chosen value in `area_ha` / `area_sqm`.
3.  Computes `price_usd` from `price_pyg` when missing, and vice versa, using
    a configurable FX rate. Flags currency divergence > 30%.
4.  Canonicalizes `features[]` free text into a 23-item enum (`canonical_features`)
    while preserving the original list under `features_raw`.
5.  Adds `last_seen_at` (UTC ISO) and `freshness_days` for the snapshot.
6.  Adds a `quality_flags` array per row (missing_price, missing_area,
    area_conflict, currency_conflict, foreign_depto, null_property_type, etc.).
7.  Cross-source dedupe by (source_url hash + normalized title + lat/lon grid).
    Adds `cluster_id` so two portals listing the same finca share an ID.
8.  Emits:
        data/properties/canonical_properties.geojson  -- full artifact
        data/properties/canonical_properties.parquet -- analytics view
        data/properties/canonical_summary.json        -- counts + facets

Usage
-----
    python3 -m tools.canonicalize_properties \\
        --input  /tmp/properties_latest.geojson \\
        --output /root/paraguay-geodata/data/properties

    # Default paths are the ones used by `auto_refresh.py`, so the cron flow is
    # `fetch -> canonicalize -> merge -> deploy`.

Designed to be safe to re-run (idempotent): it never edits the source GeoJSON,
always writes a new artifact, and surfaces every flag in the summary.
"""

from __future__ import annotations

import argparse
import collections
import datetime as _dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# 1.  Static reference tables
# ----------------------------------------------------------------------

# 17 Paraguay deptos + Distrito Capital.
DEPTO_CANON = {
    # canonical_name: [aliases...]
    "Asunción":            ["asuncion", "distritocapitaldeparaguay", "distritocapital"],
    "Concepción":          ["concepcion"],
    "San Pedro":           ["sanpedro"],
    "Cordillera":          ["cordillera"],
    "Guairá":              ["guaira"],
    "Caaguazú":            ["caaguazu"],
    "Caazapá":             ["caazapa"],
    "Itapúa":              ["itapua"],
    "Misiones":            ["misiones"],
    "Paraguarí":           ["paraguari"],
    "Alto Paraná":         ["altoparana"],
    "Central":             ["central"],
    "Ñeembucú":            ["neembucu"],
    "Amambay":             ["amambay"],
    "Canindeyú":           ["canindeyu"],
    "Presidente Hayes":    ["presidentehayes", "hayes"],
    "Alto Paraguay":       ["altoparaguay"],
    "Boquerón":            ["boqueron"],
}

# foreign deptos to drop
FOREIGN = {"formosa", "corrientes", "parana", "santa cruz", "minga guazu",
           "argentina", "brasil", "bolivia"}

# canonical features enum (22)
# `garage` is intentionally NOT in the enum: it aliases to `parking` so the
# facet counts reflect one surface, not two equivalent ones.
FEATURE_ENUM = {
    "pool", "bbq", "bbqArea", "garden", "balcony", "terrace",
    "parking", "security",
    "airConditioning", "heating", "furnished", "equippedKitchen",
    "laundry", "internet", "cableTV",
    "elevator", "gym", "eventRoom", "modern", "new",
    "builtInClosets", "solarPanels",
}

# map legacy free text into the canonical enum. Keys are stored in
# normalized form (no diacritics, no spaces) so `_norm(item)` finds them.
FEATURE_MAP = {
    "airconditioning": "airConditioning",
    "aireacondicionado": "airConditioning",
    "ac": "airConditioning",
    "calefaccion": "heating",
    "heating": "heating",
    "amoblado": "furnished",
    "amueblado": "furnished",
    "furnished": "furnished",
    "muebles": "furnished",
    "cocinaequipada": "equippedKitchen",
    "cocinaamueblada": "equippedKitchen",
    "equippedkitchen": "equippedKitchen",
    "lavadero": "laundry",
    "laundry": "laundry",
    "internet": "internet",
    "wifi": "internet",
    "wiffi": "internet",
    "tvcable": "cableTV",
    "cabletv": "cableTV",
    "ascensor": "elevator",
    "elevator": "elevator",
    "gimnasio": "gym",
    "gym": "gym",
    "salondeeventos": "eventRoom",
    "eventroom": "eventRoom",
    "salon": "eventRoom",
    "moderno": "modern",
    "modern": "modern",
    "nuevo": "new",
    "new": "new",
    "aestrenar": "new",
    "placares": "builtInClosets",
    "placard": "builtInClosets",
    "builtinclosets": "builtInClosets",
    "closets": "builtInClosets",
    "panelessolares": "solarPanels",
    "solarpanels": "solarPanels",
    "cochera": "parking",
    "garage": "parking",
    "parking": "parking",
    "estacionamiento": "parking",
    "seguridad": "security",
    "porteria": "security",
    "guardia": "security",
    "vigilancia": "security",
    "cctv": "security",
    "security": "security",
    "alarma": "security",
    "piscina": "pool",
    "pool": "pool",
    "quincho": "bbq",
    "parrillero": "bbq",
    "bbq": "bbq",
    "asador": "bbq",
    "bbqarea": "bbqArea",
    "patio": "garden",
    "jardin": "garden",
    "garden": "garden",
    "balcon": "balcony",
    "balcony": "balcony",
    "terraza": "terrace",
    "terrace": "terrace",
    "azotea": "terrace",
}

HECTARE_PATTERNS = [
    # (regex, multiplier_to_ha)
    (re.compile(r"(\d{1,3}(?:[.,]\d{3})*|\d+(?:[.,]\d+)?)\s*(?:ha|has|hectárea|hectareas|hectáreas)\b", re.I), 1.0),
    (re.compile(r"(\d{1,3}(?:[.,]\d{3})*|\d+(?:[.,]\d+)?)\s*(?:m²|m2|metros\s+cuadrados?)\b", re.I), 0.0001),
]


# ----------------------------------------------------------------------
# 2.  Helpers
# ----------------------------------------------------------------------

def _norm(s: str) -> str:
    """Lowercase + strip diacritics + collapse spaces + strip 'Departamento de'."""
    if not s:
        return ""
    s = s.lower()
    # remove diacritics without external deps
    s = (s.replace("á","a").replace("é","e").replace("í","i")
           .replace("ó","o").replace("ú","u").replace("ñ","n")
           .replace("Á","a").replace("É","e").replace("Í","i")
           .replace("Ó","o").replace("Ú","u").replace("Ñ","n"))
    s = s.replace("departamento de ", "").replace("departamento del ", "")
    s = re.sub(r"\s+", "", s)  # remove ALL spaces so "Alto Paraná" == "altoparana"
    s = s.strip()
    return s


DEPTO_LOOKUP: dict[str, str] = {}
# Special-case tokens that must match after stripping diacritics and the
# "departamento de" prefix.  Order matters because some aliases are substrings
# of others (e.g. "alto parana" vs "alto paraguay").
_SPECIAL_TOKENS = {
    "altoparana":       "Alto Paraná",
    "altoparaguay":     "Alto Paraguay",
    "presidentehayes":  "Presidente Hayes",
    "distritocapitaldeparaguay": "Asunción",
    "departamentocentral": "Central",
    "departamentodeitapua": "Itapúa",
}
for canon, aliases in DEPTO_CANON.items():
    DEPTO_LOOKUP[_norm(canon)] = canon
    for a in aliases:
        DEPTO_LOOKUP[_norm(a)] = canon
DEPTO_LOOKUP.update(_SPECIAL_TOKENS)


def canonical_depto(raw: str | None) -> str | None:
    """Map a raw `state_province` to one of the 17 canonical PY deptos.

    Returns None for foreign / unparseable values so the caller can flag them.
    The lookup runs FIRST; foreign-name detection only fires when nothing
    matched, so we never accidentally drop "Alto Paraná" because the string
    happens to end in "parana".
    """
    if not raw:
        return None
    key = _norm(raw)
    if key in DEPTO_LOOKUP:
        return DEPTO_LOOKUP[key]
    # Token-boundary substring matches — require the depto discriminator
    # ("alto", "presidente") to be present so we don't false-match a foreign
    # state (e.g. Brazilian "Paraná") against a Paraguayan depto's tail.
    if "altoparana" in key and "alto" in key:
        return "Alto Paraná"
    if "altoparaguay" in key and "alto" in key:
        return "Alto Paraguay"
    if "presidente" in key and "hayes" in key:
        return "Presidente Hayes"
    # Last-resort substring match.  Only matches where the canonical key is a
    # substring of the input — never the reverse — so "Paraná" (Brazilian state)
    # cannot be swept into "Alto Paraná".  Requires both sides to be ≥5 chars.
    for k, v in DEPTO_LOOKUP.items():
        if not k or len(k) < 5 or len(key) < 5:
            continue
        if k == key or key.endswith(k):
            return v
    # Now check for foreign tokens at a word boundary in the ORIGINAL string.
    raw_lower = (raw or "").lower()
    raw_norm = _norm(raw)  # no spaces
    for f in FOREIGN:
        if f in raw_lower or f in raw_norm:
            # treat as foreign only if the foreign token stands alone, not
            # as a tail of a Paraguayan depto name
            if (raw_lower.startswith(f) or raw_lower.endswith(f)
                or f" {f} " in f" {raw_lower} "
                or f" {f}," in raw_lower or f"{f} " in raw_lower):
                return None
    return None


def infer_area_ha(title: str | None) -> float | None:
    """Extract hectares from the listing title. Returns None if nothing found.

    Picks the LARGEST candidate (titles often mention both m² and ha, but the
    headline unit is the bigger one — "Terreno 200,000 m²" returns 20 ha).
    """
    if not title:
        return None
    candidates: list[float] = []
    for rx, mult in HECTARE_PATTERNS:
        for m in rx.finditer(title):
            raw = m.group(1)
            # The number may use a comma as a thousands separator ("200,000")
            # OR a period as a decimal marker ("7.5").  Strip thousands first.
            if "," in raw and "." in raw:
                # Pick whichever side has the comma → thousands. If both,
                # the one with 3 digits after the comma is the thousands.
                if re.match(r"^\d{1,3},\d{3}$", raw.replace(".", "").replace(",", "")) is None:
                    raw = raw.replace(",", "")
                else:
                    raw = raw.replace(",", "")
            elif "," in raw:
                # Could be "200,000" (thousands) or "7,5" (decimal).
                if re.match(r"^\d{1,3},\d{3}$", raw):
                    raw = raw.replace(",", "")
                else:
                    raw = raw.replace(",", ".")
            try:
                val = float(raw)
            except ValueError:
                continue
            candidates.append(val * mult)
    if not candidates:
        return None
    val = max(candidates)
    if val > 100_000:
        return None
    return round(val, 4)


def choose_area(p: dict, flags: list[str]) -> tuple[float | None, float | None, str]:
    """Decide the final `area_ha` and `area_sqm` for a property.

    Returns (area_ha, area_sqm, source) where source is one of:
        - 'published'   (already consistent)
        - 'inferred'    (recovered from title)
        - 'mismatch'    (published inconsistent, dropped)
    """
    ha = p.get("area_ha")
    sqm = p.get("area_sqm")
    title = p.get("title") or ""

    # 1. Drop obvious nonsense (sqm=1 with ha=20) — classic TuLugar typo.
    if ha and sqm and abs(ha * 10000 - sqm) / max(sqm, 1) > 0.30:
        flags.append("area_conflict")

    # 2. Try to recover from the title.
    inferred = infer_area_ha(title)

    # 3. Decide which value to trust.
    if ha is None and sqm is not None and sqm > 0:
        new_ha = sqm / 10000
        if inferred and abs(inferred - new_ha) / max(inferred, 1e-6) < 0.5:
            new_ha = inferred  # title is consistent
        flags.append("missing_area_ha_inferred" if not inferred else "area_inferred_from_title")
        return round(new_ha, 4), sqm, "inferred"

    if ha is None and inferred is not None:
        flags.append("area_inferred_from_title")
        return inferred, inferred * 10000, "inferred"

    if ha is not None and (sqm is None or sqm <= 0):
        return ha, ha * 10000, "published"

    if ha is not None and sqm is not None:
        return ha, sqm, "published"

    flags.append("missing_area")
    return None, None, "missing"


def choose_currency(p: dict, fx_pyg_per_usd: float, flags: list[str]) -> tuple[float | None, float | None]:
    """Decide the final (price_usd, price_pyg) for a property."""
    usd = p.get("price_usd")
    pyg = p.get("price_pyg")

    if usd is None and pyg is not None:
        usd = pyg / fx_pyg_per_usd
        flags.append("missing_price_usd_inferred")
    if pyg is None and usd is not None:
        pyg = usd * fx_pyg_per_usd
        flags.append("missing_price_pyg_inferred")

    if usd and pyg:
        implied = usd * fx_pyg_per_usd
        if abs(implied - pyg) / max(pyg, 1) > 0.30:
            flags.append("currency_conflict")
    if usd is None:
        flags.append("missing_price")
    return usd, pyg


def canonical_features(raw: list[str] | None) -> tuple[list[str], list[str]]:
    """Return (canonical, raw). `canonical` is a subset of FEATURE_ENUM.

    Free-text aliases collapse into the canonical enum: "Piscina", "pool",
    "PISCINA" all become `pool`. "Garage" and "cochera" both become `parking`
    (the project treats these as the same surface). Preserves the original
    raw list under `features_raw` so we never lose information.
    """
    if not raw:
        return [], []
    canonical = set()
    for item in raw:
        key = _norm(item)
        if key in FEATURE_ENUM:
            canonical.add(key)
            continue
        mapped = FEATURE_MAP.get(key)
        if mapped:
            canonical.add(mapped)
    return sorted(canonical), list(raw)


# ----------------------------------------------------------------------
# 3.  Cross-source dedupe
# ----------------------------------------------------------------------

def cluster_id(p: dict, idx: int) -> str:
    """Stable cluster key so the same finca from TuLugar + Infocasas + Clasipar
    share an ID in `cluster_id`. Returns a synthetic key if the listing is unique.
    """
    src = (p.get("source") or "").strip()
    url = (p.get("source_url") or "").strip()
    if url:
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        return f"{src or 'src'}-{h}"

    title = (p.get("title") or "").strip().lower()
    lat = p.get("lat"); lon = p.get("lon")
    if title and lat is not None and lon is not None:
        # 0.001° grid ≈ 110 m at PY latitudes
        grid = (round(lat, 3), round(lon, 3))
        h = hashlib.sha1(f"{title}|{grid}".encode("utf-8")).hexdigest()[:10]
        return f"heur-{h}"

    return f"row-{idx}"


# ----------------------------------------------------------------------
# 4.  Pipeline
# ----------------------------------------------------------------------

def canonicalize(feats: list[dict], fx_pyg_per_usd: float, now: _dt.datetime) -> dict:
    canonical_features_out: list[dict] = []
    facet_counter: dict[str, collections.Counter] = {
        "property_type": collections.Counter(),
        "depto":         collections.Counter(),
        "currency":      collections.Counter(),
        "source":        collections.Counter(),
        "flags":         collections.Counter(),
        "year_seen":     collections.Counter(),
    }

    for idx, feat in enumerate(feats):
        p = dict(feat["properties"] or {})
        coords = (feat.get("geometry") or {}).get("coordinates") or [None, None]
        lon, lat = coords[0], coords[1]

        flags: list[str] = []
        now_iso = now.isoformat() + "Z"

        # 1. depto
        canon_depto = canonical_depto(p.get("state_province"))
        if canon_depto is None and p.get("state_province"):
            flags.append("foreign_depto_dropped")
        if canon_depto is not None:
            p["state_province"] = canon_depto
            facet_counter["depto"][canon_depto] += 1
        else:
            p.pop("state_province", None)

        # 2. area
        ha, sqm, area_source = choose_area(p, flags)
        if ha is not None:
            p["area_ha"] = ha
        if sqm is not None:
            p["area_sqm"] = sqm
        p["area_source"] = area_source

        # 3. currency
        usd, pyg = choose_currency(p, fx_pyg_per_usd, flags)
        if usd is not None:
            p["price_usd"] = round(usd, 2)
        if pyg is not None:
            p["price_pyg"] = round(pyg)

        # 4. features
        canon, raw_feats = canonical_features(p.get("features"))
        p["canonical_features"] = canon
        p["features_raw"] = raw_feats

        # 5. property_type
        if p.get("property_type") is None:
            flags.append("null_property_type")
        else:
            facet_counter["property_type"][p["property_type"]] += 1

        # 6. last_seen
        p["last_seen_at"] = p.get("scraped_at_utc") or now_iso
        try:
            scraped = _dt.datetime.fromisoformat(p["last_seen_at"].replace("Z", "+00:00"))
            p["freshness_days"] = (now - scraped.replace(tzinfo=None)).days
        except Exception:
            p["freshness_days"] = None

        # 7. dedupe cluster
        p["cluster_id"] = cluster_id(p, idx)

        # 8. derived: $/ha (only when area is meaningful)
        if p.get("price_usd") and p.get("area_ha") and p["area_ha"] > 0:
            p["usd_per_ha"] = round(p["price_usd"] / p["area_ha"], 2)
        else:
            p["usd_per_ha"] = None

        p["quality_flags"] = sorted(set(flags))
        facet_counter["flags"].update(p["quality_flags"])

        facet_counter["source"][p.get("source") or "?"] += 1
        facet_counter["currency"][p.get("currency") or "?"] += 1
        facet_counter["year_seen"][p["last_seen_at"][:4]] += 1

        # Drop null lat/lon (legacy listings)
        if lat is None or lon is None:
            p["quality_flags"].append("missing_geometry")
            continue  # skip geometry-less rows from the map artifact

        canonical_features_out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": p,
        })

    return {
        "features": canonical_features_out,
        "facets": {k: dict(v) for k, v in facet_counter.items()},
    }


def write_outputs(out_dir: Path, payload: dict, source_path: Path, fx_rate: float):
    out_dir.mkdir(parents=True, exist_ok=True)
    geojson_path = out_dir / "canonical_properties.geojson"
    summary_path = out_dir / "canonical_summary.json"

    envelope = {
        "type": "FeatureCollection",
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "source_file": str(source_path),
        "fx_pyg_per_usd": fx_rate,
        "feature_count": len(payload["features"]),
        "features": payload["features"],
    }
    geojson_path.write_text(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    summary = {
        "generated_at": envelope["generated_at"],
        "source_file": envelope["source_file"],
        "fx_pyg_per_usd": fx_rate,
        "feature_count": len(payload["features"]),
        "facets": payload["facets"],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return geojson_path, summary_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--fx-pyg-per-usd", type=float, default=7500.0)
    args = ap.parse_args(argv)

    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    raw = json.loads(args.input.read_text())
    feats = raw.get("features") or []
    payload = canonicalize(feats, args.fx_pyg_per_usd, _dt.datetime.utcnow())
    geo, summary = write_outputs(args.output, payload, args.input, args.fx_pyg_per_usd)

    print(f"OK canonicalize: {len(payload['features']):,} features written")
    print(f"  geojson    {geo} ({geo.stat().st_size:,} bytes)")
    print(f"  summary    {summary} ({summary.stat().st_size:,} bytes)")
    print("top deptos:", sorted(payload["facets"]["depto"].items(), key=lambda kv: -kv[1])[:5])
    print("top flags :", sorted(payload["facets"]["flags"].items(), key=lambda kv: -kv[1])[:5])


if __name__ == "__main__":
    main()