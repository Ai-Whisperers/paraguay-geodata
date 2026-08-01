#!/usr/bin/env python3
"""scripts/build_inbio_series.py

Parse every available INBIO zafra PDF into a single time-series JSON so the
viewer can show a 5-year strip chart of soja, arroz, maíz zafriña area by
depto.

Inputs (already in /tmp/inbio_pdfs.txt after running tools/fetch_inbio.py)
    /tmp/inbio_pdfs.txt            — one URL per line
    Zafra-YYYY-YYYY.pdf             — saved alongside by the fetcher

Output
    data/properties/inbio_series.json
        {
          "zafras": [{"year": "2025/2026", "crops": {"soja": {...},
                                                     "arroz": {...},
                                                     "maizZaf": {...}}}],
          "deptos": ["Alto Paraná", "Itapúa", ...]
        }

Usage
    python3 -m scripts.build_inbio_series            # default paths
    python3 -m scripts.build_inbio_series --dry-run   # only parse names
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover
    pdfplumber = None


ZAFRA_RE = re.compile(r"Zafra[- ]?(\d{4})[- ]?(\d{4})", re.I)
ZAFRA_REV = re.compile(r"(\d{4})[- ]?(\d{4})")

# Lines in the PDF text stream look like:
#   "10  ITAPÚA  16.744  16.064  (6.8)"
# Per crop: page 2 (soja), page 4 (arroz), page 6 (maíz zafriña).
ROW_RE = re.compile(
    r"^\s*(\d{1,2})\s+([\wÁÉÍÓÚÑáéíóúñ .-]+?)\s+([\d.,]+|-)\s+([\d.,]+|-)\s*\(?(-?[\d.,%]+)?\)?\s*$"
)

DEPTO_CANON = {
    "ASUNCION": "Asunción", "CONCEPCION": "Concepción", "SAN PEDRO": "San Pedro",
    "CORDILLERA": "Cordillera", "GUAIRA": "Guairá", "CAAGUAZU": "Caaguazú",
    "CAAZAPA": "Caazapá", "ITAPUA": "Itapúa", "MISIONES": "Misiones",
    "PARAGUARI": "Paraguarí", "ALTO PARANA": "Alto Paraná", "CENTRAL": "Central",
    "NEEMBUCU": "Ñeembucú", "AMAMBAY": "Amambay", "CANINDEYU": "Canindeyú",
    "PRESIDENTE HAYES": "Presidente Hayes", "ALTO PARAGUAY": "Alto Paraguay",
    "BOQUERON": "Boquerón",
}


def _norm_depto(raw: str) -> str | None:
    s = raw.upper().strip().replace("DPT.", "").replace("DPTO.", "")
    s = (s.replace("Á","A").replace("É","E").replace("Í","I")
           .replace("Ó","O").replace("Ú","U").replace("Ñ","N"))
    if s in DEPTO_CANON:
        return DEPTO_CANON[s]
    for k, v in DEPTO_CANON.items():
        if k.startswith(s) or s.startswith(k):
            return v
    return None


def _parse_number(token: str) -> float | None:
    if not token or token == "-":
        return None
    # Spanish-formatted: "16.744" is 16744, "1.234,5" is 1234.5
    s = token.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _pdf_to_rows(path: Path) -> dict[str, list[tuple[str, float | None, float | None]]]:
    """Return {crop_name: [(depto, v1, v2), ...]} from the INBIO PDF."""
    if pdfplumber is None:
        raise SystemExit("pdfplumber required: pip install pdfplumber")
    out: dict[str, list[tuple[str, float | None, float | None]]] = {
        "soja": [], "arroz": [], "maizZaf": [],
    }
    with pdfplumber.open(str(path)) as pdf:
        for pidx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            crop = None
            if "SOJA" in text[:200].upper() or "SOJA" in text.upper():
                crop = "soja"
            elif "ARROZ" in text[:200].upper() or "ARROZ" in text.upper():
                crop = "arroz"
            elif "MAIZ" in text[:200].upper() or "MAÍZ" in text[:200].upper() or "MAIZ" in text.upper():
                crop = "maizZaf"
            if not crop:
                continue
            for line in text.splitlines():
                m = ROW_RE.match(line)
                if not m:
                    continue
                code, name, v1, v2, _diff = m.groups()
                depto = _norm_depto(name)
                if not depto:
                    continue
                out[crop].append((depto, _parse_number(v1), _parse_number(v2)))
    return out


def build(pdf_paths: list[Path]) -> dict:
    series: list[dict] = []
    seen_deptos: set[str] = set()

    for pdf in sorted(pdf_paths):
        # Derive "2025/2026" from filename
        m = ZAFRA_RE.search(pdf.name) or ZAFRA_REV.search(pdf.name)
        if not m:
            print(f"skip (no zafra year): {pdf.name}")
            continue
        year = f"{m.group(1)}/{m.group(2)}"
        try:
            rows = _pdf_to_rows(pdf)
        except Exception as exc:
            print(f"skip (parse error: {exc}): {pdf.name}")
            continue
        # Build per-zafra entry, dropping empty crops so the timeline stays clean
        crops: dict[str, dict] = {}
        for crop, items in rows.items():
            depto_data = {}
            for depto, v1, v2 in items:
                depto_data[depto] = {"prev_ha": v1, "current_ha": v2}
                if v2 is not None:
                    seen_deptos.add(depto)
            if depto_data:
                crops[crop] = depto_data
        if not crops:
            continue
        series.append({"year": year, "crops": crops,
                       "source_pdf": pdf.name})

    return {
        "zafras": series,
        "deptos": sorted(seen_deptos),
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf-list", type=Path, default=Path("/tmp/inbio_pdfs.txt"))
    ap.add_argument("--pdf-dir", type=Path,
                    default=Path("/root/paraguay-geodata/data/inbio_pdfs"))
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data/properties/inbio_series.json")
    args = ap.parse_args(argv)

    pdf_paths: list[Path] = []
    if args.pdf_list.exists():
        for line in args.pdf_list.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pdf_paths.append(args.pdf_dir / Path(line).name)
    elif args.pdf_dir.exists():
        pdf_paths = sorted(args.pdf_dir.glob("*.pdf"))

    if not pdf_paths:
        sys.exit("no PDFs found; pass --pdf-list or --pdf-dir")

    payload = build(pdf_paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK inbio-series: {len(payload['zafras'])} zafras, {len(payload['deptos'])} deptos, "
          f"{len(payload['zafras'][0]['crops']) if payload['zafras'] else 0} crops")


if __name__ == "__main__":
    main()