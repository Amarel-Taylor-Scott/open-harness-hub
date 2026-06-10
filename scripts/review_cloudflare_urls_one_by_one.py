#!/usr/bin/env python3
"""scripts.review_cloudflare_urls_one_by_one — step through the Cloudflare URLs one at a time.

Commands: --next · --current · --mark-pass · --mark-pass-with-notes "..." · --mark-fail "..." · --reset · --summary
Operates on .agent/cloudflare-url-review-state.json; refreshes dist/cloudflare-url-review-progress.md.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_STATE = _REPO / ".agent" / "cloudflare-url-review-state.json"
_PROGRESS = _REPO / "dist" / "cloudflare-url-review-progress.md"


def _load() -> dict:
    return json.loads(_STATE.read_text())


def _save(st: dict) -> None:
    _STATE.write_text(json.dumps(st, indent=2))
    done = sum(1 for r in st["reviews"] if r["status"] != "not_reviewed")
    md = ["# Cloudflare URL review — progress", "", f"{done}/{st['total_reviews']} reviewed",
          f"current: review {st['current_review_index']}", "", "| # | Surface | Status | Cloudflare URL |", "|---|---|---|---|"]
    for r in st["reviews"]:
        md.append(f"| {r['review_order']} | {r['display_name']} | {r['status']} | {r['cloudflare_url'] or '—'} |")
    _PROGRESS.write_text("\n".join(md) + "\n")


def _current(st: dict) -> dict | None:
    idx = st["current_review_index"]
    return next((r for r in st["reviews"] if r["review_order"] == idx), None)


def _print(r: dict | None) -> None:
    if not r:
        print("No current review (all done or empty). Use --reset or --summary.")
        return
    print(f"\n## Review {r['review_order']:02d} — {r['display_name']}  [{r['status']}]")
    print(f"  Cloudflare: {r['cloudflare_url']}")
    print(f"  Local:      {r['local_url']}")
    print(f"  → open dist/cloudflare-url-review-checklist.md → 'Review {r['review_order']:02d}' for the full checklist.")
    if r["notes"]:
        print(f"  notes: {r['notes']}")


def _mark(st: dict, status: str, notes: str = "") -> None:
    r = _current(st)
    if r:
        r["status"] = status
        if notes:
            r["notes"] = notes
        nxt = [x for x in st["reviews"] if x["review_order"] > r["review_order"]]
        st["current_review_index"] = nxt[0]["review_order"] if nxt else r["review_order"]
    _save(st)
    print(f"marked review {r['review_order'] if r else '?'} = {status}")
    _print(_current(st))


def main(argv: list[str]) -> int:
    st = _load()
    if not argv or argv[0] == "--current":
        _print(_current(st))
    elif argv[0] == "--next":
        cur = _current(st)
        nxt = [x for x in st["reviews"] if x["review_order"] > (cur["review_order"] if cur else 0)]
        if nxt:
            st["current_review_index"] = nxt[0]["review_order"]; _save(st)
        _print(_current(st))
    elif argv[0] == "--mark-pass":
        _mark(st, "pass")
    elif argv[0] == "--mark-pass-with-notes":
        _mark(st, "pass_with_notes", argv[1] if len(argv) > 1 else "")
    elif argv[0] == "--mark-fail":
        _mark(st, "fail", argv[1] if len(argv) > 1 else "")
    elif argv[0] == "--reset":
        for r in st["reviews"]:
            r["status"] = "not_reviewed"; r["notes"] = ""
        st["current_review_index"] = 1; _save(st); print("reset.")
    elif argv[0] == "--summary":
        counts: dict[str, int] = {}
        for r in st["reviews"]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        print(json.dumps({"total": st["total_reviews"], "counts": counts}, indent=2))
    elif argv[0] == "--self-test":
        raise SystemExit(0 if _STATE.exists() and st.get("reviews") else 1)
    else:
        print("usage: --next|--current|--mark-pass|--mark-pass-with-notes '..'|--mark-fail '..'|--reset|--summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
