#!/usr/bin/env python3
"""Generate docs/INDEX.md - single-page browsable catalog.

Groups all artifacts by type, then by industry vertical, with a
short description per artifact. Solves Taylor's 'single place to
explore' + Hassan's discoverability gap.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oh_hub import load_catalog, ARTIFACT_TYPES


def main() -> int:
    catalog = load_catalog()
    out = []

    out.append("# Open Harness Hub - single-page catalog index")
    out.append("")
    out.append(f"Auto-generated from `scripts/build_index_page.py` against {len(catalog)} live artifacts. Run that script to refresh after any catalog change.")
    out.append("")
    out.append("Use `python scripts/oh_hub.py describe <id>` for the full manifest + dependency tree of any entry below.")
    out.append("")

    # ---- stats header ----
    by_type: dict[str, list[dict]] = defaultdict(list)
    by_industry: dict[str, list[dict]] = defaultdict(list)
    for art in catalog.values():
        by_type[art.get("type", "?")].append(art)
        for ind in art.get("industry") or []:
            by_industry[ind].append(art)

    out.append("## Stats")
    out.append("")
    out.append(f"- **Total artifacts:** {len(catalog)}")
    out.append(f"- **Artifact types:** {len(by_type)}")
    out.append(f"- **Industries:** {len(by_industry)}")
    out.append("")

    # ---- table of contents ----
    out.append("## Table of contents")
    out.append("")
    for t in ARTIFACT_TYPES:
        if t in by_type:
            out.append(f"- [{t} ({len(by_type[t])})](#{t.replace('-','-')})")
    out.append("")

    # ---- by type ----
    for t in ARTIFACT_TYPES:
        if t not in by_type:
            continue
        out.append(f"## {t}")
        out.append("")
        rows = sorted(by_type[t], key=lambda a: a["id"])
        for art in rows:
            name = art.get("name", "")
            desc = (art.get("description") or "").strip().split("\n\n")[0].strip().replace("\n", " ")
            desc_short = desc[:180] + ("…" if len(desc) > 180 else "")
            industries = ", ".join((art.get("industry") or [])[:4])
            out.append(f"- **`{art['id']}`** - {name}  ")
            out.append(f"  _{industries}_ • {desc_short}")
        out.append("")

    # ---- by industry ----
    out.append("## Index by industry vertical")
    out.append("")
    for ind in sorted(by_industry.keys()):
        out.append(f"### {ind}")
        out.append("")
        for art in sorted(by_industry[ind], key=lambda a: (a.get("type",""), a["id"])):
            out.append(f"- `{art['id']}` - {art.get('name', '')}")
        out.append("")

    target = Path(__file__).resolve().parent.parent / "docs" / "INDEX.md"
    target.write_text("\n".join(out))
    print(f"wrote {target} ({len(out)} lines, {len(catalog)} artifacts indexed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
