#!/usr/bin/env python3
"""promote_synthesized_to_cards — reshape the synthesized-working primitives into searchable typed cards.

The 427K oracle-passing primitives from primitive_synthesis_loop live in working_primitives.jsonl with a synthesis
schema (title + typed edges + code + family, verification_level='execution', no blackbox). They are TYPED + DISTINCT
+ WORKING but NOT in the searchable card tier (the linker only queries the 112K facet store). This converts them to
the card schema so a facet-store resume-build makes them semantic-searchable — the owner's "all 4M+ typed, searchable,
distinct, not just 112K" (this closes a big chunk: 112K -> ~540K searchable).

Honest note: these are NARROW transform micro-ops (count/sort/unique/join over specific edges), often with truncated
titles/edges — real + typed + working, but lower retrieval value than the rich edge-foundry cards. The facet race
decides which of their surfaces matter. candidate-only, serves_truth=false.

    PYTHONPATH=. python3 scripts/promote_synthesized_to_cards.py --run
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
_SRC = _REPO / "data" / "dev-intel" / "primitive_synthesis" / "working_primitives.jsonl"
_OUT = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry" / "minted_synthesized_working_cards.jsonl"


def _card(row: dict) -> Optional[dict]:
    pid = row.get("primitive_id")
    ie = str(row.get("input_edge") or "").replace("edge:", "").strip()
    oe = str(row.get("output_edge") or "").replace("edge:", "").strip()
    title = str(row.get("title") or "").strip()
    code = str(row.get("code") or "").strip()
    if not (pid and title and ie and oe):
        return None
    # carry the VERIFIED BODY so the card is WORKING (not a descriptor). verification_level='execution' is honest
    # ONLY when the synthesis row actually passed its oracle (working=True); otherwise the card is a candidate draft.
    working = bool(row.get("working")) and bool(code)
    card = {"primitive_id": pid, "title": title, "blackbox": title,  # no separate blackbox in synthesis output
            "input_edge": ie, "output_edge": oe, "capability_tags": [row.get("family", "transform")],
            "domains": [], "effects": [], "mutations": [], "trust": "candidate",
            "candidate": True, "serves_truth": False,
            "verification_level": "execution" if working else "draft",
            "source_family": "synthesized_working", "source_evidence_status": "authored",
            "kind": "capability", "primitive_kind": "action"}
    if code:
        card["source_code"] = code
        card["body_sha"] = f"crc32:{zlib.crc32(code.encode()) & 0xFFFFFFFF:08x}"
        card["has_working_body"] = working
    return card


def run(src: Path = _SRC, out: Path = _OUT) -> dict:
    if not src.exists():
        return {"error": f"source not found: {src}"}
    out.parent.mkdir(parents=True, exist_ok=True)
    n_in = n_out = 0
    seen: set[str] = set()
    with src.open() as fin, out.open("w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            try:
                card = _card(json.loads(line))
            except json.JSONDecodeError:
                continue
            if card and card["primitive_id"] not in seen:  # distinct by id
                seen.add(card["primitive_id"])
                fout.write(json.dumps(card, sort_keys=True) + "\n")
                n_out += 1
    return {"in": n_in, "out": n_out, "distinct": len(seen), "out_path": str(out)}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Reshape synthesized-working primitives into searchable typed cards.")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.run:
        print(json.dumps(run(), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
