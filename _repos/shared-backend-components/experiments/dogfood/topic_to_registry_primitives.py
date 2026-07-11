#!/usr/bin/env python3
"""experiments/dogfood/topic_to_registry_primitives — the DEFINED, REUSABLE capability that grows the registry
from a topic. NOT a one-off demo: run it with any topics, for any future demo, to consume our own dogfood
(scrape new topics -> registry-visible candidate primitives you can then search, compose, and promote).

ROUTE CONTRACT (a defined, scoped capability — could itself be registered as a primitive route)
  route:        topic_to_registry_primitives
  input_edge:   TopicSet + IntakePolicy
  output_edge:  RegisteredCandidatePrimitives + IntakeReceipt
  stages:       scrape+ideate  ->  screen+shape  ->  bridge  ->  count+receipt
  reuses:       discovery_pipeline.run  (scrape/govern/ideate; self-tested)
                load_verified_candidates_into_registry.{map_row,build_cards,write_pack}  (the registry bridge)
  new seam:     screen+shape — turn a governed discovered idea into a registry-loadable verified_candidate row
  effects:      [network_read(github), file_write, registry_write]
  proof:        [shaped_row_maps_to_card, non_component_screened_out, registry_count_increases, candidate_serves_truth_false]
  candidate:    true   serves_truth: false   surface_visibility: private_internal_only

Standalone via _repo_paths.install() (the cross-repo bootstrap). Deterministic: the run stamp is derived from
the topics, never wall-clock.
"""
import hashlib
import json
import sys
from pathlib import Path

# --- cross-repo bootstrap so `import src.*` resolves outside the proof harness ---
_here = Path(__file__).resolve()
_root = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[2])
sys.path.insert(0, str(_root))
from scripts._repo_paths import install as _install  # noqa: E402
_install()

ROUTE = {
    "route": "topic_to_registry_primitives",
    "input_edge": "TopicSet+IntakePolicy",
    "output_edge": "RegisteredCandidatePrimitives+IntakeReceipt",
    "stages": ["scrape_ideate", "screen_shape", "bridge", "count_receipt"],
    "candidate": True, "serves_truth": False, "surface_visibility": "private_internal_only",
}


def _stamp(topics: list[str]) -> str:
    """Deterministic run label from the topics — never wall-clock (harness determinism)."""
    return hashlib.sha256(",".join(sorted(topics)).encode("utf-8")).hexdigest()[:12]


def _edges_for(plane: str) -> tuple[str, str]:
    """A deterministic, meaning-bearing primitive edge for a discovered component on a plane."""
    p = plane or "generic"
    return f"SourceRef+{p}Policy", f"{p}Result+Receipt"


def shape_candidate(idea: dict, run_stamp: str) -> dict | None:
    """SCREEN + SHAPE: a governed discovered idea -> a registry-loadable verified_candidate row, or None if it
    doesn't clear the screen. Only real components (a classified plane + a tool/capability idea kind) become
    primitive candidates; everything else is held out (lossless — discovery keeps it in the feed). The row is
    honestly labelled provenance=discovered / candidate / serves_truth=false, and carries the exact fields
    map_row requires (kind, input_edge, output_edge, primitive_id, dedupe_key)."""
    plane = idea.get("plane")
    kinds = set(idea.get("idea_kinds", []))
    if not plane or not (kinds & {"tool", "capability"}):
        return None                                            # screened out — held out in the discovery feed, not dropped
    cid = idea.get("id") or idea.get("name") or ""
    if not cid:
        return None
    ie, oe = _edges_for(plane)
    return {
        "kind": "primitive",
        "primitive_id": f"discovered.{plane}.{cid}",
        "primitive_kind": plane,
        "input_edge": ie,
        "output_edge": oe,
        "dedupe_key": f"{plane}:{cid}",
        "title": idea.get("name") or cid,
        "contract": {"summary": (idea.get("idea_rationale") or "")[:200]},
        "effects": [],
        "source_provider": "discovered_github",
        "source_refs": [idea["url"]] if idea.get("url") else [],
        "provenance": "discovered",
        "candidate": True,
        "serves_truth": False,
        "verified_at": run_stamp,                              # deterministic; the loader copies this into generated_at
    }


def run(topics: list[str]) -> dict:
    """The whole capability, end to end — NON-DESTRUCTIVE: it APPENDS newly-discovered cards to the registered
    pack (dedup by id), never rebuilds/shrinks it. Returns an IntakeReceipt."""
    from scripts import discovery_pipeline as dp
    from scripts import load_verified_candidates_into_registry as loader
    stamp = _stamp(topics)

    ideas = dp.run(topics)                                     # stage 1: scrape + govern + ideate
    rows = [r for r in (shape_candidate(i, stamp) for i in ideas) if r]   # stage 2: screen + shape
    label = f"discovered-{stamp}"
    dest = loader.VERIFIED_ROOT / label / "verified_candidates.jsonl"     # keep the source rows (lineage — a full
    dest.parent.mkdir(parents=True, exist_ok=True)                        # flywheel rebuild would include them too)
    dest.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    # stage 3: bridge = map rows -> cards, APPEND the new ones to the registered pack (dedup; never shrinks it)
    pack = loader.OUTPUT_PATH
    have: set[str] = set()
    for ln in (pack.read_text(encoding="utf-8").splitlines() if pack.exists() else []):
        try:
            have.add(json.loads(ln)["primitive_id"])
        except (ValueError, KeyError):
            pass
    before = len(have)
    new_cards, seen = [], set()
    for r in rows:
        c = loader.map_row(r, label=label, visibility="private_internal_only")
        if c and c["primitive_id"] not in have and c["primitive_id"] not in seen:
            seen.add(c["primitive_id"])
            new_cards.append(c)
    pack.parent.mkdir(parents=True, exist_ok=True)
    with pack.open("a", encoding="utf-8") as fh:
        for c in new_cards:
            fh.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    after = before + len(new_cards)
    if loader.MANIFEST_PATH.exists():                         # bump the count; record the appended discovered rows
        man = json.loads(loader.MANIFEST_PATH.read_text())
        man["cards_out"] = after
        man["discovered_appended"] = man.get("discovered_appended", 0) + len(new_cards)
        loader.MANIFEST_PATH.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {                                                  # stage 4: receipt
        "record_type": "topic_to_registry_intake_receipt",
        "route": ROUTE["route"], "topics": topics, "run_label": label,
        "ideas_discovered": len(ideas), "screened_shaped": len(rows),
        "cards_before": before, "cards_after": after, "cards_delta": len(new_cards),
        "all_candidate_serves_truth_false": all(r["serves_truth"] is False for r in rows),
        "surface_visibility": ROUTE["surface_visibility"],
    }


def self_test() -> int:
    from scripts import load_verified_candidates_into_registry as loader
    checks: list[tuple[str, bool]] = []
    idea = {"id": "paddleocr", "name": "paddleocr", "plane": "ocr", "idea_kinds": ["tool", "capability"],
            "idea_rationale": "vendorable Apache-2.0 ocr component", "url": "https://github.com/x/paddleocr",
            "status": "candidate", "serves_truth": False}
    row = shape_candidate(idea, "stamp0")
    checks.append(("a governed component idea shapes into a primitive row", row is not None and row["kind"] == "primitive"))
    checks.append(("shaped row carries input + output edges", bool(row["input_edge"]) and bool(row["output_edge"])))
    checks.append(("shaped row stays candidate + serves_truth=false", row["candidate"] and row["serves_truth"] is False))
    card = loader.map_row(row, label="discovered-test", visibility="private_internal_only")
    checks.append(("the registry bridge ACCEPTS the shaped row as a card", card is not None and card["kind"] == "route.primitive"))
    checks.append(("a non-component idea is screened OUT (held, not shaped)",
                   shape_candidate({"id": "z", "plane": None, "idea_kinds": ["watch"]}, "s") is None))
    checks.append(("the run stamp is deterministic (no wall-clock)", _stamp(["b", "a"]) == _stamp(["a", "b"])))
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - topic_to_registry_primitives:\n  " + "\n  ".join(failed)); return 1
    print("PASS - topic_to_registry_primitives: governed idea -> screened+shaped -> the registry bridge accepts "
          "it as a candidate card; non-components are held out; deterministic run label.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    topics = [a for a in argv if not a.startswith("-")] or ["ocr", "reranker", "pdf table extraction"]
    print(f"== capability: topic_to_registry_primitives — {len(topics)} topic(s) ==")
    r = run(topics)
    print("\n== IntakeReceipt ==")
    for k in ("topics", "ideas_discovered", "screened_shaped", "cards_before", "cards_after", "cards_delta",
              "all_candidate_serves_truth_false", "run_label"):
        print(f"  {k}: {r[k]}")
    print(f"\n  {r['cards_delta']} new candidate primitives are now registry-visible "
          f"(private_internal_only, serves_truth=false). Re-run any time with new topics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
