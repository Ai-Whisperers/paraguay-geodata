#!/usr/bin/env python3
"""scripts/inbio_pdf_to_json.py — parse INBIO zafra PDFs to per-dept area JSON.

INBIO PDFs all share the same structure:
  - Title: "Estimación de Superficies"
  - Page(s) with 4-col table:
      Departamentos | CampañaN-1 / N | CampañaN / N | Diferencia
  - Followed by "Totales X.XXX"

Run:  python3 scripts/inbio_pdf_to_json.py <pdf> <output.json>

Output: list of {depto_code, depto_name, area_ha_{y1}, area_ha_{y2}, diff}
        + campaign header
        + totals
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

DEPT_MAP = {
    "Concepción": "PY-1",
    "San Pedro": "PY-2",
    "Cordillera": "PY-3",
    "Guairá": "PY-4",
    "Caaguazú": "PY-5",
    "Caazapá": "PY-6",
    "Itapúa": "PY-7",
    "Misiones": "PY-8",
    "Paraguarí": "PY-9",
    "Alto Paraná": "PY-10",
    "Central": "PY-11",
    "Ñeembucú": "PY-12",
    "Amambay": "PY-13",
    "Canindeyú": "PY-14",
    "Presidente Hayes": "PY-15",
    "Boquerón": "PY-16",
    "Alto Paraguay": "PY-17",
    "Asunción": "PY-ASU",
}


def parse_number(s: str) -> float | None:
    """Parse dot-separated PY numbers, including '(-1.234)'."""
    if not s:
        return None
    s = s.strip()
    if s in ("-", "—", ""):
        return None
    # parenthesized = negative
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(".", "").replace(",", "")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def parse_pdf(path: Path) -> dict:
    out = {"source_pdf": str(path), "tables": []}
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for t_idx, t in enumerate(tables):
                if not t or len(t[0]) < 4:
                    continue
                # First col must be depto
                if t[0][0] not in ("Departamentos", "Departamento"):
                    continue
                # Extract campaign years from text
                text = page.extract_text() or ""
                campaign_match = re.search(r"(\d{4}/\d{4})\s*[-–]\s*(\d{4}/\d{4})", text)
                if not campaign_match:
                    continue
                c1, c2 = campaign_match.group(1), campaign_match.group(2)
                crop_match = re.search(r"(SOJA|ARROZ|MA[IÍ]Z|TRIGO|CANOLA|GIRASOL|SESA?MO|KA['\u2019]?A HE[ÊE]?E|SESAMO)", text, re.I)
                region_match = re.search(r"Regi[oó]n\s+Oriental|Rep[uú]blica\s+del\s+Paraguay|Chaco|Occidental", text, re.I)
                crop = crop_match.group(1).upper() if crop_match else "?"
                region = region_match.group(0) if region_match else "?"

                # INBIO PDFs put dept name in the text stream, not in table cells.
                # Extract dept rows from the text instead.
                text_lines = (page.extract_text() or "").split("\n")
                rows = []
                total_v1 = total_v2 = None
                # Pattern: "DD Name 1.234 5.678 (.123)" — department code, name, then 4 numbers (v1 v2 diff)
                DEPTO_LINE_RE = re.compile(
                    r"^(\d{1,2})\s+([A-ZÁÉÍÓÚÑa-záéíóúñ .-]+?)\s+([\d.,]+|-)\s+([\d.,]+|-|-)?\s*\(?(-?[\d.,]+)?\)?\s*$"
                )
                # More flexible: any line that looks like a depto table row
                for line in text_lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.lower().startswith("total"):
                        # parse numbers
                        nums = re.findall(r"\(?-?[\d.,]+\)?", line)
                        nums = [parse_number(n) for n in nums if parse_number(n) is not None]
                        if len(nums) >= 2:
                            total_v1, total_v2 = nums[0], nums[1]
                        continue
                    # Try dept-row pattern: "## Name V1 V2 (diff)"
                    # Split line into tokens, take last 4 as v1, v2, then diff in parens
                    parts = line.split()
                    if len(parts) >= 4 and parts[0].isdigit():
                        code = parts[0]
                        # Reconstruct name (everything except first + last 4 tokens)
                        # Last 3 tokens are: v1 v2 (diff)
                        # Actually it's v1 v2 then (diff) which is 1 token with parentheses, or diff
                        # Find the first numeric token
                        name_parts = []
                        i = 1
                        while i < len(parts) and not re.match(r"^[\d.,\-()]+$", parts[i]):
                            name_parts.append(parts[i])
                            i += 1
                        name = " ".join(name_parts).strip()
                        # remaining = numbers and maybe parens
                        numbers = []
                        while i < len(parts):
                            tok = parts[i]
                            if re.match(r"^[\d.,]+$|^\(?-?[\d.,]+\)?$", tok):
                                # strip parens
                                clean = tok.strip("()")
                                v = parse_number(clean)
                                if v is not None:
                                    numbers.append(v)
                            i += 1
                        if name and len(numbers) >= 2:
                            v1, v2 = numbers[0], numbers[1]  # first 2 are v1 + v2 (PDF: prev year, current year)
                            # Map code to name (INBIO codes 1-17 + 0=Asunción)
                            code_to_name = {
                                "0": "Asunción", "1": "Concepción", "2": "San Pedro",
                                "3": "Cordillera", "4": "Guairá", "5": "Caaguazú",
                                "6": "Caazapá", "7": "Itapúa", "8": "Misiones",
                                "9": "Paraguarí", "10": "Alto Paraná", "11": "Central",
                                "12": "Ñeembucú", "13": "Amambay", "14": "Canindeyú",
                                "15": "Presidente Hayes", "16": "Boquerón", "17": "Alto Paraguay",
                                "18": "TOTAL",
                            }
                            canonical = code_to_name.get(int(code), name) if code.isdigit() else name
                            rows.append({
                                "depto_inbio_code": int(code) if code.isdigit() else 0,
                                "depto_name": canonical,
                                "depto_code": DEPT_MAP.get(canonical, ""),
                                f"area_ha_{c1}": v1,
                                f"area_ha_{c2}": v2,
                            })
                out["tables"].append({
                    "page": i + 1,
                    "campaign_1": c1,
                    "campaign_2": c2,
                    "crop": crop,
                    "region": region,
                    "unit": "ha",
                    "totals": {
                        "v1": total_v1,
                        "v2": total_v2,
                    },
                    "rows": rows,
                })
    return out


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        print("usage: inbio_pdf_to_json.py <pdf> <output.json> [--crop CROP]")
        return 1
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    # Optional --crop on cmdline
    crop_arg = None
    rest = sys.argv[3:]
    if rest and rest[0] == "--crop":
        crop_arg = rest[1].upper() if len(rest) > 1 else None

    # Try to detect crop from filename (e.g. "zafra_2025_2026.pdf" or "SOJA-ARROZ-MAIZ-zafra-2024-2025.pdf")
    fname = src.name.upper()
    crop_from_name = None
    for crop in ("SOJA", "ARROZ", "TRIGO", "CANOLA", "GIRASOL", "MAIZ"):
        if crop in fname:
            if crop_from_name is None:
                crop_from_name = crop
            elif crop == "MAIZ" and crop_from_name in ("SOJA", "ARROZ"):
                pass
            else:
                crop_from_name = crop  # last match wins
    if crop_arg:
        crop_from_name = crop_arg

    parsed = parse_pdf(src)
    # If we detected a crop from filename, attach it to all tables that don't have one
    if crop_from_name:
        for tbl in parsed["tables"]:
            if tbl["crop"] == "?":
                tbl["crop"] = crop_from_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(parsed, indent=2))
    n_tables = len(parsed["tables"])
    n_rows = sum(len(t["rows"]) for t in parsed["tables"])
    print(f"parsed {src.name}: {n_tables} tables, {n_rows} dept records")
    for t in parsed["tables"]:
        print(f"  p.{t['page']}  crop={t['crop']}  region={t['region']}  {t['campaign_1']}→{t['campaign_2']}  "
              f"{len(t['rows'])} dept rows  totals={t['totals']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())