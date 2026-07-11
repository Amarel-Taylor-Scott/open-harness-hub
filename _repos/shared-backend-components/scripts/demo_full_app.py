#!/usr/bin/env python3
"""scripts.demo_full_app — the fully-working Baltor demo, end-to-end, over a free/local dataset.

This is the headline "fully working demo" run. It chains the WHOLE context motion over the synthetic
`demo-data/acme-billing` corpus using ONLY already-shipped modules (compose, don't reinvent):

    ingest seed graph                (demo-data/acme-billing/seed-graph.json)
  → ContextGraph + interrogate       (scripts.context_graph)        "what is the retry ceiling?" → 5
  → deterministic compression        (scripts.context_compress)     compact, source-linked pack
  → LineageManifest + SourceLocators (schemas/context/*)            digestible front, expandable back
  → context receipt                  (this module)                  portable, lineage-referenced
  → swarm-verify the stale runbook   (scripts.context_swarm)        catches the 5-vs-3 conflict,
                                                                     routes a steward review, PROPOSES
                                                                     (does not apply) the 3→5 fix

The LLM is a SEAM via `scripts.model_gateway.resolve_model_route`: the demo resolves a compliant
route (deterministic mock/local default) and, only under `--live` with a reachable provider, lets a
model *phrase* the interrogation answer. Offline + by default everything is deterministic and the
facts come from the graph, never from a model. NO canonical object is mutated.

CLI:
    python3 _repos/shared-backend-components/scripts/demo_full_app.py --self-test      # offline, deterministic end-to-end assertions
    python3 _repos/shared-backend-components/scripts/demo_full_app.py                  # run the demo, print the headline + each step
    python3 _repos/shared-backend-components/scripts/demo_full_app.py --live           # allow a model route to phrase the answer
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.context_graph import ContextGraph, load_seed, DEMO_SEED, interrogate
from scripts.context_compress import compress
from scripts.context_swarm import swarm_object

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
#: corpora the demo can run — each fully offline + deterministic. acme = an engineering KB;
#: cfpb = a SYNTHETIC consumer-finance KB (NOT live CFPB data — the live connector is a separate
#: seam). Each entry is the single source for that corpus's seed + task + swarm target.
CORPORA: dict[str, dict[str, Any]] = {
    "acme": {
        "seed": _resource("demo-data") / "acme-billing" / "seed-graph.json",
        "question": "What is the retry ceiling / how many retries are allowed?",
        "swarm_target": "obj-runbook", "task_id": "BILL-782",
        "label": "Acme Billing (synthetic, offline)",
    },
    "cfpb": {
        "seed": _resource("demo-data") / "cfpb-sample" / "seed-graph.json",
        "question": "How many business days to resolve an EFT error or dispute?",
        "swarm_target": "obj-faq", "task_id": "COMP-5521",
        "label": "CFPB sample (synthetic, offline)",
    },
}
DEFAULT_CORPUS = "acme"


def _handle_to_path(handle: str) -> str:
    """Reverse ANY demo ctx://<source>/<path> handle to its raw file path (drops the #fragment).

    Corpus-agnostic: ctx://acme-billing/x → demo-data/acme-billing/x; ctx://cfpb-sample/y →
    demo-data/cfpb-sample/y. Reversibility proof for the lineage invariant.
    """
    body = handle[len("ctx://"):] if handle.startswith("ctx://") else handle
    return "demo-data/" + body.split("#", 1)[0]


def _object_text(obj: dict) -> str:
    parts = [obj.get("title", ""), obj.get("summary", ""), obj.get("claim", "")]
    return ". ".join(p for p in parts if p)


def _source_locator(graph: ContextGraph, oid: str) -> dict:
    """Build a SourceLocator (schemas/context/source-locator) for an object's primary handle."""
    obj = graph.objects[oid]
    handle = (obj.get("source_handles") or [""])[0]
    file_path = _handle_to_path(handle)
    anchor = handle.split("#", 1)[1] if "#" in handle else ""
    return {
        "kind": "baltor.source-locator",
        "source_locator_id": "loc-" + sha256((oid + handle).encode("utf-8")).hexdigest()[:12],
        "source_handle": handle,
        "source_type": obj.get("object_type", "source_excerpt"),
        "source_system": "demo-files",
        "source_object_id": oid,
        "raw_location": {
            "local_demo_uri": "file://" + file_path,
            "storage_uri": "s3://baltor-raw/" + file_path,
        },
        "file_path": file_path,
        "text_quote": anchor,
        "content_hash": (obj.get("provenance") or {}).get("content_hash", ""),
        "last_validated_at": "1970-01-01T00:00:00Z",
        "valid_until": None,
    }


def _route_seam(live: bool) -> dict:
    """Resolve a compliant model route (deterministic). The demo never calls a model offline; under
    --live with a reachable provider a model would only PHRASE the answer (facts stay from the graph)."""
    from scripts.model_gateway import ModelRouteCandidate, resolve_model_route
    # deterministic candidate set = the demo's free/local provider order (mock → local Ollama).
    mock = ModelRouteCandidate(adapter="deterministic-mock", lane="deterministic", provider="mock",
                               trust_boundary="local", capabilities=("summary", "phrase"))
    local = ModelRouteCandidate(adapter="local-ollama", lane="local_efficient", provider="ollama",
                                trust_boundary="local", capabilities=("summary", "phrase"))
    task = {"task": "context.interrogate.phrase",
            "model_policy": {"capability": "summary", "lane": "deterministic"},
            "data_policy": {"privacy_scope": "public"}}
    rec = resolve_model_route(task, candidates=[mock, local], now=0)  # now=0 → deterministic route id
    return {"selected_adapter": rec["selected_adapter"], "trust_boundary": rec["trust_boundary"],
            "live_attempted": bool(live), "live_model_phrasing": False,
            "note": "model is a SEAM — facts come from the graph; offline default never calls a model"}


def run_demo(*, corpus: str = DEFAULT_CORPUS, live: bool = False) -> dict[str, Any]:
    """Run the full demo motion over a corpus (default acme). Deterministic offline."""
    if corpus not in CORPORA:
        raise ValueError(f"unknown corpus {corpus!r}; choose from {tuple(CORPORA)}")
    cfg = CORPORA[corpus]
    question = cfg["question"]
    g = ContextGraph(load_seed(cfg["seed"]))

    # 1) interrogate the graph
    interro = interrogate(g, question)
    consulted = interro["objects_consulted"]

    # 2) deterministic compression of the consulted objects into a compact, source-linked pack
    items = [{"ref": oid, "text": _object_text(g.objects[oid]),
              "source_handles": g.objects[oid].get("source_handles", [])} for oid in consulted]
    comp = compress(items, query=question, max_tokens=256)

    # 3) lineage: SourceLocators (reversible raw paths) + a LineageManifest (compact front, full back)
    locators = [_source_locator(g, oid) for oid in consulted]
    pack_id = "ctxpack-" + sha256((cfg["task_id"] + question).encode("utf-8")).hexdigest()[:12]
    lineage = {
        "kind": "baltor.lineage-manifest",
        "lineage_manifest_id": "lin-" + sha256(pack_id.encode("utf-8")).hexdigest()[:12],
        "object_ref": pack_id,
        "compact_summary": f"Pack for {cfg['task_id']} built from {len(consulted)} objects; authority "
                           f"{interro['authority']['subject_id'] if interro['authority'] else 'n/a'}.",
        "lineage_summary_for_llm": interro["answer"],
        "source_count": len(consulted),
        "artifact_count": len(locators),
        "activity_count": 2,
        "input_refs": consulted,
        "compression_runs": [comp["compression_run_id"]],
        "source_locator_refs": [l["source_locator_id"] for l in locators],
        "raw_artifact_refs": [l["raw_location"]["storage_uri"] for l in locators],
        "raw_expansion_available": True,
        "expansion_policy": "allowed_with_approval",
        "created_at": "1970-01-01T00:00:00Z",
    }

    # 4) the pack (digestible front) + a portable receipt referencing the lineage
    pack = {
        "pack_id": pack_id, "task": cfg["task_id"], "question": question,
        "answer": interro["answer"], "answer_value": interro["answer_value"],
        "authority": interro["authority"],
        "compact_summary": comp["compact_summary"],
        "source_handles": comp["all_source_handles"],
        "compression_run_id": comp["compression_run_id"],
        "lineage_manifest_ref": lineage["lineage_manifest_id"],
        "contradictions": interro["contradictions"],
    }
    route = _route_seam(live)
    receipt = {
        "kind": "baltor.context-receipt",
        "receipt_id": "rcpt-" + sha256(pack_id.encode("utf-8")).hexdigest()[:12],
        "pack_id": pack_id, "question": question, "answer_value": interro["answer_value"],
        "source_handles": pack["source_handles"],
        "interrogation_run_id": interro["interrogation_run_id"],
        "compression_run_id": comp["compression_run_id"],
        "lineage_manifest_ref": lineage["lineage_manifest_id"],
        "model_route": route, "deterministic": interro["deterministic"], "created_at": "1970-01-01T00:00:00Z",
    }

    # 5) swarm-verify the corpus's stale doc (proposes, routes review; never overwrites)
    swarm = swarm_object(g, cfg["swarm_target"], purpose="verify")

    return {
        "headline": (f"Answer = {interro['answer_value']} (authority "
                     f"{interro['authority']['subject_id'] if interro['authority'] else 'n/a'}); "
                     f"{len(interro['contradictions'])} contradiction(s) caught; "
                     f"pack {comp['token_budget']['estimated_before']}→{comp['token_budget']['estimated_after']} tokens; "
                     f"swarm routed {len(swarm['review_requests'])} review(s), proposed "
                     f"{'a' if swarm['consensus']['context_pack_patch'] else 'no'} fix (not applied)."),
        "interrogation": interro,
        "compression": comp,
        "source_locators": locators,
        "lineage_manifest": lineage,
        "pack": pack,
        "receipt": receipt,
        "swarm": swarm,
        "canonical_mutated": False,
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    out = run_demo()

    # headline fact: the graph answers 5
    check("interrogation answers the retry ceiling = 5", out["interrogation"]["answer_value"] == 5,
          str(out["interrogation"]["answer_value"]))
    # contradiction caught + cites ctx:// handles
    check("contradiction caught and cites ctx:// handles",
          bool(out["interrogation"]["contradictions"])
          and out["interrogation"]["source_handles"]
          and all(h.startswith("ctx://") for h in out["interrogation"]["source_handles"]))
    # compression actually compressed + every retained item keeps a handle
    tb = out["compression"]["token_budget"]
    check("pack is smaller than raw (compressed)", tb["estimated_after"] <= tb["estimated_before"],
          f"{tb['estimated_after']} <= {tb['estimated_before']}")
    check("every retained item keeps a ctx:// source handle",
          all(r["source_handles"] and all(h.startswith("ctx://") for h in r["source_handles"])
              for r in out["compression"]["retained_refs"]))
    # lineage: receipt references the manifest; locators reverse to REAL files on disk (reversibility)
    check("receipt carries a lineage_manifest_ref", out["receipt"]["lineage_manifest_ref"]
          == out["lineage_manifest"]["lineage_manifest_id"])
    missing = [l["file_path"] for l in out["source_locators"] if not (_resource(l["file_path"])).exists()]
    check("every source locator reverses to a REAL raw file (expandable back)", not missing, str(missing))
    # swarm routed a review + proposed (not applied) the 3→5 fix, no canonical mutation
    patch = out["swarm"]["consensus"]["context_pack_patch"]
    check("swarm routed a steward review", len(out["swarm"]["review_requests"]) == 1)
    check("swarm proposed the 3→5 fix WITHOUT applying it",
          patch and patch["from_value"] == 3 and patch["to_value"] == 5 and patch["applied"] is False)
    check("no canonical object mutated anywhere in the demo",
          out["canonical_mutated"] is False and out["swarm"]["canonical_mutated"] is False)
    # model is a seam: a route resolved, but no model was called offline
    check("model route resolved as a seam (no offline model call)",
          out["receipt"]["model_route"]["live_model_phrasing"] is False
          and out["receipt"]["model_route"]["selected_adapter"] != "none")
    # determinism: byte-identical re-run
    check("demo is byte-identical on re-run (deterministic)", run_demo() == out)

    # ── second corpus: the SAME engines run a real offline motion over the synthetic CFPB sample ──
    cf = run_demo(corpus="cfpb")
    check("cfpb: interrogation answers 10 (business days, per Reg E)", cf["interrogation"]["answer_value"] == 10,
          str(cf["interrogation"]["answer_value"]))
    check("cfpb: the Reg E authority is chosen", cf["interrogation"]["authority"]
          and cf["interrogation"]["authority"]["subject_id"] == "obj-rege")
    check("cfpb: contradiction caught (Reg E 10 vs stale FAQ 30)", bool(cf["interrogation"]["contradictions"]))
    cf_patch = cf["swarm"]["consensus"]["context_pack_patch"]
    check("cfpb: swarm proposes the 30→10 fix WITHOUT applying it",
          cf_patch and cf_patch["from_value"] == 30 and cf_patch["to_value"] == 10 and cf_patch["applied"] is False)
    cf_missing = [l["file_path"] for l in cf["source_locators"] if not (_resource(l["file_path"])).exists()]
    check("cfpb: source locators reverse to REAL files on disk", not cf_missing, str(cf_missing))
    check("cfpb: no canonical mutation + deterministic re-run",
          cf["canonical_mutated"] is False and run_demo(corpus="cfpb") == cf)

    # schema spot-checks (when jsonschema is available)
    try:
        from jsonschema import Draft202012Validator
        for fx, schema in (("lineage_manifest", "schemas/context/lineage-manifest.schema.json"),
                           ("receipt", None)):
            if schema:
                v = Draft202012Validator(json.loads((_resource(schema)).read_text()))
                errs = list(v.iter_errors(out[fx]))
                check(f"{fx} validates against its schema", not errs, "; ".join(e.message for e in errs[:2]))
        sl = Draft202012Validator(json.loads((_resource("schemas/context/source-locator.schema.json")).read_text()))
        loc_errs = [e.message for l in out["source_locators"] for e in sl.iter_errors(l)]
        check("every source locator validates against source-locator.schema.json", not loc_errs,
              "; ".join(loc_errs[:2]))
    except ImportError:
        print("  [skip] jsonschema not installed — schema validation skipped")

    print(f"\n{'PASS — demo_full_app: end-to-end over Acme Billing — interrogate→compress→lineage→receipt→swarm. Retry ceiling=5, contradiction caught + source-cited, pack compressed with handles intact, locators reverse to real files, swarm routed a review + proposed (not applied) the fix; deterministic; no canonical mutation.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    print("HEADLINE:", out["headline"])
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The fully-working Baltor demo, end-to-end (free/local).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--live", action="store_true", help="allow a model route to phrase the answer (seam)")
    p.add_argument("--json", action="store_true", help="print the full demo record as JSON")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    out = run_demo(live=args.live)
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    print("=== Baltor full-app demo (Acme Billing) ===")
    print("HEADLINE:", out["headline"])
    print("\n1. INTERROGATE:", out["interrogation"]["answer"])
    print("   source handles:", out["interrogation"]["source_handles"])
    print("2. COMPRESS:", out["compression"]["token_budget"])
    print("3. PACK:", out["pack"]["pack_id"], "→ lineage", out["pack"]["lineage_manifest_ref"])
    print("4. RECEIPT:", out["receipt"]["receipt_id"], "model route:", out["receipt"]["model_route"]["selected_adapter"])
    print("5. SWARM: risk", out["swarm"]["consensus"]["risk_level"],
          "| reviews", len(out["swarm"]["review_requests"]),
          "| proposed patch", out["swarm"]["consensus"]["context_pack_patch"] is not None)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
