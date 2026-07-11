#!/usr/bin/env python3
"""multi_model_improvement_loop — sweep the codebase with Kimi + GLM-5.2, accumulate improvement opportunities,
and DEFER to them when Claude is stuck.

Loops through every PLANE (surface_map surfaces), every WEDGE (their differentiators), and every MODULE
(symbol_graph — covering its functions/classes/constants), sending each a focused context to GLM-5.2 + Kimi-2.7 (the
Ollama Cloud lane) asking for concrete improvement opportunities + next steps. Findings are recorded to an append-only
ledger (governed: serves_truth=false, candidate). Resumable via a cursor so it runs for HOURS and picks up where it
left off. ``--ask`` is the escalation: when Claude (or the loop) is stuck, defer to Kimi + GLM for insights + next steps.

  --self-test          offline: enumerate targets, build focused context, governance + cursor roundtrip (no model calls)
  --run [--limit N] [--kinds plane,wedge,module]   review the next N unreviewed targets (live model calls)
  --ask "<question>" [--context-file F]            DEFER to Kimi + GLM for insights + next steps when stuck
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/multi_model_improvement_loop.py --run --limit 5
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LEDGER = _resource("data") / "dev-intel" / "findings.jsonl"
CURSOR = _resource("data") / "dev-intel" / "_cursor.json"
_CTX_CAP = int(os.environ.get("OH_MULTI_MODEL_CONTEXT_CHARS", "200000"))
DEFAULT_TARGET_WORKERS = int(os.environ.get("OH_MULTI_MODEL_TARGET_WORKERS", "1"))
DEFAULT_MODEL_WORKERS = int(os.environ.get("OH_MULTI_MODEL_MODEL_WORKERS", "2"))


def _models() -> list[dict]:
    """The defer-to panel: GLM + Kimi, optionally Gemma coding on Open WebUI."""
    from scripts._config import OPENWEBUI_DEFAULT_MODEL, OPENWEBUI_MODEL_ENV
    from scripts._llm_client import resolve_provider

    models = [
        {"name": "glm-5.2", "provider": "ollama", "model": "glm-5.2"},
        {"name": "kimi-k2.7-code", "provider": "ollama", "model": "kimi-k2.7-code"},
    ]
    openwebui = resolve_provider("openwebui")
    include_gemma = bool(openwebui.get("key")) or os.environ.get("OH_MULTI_MODEL_INCLUDE_OPENWEBUI") in {"1", "true", "yes", "on"}
    if include_gemma:
        model = os.environ.get(OPENWEBUI_MODEL_ENV, OPENWEBUI_DEFAULT_MODEL)
        models.append({
            "name": model,
            "provider": "openwebui",
            "model": model,
        })
    return models


# ── target enumeration: EVERY aspect — planes, wedges, architecture, business, design, presentation, demos,
#    integrations, and every code module (its functions/classes/constants) ───────────────────────────────────
_ARCH_DIMENSIONS = ["monoliths", "hierarchies", "base_classes_extension", "taxonomy", "flexibility", "abstractions",
                    "coordination"]   # coordination = do the components fit together coherently + stay flexible?

#: The everyday sweep deliberately covers BOTH directions every pass — TOP-DOWN architecture + coordination AND
#: BOTTOM-UP modules (plus planes/wedges). Architecture dims are enumerated first, so a batch reviews the big picture
#: before drilling into modules. (enumerate_targets/run_loop/_fw_sweep all key off this so they never drift apart.)
_SWEEP_KINDS = ("architecture", "module", "plane", "wedge")
_DOC_DIRS = {"business": ["docs/strategy"], "design": ["docs/design", "docs/ui", "docs/brand"], "presentation": ["docs/portfolio"]}
_ALL_KINDS = ("plane", "wedge", "architecture", "business", "design", "presentation", "demo", "integration", "module", "research")


def enumerate_targets(kinds: tuple = _ALL_KINDS) -> list[dict]:
    """Every aspect of the platform — not just code: planes, wedges, cross-cutting ARCHITECTURE dimensions
    (monolith-avoidance / thin-base-classes / hierarchies / taxonomy / flexibility / abstractions), business +
    design + presentation docs, demos, integrations, and every code module."""
    out: list[dict] = []
    if "plane" in kinds or "wedge" in kinds:
        try:
            for s in json.loads((_resource("architecture") / "surface_map.json").read_text())["surfaces"]:
                if "plane" in kinds: out.append({"id": f"plane:{s['id']}", "kind": "plane", "ref": s["id"]})
                if "wedge" in kinds: out.append({"id": f"wedge:{s['id']}", "kind": "wedge", "ref": s["id"]})
        except Exception:
            pass
    if "architecture" in kinds:
        for dim in _ARCH_DIMENSIONS:
            out.append({"id": f"architecture:{dim}", "kind": "architecture", "ref": dim})
    if "research" in kinds:   # OUTWARD research: competitors / repos / packages / news / market gaps (free APIs)
        try:
            from scripts.research_radar import radar_targets
            out.extend(radar_targets())
        except Exception:
            pass
    for k, dirs in _DOC_DIRS.items():
        if k in kinds:
            for d in dirs:
                base = _resource(d)   # docs/* moved under _repos/shared-backend-components/ — resolve via the migration-aware resolver
                if base.exists():
                    for f in sorted(base.glob("*.md")):
                        out.append({"id": f"{k}:{f.relative_to(REPO)}", "kind": k, "ref": str(f.relative_to(REPO))})
    if "presentation" in kinds:
        extra = [str(_resource("architecture/teleon_pitch_deck.json").relative_to(REPO))] + [str(p.relative_to(REPO)) for p in sorted(_resource("docs/strategy").glob("yc-application*.md"))]
        for rel in extra:
            if (_resource(rel)).exists():
                out.append({"id": f"presentation:{rel}", "kind": "presentation", "ref": rel})
    if "demo" in kinds:
        try:
            for dm in json.loads((_resource("architecture") / "teleon_demo_catalog.json").read_text())["demos"]:
                out.append({"id": f"demo:{dm['id']}", "kind": "demo", "ref": dm["id"]})
        except Exception:
            pass
    if "integration" in kinds:
        a = _resource("architecture")
        for f in sorted(set(list(a.glob("*registry*.json")) + list(a.glob("*catalog*.json")) + list(a.glob("*policy*.json")))):
            out.append({"id": f"integration:{f.relative_to(REPO)}", "kind": "integration", "ref": str(f.relative_to(REPO))})
    if "module" in kinds:
        for root in ("_repos/teleon/backend/src/teleon", "_repos/baltor/backend/src/baltor"):
            base = _resource(root)
            if base.exists():
                for f in sorted(base.rglob("*.py")):
                    if "__pycache__" not in f.parts and f.name != "__init__.py":
                        rel = str(f.relative_to(REPO))
                        out.append({"id": f"module:{rel}", "kind": "module", "ref": rel})
    return out


def _architecture_context(ref: str) -> str:
    """Compute the cross-cutting view for an architecture dimension from the symbol graph."""
    from collections import Counter
    from scripts.symbol_graph import build_graph
    g = build_graph(["src"])
    nodes, edges = g["nodes"], g["edges"]
    if ref == "monoliths":
        per = Counter(n.get("module") for n in nodes if n.get("module"))
        return ("TOP MODULES BY SYMBOL COUNT (monolith candidates — should any be split into thin, focused modules?):\n"
                + "\n".join(f"  {m}: {c} symbols" for m, c in per.most_common(20)))
    if ref in ("hierarchies", "base_classes_extension", "abstractions"):
        inh = [(e["src"], e["dst"]) for e in edges if e["type"] == "inherits"]
        classes = [n["id"] for n in nodes if n["kind"] == "class"]
        return (f"CLASS HIERARCHY ({len(inh)} inherits edges over {len(classes)} classes). Are base classes THIN and "
                f"EXTENDED (vs fat/monolithic)? hierarchies + abstractions appropriate?\n"
                + "\n".join(f"  {s} -> {d}" for s, d in inh[:60])
                + ("\n(NOTE: few inherits edges may mean missing base-class/extension structure.)" if len(inh) < 5 else ""))
    if ref == "taxonomy":
        _vd = _resource("vocabularies")
        vocab = [p.name for p in _vd.glob("*.yaml")] if _vd.exists() else []
        regs = [p.name for p in (_resource("architecture")).glob("*registry*.json")]
        return (f"TAXONOMY — is it coherent, non-overlapping, single-sourced?\nvocabularies/: {vocab}\n"
                f"architecture registries: {regs[:30]}")
    if ref == "flexibility":
        seams = sorted({n["id"] for n in nodes if n["kind"] == "class" and ("Port" in n["id"] or "Provider" in n["id"] or "Adapter" in n["id"])})
        return ("FLEXIBILITY SEAMS (ports/providers/adapters) — is the system swappable, no lock-in, thin-base+extensions?\n"
                + "\n".join(f"  {s}" for s in seams[:50]))
    if ref == "coordination":
        # cross-component coherence + flexibility: do the pieces fit together, stay swappable, and share ONE source?
        law = _resource("architecture") / "portfolio_dependency_law.json"
        seams = sorted({n["id"] for n in nodes if n["kind"] == "class"
                        and any(s in n["id"] for s in ("Port", "Provider", "Adapter", "Registry", "Store", "Client"))})
        try:
            surfaces = json.loads((_resource("architecture") / "surface_map.json").read_text())["surfaces"]
            edges = [f"{s['id']} -> {e['to']} ({e['relation']})" for s in surfaces for e in s.get("communicates_with", [])]
        except Exception:
            edges = []
        return ("COORDINATION & COHERENCE — do the components coordinate cleanly AND stay flexible? Assess: (a) the "
                "dependency law Baltor->Teleon->OpenHubForAI holds (never reversed); (b) cross-surface communication "
                "is consistent + intentional; (c) shared values/types are single-sourced (no drift across modules); "
                "(d) seams stay swappable (ports/providers/adapters), no lock-in. Name the specific coupling/drift + the "
                "thin-wrapper fix.\n"
                f"dependency law file: {'present' if law.exists() else 'MISSING'}\n"
                f"swappable seams ({len(seams)}): " + ", ".join(seams[:40]) + "\n"
                "cross-surface edges:\n" + "\n".join(f"  {e}" for e in edges[:40]))
    return f"architecture dimension {ref}"


def focused_context(target: dict) -> str:
    """A COMPACT, kind-aware context for one target (capped). Code -> API signatures + call edges; architecture ->
    computed cross-cutting view; business/design/presentation/integration -> the doc/config; demo -> the catalog entry."""
    kind, ref = target["kind"], target["ref"]
    if kind in ("plane", "wedge"):
        try:
            surfaces = {s["id"]: s for s in json.loads((_resource("architecture") / "surface_map.json").read_text())["surfaces"]}
            s = surfaces.get(ref, {})
            edges = "; ".join(f"{e['to']} ({e['relation']})" for e in s.get("communicates_with", []))
            return (f"SURFACE {ref} [{s.get('status')}]\nwedge: {s.get('wedge')}\nbuyer: {s.get('buyer')}\n"
                    f"communicates_with: {edges}\n")
        except Exception:
            return f"surface {ref}"
    if kind == "architecture":
        try:
            return _architecture_context(ref)[:_CTX_CAP]
        except Exception as e:  # noqa: BLE001
            return f"architecture:{ref} (context unavailable: {e})"
    if kind == "research":
        try:
            from scripts.research_radar import research, format_results
            src, topic = ref.split("::", 1)
            return format_results(topic, src, research(topic, src))[:_CTX_CAP]
        except Exception as e:  # noqa: BLE001
            return f"research:{ref} (unavailable: {e})"
    if kind == "demo":
        try:
            for dm in json.loads((_resource("architecture") / "teleon_demo_catalog.json").read_text())["demos"]:
                if dm["id"] == ref:
                    return f"DEMO {ref}\n" + json.dumps(dm, indent=1)[:_CTX_CAP]
        except Exception:
            pass
        return f"demo {ref}"
    if kind in ("business", "design", "presentation", "integration"):
        p = _resource(ref)
        if not p.exists():
            return f"{kind} {ref} (missing)"
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".json":
            try:
                d = json.loads(text)
                return f"{kind.upper()} {ref}\nkeys: {list(d)[:25]}\n" + text[:8000]
            except Exception:
                return text[:_CTX_CAP]
        return f"{kind.upper()} {ref}\n" + text[:_CTX_CAP]
    # module
    parts = [f"MODULE {ref}\n"]
    try:
        from scripts.context_pack_builder import signatures
        parts.append("## API signatures\n```python\n" + signatures(_resource(ref)) + "\n```\n")
    except Exception:
        pass
    try:
        from scripts.symbol_graph import build_graph
        g = build_graph([ref])
        calls = [f"{e['src']} -> {e['dst']}" for e in g["edges"] if e["type"] == "calls"][:20]
        if calls:
            parts.append("## intra-module call edges\n" + "\n".join(calls) + "\n")
    except Exception:
        pass
    return "".join(parts)[:_CTX_CAP]


IMPROVEMENT_SYSTEM = ("You are a senior staff engineer + product/design lead reviewing ONE aspect of a governed AI "
                      "platform (Baltor context engine + Teleon thin control plane) — could be code, architecture, "
                      "business/PMF, design, a presentation, a demo, or an integration. Find CONCRETE, actionable "
                      "improvement opportunities. Review BOTH directions: TOP-DOWN architecture (how this fits the whole "
                      "system) AND BOTTOM-UP module quality (this unit on its own). For code/architecture also assess: "
                      "monolith-avoidance, THIN base classes that get extended (vs fat ones), appropriate hierarchies + "
                      "taxonomy, flexibility/swappability (no lock-in), clean abstractions, AND whether components "
                      "COORDINATE coherently (cross-cutting consistency, single-source/no-drift, swappable seams). Be "
                      "specific to what's shown; no generic advice; no flattery.")

#: the per-kind review lens (what to look for in this aspect).
_KIND_FOCUS = {
    "module": "code quality: bugs, fragility, governance/receipts, simplification, tests, AND abstraction quality "
              "(thin base class extended? not a monolith? clean hierarchy?).",
    "plane": "is this plane coherently scoped vs the others; right responsibilities; clean seams?",
    "wedge": "is the wedge sharp, defensible, differentiated? who buys, why now, what kills it?",
    "architecture": "ARCHITECTURE on this dimension: monolith-avoidance, THIN base classes that get extended, "
                    "appropriate hierarchies + taxonomy, flexibility/swappability, clean abstractions. Name specific "
                    "offenders + the concrete refactor.",
    "business": "PMF / monetization / GTM clarity + defensibility; sharpen the value prop; what's missing.",
    "design": "design/UX quality, design-system consistency, surface clarity, accessibility.",
    "presentation": "narrative for an investor/YC partner: compelling, honest, sharp; what to cut or strengthen.",
    "demo": "is it end-to-end, REAL (not stubbed), and does it prove the thesis with measured numbers?",
    "integration": "completeness, flexibility/swappability, no lock-in, governance, single-source config.",
    "research": "OUTWARD scan: is this a competitor/similar product? what do they do that we DON'T (verification, "
                "receipts, governed-truth promotion, CDC freshness, multi-axis descent)? what's the PRODUCT-MARKET GAP "
                "/ white space we should exploit? which free/MIT building block to wrap as a CANDIDATE behind a port "
                "(discovery != trust)? Be concrete: name the repo/product + the gap + our next step.",
}


def improvement_user(target: dict, ctx: str) -> str:
    focus = _KIND_FOCUS.get(target["kind"], "")
    return (f"Review this {target['kind']} for improvement opportunities. Lens: {focus}\nList up to 5, each as: "
            f"OPPORTUNITY (what + why) then NEXT STEP (the concrete change). If it's already solid, say so and give "
            f"the single highest-leverage improvement.\n\n=== UNIT ===\n{ctx}\n=== END ===")

ASK_SYSTEM = ("You are an expert pair for a stuck engineer on a governed AI platform. Give specific, actionable "
              "insights + concrete next steps. State assumptions; flag what you can't know from the context.")


def ask_user(question: str, ctx: str) -> str:
    return (f"A teammate (Claude) is stuck. Question:\n{question}\n\n"
            + (f"Relevant context:\n{ctx}\n\n" if ctx else "")
            + "Give: (1) your read of the problem, (2) 2-3 concrete next steps, (3) anything they're likely missing.")


def _chat(model: str, system: str, user: str, *, provider_name: str = "ollama") -> dict:
    from scripts._llm_client import resolve_provider, chat
    prov = resolve_provider(provider_name)
    if not prov["key"]:
        return {"text": "", "error": f"{provider_name} lane not configured ({prov['key_var']} empty)"}
    return chat(model, system, user, prov)


def record_findings(records: list[dict]) -> int:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sum(1 for _ in LEDGER.read_text(encoding="utf-8").splitlines() if _.strip())


def load_cursor() -> set:
    if CURSOR.exists():
        return set(json.loads(CURSOR.read_text(encoding="utf-8")).get("reviewed", []))
    return set()


def save_cursor(reviewed: set) -> None:
    CURSOR.parent.mkdir(parents=True, exist_ok=True)
    CURSOR.write_text(json.dumps({"reviewed": sorted(reviewed)}, indent=1), encoding="utf-8")


_COMPRESS = True   # toggle with --no-compress; reversible CCR compression of the context we send (cheaper per cycle)


def review_target(target: dict) -> list[dict]:
    raw = focused_context(target)
    comp = {"compressed": raw, "ratio": 0.0, "handle": "", "raw_tokens": 0, "compressed_tokens": 0}
    if _COMPRESS:
        try:
            from src.teleon.context.compressor import compress
            comp = compress(raw)
        except Exception:  # noqa: BLE001 — compression is an optimization; never block a review on it
            pass
    ctx = comp["compressed"]
    cmeta = {"ratio": comp["ratio"], "handle": comp["handle"], "raw_tokens": comp.get("raw_tokens", 0),
             "sent_tokens": comp.get("compressed_tokens", 0)}
    models = _models()
    prompt = improvement_user(target, ctx)

    def _review_model(m: dict) -> dict:
        res = _chat(m["model"], IMPROVEMENT_SYSTEM, prompt, provider_name=m.get("provider", "ollama"))
        return {"target": target["id"], "kind": target["kind"], "model": m["name"],
                "provider": m.get("provider", "ollama"),
                "opportunities": res.get("text", ""), "error": res.get("error"),
                "compression": cmeta, "status": "candidate", "serves_truth": False}

    if DEFAULT_MODEL_WORKERS <= 1 or len(models) <= 1:
        return [_review_model(m) for m in models]
    with ThreadPoolExecutor(max_workers=min(DEFAULT_MODEL_WORKERS, len(models))) as pool:
        return [future.result() for future in as_completed(pool.submit(_review_model, m) for m in models)]


def ask_models(question: str, *, context: str = "") -> list[dict]:
    """DEFER-WHEN-STUCK: ask Kimi + GLM for insights + next steps. Returns one record per model (candidate)."""
    out = []
    for m in _models():
        res = _chat(m["model"], ASK_SYSTEM, ask_user(question, context), provider_name=m.get("provider", "ollama"))
        out.append({"question": question, "model": m["name"], "insight": res.get("text", ""),
                    "provider": m.get("provider", "ollama"), "error": res.get("error"),
                    "status": "candidate", "serves_truth": False})
    return out


def run_loop(*, limit: int = 5, kinds: tuple = _SWEEP_KINDS, target_workers: int = DEFAULT_TARGET_WORKERS) -> int:
    targets = enumerate_targets(kinds)
    reviewed = load_cursor()
    todo = [t for t in targets if t["id"] not in reviewed][:limit]
    if not todo:
        print(f"sweep complete — all {len(targets)} targets reviewed (cursor: {CURSOR.relative_to(REPO)}). Reset by deleting it.")
        return 0
    print(
        f"reviewing {len(todo)} of {len(targets) - len(reviewed)} remaining targets "
        f"({', '.join(m['name'] for m in _models())}; target_workers={max(1, target_workers)}; "
        f"model_workers={DEFAULT_MODEL_WORKERS}) ..."
    )
    n = 0
    def _review_one(t: dict) -> tuple[dict, list[dict]]:
        try:
            recs = review_target(t)
        except Exception as e:  # noqa: BLE001 — a single bad target NEVER halts the sweep; record + advance
            recs = [{"target": t["id"], "kind": t["kind"], "model": m["name"], "provider": m.get("provider", "ollama"), "opportunities": "",
                     "error": f"target error: {type(e).__name__}: {e}", "status": "candidate", "serves_truth": False}
                    for m in _models()]
        return t, recs

    work: list[tuple[dict, list[dict]]] = []
    if target_workers <= 1 or len(todo) <= 1:
        for t in todo:
            work.append(_review_one(t))
    else:
        with ThreadPoolExecutor(max_workers=min(max(1, target_workers), len(todo))) as pool:
            futures = [pool.submit(_review_one, t) for t in todo]
            for future in as_completed(futures):
                work.append(future.result())

    for t, recs in work:
        ok = [r for r in recs if not r["error"]]
        if any(r["error"] for r in recs):
            print(f"  {t['id']}: ERROR {next(r['error'] for r in recs if r['error'])[:80]} (continuing)")
        else:
            cm = recs[0].get("compression", {})
            saved = f" · ctx {cm.get('raw_tokens',0)}->{cm.get('sent_tokens',0)} tok ({int(cm.get('ratio',0)*100)}% smaller)" if cm.get("ratio") else ""
            print(f"  {t['id']}: opportunities from {len(ok)} models{saved}")
        record_findings(recs)
        reviewed.add(t["id"]); n += 1            # advance the cursor even on error -> never gets stuck on one target
        save_cursor(reviewed)                    # persist after EACH target -> resilient to mid-batch interruption
    save_cursor(reviewed)
    total = record_findings([])
    print(f"\nrecorded -> {LEDGER.relative_to(REPO)} ({total} findings) · {len(reviewed)}/{len(targets)} targets swept")
    return 0


def run_all(*, limit: int = 8, kinds: tuple = _ALL_KINDS, forever: bool = False,
            target_workers: int = DEFAULT_TARGET_WORKERS) -> int:
    """Sweep ALL remaining targets in back-to-back batches. RESILIENT (a batch error is logged + skipped, never
    fatal) and FORWARD-LOOKING: with ``forever=True`` a completed pass RE-SWEEPS (fresh cursor) so improvement never
    stops. The ONLY halt is .agent/STOP_REQUESTED. Resumable; safe to re-run."""
    stop = (REPO / ".agent") / "STOP_REQUESTED"
    batch = passes = 0
    while True:
        if stop.exists():
            print("STOP_REQUESTED — halting (cursor preserved)."); return 0
        remaining = [t for t in enumerate_targets(kinds) if t["id"] not in load_cursor()]
        if not remaining:
            passes += 1
            if not forever:
                print(f"SWEEP COMPLETE (pass {passes}) — every aspect reviewed. (use --forever for a perpetual loop)"); return 0
            print(f"\n=== PASS {passes} COMPLETE — re-sweeping for new opportunities (forever; stop via .agent/STOP_REQUESTED) ===")
            save_cursor(set())   # forward-looking: a fresh pass keeps surfacing improvements
            continue
        batch += 1
        print(f"\n--- batch {batch} ({len(remaining)} targets remaining) ---")
        try:
            run_loop(limit=limit, kinds=kinds, target_workers=target_workers)
        except Exception as e:  # noqa: BLE001 — never let a batch failure stop the loop; log + keep going
            print(f"  batch error (continuing, not stopping): {type(e).__name__}: {e}")
            continue


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    targets = enumerate_targets()
    kinds = {t["kind"] for t in targets}
    ck("enumerates EVERY aspect incl. outward RESEARCH (planes/wedges/architecture/business/design/presentation/demo/integration/module/research)",
       {"plane", "wedge", "architecture", "business", "design", "presentation", "demo", "integration", "module", "research"} <= kinds, str(kinds))
    rsr = [t for t in targets if t["kind"] == "research"]
    ck("outward research targets enumerated (competitors/repos/news/market-gaps via free APIs)", len(rsr) >= 10, str(len(rsr)))
    ck("a research context degrades gracefully (offline-safe)", isinstance(focused_context(rsr[0]), str))
    ck("there are many module targets (functions/classes covered)", sum(1 for t in targets if t["kind"] == "module") >= 50)
    mod = next(t for t in targets if t["kind"] == "module" and "descent_attempt_store" in t["ref"])
    ctx = focused_context(mod)
    ck("module context includes its API signatures + relationships", "API signatures" in ctx and "best_strategy_for" in ctx)
    pl = next(t for t in targets if t["kind"] == "wedge" and t["ref"] == "teleon")
    ck("a wedge target carries the wedge + buyer + communication", "wedge" in focused_context(pl).lower())
    arch = next(t for t in targets if t["kind"] == "architecture" and t["ref"] == "monoliths")
    ck("an architecture dimension computes a cross-cutting view (monolith candidates by symbol count)",
       "MODULES BY SYMBOL COUNT" in focused_context(arch))
    ck("architecture covers the requested lenses (thin base classes, hierarchies, taxonomy, flexibility, abstractions, coordination)",
       {"monoliths", "hierarchies", "base_classes_extension", "taxonomy", "flexibility", "abstractions", "coordination"} <= {t["ref"] for t in targets if t["kind"] == "architecture"})
    coord = next(t for t in targets if t["kind"] == "architecture" and t["ref"] == "coordination")
    ck("the COORDINATION lens reviews cross-component coherence + flexibility (dependency law, seams, cross-surface edges)",
       "COORDINATION" in focused_context(coord) and "dependency law" in focused_context(coord).lower())
    ck("the everyday sweep covers BOTH top-down architecture AND bottom-up modules (not just plane/wedge/module)",
       "architecture" in _SWEEP_KINDS and "module" in _SWEEP_KINDS)
    ck("parallel GLM/Kimi model workers are enabled by default", DEFAULT_MODEL_WORKERS >= 2)
    ck("improvement prompt asks for opportunity + next step", "OPPORTUNITY" in improvement_user(mod, "x") and "NEXT STEP" in improvement_user(mod, "x"))
    ck("ask (defer-when-stuck) prompt asks for next steps + blind spots", "next steps" in ask_user("q", "").lower())
    with tempfile.TemporaryDirectory() as d:
        global LEDGER, CURSOR
        _l, _c = LEDGER, CURSOR
        try:
            LEDGER = Path(d) / "f.jsonl"; CURSOR = Path(d) / "c.json"
            record_findings([{"target": "x", "model": "glm-5.2", "opportunities": "o", "error": None, "status": "candidate", "serves_truth": False}])
            ck("findings are recorded as governed candidates (serves_truth=false)",
               json.loads(LEDGER.read_text().splitlines()[0])["serves_truth"] is False)
            save_cursor({"module:a"}); ck("cursor roundtrips (resumable for hours)", "module:a" in load_cursor())
        finally:
            LEDGER, CURSOR = _l, _c
    print("\n" + ("PASS - multi_model_improvement_loop: sweeps every plane/wedge/module (functions/classes) with Kimi + "
                  "GLM-5.2, records improvement opportunities as governed candidates, resumable via a cursor (runs for "
                  "hours), and --ask defers to Kimi+GLM when Claude is stuck. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    global _COMPRESS
    argv = sys.argv[1:] if argv is None else argv
    if "--no-compress" in argv:
        _COMPRESS = False
    limit, kinds, question, ctxfile, target_workers = 5, _ALL_KINDS, None, None, DEFAULT_TARGET_WORKERS
    for i, a in enumerate(argv):
        if a == "--limit" and i + 1 < len(argv): limit = int(argv[i + 1])
        if a == "--kinds" and i + 1 < len(argv): kinds = tuple(argv[i + 1].split(","))
        if a == "--ask" and i + 1 < len(argv): question = argv[i + 1]
        if a == "--context-file" and i + 1 < len(argv): ctxfile = argv[i + 1]
        if a == "--target-workers" and i + 1 < len(argv): target_workers = int(argv[i + 1])
    if "--self-test" in argv:
        return _self_test()
    if question:
        ctx = Path(ctxfile).read_text(encoding="utf-8")[:_CTX_CAP] if ctxfile and Path(ctxfile).exists() else ""
        for r in ask_models(question, context=ctx):
            print(f"\n===== {r['model']} =====")
            print(r["error"] and f"ERROR: {r['error']}" or r["insight"])
        return 0
    if "--all" in argv or "--forever" in argv:
        return run_all(limit=limit, kinds=kinds, forever="--forever" in argv, target_workers=target_workers)
    if "--run" in argv:
        return run_loop(limit=limit, kinds=kinds, target_workers=target_workers)
    print("usage: multi_model_improvement_loop.py --self-test | --run [--limit N] [--target-workers N] | --all | --forever | --kinds ... | --ask \"q\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
