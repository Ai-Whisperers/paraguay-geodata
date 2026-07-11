"""
tools/fetch_bcp_rates.py — BCP interest rates + macro indicators (Phase 1.5 stub).

Sources (all free, public):
  - Tasas Bancos XLSX (monthly, since 1991)
  - Tasas Financieras XLSX (monthly, since 2012)
  - TPM / Tasa Interbancaria / IPC / RIN (daily + monthly)
  - Tipo de cambio PYG/USD (daily)
  - Remesas familiares (quarterly)
  - Mercado de valores / BVPASA (registry)

Run:
    python3 -m tools.fetch_bcp_rates --indicator rates
    python3 -m tools.fetch_bcp_rates --indicator remesas
    python3 -m tools.fetch_bcp_rates --indicator macro
    python3 -m tools.fetch_bcp_rates --indicator all --apply

TODO(Phase 1.5): implement against bcp.gov.py XLSX downloads.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


INDICATORS = {
    # Core rates
    "rates_bancos":       {"label": "Tasas Bancos XLSX (tasas activas/pasivas)",   "freq": "monthly", "series_from": 1991, "phase": "1.5"},
    "rates_financieras":  {"label": "Tasas Financieras XLSX",                       "freq": "monthly", "series_from": 2012, "phase": "1.5"},
    "tpm":                {"label": "Tasa de Política Monetaria",                   "freq": "daily",   "series_from": 2010, "phase": "1.5"},
    "tasa_interbancaria": {"label": "Tasa Interbancaria",                          "freq": "daily",   "series_from": 2010, "phase": "1.5"},
    "usuraria_mn":        {"label": "Tasa Usuraria (Moneda Nacional)",              "freq": "monthly", "series_from": 2010, "phase": "1.5"},
    "usuraria_me":        {"label": "Tasa Usuraria (Moneda Extranjera)",           "freq": "monthly", "series_from": 2010, "phase": "1.5"},
    "morosidad_bancos":   {"label": "Morosidad Bancaria",                          "freq": "monthly", "series_from": 2010, "phase": "1.5"},
    "morosidad_financ":   {"label": "Morosidad Financieras",                       "freq": "monthly", "series_from": 2010, "phase": "1.5"},
    # Macro
    "ipc":                {"label": "Índice de Precios al Consumidor",             "freq": "monthly", "series_from": 2008, "phase": "1.5"},
    "ipp":                {"label": "Índice de Precios del Productor",              "freq": "monthly", "series_from": 2008, "phase": "1.5"},
    "imaep":              {"label": "Indicador Mensual Actividad Económica",       "freq": "monthly", "series_from": 1994, "phase": "1.5"},
    "pib":                {"label": "Producto Interno Bruto",                       "freq": "quarterly", "series_from": 1994, "phase": "1.5"},
    "rin":                {"label": "Reservas Internacionales Netas",              "freq": "daily",   "series_from": 2000, "phase": "1.5"},
    "fx":                 {"label": "Tipo de Cambio PYG/USD",                      "freq": "daily",   "series_from": 1990, "phase": "1.5"},
    # Money flows
    "remesas":            {"label": "Remesas Familiares (BCP)",                    "freq": "quarterly", "series_from": 2008, "phase": "2"},
    "inclusion":          {"label": "Indicadores de Inclusión Financiera",          "freq": "annual", "series_from": 2014, "phase": "2"},
    # Capital markets
    "bvpasa":             {"label": "BVPASA Bolsa — listed companies + index",     "freq": "daily",   "phase": "3"},
    "valores":            {"label": "Superintendencia de Valores — emisores",      "freq": "monthly", "phase": "3"},
    # Development bank
    "afd_ifi":            {"label": "AFD — Catálogo de IFI autorizadas",            "freq": "quarterly", "phase": "2"},
    "muvh_fonavis":       {"label": "MUVH FONAVIS — programas + viviendas",       "freq": "annual", "phase": "2.5"},
    "incoop":             {"label": "INCOOP — registro cooperativas",                "freq": "quarterly", "phase": "2"},
    "sep_relad":          {"label": "Seprelad — entidades registradas (AML)",      "freq": "quarterly", "phase": "2.5"},
}


def fetch_indicator(name: str, dry_run: bool = True) -> int:
    if name not in INDICATORS:
        print(f"  [fetch_bcp_rates] ERROR: unknown indicator '{name}'. Known: {list(INDICATORS)}")
        return 0
    meta = INDICATORS[name]
    if dry_run:
        series = f" (series from {meta['series_from']})" if "series_from" in meta else ""
        print(f"  [fetch_bcp_rates] STUB indicator={name}  "
              f"label={meta['label']}  freq={meta['freq']}{series}  phase={meta['phase']}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="BCP rates + macro + money flows (Phase 1.5 stub).")
    parser.add_argument("--indicator", default="rates", choices=list(INDICATORS) + ["rates", "macro", "money", "all"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    dry_run = not args.apply

    # Convenience aliases
    aliases = {
        "rates": ["rates_bancos", "rates_financieras", "tpm", "tasa_interbancaria",
                  "usuraria_mn", "usuraria_me", "morosidad_bancos", "morosidad_financ"],
        "macro": ["ipc", "ipp", "imaep", "pib", "rin", "fx"],
        "money": ["remesas", "inclusion", "bvpasa", "valores", "afd_ifi",
                  "muvh_fonavis", "incoop", "sep_relad"],
    }
    if args.indicator == "all":
        chosen = list(INDICATORS)
    elif args.indicator in aliases:
        chosen = aliases[args.indicator]
    else:
        chosen = [args.indicator]

    for ind in chosen:
        fetch_indicator(ind, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))