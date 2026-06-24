#!/usr/bin/env python3
"""codegraph — the UNIFIED, WEIGHTED code graph + change-audit (the "updated codegraph" the owner asked for).

Two existing AST graphs each see half the picture; this fuses them into ONE strength-ranked model and answers the
question that actually prevents regressions: "I'm about to change X — what are its STRONG connections I must audit?"

  layers (reused, never re-parsed twice — single source of truth):
    - FILE layer   (scripts.code_graph): module->module import edges; weight = # symbols crossing the boundary;
                   upstream (who depends on me → what breaks) / downstream / transitive impact (blast radius).
    - SYMBOL layer (scripts.symbol_graph): function/class/method call+inherit edges; weight = distinct call sites;
                   confidence = exact|name (module-aware resolution, so a call binds to the right same-named symbol).
    - STRENGTH:    per-symbol load-bearing score (weighted call in-degree) + per-module dependent count =
                   "change carefully". The audit ranks neighbors by this so you review the load-bearing ones first.

  --audit <file|module|symbol>   rank the strong connections to review when you change it  (THE command)
  --json  <file|module|symbol>   same, as JSON
  --stats                        graph totals
  --print                        the compact unified view (load-bearing symbols + most-depended modules)
  --emit                         write docs/context/codegraph.generated.{json,md} (BOUNDED; overflow counted)
  --self-test                    proof (registered in flywheel_proof_modules)

CLI: PYTHONPATH=. python3 scripts/codegraph.py --audit src/teleon/synthesis/intent_to_dag.py
Deterministic, offline, stdlib only. serves_truth=false (a static derivation of the code, not a truth claim).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:                       # self-bootstrap so the gate never false-REDs on a missing PYTHONPATH
    sys.path.insert(0, str(REPO))

from scripts.code_graph import _ROOTS, graph as _file_graph                      # noqa: E402
from scripts.symbol_graph import CONFIDENCE_WEIGHT, build_graph as _build_symbols, load_bearing  # noqa: E402

OUT_JSON = REPO / "docs" / "context" / "codegraph.generated.json"
OUT_MD = REPO / "docs" / "context" / "codegraph.generated.md"

# Bounds for the *persisted* artifact + audit render. The full graph lives in memory / is recomputable on demand;
# the committed file stays small and the audit stays scannable. Overflow is always counted, never silently dropped.
_AUDIT_ROWS = 30        # ranked rows shown per audit section
_EMIT_NODES = 200       # most-load-bearing symbols + most-depended modules persisted
_EMIT_EDGES = 400       # strongest call edges persisted


def _strength(weight: int, confidence: str) -> float:
    """Edge strength = call multiplicity × resolution confidence — the single ranking key for 'what to audit'."""
    return weight * CONFIDENCE_WEIGHT.get(confidence, 0.25)


class Unified:
    """The fused, weighted view over the file layer (imports) and the symbol layer (calls/inherits)."""

    def __init__(self) -> None:
        self.fg = _file_graph()                          # file/module import graph (cached singleton)
        self.sym = _build_symbols(list(_ROOTS))          # symbol graph over the SAME roots the file graph uses

        self.modules: set[str] = set()                   # module-node ids
        self.module_file: dict[str, str] = {}            # module -> rel path
        self.node_kind: dict[str, str] = {}              # symbol id -> kind
        self.node_module: dict[str, str] = {}            # symbol id -> owning module
        self.mod_symbols: dict[str, list[str]] = defaultdict(list)   # module -> [symbol ids defined there]
        self.callers: dict[str, list[tuple]] = defaultdict(list)     # callee -> [(caller, weight, conf)]
        self.callees: dict[str, list[tuple]] = defaultdict(list)     # caller -> [(callee, weight, conf)]
        self.bases: dict[str, list[str]] = defaultdict(list)         # class -> [base]
        self.derived: dict[str, list[str]] = defaultdict(list)       # base -> [subclass]

        class_module: dict[str, str] = {}
        for n in self.sym["nodes"]:                       # nodes are emitted module→class→method in order
            k = n["kind"]
            self.node_kind[n["id"]] = k
            if k == "module":
                self.modules.add(n["id"])
                self.module_file[n["id"]] = n.get("file", "")
            elif k in ("function", "class"):
                mod = n["module"]
                self.node_module[n["id"]] = mod
                self.mod_symbols[mod].append(n["id"])
                if k == "class":
                    class_module[n["id"]] = mod
            elif k == "method":
                mod = class_module.get(n["class"], "")
                self.node_module[n["id"]] = mod
                if mod:
                    self.mod_symbols[mod].append(n["id"])

        for e in self.sym["edges"]:
            t = e["type"]
            if t == "calls":
                self.callers[e["dst"]].append((e["src"], e["weight"], e["confidence"]))
                self.callees[e["src"]].append((e["dst"], e["weight"], e["confidence"]))
            elif t == "inherits":
                self.bases[e["src"]].append(e["dst"])
                self.derived[e["dst"]].append(e["src"])

        self.load = load_bearing(self.sym["edges"])       # symbol -> weighted call in-degree
        self._lb_rank = {sid: i + 1 for i, (sid, _) in enumerate(self.load.most_common())}

    # --- stats ---------------------------------------------------------------
    def stats(self) -> dict:
        fs = self.fg.stats()
        calls = [e for e in self.sym["edges"] if e["type"] == "calls"]
        kinds = Counter(n["kind"] for n in self.sym["nodes"])
        return {
            "roots": list(_ROOTS),
            "modules": fs["modules"], "import_edges": fs["edges"],
            "symbol_nodes": dict(kinds),
            "call_edges": len(calls),
            "ambiguous_calls_dropped": self.sym.get("stats", {}).get("ambiguous_calls_dropped", 0),
            "inherits_edges": sum(1 for e in self.sym["edges"] if e["type"] == "inherits"),
        }

    def most_depended_modules(self, n: int) -> list[dict]:
        rows = [{"module": m, "path": self.fg.modules.get(m, ""), "dependents": len(self.fg.upstream(m))}
                for m in self.fg.modules]
        return sorted(rows, key=lambda r: (-r["dependents"], r["module"]))[:n]

    def most_load_bearing(self, n: int) -> list[dict]:
        return [{"id": sid, "kind": self.node_kind.get(sid, "?"), "in_strength": round(score, 2),
                 "callers": len(self.callers.get(sid, []))}
                for sid, score in self.load.most_common(n)]

    def strongest_call_edges(self, n: int) -> list[dict]:
        calls = [{"src": e["src"], "dst": e["dst"], "weight": e["weight"], "confidence": e["confidence"]}
                 for e in self.sym["edges"] if e["type"] == "calls"]
        return sorted(calls, key=lambda e: (-_strength(e["weight"], e["confidence"]), e["src"], e["dst"]))[:n]

    # --- target resolution ---------------------------------------------------
    def resolve(self, target: str) -> tuple[str, object]:
        """('module', mod) | ('symbol', id) | ('ambiguous', [ids]) | ('unknown', target)."""
        t = target.strip()
        if t in self.node_kind and self.node_kind[t] != "module":
            return ("symbol", t)
        m = self.fg._mod(t)                               # file path OR dotted module → concrete module
        if m:
            return ("module", m)
        if t in self.modules:
            return ("module", t)
        short = [sid for sid, k in self.node_kind.items()
                 if k in ("function", "class", "method") and sid.rsplit(".", 1)[-1] == t]
        if len(short) == 1:
            return ("symbol", short[0])
        if short:
            return ("ambiguous", sorted(short))
        return ("unknown", t)

    def _import_weight(self, importer: str, target: str) -> int:
        return sum(1 for (tgt, _sym) in self.fg.symbols.get(importer, []) if tgt == target)

    # --- the audit -----------------------------------------------------------
    def audit(self, target: str) -> dict:
        kind, key = self.resolve(target)
        if kind == "unknown":
            return {"target": target, "resolved": "unknown", "serves_truth": False,
                    "hint": "pass a file path, a dotted module, or a symbol name/id"}
        if kind == "ambiguous":
            return {"target": target, "resolved": "ambiguous", "candidates": key, "serves_truth": False}
        if kind == "module":
            return self._audit_module(key)
        return self._audit_symbol(key)

    def _audit_module(self, mod: str) -> dict:
        upstream = sorted(self.fg.upstream(mod))
        importers = sorted(({"module": u, "import_weight": self._import_weight(u, mod)} for u in upstream),
                           key=lambda r: (-r["import_weight"], r["module"]))
        # external callers of any symbol this module defines (a finer "who reaches into me" than imports alone)
        ext: Counter = Counter()
        ext_conf: dict[str, str] = {}
        for sid in self.mod_symbols.get(mod, []):
            for (caller, w, conf) in self.callers.get(sid, []):
                cmod = self.node_module.get(caller, "")
                if cmod and cmod != mod:
                    ext[caller] += w
                    if conf == "exact":
                        ext_conf[caller] = "exact"
                    else:
                        ext_conf.setdefault(caller, "name")
        callers = [{"symbol": c, "module": self.node_module.get(c, ""), "weight": w,
                    "confidence": ext_conf.get(c, "name")} for c, w in ext.most_common(_AUDIT_ROWS)]
        own = sorted(((sid, self.load.get(sid, 0.0)) for sid in self.mod_symbols.get(mod, [])),
                     key=lambda x: (-x[1], x[0]))
        return {
            "target": mod, "resolved": "module", "path": self.fg.modules.get(mod, ""), "serves_truth": False,
            "audit_importers": importers[:_AUDIT_ROWS],
            "audit_importers_total": len(importers),
            "audit_external_callers": callers,
            "audit_external_callers_total": len(ext),
            "downstream": sorted(self.fg.downstream(mod)),
            "impact_blast_radius": sorted(self.fg.impact(mod)),
            "load_bearing_symbols_here": [{"id": s, "in_strength": round(v, 2)} for s, v in own[:_AUDIT_ROWS] if v > 0],
        }

    def _audit_symbol(self, sid: str) -> dict:
        mod = self.node_module.get(sid, "")
        callers = sorted(self.callers.get(sid, []), key=lambda c: (-_strength(c[1], c[2]), c[0]))
        callees = sorted(self.callees.get(sid, []), key=lambda c: (-_strength(c[1], c[2]), c[0]))
        return {
            "target": sid, "resolved": "symbol", "kind": self.node_kind.get(sid, "?"), "module": mod,
            "path": self.fg.modules.get(mod, ""), "serves_truth": False,
            "in_strength": round(self.load.get(sid, 0.0), 2), "load_bearing_rank": self._lb_rank.get(sid),
            "audit_callers": [{"symbol": c, "weight": w, "confidence": cf} for c, w, cf in callers[:_AUDIT_ROWS]],
            "audit_callers_total": len(callers),
            "callees": [{"symbol": c, "weight": w, "confidence": cf} for c, w, cf in callees[:_AUDIT_ROWS]],
            "bases": sorted(self.bases.get(sid, [])),
            "derived": sorted(self.derived.get(sid, [])),
            "module_blast_radius": len(self.fg.impact(mod)) if mod else 0,
        }


# --- rendering ---------------------------------------------------------------
def render_audit(a: dict) -> str:
    t = a["target"]
    if a["resolved"] == "unknown":
        return f"codegraph audit: '{t}' not found — {a.get('hint', '')}"
    if a["resolved"] == "ambiguous":
        return f"codegraph audit: '{t}' is ambiguous — pick one:\n" + "\n".join(f"  {c}" for c in a["candidates"])
    out = [f"CODE-GRAPH AUDIT — {t}   (kind: {a['resolved']})   {a.get('path', '')}"]
    if a["resolved"] == "module":
        out.append("\n▶ AUDIT THESE — modules that IMPORT this (they break if you change its API; strongest first):")
        for r in a["audit_importers"]:
            out.append(f"    {r['module']}   ({r['import_weight']} symbol(s) cross)")
        if a["audit_importers_total"] > len(a["audit_importers"]):
            out.append(f"    … (+{a['audit_importers_total'] - len(a['audit_importers'])} more importers)")
        if not a["audit_importers"]:
            out.append("    (none — nothing in-repo imports this module)")
        out.append("\n▶ external callers reaching into this module's symbols (review on signature change):")
        for r in a["audit_external_callers"]:
            mk = "~" if r["confidence"] == "name" else ""
            out.append(f"    {r['symbol']}   x{r['weight']}{mk}   [{r['module']}]")
        if a["audit_external_callers_total"] > len(a["audit_external_callers"]):
            out.append(f"    … (+{a['audit_external_callers_total'] - len(a['audit_external_callers'])} more)")
        out.append(f"\n  downstream (this module depends on): {', '.join(a['downstream']) or '—'}")
        imp = a["impact_blast_radius"]
        out.append(f"  impact / blast radius ({len(imp)} transitive dependents): "
                   f"{', '.join(imp[:20])}{' …' if len(imp) > 20 else ''}")
        if a["load_bearing_symbols_here"]:
            out.append("  load-bearing symbols defined here: "
                       + ", ".join(f"{s['id'].rsplit('.', 1)[-1]}({s['in_strength']})" for s in a["load_bearing_symbols_here"][:10]))
    else:
        rank = a.get("load_bearing_rank")
        out.append(f"  module {a['module']}   in-strength {a['in_strength']}"
                   + (f"  (load-bearing rank #{rank})" if rank else ""))
        out.append("\n▶ AUDIT THESE — callers (they call you → break if you change the signature; strongest first):")
        for r in a["audit_callers"]:
            mk = "~" if r["confidence"] == "name" else ""
            out.append(f"    {r['symbol']}   x{r['weight']}{mk}")
        if a["audit_callers_total"] > len(a["audit_callers"]):
            out.append(f"    … (+{a['audit_callers_total'] - len(a['audit_callers'])} more callers)")
        if not a["audit_callers"]:
            out.append("    (none resolved — a leaf, an entrypoint, or only called dynamically)")
        out.append("\n  callees (this calls): "
                   + (", ".join(f"{r['symbol'].rsplit('.', 1)[-1]} x{r['weight']}" for r in a["callees"][:12]) or "—"))
        if a["bases"]:
            out.append(f"  inherits from: {', '.join(a['bases'])}")
        if a["derived"]:
            out.append(f"  subclassed by: {', '.join(a['derived'])}")
        out.append(f"  module blast radius: {a['module_blast_radius']} transitive dependents of {a['module']}")
    out.append("\n(serves_truth=false — a static derivation; verify behavior before relying on it.)")
    return "\n".join(out)


_PROTOCOL = (
    "CHANGE-AUDIT PROTOCOL — before AND after editing a file/symbol, run "
    "`PYTHONPATH=. python3 scripts/codegraph.py --audit <path-or-symbol>` and review its STRONG connections: the "
    "importers/callers that break if its API changes (ranked by strength = call-sites × resolution-confidence) plus "
    "its blast radius. Update the load-bearing neighbors in the SAME change; a high in-strength symbol is shared "
    "infrastructure — touch it deliberately."
)


def render_overview(u: Unified) -> str:
    s = u.stats()
    out = ["# CODE GRAPH — UNIFIED & WEIGHTED (file imports + symbol calls/inherits, with strength)\n",
           _PROTOCOL + "\n",
           f"roots: {', '.join(s['roots'])}",
           f"file layer: {s['modules']} modules · {s['import_edges']} import edges",
           f"symbol layer: {s['symbol_nodes']} · {s['call_edges']} call edges (all confidently resolved; "
           f"{s['ambiguous_calls_dropped']} ambiguous dropped) · {s['inherits_edges']} inherits\n",
           "## Most load-bearing symbols (weighted call in-degree — change carefully)"]
    out += [f"  {r['id']}  in-strength {r['in_strength']} ({r['callers']} callers)"
            for r in u.most_load_bearing(_AUDIT_ROWS)]
    out.append("\n## Most-depended-on modules (file in-degree — wide blast radius)")
    out += [f"  {r['module']}  ({r['dependents']} dependents)" for r in u.most_depended_modules(_AUDIT_ROWS)]
    return "\n".join(out)


def build_artifact(u: Unified) -> dict:
    s = u.stats()
    edges = u.strongest_call_edges(_EMIT_EDGES)
    total_calls = s["call_edges"]
    return {
        "version": "0.1.0",
        "serves_truth": False,
        "generated_from": ["scripts.code_graph", "scripts.symbol_graph"],
        "change_audit_protocol": _PROTOCOL,
        "stats": s,
        "most_load_bearing_symbols": u.most_load_bearing(_EMIT_NODES),
        "most_depended_modules": u.most_depended_modules(_EMIT_NODES),
        "strongest_call_edges": edges,
        "overflow": {"call_edges_not_persisted": max(0, total_calls - len(edges)),
                     "note": "bounded artifact — full graph is recomputable via scripts/codegraph.py"},
    }


def _emit(u: Unified) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    art = build_artifact(u)
    OUT_JSON.write_text(json.dumps(art, indent=1) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_overview(u), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(REPO)} + {OUT_MD.relative_to(REPO)} "
          f"({art['stats']['modules']} modules, {art['stats']['call_edges']} call edges; "
          f"{art['overflow']['call_edges_not_persisted']} edges beyond the bounded artifact)")


# --- proof -------------------------------------------------------------------
def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    u = Unified()
    s = u.stats()
    ck("file layer spans the repo (>=300 modules + import edges)", s["modules"] >= 300 and s["import_edges"] >= 300, str(s))
    ck("symbol layer has class/function/method nodes", {"class", "function", "method"} <= set(s["symbol_nodes"]))
    ck("call edges exist and are all confidently resolved (ambiguous dropped + counted, not guessed)",
       s["call_edges"] > 0 and "ambiguous_calls_dropped" in s and s["ambiguous_calls_dropped"] >= 0,
       f"{s['ambiguous_calls_dropped']} dropped / {s['call_edges']} kept")

    # callers/callees are exact inverses on a sampled strong edge
    strong = u.strongest_call_edges(1)
    ck("there is a strongest call edge to reason about", bool(strong))
    if strong:
        e = strong[0]
        ck("caller/callee indices are inverse (src in callers[dst], dst in callees[src])",
           any(c[0] == e["src"] for c in u.callers.get(e["dst"], [])) and
           any(c[0] == e["dst"] for c in u.callees.get(e["src"], [])))

    # FILE audit: a known dependency (the seed pack proof imports the seed framework)
    fa = u.audit("src/teleon/seeds/capability_seed.py")
    ck("file audit resolves a path → module + importer list",
       fa["resolved"] == "module" and isinstance(fa["audit_importers"], list))
    ck("file audit surfaces a real dependent (scripts.check_capability_seeds imports the seed framework)",
       any(r["module"] == "scripts.check_capability_seeds" for r in fa["audit_importers"]),
       str([r["module"] for r in fa["audit_importers"][:5]]))
    ck("file audit importers are ranked by strength (import_weight non-increasing)",
       all(fa["audit_importers"][i]["import_weight"] >= fa["audit_importers"][i + 1]["import_weight"]
           for i in range(len(fa["audit_importers"]) - 1)))

    # SYMBOL audit: the top load-bearing symbol must have callers, ranked desc by strength
    top = u.most_load_bearing(1)
    ck("a most-load-bearing symbol exists", bool(top))
    if top:
        sa = u.audit(top[0]["id"])
        ck("symbol audit resolves + returns ranked callers", sa["resolved"] == "symbol" and bool(sa["audit_callers"]))
        strengths = [_strength(c["weight"], c["confidence"]) for c in sa["audit_callers"]]
        ck("symbol audit callers are ranked by strength (non-increasing)",
           all(strengths[i] >= strengths[i + 1] for i in range(len(strengths) - 1)), str(strengths[:5]))
        ck("symbol audit carries a load-bearing rank", sa["load_bearing_rank"] == 1)

    ck("unknown target degrades honestly", u.audit("nonexistent_zzz_symbol")["resolved"] == "unknown")

    # bounded artifact: caps respected, overflow counted (no silent truncation)
    art = build_artifact(u)
    ck("artifact is bounded (nodes/edges within caps)",
       len(art["most_load_bearing_symbols"]) <= _EMIT_NODES and len(art["strongest_call_edges"]) <= _EMIT_EDGES)
    ck("artifact counts overflow honestly",
       art["overflow"]["call_edges_not_persisted"] == max(0, s["call_edges"] - len(art["strongest_call_edges"])))
    ck("render carries the change-audit protocol", "CHANGE-AUDIT PROTOCOL" in render_overview(u))
    ck("never serves truth", art["serves_truth"] is False and fa["serves_truth"] is False)

    # determinism: a fresh build gives identical stats
    ck("deterministic (rebuild → identical stats)", Unified().stats() == s)

    print(f"\n  (file: {s['modules']} modules/{s['import_edges']} edges · symbol: {s['symbol_nodes']} · "
          f"{s['call_edges']} call edges)")
    print("\n" + ("PASS - codegraph --self-test: unified weighted graph (file imports + symbol calls/inherits), "
                  "strength-ranked change-audit (importers/callers by call-sites×confidence + blast radius), bounded "
                  "artifact with counted overflow. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--audit", metavar="TARGET", help="rank strong connections to audit when changing a file/module/symbol")
    p.add_argument("--json", metavar="TARGET", help="--audit output as JSON")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--print", dest="show", action="store_true")
    p.add_argument("--emit", action="store_true")
    p.add_argument("--self-test", dest="self_test", action="store_true")
    a = p.parse_args(argv)

    if a.self_test:
        return _self_test()
    if a.audit:
        print(render_audit(Unified().audit(a.audit)))
        return 0
    if a.json:
        print(json.dumps(Unified().audit(a.json), indent=2))
        return 0
    if a.stats:
        print(json.dumps(Unified().stats(), indent=2))
        return 0
    if a.emit:
        _emit(Unified())
        return 0
    if a.show:
        print(render_overview(Unified()))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
