#!/usr/bin/env python3
"""primitive_scale_and_containment — a primitive spans orders of magnitude; the model must too.

Owner (2026-07-10): "A primitive could be a very large 100K line python K8 application with src files,
folders, etc." — a primitive is NOT always a small snippet. It ranges from a 20-line function to a
100,000-line, multi-folder, multi-service application. Two things have to scale with it:

  1. REPRESENTATION. A small primitive can carry its body inline (the card's blackbox). A large one CANNOT
     and MUST NOT — you never store 100K lines in a row (repo law: "store handles, digests, components, and
     receipts; raw source bodies do not go in primitive rows"). A large primitive is a SOURCE-TREE REFERENCE:
     a handle (repo/uri) + subtree path + content digest + file/line counts + entrypoints — never the bytes.

  2. DELIVERY. You never prompt-inject a 100K-line app, and you rarely `pip import` a whole service. Bigger
     primitives climb the reuse ladder toward reference/vendor/DEPLOY (from the storage-and-delivery model):
     an application is retrieved by reference and RUN as a service, not pasted into a prompt.

And the load-bearing property: a large primitive is FRACTAL. It has an EXTERNAL contract (its typed
input/output edges — how it composes with peers, exactly like a small one) AND an INTERNAL decomposition (its
src files/modules are themselves primitives). So the composition layer (groups · networks · integrators)
applies to its INSIDES, and a large primitive can be viewed as one atom OR as a whole network — same record
shape at every zoom level ("primitives of primitives").

    PYTHONPATH=. python3 scripts/primitive_scale_and_containment.py --self-test
    PYTHONPATH=. python3 scripts/primitive_scale_and_containment.py --classify --lines 100000 --files 1200
    PYTHONPATH=. python3 scripts/primitive_scale_and_containment.py --measure ../teleon/backend/src
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_scale_and_containment requires canonical_id; import failed: {exc}")

OUT_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "scale_profiles"
PROFILES_PATH = OUT_DIR / "primitive_scale_profiles.jsonl"
MANIFEST_PATH = OUT_DIR / "scale_profile_manifest.json"
SCALE_ID_PREFIX = "pscale"
REF_ID_PREFIX = "psref"
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}

#: The 5 reuse rungs from the storage-and-delivery model (+ deploy). Larger primitives lose the small-only
#: rungs from the top down (you cannot prompt-inject a service; you cannot pip-import an application).
_ALL_RUNGS = ("reference", "source_inline", "package_import", "vendor_copy", "deterministic_compose", "deploy")

#: GRANULARITY LADDER (ascending). A tier is the FIRST whose line AND file caps both hold; else `application`.
#: Each row: name, max_lines, max_files, representation, prompt_inline_viable, delivery_rungs, typical_media, note.
#: Extend = one row. Caps are deliberate round bands (a classification, not a measurement).
GRANULARITY_TIERS: list[dict[str, Any]] = [
    {"tier": "atom", "max_lines": 30, "max_files": 1, "representation": "inline_body",
     "prompt_inline_viable": True,
     "delivery_rungs": ["reference", "source_inline", "package_import", "vendor_copy", "deterministic_compose"],
     "typical_media": ["local_cli", "cloud_function"],
     "note": "a single expression/helper — the card's blackbox IS the body"},
    {"tier": "function", "max_lines": 150, "max_files": 1, "representation": "inline_body",
     "prompt_inline_viable": True,
     "delivery_rungs": ["reference", "source_inline", "package_import", "vendor_copy", "deterministic_compose"],
     "typical_media": ["local_cli", "cloud_function"],
     "note": "one self-contained function — inline still cheap and reliable"},
    {"tier": "module", "max_lines": 2500, "max_files": 15, "representation": "source_tree_reference",
     "prompt_inline_viable": False,
     "delivery_rungs": ["reference", "package_import", "vendor_copy", "deterministic_compose", "deploy"],
     "typical_media": ["cloud_function", "container_service"],
     "note": "a cohesive module/small package — import or vendor it; inlining is unreliable past a screenful"},
    {"tier": "package", "max_lines": 20_000, "max_files": 250, "representation": "source_tree_reference",
     "prompt_inline_viable": False,
     "delivery_rungs": ["reference", "package_import", "vendor_copy", "deploy"],
     "typical_media": ["container_service", "k8s_deployment"],
     "note": "a real library/component — a package artifact + its declared internal components"},
    {"tier": "service", "max_lines": 100_000, "max_files": 1000, "representation": "source_tree_reference",
     "prompt_inline_viable": False,
     "delivery_rungs": ["reference", "vendor_copy", "deploy"],
     "typical_media": ["k8s_deployment", "k8s_job", "stream_worker"],
     "note": "a deployable service — retrieved by reference and RUN, decomposed into modules internally"},
    {"tier": "application", "max_lines": float("inf"), "max_files": float("inf"),
     "representation": "source_tree_reference", "prompt_inline_viable": False,
     "delivery_rungs": ["reference", "deploy"],
     "typical_media": ["k8s_deployment", "batch_job", "stream_worker"],
     "note": "a 100K+-line, multi-folder, possibly multi-service application — a source-tree reference you "
             "deploy and call; its src tree IS a whole network of smaller primitives"},
]


def classify(lines: int, files: int) -> dict[str, Any]:
    """The tier for a (lines, files) shape — the FIRST whose caps both hold, else application."""
    for row in GRANULARITY_TIERS:
        if lines <= row["max_lines"] and files <= row["max_files"]:
            return row
    return GRANULARITY_TIERS[-1]


def source_tree_reference(handle: str, subtree: str, content_digest: str, file_count: int, line_count: int,
                          language: str = "python", entrypoints: Optional[list[str]] = None,
                          components: Optional[list[str]] = None) -> dict[str, Any]:
    """The representation for a LARGE primitive: a governed reference to a source tree. Carries handle +
    digest + counts + entrypoints + declared internal components — NEVER the source bytes (repo law)."""
    return {
        "ref_id": canonical_id(REF_ID_PREFIX, handle, subtree, content_digest),
        "record_type": "primitive_source_tree_reference",
        "handle": handle, "subtree": subtree, "content_digest": content_digest,
        "language": language, "file_count": file_count, "line_count": line_count,
        "entrypoints": sorted(entrypoints or []),
        "internal_components": sorted(components or []),   # sub-primitive refs — the fractal decomposition
        "body_inlined": False,   # a large primitive NEVER inlines its body
        "governance_note": "handle + digest + counts only; raw source bytes are not stored in the row",
        "schema_version": "1", **_CANDIDATE_BITS,
    }


def profile_scale(primitive: dict[str, Any]) -> dict[str, Any]:
    """Full scale profile for a primitive that declares its size (line_count/file_count) or inline body.
    Small -> inline representation; module+ -> a source-tree reference (governance-preserving)."""
    lines = int(primitive.get("line_count") or _count_inline_lines(primitive))
    files = int(primitive.get("file_count") or 1)
    tier = classify(lines, files)
    representation: dict[str, Any]
    if tier["representation"] == "inline_body":
        representation = {"mode": "inline_body", "body_inlined": True,
                          "note": "small enough to carry its body in the card blackbox"}
    else:
        representation = {"mode": "source_tree_reference", "body_inlined": False,
                          "reference": source_tree_reference(
                              handle=str(primitive.get("handle") or "handle://unspecified"),
                              subtree=str(primitive.get("subtree") or "."),
                              content_digest=str(primitive.get("content_digest")
                                                 or canonical_id("treedigest", str(primitive.get("primitive_id")),
                                                                 str(lines), str(files)).rsplit("-", 1)[-1]),
                              file_count=files, line_count=lines,
                              language=str(primitive.get("language") or "python"),
                              entrypoints=primitive.get("entrypoints"),
                              components=primitive.get("internal_components"))}
    return {
        "scale_id": canonical_id(SCALE_ID_PREFIX, str(primitive.get("primitive_id") or ""),
                                 tier["tier"], str(lines), str(files)),
        "record_type": "primitive_scale_profile",
        "primitive_id": primitive.get("primitive_id") or primitive.get("card_id"),
        "title": primitive.get("title"),
        "tier": tier["tier"], "line_count": lines, "file_count": files,
        "prompt_inline_viable": tier["prompt_inline_viable"],
        "delivery_rungs": tier["delivery_rungs"],
        "excluded_rungs": [r for r in _ALL_RUNGS if r not in tier["delivery_rungs"]],
        "typical_media": tier["typical_media"],
        "representation": representation,
        "external_contract": {"input_edge": primitive.get("input_edge"),
                              "output_edge": primitive.get("output_edge")},
        "fractal_note": ("a large primitive composes with peers by its typed edges AND decomposes internally "
                         "into sub-primitives — the composition layer (groups/networks/integrators) applies "
                         "recursively to its src tree"),
        "tier_note": tier["note"],
        "schema_version": "1", **_CANDIDATE_BITS,
    }


def _count_inline_lines(primitive: dict[str, Any]) -> int:
    body = str(primitive.get("body") or primitive.get("blackbox") or "")
    return body.count("\n") + 1 if body else 1


def measure_subtree(root: Path, suffix: str = ".py") -> dict[str, int]:
    """Deterministically measure a real source subtree (for the worked examples) — file + line counts only."""
    files = sorted(p for p in root.rglob(f"*{suffix}") if p.is_file())
    line_count = 0
    for f in files:
        try:
            line_count += sum(1 for _ in f.open("rb"))
        except OSError:
            continue
    return {"file_count": len(files), "line_count": line_count}


# ── worked examples: REAL subtrees measured live + a synthetic 100K-line K8s application descriptor. ─────────
def _worked_examples() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = [
        {"primitive_id": "example:atom:jitter", "title": "exponential backoff jitter (one expression)",
         "body": "return base * 2 ** attempt + random.uniform(0, jitter)",
         "input_edge": "AttemptCount", "output_edge": "DelayMs"},
        {"primitive_id": "example:function:csv_sniff", "title": "CSV dialect sniffer",
         "line_count": 90, "file_count": 1, "input_edge": "CsvSample", "output_edge": "DialectSpec"},
        {"primitive_id": "example:app:k8s_100k",
         "title": "A 100K-line multi-folder Python K8s application (the owner's example)",
         "line_count": 100_000, "file_count": 1200, "handle": "git://internal/some-k8s-app",
         "subtree": "src/", "language": "python",
         "entrypoints": ["src/app/main.py", "deploy/helm/Chart.yaml", "src/workers/consumer.py"],
         "internal_components": ["example:package:api_layer", "example:package:worker_pool",
                                 "example:module:auth", "example:module:db"],
         "input_edge": "ClusterConfig+DataSource", "output_edge": "ServedApi+Metrics"},
    ]
    # measure two REAL trees in this monorepo so the ladder is grounded, not asserted
    for pid, title, rel in (("example:service:teleon_src", "Teleon backend src (real subtree)",
                             _ROOT / "_repos" / "teleon" / "backend" / "src"),
                            ("example:package:baltor_src", "Baltor backend src (real subtree)",
                             _ROOT / "_repos" / "baltor" / "backend" / "src")):
        if rel.exists():
            counts = measure_subtree(rel)
            examples.append({"primitive_id": pid, "title": title, "handle": f"repo://{rel.name}",
                             "subtree": str(rel.relative_to(_ROOT)), **counts,
                             "input_edge": "PurposeTask", "output_edge": "CapabilityReceipt"})
    return examples


def build(write: bool = True) -> dict[str, Any]:
    profiles = [profile_scale(ex) for ex in _worked_examples()]
    from collections import Counter
    manifest = {
        "record_type": "scale_profile_manifest",
        "profiled": len(profiles),
        "tier_histogram": dict(Counter(p["tier"] for p in profiles)),
        "tiers_defined": [t["tier"] for t in GRANULARITY_TIERS],
        "reuse_rungs": list(_ALL_RUNGS),
        "source_ref": "owner-intent:primitive-scale-and-containment:2026-07-10", **_CANDIDATE_BITS,
    }
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_PATH.write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in profiles))
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"manifest": manifest, "profiles": profiles}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) the ladder classifies the full range: a one-liner -> atom/function; the 100K/1200-file app ->
    #     application; real measured monorepo subtrees land in the middle tiers.
    tiny = classify(20, 1)["tier"]
    app = classify(100_000, 1200)["tier"]
    checks.append(("granularity ladder spans the range: 20-line/1-file -> atom; 100K-line/1200-file K8s app "
                   "-> application (the owner's example classifies correctly)",
                   tiny == "atom" and app == "application", f"tiny={tiny}, app={app}"))

    # (2) monotonic: growing lines OR files never LOWERS the tier.
    order = [t["tier"] for t in GRANULARITY_TIERS]
    seq = [classify(n, f)["tier"] for n, f in [(10, 1), (100, 1), (2000, 8), (18000, 200),
                                               (80000, 700), (500000, 3000)]]
    checks.append(("tier is monotonic in size (more lines/files -> same-or-higher tier)",
                   all(order.index(seq[i]) <= order.index(seq[i + 1]) for i in range(len(seq) - 1))
                   and seq[-1] == "application", json.dumps(seq)))

    # (3) THE governance point: a large primitive is a SOURCE-TREE REFERENCE with NO inline body — handle +
    #     digest + counts only, never the 100K lines. A small one inlines its body.
    profiles = build(write=True)["profiles"]
    by_id = {p["primitive_id"]: p for p in profiles}
    big = by_id["example:app:k8s_100k"]
    small = by_id["example:atom:jitter"]
    ref = big["representation"]["reference"]
    checks.append(("large primitive -> source-tree REFERENCE (handle+digest+counts, body_inlined=false, no "
                   "raw bytes); small primitive -> inline body — the 100K lines are never stored in the row",
                   big["representation"]["mode"] == "source_tree_reference"
                   and ref["body_inlined"] is False and ref["content_digest"] and ref["line_count"] == 100_000
                   and "body" not in ref and "source" not in ref
                   and small["representation"]["body_inlined"] is True,
                   f"big.mode={big['representation']['mode']}, small.inlined={small['representation']['body_inlined']}"))

    # (4) DELIVERY scales with size: the app can only be referenced or DEPLOYED (no prompt-inline, no import);
    #     the atom can be reused every way. The excluded rungs are explicit.
    checks.append(("delivery rungs scale with size: application = {reference, deploy} only (prompt-inline + "
                   "package-import EXCLUDED); atom = every rung; prompt_inline_viable false for the app",
                   set(big["delivery_rungs"]) == {"reference", "deploy"}
                   and "source_inline" in big["excluded_rungs"] and "package_import" in big["excluded_rungs"]
                   and big["prompt_inline_viable"] is False
                   and "source_inline" in small["delivery_rungs"] and small["prompt_inline_viable"] is True,
                   json.dumps({"app_rungs": big["delivery_rungs"], "app_excluded": big["excluded_rungs"]})))

    # (5) FRACTAL: the large primitive has BOTH an external contract (typed edges) AND an internal
    #     decomposition (sub-primitive components) — it is an atom to peers and a network inside.
    checks.append(("large primitive is fractal: external typed edges (composes with peers) + internal "
                   "components (decomposes into sub-primitives, recursion into the composition layer)",
                   big["external_contract"]["input_edge"] and big["external_contract"]["output_edge"]
                   and len(ref["internal_components"]) >= 2, json.dumps(ref["internal_components"])))

    # (6) the REAL measured subtrees ground the ladder (not just asserted bands).
    real_service = by_id.get("example:service:teleon_src")
    real_pkg = by_id.get("example:package:baltor_src")
    grounded = (real_service is not None and real_service["line_count"] > 10_000
                and real_service["tier"] in ("package", "service", "application")
                and real_pkg is not None and real_pkg["representation"]["mode"] == "source_tree_reference")
    checks.append(("grounded on REAL monorepo subtrees (teleon/baltor src measured live -> mid-tier "
                   "source-tree references, not inline)",
                   grounded, f"teleon={real_service['tier'] if real_service else 'absent'} "
                             f"({real_service['line_count'] if real_service else 0} lines)"))

    # (7) determinism + candidate-only + computed manifest.
    first = PROFILES_PATH.read_bytes()
    built = build(write=True)
    checks.append(("deterministic rebuild (byte-identical); every row candidate-only; manifest counts computed",
                   first == PROFILES_PATH.read_bytes()
                   and all(p["candidate"] is True and p["serves_truth"] is False for p in built["profiles"])
                   and built["manifest"]["profiled"] == len(built["profiles"]), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_scale_and_containment: primitives span atom→application "
          f"({len(GRANULARITY_TIERS)} tiers); large ones are governed SOURCE-TREE REFERENCES (handle+digest+"
          f"counts, never raw bytes) delivered by reference/deploy (not prompt-inline), and are FRACTAL "
          f"(external edges + internal sub-primitive decomposition). serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scale + containment model for primitives (atom→application).")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--classify", action="store_true")
    parser.add_argument("--lines", type=int, default=0)
    parser.add_argument("--files", type=int, default=1)
    parser.add_argument("--measure", help="a real subtree path to measure + classify")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        print(json.dumps(build(write=True)["manifest"], indent=2, sort_keys=True))
        return 0
    if args.classify:
        tier = classify(args.lines, args.files)
        print(json.dumps({"lines": args.lines, "files": args.files, "tier": tier["tier"],
                          "representation": tier["representation"],
                          "prompt_inline_viable": tier["prompt_inline_viable"],
                          "delivery_rungs": tier["delivery_rungs"], "typical_media": tier["typical_media"],
                          "note": tier["note"]}, indent=2))
        return 0
    if args.measure:
        root = Path(args.measure)
        if not root.exists():
            print(json.dumps({"error": f"no such path {args.measure!r}"}))
            return 1
        counts = measure_subtree(root)
        profile = profile_scale({"primitive_id": f"measured:{root.name}", "title": f"{root} (measured)",
                                 "handle": f"repo://{root.name}", "subtree": str(root), **counts,
                                 "input_edge": "Input", "output_edge": "Output"})
        print(json.dumps(profile, indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
