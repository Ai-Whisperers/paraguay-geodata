"""tools/apply_gn_translations.py — integrate a translator's Guaraní JSON.

A native Paraguayan Guaraní speaker will deliver translations/i18n-gn.json.
This script reads that file and integrates it into:
  - exports/web/i18n.js (the gn locale block)
  - exports/web/page-content.js (the gn locale blocks for faq, use-cases, pricing)

Usage:
  python3 -m tools.apply_gn_translations
  python3 -m tools.apply_gn_translations --dry-run   # preview only
  python3 -m tools.apply_gn_translations --strict     # fail if any key missing

Translation file format:
  {
    "i18n": {"home.title": "...", ...},
    "page_content": {
      "faq": {"body": "<h2>...</h2>..."},
      "use-cases": {"body": "..."},
      "pricing": {"body": "..."}
    }
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TRANSLATION_FILE = REPO / "translations" / "i18n-gn.json"
I18N = REPO / "exports" / "web" / "i18n.js"
PAGE_CONTENT = REPO / "exports" / "web" / "page-content.js"


def patch_i18n(content: str, translations: dict, strict: bool = False) -> tuple[str, int, list]:
    """Replace the gn locale in i18n.js with the translator's values.

    Returns: (new_content, n_patched, missing_keys)
    """
    m = re.search(r'"gn"\s*:\s*\{', content)
    if not m:
        return content, 0, ["<- 'gn' locale not found in i18n.js"]
    pos = m.end()
    depth = 1
    end = pos
    while depth > 0 and end < len(content):
        if content[end] == '{': depth += 1
        elif content[end] == '}': depth -= 1
        end += 1
    gn_block = content[pos:end-1]

    existing_keys = set(re.findall(r'"([\w.]+)"\s*:', gn_block))

    new_block = gn_block
    n_patched = 0
    missing = []
    for key, value in translations.items():
        if key not in existing_keys:
            missing.append(key)
            continue
        pattern = re.compile(
            r'("' + re.escape(key) + r'"\s*:\s*)"[^"]*"',
            re.DOTALL,
        )
        new_value_json = json.dumps(value, ensure_ascii=False)
        new_block, n = pattern.subn(r'\g<1>' + new_value_json, new_block, count=1)
        if n > 0:
            n_patched += 1

    if strict and missing:
        raise ValueError(f"i18n: missing keys in gn block: {missing}")

    new_content = content[:pos] + new_block + content[end-1:]
    return new_content, n_patched, missing


def patch_page_content(content: str, translations: dict, strict: bool = False) -> tuple[str, int, list]:
    """Replace gn blocks for each page in page-content.js."""
    n_patched = 0
    missing = []
    for page, body_dict in translations.items():
        if "body" not in body_dict:
            if strict:
                missing.append(f"{page}.body")
            continue
        body = body_dict["body"]
        # Keys are unquoted JS identifiers (e.g. `pricing: { es: ... }`) but
        # `use-cases` is quoted because of the hyphen. Match either form.
        page_m = re.search(
            rf'(?<![\w-])(["\']?){re.escape(page)}\1\s*:\s*\{{',
            content,
        )
        if not page_m:
            missing.append(f"{page} (page not found)")
            continue
        gn_m = re.search(r'gn:\s*`[^`]*`', content[page_m.end():], re.DOTALL)
        if not gn_m:
            missing.append(f"{page}.gn (block not found)")
            continue
        pos = page_m.end() + gn_m.start()
        end = page_m.end() + gn_m.end()
        new_text = f'gn: `{body}`'
        content = content[:pos] + new_text + content[end:]
        n_patched += 1

    if strict and missing:
        raise ValueError(f"page_content: missing pages: {missing}")

    return content, n_patched, missing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Apply translator's Guaraní translations.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="Fail if any keys are missing from the gn locale")
    args = ap.parse_args(argv)

    if not TRANSLATION_FILE.exists():
        print(f"  ERR: {TRANSLATION_FILE} not found")
        print(f"  → translator should deliver translations/i18n-gn.json")
        return 1

    data = json.loads(TRANSLATION_FILE.read_text())
    i18n_keys = data.get("i18n", {})
    page_content = data.get("page_content", {})

    print(f"  translation file: {len(i18n_keys)} i18n keys, {len(page_content)} pages")

    i18n_content = I18N.read_text()
    new_i18n, n_i18n, missing_i18n = patch_i18n(i18n_content, i18n_keys, strict=args.strict)
    print(f"  i18n.js: {n_i18n} keys patched" + (f" ({len(missing_i18n)} missing)" if missing_i18n else ""))
    if missing_i18n and not args.strict:
        for k in missing_i18n[:10]:
            print(f"    - {k}")

    pc_content = PAGE_CONTENT.read_text()
    new_pc, n_pc, missing_pc = patch_page_content(pc_content, page_content, strict=args.strict)
    print(f"  page-content.js: {n_pc} pages patched" + (f" ({len(missing_pc)} missing)" if missing_pc else ""))

    if args.dry_run:
        print(f"\n  --dry-run: no writes")
        return 0

    I18N.write_text(new_i18n)
    PAGE_CONTENT.write_text(new_pc)
    print(f"\n  wrote {I18N.relative_to(REPO)}")
    print(f"  wrote {PAGE_CONTENT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
