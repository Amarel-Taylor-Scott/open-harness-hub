#!/usr/bin/env python3
"""scripts.check_pipeline_pages_full_stack — proof (UI-PIPELINE-FULL-1): the COHESIVE Baltor pipeline-journey
series is a complete, projection-only walk of ONE run.

This is the synthesis proof over the whole series (the per-stage proofs cover each page in isolation). It
asserts, statically + offline + deterministically:

  1. all 8 pages exist — the journey index plus the 7 stage pages, in order;
  2. STEPPER CONTINUITY — every stage page links to its NEXT and PREV stage (so the series reads as one
     continuous run), whether the stepper is static <a href> or built from a STAGES array;
  3. PROJECTION-ONLY — the forbidden tokens (.agent/, MEMORY.md, baltor-goal-loop, .claude/, INSERT INTO,
     UPDATE , DELETE FROM, sqlite3, secrets, client truth storage) are absent from every page;
  4. LOSSLESS PANEL — every stage page references a lossless / held-out panel (the star of this UI);
  5. CONTRACTED API — every stage page references its contracted /api/pipeline/<stage> endpoint, and the
     index references /api/pipeline/overview;
  6. the projection API actually answers all 8 contracted shapes (the data source behind every page is live),
     via the pure handler — no socket, no writes.

It prints a table  STAGE | PAGE | API | LOSSLESS_PANEL | PROJECTION_ONLY | STEPPER | STATUS.

CLI: python3 _repos/shared-backend-components/scripts/check_pipeline_pages_full_stack.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

from scripts.api_pipeline_handler import handle

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PIPE = _resource("web/baltor/pipeline")

#: the journey, in order: (stage_id, page_filename, contracted_api_endpoint).
#: the index has no single stage endpoint — it drives the whole journey off /api/pipeline/overview.
_INDEX = ("index", "index.html", "/api/pipeline/overview")
_STAGES = [
    ("upload",         "upload.html",         "/api/pipeline/upload"),
    ("decomposition",  "decomposition.html",  "/api/pipeline/decomposition"),
    ("reconciliation", "reconciliation.html", "/api/pipeline/reconciliation"),
    ("enhancement",    "enhancement.html",    "/api/pipeline/enhancement"),
    ("optimization",   "optimization.html",   "/api/pipeline/optimization"),
    ("verification",   "verification.html",   "/api/pipeline/verification"),
    ("consumption",    "consumption.html",    "/api/pipeline/consumption"),
]
_ALL = [_INDEX] + _STAGES

#: a projection-only page must never reference these (durable truth / private memory / secrets / client truth).
_FORBIDDEN = (
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "sqlite3",
    "localStorage", "sessionStorage", "indexedDB",
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",
)
#: substrings that mark a lossless / held-out panel (the page must surface omitted-but-kept items).
_LOSSLESS_MARKERS = ("lossless", "held out", "held-out", "held_out")


def _stage_id_links(text: str, stage_id: str) -> bool:
    """True if the page links to `stage_id` either as a static href ("./<id>.html") or as a STAGES-array
    entry ("<id>" + ".html" built dynamically — every dynamic stepper carries the id literal AND builds
    "./" + id + ".html")."""
    href = f'"./{stage_id}.html"'
    if href in text:
        return True
    # dynamic stepper: the stage id appears as a quoted literal in the STAGES catalogue and the page builds
    # the href from it (the proof for that pattern: id literal present AND a "+ ".html"" builder present).
    id_literal = (f'"{stage_id}"' in text) or (f"'{stage_id}'" in text)
    builds_href = '.html' in text and ('+ "./"' in text or '"./" +' in text or '"./"+' in text or '+"./"' in text)
    return id_literal and builds_href


def _stepper_continuity(text: str, idx: int) -> tuple[bool, str]:
    """Each stage page must link to its NEXT and PREV stage so the series is one continuous run.
    The index links forward into the first stage. Returns (ok, detail)."""
    # index: must link into the first stage (forward entry into the journey).
    if idx == 0:
        ok = _stage_id_links(text, _STAGES[0][0])
        return ok, ("links→upload" if ok else "MISSING link to upload")
    # stage pages: idx in _ALL is 1..7 → position in _STAGES is idx-1.
    pos = idx - 1
    parts = []
    ok = True
    if pos > 0:
        prev_id = _STAGES[pos - 1][0]
        has = _stage_id_links(text, prev_id)
        ok = ok and has
        parts.append(("←" + prev_id) if has else ("MISSING←" + prev_id))
    else:
        parts.append("←(start)")
    if pos < len(_STAGES) - 1:
        next_id = _STAGES[pos + 1][0]
        has = _stage_id_links(text, next_id)
        ok = ok and has
        parts.append(("→" + next_id) if has else ("MISSING→" + next_id))
    else:
        # last stage must close the loop back to the journey index.
        has = _stage_id_links(text, "index")
        ok = ok and has
        parts.append(("→index") if has else "MISSING→index")
    return ok, " ".join(parts)


def _self_test() -> int:
    fails: list[str] = []
    rows: list[tuple] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")

    # ── 1) the projection API answers every contracted shape (the live data source behind the pages) ──
    q = {"tenant": "demo", "corpus": "cfpb"}
    api_ok: dict[str, bool] = {}
    for _sid, _page, ep in _ALL:
        code, payload = handle("GET", ep, q)
        ok = code == 200 and isinstance(payload, dict) and payload.get("available") is True
        api_ok[ep] = ok
        check(f"{ep} answers 200 + available", ok, f"code={code}")

    # ── 2..6) per-page static checks ──
    for i, (sid, page, ep) in enumerate(_ALL):
        path = _PIPE / page
        exists = path.exists()
        check(f"page exists: pipeline/{page}", exists)
        text = path.read_text(encoding="utf-8") if exists else ""

        # API reference on the page
        api_ref = ep in text
        check(f"{page} references its API endpoint {ep}", api_ref if exists else False)

        # lossless panel (index is the journey hub — it must still carry the lossless law copy)
        lossless = any(m.lower() in text.lower() for m in _LOSSLESS_MARKERS)
        if sid == "index":
            check(f"{page} carries the lossless law copy", lossless if exists else False)
        else:
            check(f"{page} references a lossless / held-out panel", lossless if exists else False)

        # projection-only (forbidden tokens absent, incl. the sk- secret prefix)
        offenders = [f for f in _FORBIDDEN if f in text]
        if ("sk" + "-") in text:
            offenders.append("sk-")
        proj_ok = (offenders == []) and exists
        check(f"{page} is projection-only (no forbidden tokens)", proj_ok, str(offenders))

        # explicit PROJECTION ONLY marker (cohesion: every page declares itself)
        marker = "PROJECTION ONLY" in text.upper()
        check(f"{page} declares the PROJECTION ONLY marker", marker if exists else False)

        # stepper continuity
        step_ok, step_detail = _stepper_continuity(text, i) if exists else (False, "missing")
        check(f"{page} stepper continuity ({step_detail})", step_ok)

        status = "OK" if (exists and api_ref and lossless and proj_ok and marker and step_ok and api_ok.get(ep, False)) else "FAIL"
        rows.append((
            sid,
            page,
            ("ok" if api_ref and api_ok.get(ep, False) else "FAIL"),
            ("yes" if lossless else "NO"),
            ("yes" if proj_ok else "NO"),
            ("yes" if step_ok else "NO"),
            status,
        ))

    # ── cohesion: the shared stylesheet exists and the index references it ──
    css = _PIPE / "pipeline.css"
    check("shared design system _repos/baltor/frontend/pipeline/pipeline.css exists", css.exists())
    idx_text = (_PIPE / "index.html").read_text(encoding="utf-8") if (_PIPE / "index.html").exists() else ""
    check("index.html references the shared pipeline.css", "pipeline.css" in idx_text)

    # ── the table ──
    print(f"  {'STAGE':<15}{'PAGE':<22}{'API':<6}{'LOSSLESS':<10}{'PROJ_ONLY':<11}{'STEPPER':<9}STATUS")
    print(f"  {'-'*15}{'-'*22}{'-'*6}{'-'*10}{'-'*11}{'-'*9}{'-'*6}")
    for sid, page, api, loss, proj, step, status in rows:
        print(f"  {sid:<15}{page:<22}{api:<6}{loss:<10}{proj:<11}{step:<9}{status}")
    print()

    if fails:
        print(f"{len(fails)} FAILURES:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("PASS — check_pipeline_pages_full_stack: all 8 pipeline-journey pages exist (index + 7 stages); the "
          "stepper is continuous across the whole series (each stage links next + prev, the last loops back to "
          "the index); every page is projection-only (no forbidden tokens, declares PROJECTION ONLY); every "
          "stage page surfaces a lossless / held-out panel and the index carries the lossless law; every page "
          "references its contracted /api/pipeline/* endpoint and the live projection API answers all 8 shapes; "
          "the cohesive shared pipeline.css exists and the index references it.")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the full pipeline-journey page series (cohesive, projection-only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
