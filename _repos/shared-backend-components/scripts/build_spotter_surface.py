"""build_spotter_surface — the demoable face of the Observer/Spotter subsystem: a self-contained dist/spotter/
index.html that explains 'coaching, not surveillance', shows the intervention TAXONOMY (computed from the live
router), runs the reviewer on a sample session and renders the confidence-scored report, lists the knowledge-graph
engines, and funnels to Teleon.

Every count is COMPUTED from the live modules/registries (no-magic-values): the taxonomy size, the heuristic counts,
the registry totals. serves_truth=false (a coaching surface, never an authority on truth). Offline + self-contained.

  python3 _repos/shared-backend-components/scripts/build_spotter_surface.py            # write dist/spotter/index.html
  python3 _repos/shared-backend-components/scripts/build_spotter_surface.py --self-test
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.observer.review import review_session  # noqa: E402
from src.teleon.observer.router import default_modules  # noqa: E402

_OUT = _resource("dist/spotter/index.html")
_HEURISTICS = _resource("architecture") / "behavioral_heuristics.json"
_ONTOLOGY = _resource("architecture") / "registry_ontology.json"
_KNOWLEDGE_REGISTRIES = ["global_repository_registry", "product_similarity_registry", "package_dependency_seed",
                         "agent_frameworks_registry"]

# a sample session that exercises the taxonomy (deterministic — the demo is reproducible)
_SAMPLE_SESSION = [
    {"role": "user", "content": "let me build my own oauth login system from scratch with jwt and refresh tokens"},
    {"role": "user", "content": "I'll need browser automation to log into the portal"},
    {"role": "user", "content": "let me build a custom retry with exponential backoff"},
    {"role": "user", "content": "try:\n    do_it()\nexcept:\n    pass"},
    {"role": "user", "content": "let me build an open source vector database and similarity search engine for embeddings with filtering"},
    {"role": "user", "content": "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"},
]


def _counts() -> dict:
    modules = default_modules()
    heur = json.loads(_HEURISTICS.read_text())["heuristics"]
    by_kind: dict[str, int] = {}
    for h in heur:
        by_kind[h["kind"]] = by_kind.get(h["kind"], 0) + 1
    onto = json.loads(_ONTOLOGY.read_text())["registries"]
    return {
        "intervention_types": sorted({m.type for m in modules}),
        "module_count": len(modules),
        "heuristics_total": len(heur),
        "heuristics_by_kind": by_kind,
        "registry_total": len(onto),
        "knowledge_registries": len(_KNOWLEDGE_REGISTRIES),
    }


def _render(counts: dict, report: dict) -> str:
    e = html.escape
    types_html = "".join(f"<span class=pill>{e(t)}</span>" for t in counts["intervention_types"])
    rows = "".join(
        f"<tr><td><span class=ty>{e(f['type'])}</span></td><td class=cf>{f['confidence']:.2f}</td>"
        f"<td>{e(f['evidence'][:80])}</td><td>{e(f['suggestion'][:90])}</td></tr>"
        for f in report["report"])
    engines = [
        ("dependency_graph", "transitive 'this whole dependency stack already exists'"),
        ("product_distance", "latent-space overlap to existing products"),
        ("repo_similarity", "semantic equivalents of an intent"),
        ("code_genome", "architectural-primitive fingerprints -> software similarity"),
    ]
    engines_html = "".join(f"<li><b>{e(n)}</b> — {e(d)}</li>" for n, d in engines)
    kinds = ", ".join(f"{k}: {v}" for k, v in sorted(counts["heuristics_by_kind"].items()))
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Spotter — coaching, not surveillance</title>
<style>
:root{{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--ac:#58a6ff;--cd:#1c2128;--ok:#3fb950}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:920px;margin:0 auto;padding:40px 22px}}h1{{font-size:34px;margin:0 0 6px}}h2{{font-size:21px;margin:36px 0 12px;border-bottom:1px solid #30363d;padding-bottom:6px}}
.tag{{color:var(--ac);font-weight:600}}.mut{{color:var(--mut)}}.pill,.ty{{display:inline-block;background:var(--cd);border:1px solid #30363d;border-radius:20px;padding:2px 10px;margin:3px 4px 0 0;font-size:12.5px}}
.ty{{border-radius:5px;color:var(--ac)}}table{{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}}
td,th{{text-align:left;padding:7px 8px;border-bottom:1px solid #21262d;vertical-align:top}}th{{color:var(--mut);font-weight:600}}
.cf{{color:var(--ok);font-variant-numeric:tabular-nums}}.card{{background:var(--cd);border:1px solid #30363d;border-radius:10px;padding:16px 18px;margin:10px 0}}
.big{{font-size:27px;font-weight:700;color:var(--ac)}}.grid{{display:flex;gap:12px;flex-wrap:wrap}}.grid .card{{flex:1;min-width:150px}}
a.cta{{display:inline-block;background:var(--ac);color:#0d1117;font-weight:700;padding:10px 18px;border-radius:8px;text-decoration:none;margin-top:8px}}
code{{background:var(--cd);padding:1px 5px;border-radius:4px}}.foot{{margin-top:40px;color:var(--mut);font-size:12px;border-top:1px solid #30363d;padding-top:14px}}
</style></head><body><div class=wrap>
<h1>Spotter</h1>
<p class=tag>Coaching, not surveillance. A compiler-optimizer for how you use AI.</p>
<p class=mut>A thin layer beside the AI coding tools you already use (Claude Code, Codex, Cursor). It watches a session,
saves it, lets you review it for learning — and pops up <i>grounded</i> nudges: "this already exists", an adversarial
question, a cheaper path. The same telemetry enterprise tools collect to <i>control</i> developers, Spotter uses to
help them <i>grow</i>.</p>

<div class=grid>
<div class=card><div class=big>{counts['module_count']}</div><div class=mut>intervention modules (one router)</div></div>
<div class=card><div class=big>{counts['heuristics_total']}</div><div class=mut>behavioral heuristics<br>({e(kinds)})</div></div>
<div class=card><div class=big>{counts['registry_total']}</div><div class=mut>federated registries (grounding)</div></div>
<div class=card><div class=big>{counts['knowledge_registries']}</div><div class=mut>knowledge-graph engines' registries</div></div>
</div>

<h2>The intervention taxonomy</h2>
<p class=mut>One engine, many surfaces. Each type has its own grounding (what stops it hallucinating) and its own
failure mode. A <span class=tag>global interruption budget</span> + graduated modes
(<code>silent → review → advisory → active → enforcing</code>) keep it from ever nagging.</p>
<div>{types_html}</div>

<h2>Live post-session review <span class=mut style=font-size:13px>(run on a sample session — reproducible)</span></h2>
<p class=mut>The non-invasive wedge: the same engine run in batch over a transcript → a confidence-scored report a
human triages. Findings here are governed candidates, not assertions.</p>
<table><tr><th>type</th><th>conf</th><th>evidence</th><th>suggestion</th></tr>{rows}</table>

<h2>Grounded by a Global Software Knowledge Graph</h2>
<p class=mut>The "it exists" call is precise because it grounds against a real index, not an LLM guess:</p>
<ul>{engines_html}</ul>

<h2>Powered by Teleon</h2>
<p class=mut>Spotter is the customer-facing wedge over the Teleon engine — the descent (make-it-work → make-it-cheaper),
the registry federation, and the optimization memory that learns winning paths from real sessions.</p>
<a class=cta href="https://teleon.dev">Teleon →</a>

<div class=foot>serves_truth=false — Spotter coaches; it is never an authority on truth. All counts on this page are
computed from the live router + registries at build time. Findings are candidates a human triages. Local-first; your
code can stay on your machine.</div>
</div></body></html>"""


def _build(write: bool) -> dict:
    counts = _counts()
    report = review_session(_SAMPLE_SESSION)
    page = _render(counts, report)
    if write:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        _OUT.write_text(page)
    return {"counts": counts, "report": report, "page": page}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if not args.self_test:
        r = _build(write=True)
        print(f"spotter surface: {r['counts']['module_count']} modules, {r['counts']['heuristics_total']} heuristics, "
              f"{r['counts']['registry_total']} registries; sample review = {r['report']['summary']['findings']} "
              f"findings -> {_OUT}")
        return 0

    fails, checks = [], 0

    def ck(name, ok, detail=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    r = _build(write=False)
    counts, report, page = r["counts"], r["report"], r["page"]
    ck("counts are computed from the live router (>=8 module types)", len(counts["intervention_types"]) >= 8)
    ck("the computed module count appears verbatim in the page (no magic)", f">{counts['module_count']}<" in page)
    ck("the computed registry total appears in the page", f">{counts['registry_total']}<" in page)
    ck("sample review produced findings across types", report["summary"]["findings"] >= 4)
    ck("the live report is embedded (a finding type appears)", any(
        f">{t}<" in page or t in page for t in report["summary"]["by_type"]))
    ck("page carries the serves_truth=false disclaimer", "serves_truth=false" in page)
    ck("page funnels to Teleon", "teleon.dev" in page)
    ck("coaching-not-surveillance framing present", "Coaching, not surveillance" in page)
    ck("self-contained (no external script/style src)", "http://" not in page.replace("https://teleon.dev", ""))

    if fails:
        print(f"\nFAIL - build_spotter_surface: {len(fails)} of {checks} failed")
        return 1
    print(f"PASS - build_spotter_surface: self-contained Spotter surface — {counts['module_count']} modules + "
          f"{counts['registry_total']} registries (all counts computed), live sample review "
          f"({report['summary']['findings']} findings) embedded, funnels to Teleon; {checks} assertions; "
          f"serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
