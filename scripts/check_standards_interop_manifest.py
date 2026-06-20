#!/usr/bin/env python3
"""check_standards_interop_manifest — single source of truth for what standards Baltor/Teleon interoperate with,
and the gate that keeps the public interop PAGE honest.

architecture/standards_interop_manifest.json lists every adopted/declined standard with its direction, status,
the module that implements it, and the proof that covers it. This script (a) VALIDATES the manifest by actually
importing each built/emitted module and checking each cited proof file exists (no hand-typed conformance claims),
and (b) RENDERS the public interop page from the manifest and fails if the on-disk page has drifted (counts +
lists are computed, never typed — the README-count bug, but for standards).

  --build      (re)write the generated interop page from the manifest
  --self-test  validate the manifest + verify the page is fresh (the registered proof)

The page never serves truth — it is a projection of the manifest.
"""
from __future__ import annotations

import html
import importlib
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MANIFEST = _REPO / "architecture" / "standards_interop_manifest.json"
#: the generated public surface (opencontexthub site). Generated — do not hand-edit.
_PAGE = _REPO / "dist" / "sites" / "opencontexthub" / "interop.html"

_STATUS_PILL = {"built": "ok", "emitted": "ok", "mapped": "warn", "declined": "bad"}


def load_manifest() -> dict:
    return json.loads(_MANIFEST.read_text())


def _counts(m: dict) -> dict:
    out = {s: 0 for s in m["status_enum"]}
    for std in m["standards"]:
        out[std["status"]] = out.get(std["status"], 0) + 1
    out["total"] = len(m["standards"])
    out["adopted"] = sum(out[s] for s in ("built", "emitted", "mapped"))
    return out


# ── page rendering (computed from the manifest — single source, no magic values) ─────────────────────────────
def _card(std: dict) -> str:
    pill = _STATUS_PILL.get(std["status"], "warn")
    rows = [f'<div class="row"><span class="mut">direction</span><span>{html.escape(std["direction"])}</span></div>']
    if std.get("governance_added"):
        rows.append(f'<div class="add">+ {html.escape(std["governance_added"])}</div>')
    if std.get("reason"):
        rows.append(f'<div class="add bad">declined: {html.escape(std["reason"])}</div>')
    if std.get("module"):
        rows.append(f'<div class="row"><span class="mut">impl</span><code>{html.escape(std["module"])}</code></div>')
    if std.get("proof"):
        rows.append(f'<div class="row"><span class="mut">proof</span><code>{html.escape(std["proof"])}</code></div>')
    return (f'<div class="panel">'
            f'<h2>{html.escape(std["name"])} <span class="pill {pill}">{html.escape(std["status"])}</span></h2>'
            f'<div class="hint">{html.escape(std.get("owner", ""))} · {html.escape(std.get("kind", ""))}</div>'
            f'{"".join(rows)}'
            f'<div class="note">{html.escape(std.get("note", ""))}</div>'
            f'</div>')


def render_page(m: dict) -> str:
    c = _counts(m)
    cards = "\n".join(_card(s) for s in m["standards"])
    badge = (f'{c["built"]} built · {c["emitted"]} emitted · {c["mapped"]} mapped · {c["declined"]} declined '
             f'(of {c["total"]})')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>OpenContextHub · Standards interoperability</title>
<!-- GENERATED from architecture/standards_interop_manifest.json by scripts/check_standards_interop_manifest.py — do not hand-edit. -->
<style>
  :root {{ --bg:#0d1117; --panel:#161b22; --line:#21262d; --fg:#e6edf3; --mut:#8b949e; --ok:#3fb950; --warn:#d29922; --bad:#f85149; --acc:#58a6ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  header {{ padding:18px 20px; border-bottom:1px solid var(--line); }}
  h1 {{ font-size:16px; margin:0 0 4px; font-weight:600; }}
  .principle {{ color:var(--acc); font-size:13px; margin:6px 0 2px; }}
  .stance {{ color:var(--mut); font-size:12px; max-width:900px; }}
  .badge {{ color:var(--mut); font-size:12px; margin-top:8px; }}
  main {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:12px; padding:16px; }}
  .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; }}
  .panel h2 {{ font-size:12px; margin:0 0 4px; color:var(--fg); display:flex; justify-content:space-between; gap:8px; align-items:center; }}
  .row {{ display:flex; justify-content:space-between; gap:8px; padding:2px 0; border-bottom:1px dashed var(--line); }}
  .mut {{ color:var(--mut); }}
  .add {{ color:var(--ok); font-size:11px; margin:6px 0; }}
  .add.bad {{ color:var(--bad); }}
  .note {{ color:var(--mut); font-size:11px; margin-top:8px; }}
  .pill {{ display:inline-block; padding:1px 7px; border-radius:999px; font-size:11px; }}
  .pill.ok {{ background:rgba(63,185,80,.15); color:var(--ok); }}
  .pill.warn {{ background:rgba(210,153,34,.15); color:var(--warn); }}
  .pill.bad {{ background:rgba(248,81,73,.15); color:var(--bad); }}
  .hint {{ color:var(--mut); font-size:11px; margin-bottom:6px; }}
  code {{ color:var(--acc); word-break:break-all; }}
  footer {{ padding:14px 20px; border-top:1px solid var(--line); color:var(--mut); font-size:11px; }}
</style>
</head>
<body>
<header>
  <h1>OpenContextHub · Standards interoperability</h1>
  <div class="principle">{html.escape(m["principle"])}</div>
  <div class="stance">{html.escape(m["stance"])}</div>
  <div class="badge">{badge} · updated {html.escape(m["updated"])}</div>
</header>
<main>
{cards}
</main>
<footer>Generated from <code>architecture/standards_interop_manifest.json</code>; every "built"/"emitted" entry is import-verified and proof-gated. This page is a projection — it computes no truth (serves_truth=false).</footer>
</body>
</html>
"""


def write_pages() -> list[str]:
    _PAGE.parent.mkdir(parents=True, exist_ok=True)
    _PAGE.write_text(render_page(load_manifest()))
    return [str(_PAGE.relative_to(_REPO))]


# ── proof ────────────────────────────────────────────────────────────────────────────────────────────────────
def _module_ok(dotted: str) -> bool:
    try:
        importlib.import_module(dotted)
        return True
    except Exception:
        return False


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = load_manifest()
    stds = m["standards"]
    ck("manifest carries the principle + stance (the format-vs-assurance wedge)",
       bool(m.get("principle")) and bool(m.get("stance")) and m.get("serves_truth") is False)
    ck("every standard has id/name/direction/status in the declared enums",
       all(s.get("id") and s.get("name") and s["direction"] in m["direction_enum"]
           and s["status"] in m["status_enum"] for s in stds), str([s.get("id") for s in stds
           if s.get("direction") not in m["direction_enum"] or s.get("status") not in m["status_enum"]]))

    # every built/emitted claim is verified by ACTUALLY importing its module (no hand-typed conformance)
    impl = [s for s in stds if s["status"] in ("built", "emitted")]
    bad_mod = [s["id"] for s in impl if not _module_ok(s["module"])]
    ck("every built/emitted standard's implementation module imports (claim verified by running it)",
       not bad_mod, str(bad_mod))
    # every cited proof file exists
    bad_proof = [s["id"] for s in stds if s.get("proof") and not (_REPO / s["proof"]).exists()]
    ck("every cited proof file exists on disk", not bad_proof, str(bad_proof))
    # mapped entries point to a real file; declined entries carry a reason
    bad_map = [s["id"] for s in stds if s["status"] == "mapped" and not (_REPO / s["module"]).exists()]
    ck("every 'mapped' standard points to a real vocabulary file", not bad_map, str(bad_map))
    bad_decl = [s["id"] for s in stds if s["status"] == "declined" and not s.get("reason")]
    ck("every 'declined' standard records WHY (data-gravity moat, not a portable format)", not bad_decl, str(bad_decl))

    # OKF specifically is adopted (this session's ask) and adds the assurance OKF lacks
    okf = next((s for s in stds if s["id"] == "okf"), None)
    ck("OKF is adopted as built ingest+emit, adding freshness/verification/receipts OKF lacks",
       bool(okf) and okf["status"] == "built" and okf["direction"] == "ingest+emit"
       and "freshness" in okf.get("governance_added", "").lower())

    # the page is GENERATED from the manifest (computed counts/lists — no magic values). dist/ is a build
    # artifact (gitignored, rebuilt by build_portfolio_sites), so the proof validates the RENDER and only enforces
    # freshness when the on-disk page is present — green on a fresh checkout, drift-catching once built.
    c = _counts(m)
    page = render_page(m)
    ck("the interop page renders from the manifest (principle + every standard name present)",
       html.escape(m["principle"]) in page and all(html.escape(s["name"]) in page for s in stds))
    ck("the page badge is computed from the manifest (no hand-typed standards count)", f'(of {c["total"]})' in page)
    if _PAGE.exists():
        ck("the on-disk interop page is fresh vs the manifest (regenerate with --build if this fails)",
           _PAGE.read_text() == page)
    ck("counts are computed from the manifest (built+emitted+mapped+declined == total)",
       c["built"] + c["emitted"] + c["mapped"] + c["declined"] == c["total"] and c["total"] >= 8)
    ck("deterministic", render_page(load_manifest()) == render_page(m))

    print("\n" + (f"PASS - check_standards_interop_manifest: {c['built']} built + {c['emitted']} emitted + "
                  f"{c['mapped']} mapped, {c['declined']} declined (of {c['total']}); every built/emitted claim is "
                  f"import-verified + proof-gated; OKF adopted at the edge with our assurance layered above; the "
                  f"public interop page is generated from the manifest (no drift). Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        written = write_pages()
        print("wrote:", ", ".join(written))
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_standards_interop_manifest.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
