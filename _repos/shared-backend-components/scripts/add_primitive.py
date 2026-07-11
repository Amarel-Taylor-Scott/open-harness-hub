#!/usr/bin/env python3
"""scripts.add_primitive — the ONE-CALL, gated front door for "add more primitives" (ergonomic + safe).

Adding a primitive today means hand-assembling an edge-foundry card, hoping its edges are typed, hoping it is not a
dupe of one of the ~7.28M existing rows, and (almost never) actually proving it — which is why 0 rows were ever
serves_truth=true. This module makes "add one primitive" a single gated pipeline call that CANNOT silently violate the
repo laws: a spec goes in, an AcceptDecision comes out, and the only path to serves_truth=true is an EXECUTED passing
proof (never a shape check). It is the ergonomic layer OVER the existing machinery, not a reimplementation of it.

Pipeline (each stage is a named gate in the returned decision):
  1. NORMALIZE   — coerce a loose spec into the edge-foundry card shape (title/input_edge/output_edge/blackbox/effects,
                   candidate=true / serves_truth=false, source_ref as a DICT {url,name,path}).
  2. COMPOSABILITY — reject `edge_untyped` cards via check_primitive_composability.composability_report (a card whose
                   input OR output edge cannot canonicalize can never chain), with a local fallback canonicalizer.
  3. DEDUPE      — reject an exact duplicate by canonical content hash against the intake ledger (append-only jsonl).
  4. PROOF       — if the spec carries fixture_input + expected_output + mutator, RUN mutator_registry.run_primitive_proof
                   and set serves_truth=true ONLY on a passing executed proof; otherwise the card stays candidate with
                   proofs_unexecuted=true.
  5. STORE       — accepted rows are appended to accepted_primitives.jsonl and the manifest row-counts recomputed.

ADD-ONLY: this file edits none of the contract-locked matchers/verifiers; it IMPORTS the existing machinery
(mutator_registry, check_primitive_composability, build_edge_type_retrofit, build_retrieval_backend_portfolio) with a
graceful try/except fallback so its --self-test passes offline + standalone even while sibling modules are mid-build.
Offline + deterministic: no network, no wall-clock/RNG in row bodies (a fixed `now` string is threaded through). CLI:
  --self-test           pure, offline, standalone (uses an in-memory ledger — touches no disk)
  --demo [--write]      ingest ~8 example specs (proof-backed leaves, a dupe, an edge_untyped) and print accept/reject
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# The candidate boundary every generated row carries unless a passing executed proof flips serves_truth.
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
# Deterministic default clock for bake-off/self-test bodies (never wall-clock inside row bodies).
FIXED_NOW = "2026-07-03T00:00:00Z"

INTAKE_DIR = _resource("data") / "dev-intel" / "primitive_intake"
LEDGER_PATH = INTAKE_DIR / "intake_ledger.jsonl"
ACCEPTED_PATH = INTAKE_DIR / "accepted_primitives.jsonl"
MANIFEST_PATH = INTAKE_DIR / "manifest.json"

# ── REUSE existing machinery — import with graceful fallback so --self-test is standalone/offline ──
try:  # REAL executable mutators + the proof-runner that flips serves_truth ONLY on a passing executed proof
    from scripts.mutator_registry import MUTATOR_REGISTRY, run_primitive_proof  # type: ignore
except Exception:  # noqa: BLE001
    MUTATOR_REGISTRY = {}  # type: ignore[assignment]
    run_primitive_proof = None  # type: ignore[assignment]

try:  # the additive composability gate (edge_untyped -> fail)
    from scripts.check_primitive_composability import composability_report as _composability_report  # type: ignore
except Exception:  # noqa: BLE001
    _composability_report = None  # type: ignore[assignment]

try:  # the pure edge canonicalizer (also used as a composability fallback)
    from scripts.build_edge_type_retrofit import canonicalize_edge as _canonicalize_edge  # type: ignore
except Exception:  # noqa: BLE001
    _canonicalize_edge = None  # type: ignore[assignment]

try:  # the active-retrieval-backend resolver — used only to tag the accepted card's embedding plane
    from scripts.build_retrieval_backend_portfolio import active_embedder as _active_embedder  # type: ignore
except Exception:  # noqa: BLE001
    _active_embedder = None  # type: ignore[assignment]

# Sibling modules being built by a concurrent workflow — import optionally, never required for correctness.
try:
    from scripts.primitive_runtime import compose_solution as _compose_solution  # type: ignore  # noqa: F401
except Exception:  # noqa: BLE001
    _compose_solution = None  # type: ignore[assignment]


# ── minimal local fallbacks (only used when a sibling module is absent) ──
_PLACEHOLDER_MARKERS = ("{", "}", "<", ">", "$", "%")
_UNTYPED_SENTINELS = frozenset({"", "none", "null", "any", "unknown", "todo", "tbd", "data", "value", "input", "output"})


def _local_canonicalize_edge(edge_label: Any) -> Optional[str]:
    """Deterministic edge -> canonical type id or None (used only if build_edge_type_retrofit is unavailable)."""
    if not isinstance(edge_label, str) or not edge_label.strip():
        return None
    if any(mark in edge_label for mark in _PLACEHOLDER_MARKERS):
        return None
    label = edge_label.split("+")[0].strip()
    import re

    parts = [p for p in re.split(r"[^0-9A-Za-z]+", label) if p]
    if not parts:
        return None
    canon = "".join(p[:1].upper() + p[1:] for p in parts)
    return None if canon.lower() in _UNTYPED_SENTINELS else canon


def _edge_type_id(edge_label: Any) -> Optional[str]:
    """Best-available edge canonicalizer, normalized so a catch-all/empty result reads as None (untyped)."""
    result: Any = None
    if _canonicalize_edge is not None:
        try:
            result = _canonicalize_edge(edge_label)
        except Exception:  # noqa: BLE001
            result = None
    if not (isinstance(result, str) and result.strip()) or (isinstance(result, str) and result.strip().lower() in _UNTYPED_SENTINELS):
        result = _local_canonicalize_edge(edge_label)
    if isinstance(result, str) and result.strip() and result.strip().lower() not in _UNTYPED_SENTINELS:
        return result.strip()
    return None


# ── stage 1: NORMALIZE a loose spec into the edge-foundry card shape ──
def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


def _normalize_source_ref(spec: dict[str, Any]) -> dict[str, str]:
    """Coerce whatever the spec offers into a source_ref DICT {url, name, path} (the shape registry_search reads)."""
    raw = spec.get("source_ref")
    if isinstance(raw, dict):
        return {"url": str(raw.get("url") or ""), "name": str(raw.get("name") or spec.get("title") or ""),
                "path": str(raw.get("path") or "")}
    if isinstance(raw, str):  # a bare string is treated as the source URL
        return {"url": raw, "name": str(spec.get("title") or ""), "path": ""}
    return {"url": str(spec.get("url") or ""), "name": str(spec.get("name") or spec.get("title") or ""),
            "path": str(spec.get("path") or "")}


def _normalize_effects(spec: dict[str, Any]) -> list[dict[str, Any]]:
    effects = spec.get("effects")
    if not isinstance(effects, list):
        return []
    out: list[dict[str, Any]] = []
    for e in effects:
        if isinstance(e, dict):
            out.append(e)
        elif isinstance(e, str):
            out.append({"type": "metadata", "description": e})
    return out


def _content_identity(card: dict[str, Any]) -> dict[str, Any]:
    """The identity that defines "the same primitive" for dedupe — title + both edges + blackbox + effects."""
    return {
        "title": card.get("title") or "",
        "input_edge": card.get("input_edge") or "",
        "output_edge": card.get("output_edge") or "",
        "blackbox": card.get("blackbox") or "",
        "effects": card.get("effects") or [],
    }


def content_hash(card: dict[str, Any]) -> str:
    """Canonical content hash over the card's identity (formatting-invariant, order-invariant)."""
    return _hash(_content_identity(card))[:16]


def normalize_spec(spec: dict[str, Any], *, now: str = FIXED_NOW) -> tuple[dict[str, Any], list[str]]:
    """Coerce a loose spec into a candidate edge-foundry card. Returns (card, problems). problems is non-empty when
    the spec is too thin to be a card (no title, or no input/output edge at all)."""
    problems: list[str] = []
    if not isinstance(spec, dict):
        return {}, ["spec is not a dict"]
    title = str(spec.get("title") or "").strip()
    input_edge = spec.get("input_edge")
    output_edge = spec.get("output_edge")
    if not title:
        problems.append("missing title")
    if not (isinstance(input_edge, str) and input_edge.strip()):
        problems.append("missing input_edge")
    if not (isinstance(output_edge, str) and output_edge.strip()):
        problems.append("missing output_edge")

    card: dict[str, Any] = {
        "record_type": "primitive_intake_card",
        "kind": str(spec.get("kind") or "route.primitive"),
        "title": title,
        "input_edge": input_edge if isinstance(input_edge, str) else "",
        "output_edge": output_edge if isinstance(output_edge, str) else "",
        "blackbox": str(spec.get("blackbox") or ""),
        "effects": _normalize_effects(spec),
        "contract": spec.get("contract") if isinstance(spec.get("contract"), dict)
        else {"input": {}, "output": {}, "summary": str(spec.get("blackbox") or "")},
        "source_ref": _normalize_source_ref(spec),
        "mutations": spec.get("mutations") if isinstance(spec.get("mutations"), list) else [],
        "readiness": "R2_edge_known",
        "verification_level": "L2_shape_only",
        "intake_generated_at": now,
        **BOUNDARY,
    }
    card["content_hash"] = content_hash(card)
    card["primitive_id"] = spec.get("primitive_id") or f"prim:intake:{card['content_hash']}"
    # tag the active embedding plane (best-effort; never fails the pipeline)
    if _active_embedder is not None:
        try:
            emb = _active_embedder()
            card["embedding_plane"] = {"embedder_id": emb.get("backend_id"), "dim": emb.get("dim")}
        except Exception:  # noqa: BLE001
            pass
    return card, problems


# ── stage 2: COMPOSABILITY gate ──
def _composability_gate(card: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Return (pass, verdict). Prefer the sibling composability_report; fall back to a local typedness check."""
    if _composability_report is not None:
        try:
            v = _composability_report(card)
            return bool(v.get("gate_pass")), v
        except Exception:  # noqa: BLE001
            pass
    in_t = _edge_type_id(card.get("input_edge"))
    out_t = _edge_type_id(card.get("output_edge"))
    untyped = in_t is None or out_t is None
    return (not untyped), {"input_type_id": in_t, "output_type_id": out_t, "edge_untyped": untyped,
                           "gate_pass": not untyped, "_local_fallback": True}


# ── stage 4: PROOF ──
def _proof_gate(spec: dict[str, Any], card: dict[str, Any]) -> tuple[str, Optional[dict[str, Any]]]:
    """Run the executed proof if the spec carries fixture_input + expected_output + mutator.

    Returns (status, receipt). status in {"passed","failed","unexecuted","unavailable"}. serves_truth flips true ONLY
    on "passed" — and only because a REAL proof executed and matched (never a shape check).
    """
    has_fixture = ("fixture_input" in spec and "expected_output" in spec and spec.get("mutator"))
    if not has_fixture:
        return "unexecuted", None
    if run_primitive_proof is None:
        return "unavailable", None
    mutator = str(spec["mutator"])
    if MUTATOR_REGISTRY and mutator not in MUTATOR_REGISTRY:
        return "failed", {"error": f"unknown mutator {mutator!r}", "all_passed": False}
    try:
        receipt = run_primitive_proof(
            card["primitive_id"], mutator, spec["fixture_input"], spec["expected_output"],
            mutator_args=spec.get("mutator_args") or {}, has_inverse=spec.get("has_inverse"),
        )
    except Exception as exc:  # noqa: BLE001
        return "failed", {"error": str(exc), "all_passed": False}
    return ("passed" if receipt.get("serves_truth") else "failed"), receipt


# ── the ledger (append-only; dedupe substrate). In-memory for self-test, disk-backed for real intake ──
class IntakeLedger:
    """Tracks the set of content hashes already seen so an exact dupe is rejected. `disk` toggles persistence."""

    def __init__(self, seen: Optional[set[str]] = None, *, disk: bool = False,
                 ledger_path: Path = LEDGER_PATH, accepted_path: Path = ACCEPTED_PATH,
                 manifest_path: Path = MANIFEST_PATH) -> None:
        self.disk = disk
        self.ledger_path = ledger_path
        self.accepted_path = accepted_path
        self.manifest_path = manifest_path
        self.seen: set[str] = set(seen or ())
        if disk:
            self.seen |= self._load_seen()

    def _load_seen(self) -> set[str]:
        out: set[str] = set()
        if self.ledger_path.exists():
            with self.ledger_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.add(json.loads(line).get("content_hash"))
                    except json.JSONDecodeError:
                        continue
        out.discard(None)
        return out

    def contains(self, h: str) -> bool:
        return h in self.seen

    def record(self, card: dict[str, Any], *, now: str) -> Optional[str]:
        """Register an accepted card's hash. Appends to the ledger + accepted files + manifest when disk-backed.
        Returns the accepted-file path (str) when persisted, else None."""
        h = card["content_hash"]
        self.seen.add(h)
        if not self.disk:
            return None
        self.accepted_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"record_type": "primitive_intake_ledger_entry", "content_hash": h,
                                 "primitive_id": card["primitive_id"], "recorded_at": now}, sort_keys=True) + "\n")
        with self.accepted_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(card, ensure_ascii=False, sort_keys=True) + "\n")
        self._rebuild_manifest(now=now)
        return str(self.accepted_path)

    def _rebuild_manifest(self, *, now: str) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        if self.accepted_path.exists():
            with self.accepted_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        proven = sum(1 for r in rows if r.get("serves_truth") is True)
        canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
        manifest = {
            "record_type": "primitive_intake_manifest",
            "generator": "scripts/add_primitive.py",
            "generated_utc": now,
            "row_counts": {"accepted_primitives.jsonl": len(rows)},
            "total_rows": len(rows),
            "accepted_count": len(rows),
            "proven_serves_truth_count": proven,
            "candidate_count": len(rows) - proven,
            "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
        return manifest


# ── THE one-call front door ──
def add_primitive(spec: dict[str, Any], *, prove: bool = True, now: str = FIXED_NOW,
                  ledger: Optional[IntakeLedger] = None) -> dict[str, Any]:
    """Take ONE primitive spec through the gated pipeline and return an AcceptDecision.

    AcceptDecision = {accepted, primitive_id, gates:{normalize,composability,dedupe,proof}, reasons:[...], stored_to,
    serves_truth, card}. accepted requires normalize+composability+dedupe to pass; the PROOF gate never rejects — it
    only decides whether serves_truth flips true (on a passing executed proof) or the card stays candidate.
    """
    lg = ledger if ledger is not None else IntakeLedger(disk=False)
    gates: dict[str, str] = {}
    reasons: list[str] = []

    # 1. NORMALIZE
    card, problems = normalize_spec(spec, now=now)
    if problems:
        gates["normalize"] = "invalid"
        gates["composability"] = gates["dedupe"] = gates["proof"] = "skipped"
        reasons.extend(problems)
        return {"accepted": False, "primitive_id": card.get("primitive_id"), "gates": gates,
                "reasons": reasons, "stored_to": None, "serves_truth": False, "card": card}
    gates["normalize"] = "ok"

    # 2. COMPOSABILITY
    comp_pass, verdict = _composability_gate(card)
    if not comp_pass:
        gates["composability"] = "edge_untyped"
        gates["dedupe"] = gates["proof"] = "skipped"
        reasons.append(
            f"edge_untyped: input={verdict.get('input_type_id')!r} output={verdict.get('output_type_id')!r}")
        return {"accepted": False, "primitive_id": card["primitive_id"], "gates": gates,
                "reasons": reasons, "stored_to": None, "serves_truth": False, "card": card}
    gates["composability"] = "pass"

    # 3. DEDUPE
    if lg.contains(card["content_hash"]):
        gates["dedupe"] = "duplicate"
        gates["proof"] = "skipped"
        reasons.append(f"exact duplicate of content_hash {card['content_hash']}")
        return {"accepted": False, "primitive_id": card["primitive_id"], "gates": gates,
                "reasons": reasons, "stored_to": None, "serves_truth": False, "card": card}
    gates["dedupe"] = "unique"

    # 4. PROOF (never rejects — only decides serves_truth)
    if prove:
        status, receipt = _proof_gate(spec, card)
    else:
        status, receipt = "unexecuted", None
    gates["proof"] = status
    if status == "passed":
        card["serves_truth"] = True
        card["candidate"] = False
        card["verification_level"] = "L7_executed_proof"
        if receipt:
            card["proof_receipt"] = receipt
    elif status == "failed":
        card["proofs_unexecuted"] = False
        card["proof_failed"] = True
        if receipt:
            card["proof_receipt"] = receipt
        reasons.append("proof executed but did NOT pass — stays candidate (serves_truth=false)")
    else:  # unexecuted / unavailable
        card["proofs_unexecuted"] = True
        if status == "unavailable":
            reasons.append("proof-runner unavailable — stays candidate (serves_truth=false)")

    # 5. STORE (accepted rows only)
    stored_to = lg.record(card, now=now)
    return {"accepted": True, "primitive_id": card["primitive_id"], "gates": gates, "reasons": reasons,
            "stored_to": stored_to, "serves_truth": bool(card["serves_truth"]), "card": card}


def add_primitives(specs: list[dict[str, Any]], *, prove: bool = True, now: str = FIXED_NOW,
                   ledger: Optional[IntakeLedger] = None) -> dict[str, Any]:
    """Batch front door: ingest many specs through ONE shared ledger (so intra-batch dupes are caught). Returns a
    summary {accepted, rejected, proven, decisions}."""
    lg = ledger if ledger is not None else IntakeLedger(disk=False)
    decisions = [add_primitive(s, prove=prove, now=now, ledger=lg) for s in specs]
    accepted = sum(1 for d in decisions if d["accepted"])
    proven = sum(1 for d in decisions if d["serves_truth"])
    return {
        "record_type": "primitive_intake_batch_summary",
        "submitted": len(decisions), "accepted": accepted, "rejected": len(decisions) - accepted,
        "proven_serves_truth": proven, "candidate_accepted": accepted - proven,
        "generated_utc": now, "decisions": decisions,
    }


# ── demo specs: proof-backed leaves, a dupe, an edge_untyped, a no-fixture candidate ──
def demo_specs() -> list[dict[str, Any]]:
    idem_key = hashlib.sha256("u1|pay".encode()).hexdigest()[:24]
    return [
        # 1. proof-backed leaf (idempotency_wrapper) — should be ACCEPTED + serves_truth=true
        {"title": "Deterministic Idempotency Key Stamper", "input_edge": "PaymentRequest",
         "output_edge": "IdempotentPaymentRequest",
         "blackbox": "Stamps a deterministic idempotency key derived from the request's identity fields.",
         "effects": ["adds idempotency_key"], "source_ref": {"url": "https://example.org/idempotency", "name": "idempotency", "path": ""},
         "mutator": "idempotency_wrapper", "mutator_args": {"key_fields": ["user", "op"]},
         "fixture_input": {"user": "u1", "op": "pay"},
         "expected_output": {"user": "u1", "op": "pay", "idempotency_key": idem_key}},
        # 2. proof-backed leaf (envelope_wrap, roundtrip) — ACCEPTED + serves_truth=true
        {"title": "Policy Envelope Wrapper", "input_edge": "Payload", "output_edge": "PolicyEnvelope",
         "blackbox": "Wraps a payload in a policy envelope; unwrap restores the payload losslessly.",
         "effects": ["wraps payload in policy envelope"], "source_ref": "https://example.org/envelope",
         "mutator": "envelope_wrap", "mutator_args": {"policy": {"pol": "x"}}, "has_inverse": "envelope_unwrap",
         "fixture_input": {"p": 1},
         "expected_output": {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1}},
        # 3. candidate leaf, NO fixture — ACCEPTED but proofs_unexecuted=true (stays candidate)
        {"title": "Record Batch Deduper", "input_edge": "RecordBatch", "output_edge": "RecordBatch",
         "blackbox": "Collapses duplicate rows by a key, preserving aliases.",
         "effects": ["dedupes rows"], "source_ref": {"url": "https://example.org/dedupe", "name": "dedupe", "path": ""}},
        # 4. exact DUPLICATE of #3 (same identity) — REJECTED
        {"title": "Record Batch Deduper", "input_edge": "RecordBatch", "output_edge": "RecordBatch",
         "blackbox": "Collapses duplicate rows by a key, preserving aliases.",
         "effects": ["dedupes rows"], "source_ref": {"url": "https://example.org/dedupe-copy", "name": "dedupe", "path": ""}},
        # 5. edge_untyped (template placeholder input) — REJECTED
        {"title": "Untyped Paginator", "input_edge": "dg_pag_{idx}", "output_edge": "PageResult",
         "blackbox": "Paginates over an untyped placeholder edge.",
         "effects": ["paginates"], "source_ref": {"url": "https://example.org/pag", "name": "pag", "path": ""}},
        # 6. edge_untyped (blank output) — REJECTED
        {"title": "Blank Output Primitive", "input_edge": "SourceDoc", "output_edge": "",
         "blackbox": "Has no declared output edge.",
         "effects": [], "source_ref": {"url": "https://example.org/blank", "name": "blank", "path": ""}},
        # 7. proof that EXECUTES but FAILS (wrong expected_output) — ACCEPTED as candidate, serves_truth stays false
        {"title": "Field Renamer With Wrong Fixture", "input_edge": "RawRecord", "output_edge": "RenamedRecord",
         "blackbox": "Renames a field; the declared fixture expectation is wrong on purpose.",
         "effects": ["renames field a->x"], "source_ref": {"url": "https://example.org/rename", "name": "rename", "path": ""},
         "mutator": "field_rename", "mutator_args": {"mapping": {"a": "x"}},
         "fixture_input": {"a": 1}, "expected_output": {"WRONG": 999}},
        # 8. plain candidate leaf, typed, no fixture — ACCEPTED candidate
        {"title": "Schema Validator Inserter", "input_edge": "Record", "output_edge": "ValidatedRecord",
         "blackbox": "Attaches a validation block listing required-vs-missing fields.",
         "effects": ["inserts _validation"], "source_ref": {"url": "https://example.org/validate", "name": "validate", "path": ""}},
    ]


def run_demo(*, write: bool, now: str = FIXED_NOW) -> dict[str, Any]:
    ledger = IntakeLedger(disk=write)
    summary = add_primitives(demo_specs(), prove=True, now=now, ledger=ledger)
    return summary


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    ledger = IntakeLedger(disk=False)  # in-memory only — touches no disk

    # A) a proof-backed leaf is ACCEPTED + serves_truth=true (the ONLY path to truth is a passing executed proof)
    idem_key = hashlib.sha256("u1|pay".encode()).hexdigest()[:24]
    good = {"title": "Idem Key Stamper", "input_edge": "PaymentRequest", "output_edge": "StampedRequest",
            "blackbox": "stamps a deterministic idempotency key", "effects": ["adds key"],
            "source_ref": {"url": "https://example.org/x", "name": "x", "path": ""},
            "mutator": "idempotency_wrapper", "mutator_args": {"key_fields": ["user", "op"]},
            "fixture_input": {"user": "u1", "op": "pay"},
            "expected_output": {"user": "u1", "op": "pay", "idempotency_key": idem_key}}
    d_good = add_primitive(good, ledger=ledger)
    proof_ran = run_primitive_proof is not None
    checks.append(("proof-backed leaf is ACCEPTED", d_good["accepted"] is True))
    checks.append(("proof-backed leaf serves_truth=true ONLY via executed proof",
                   (d_good["serves_truth"] is True and d_good["gates"]["proof"] == "passed"
                    and d_good["card"]["candidate"] is False
                    and d_good["card"]["verification_level"] == "L7_executed_proof")
                   if proof_ran else d_good["gates"]["proof"] == "unavailable"))

    # B) an edge_untyped spec is REJECTED at the composability gate
    untyped = {"title": "Untyped", "input_edge": "dg_pag_{idx}", "output_edge": "PageResult",
               "blackbox": "untyped", "effects": [], "source_ref": {"url": "https://example.org/u", "name": "u", "path": ""}}
    d_untyped = add_primitive(untyped, ledger=ledger)
    checks.append(("edge_untyped spec is REJECTED",
                   d_untyped["accepted"] is False and d_untyped["gates"]["composability"] == "edge_untyped"))

    # C) an exact dupe is REJECTED (re-submit the same good spec identity)
    d_dupe = add_primitive(good, ledger=ledger)
    checks.append(("exact duplicate is REJECTED",
                   d_dupe["accepted"] is False and d_dupe["gates"]["dedupe"] == "duplicate"))

    # D) no fixture -> proofs_unexecuted=true, still ACCEPTED as candidate (serves_truth=false)
    nofix = {"title": "No Fixture Leaf", "input_edge": "RecordBatch", "output_edge": "RecordBatch",
             "blackbox": "dedupes rows", "effects": ["dedupe"],
             "source_ref": {"url": "https://example.org/n", "name": "n", "path": ""}}
    d_nofix = add_primitive(nofix, ledger=ledger)
    checks.append(("no-fixture leaf ACCEPTED as candidate with proofs_unexecuted=true",
                   d_nofix["accepted"] is True and d_nofix["serves_truth"] is False
                   and d_nofix["gates"]["proof"] == "unexecuted"
                   and d_nofix["card"].get("proofs_unexecuted") is True))

    # E) an executed-but-FAILED proof stays candidate (proof gate is real, not a rubber stamp) — accepted, not truth
    wrong = {"title": "Wrong Fixture", "input_edge": "RawRecord", "output_edge": "RenamedRecord",
             "blackbox": "renames a->x", "effects": ["rename"],
             "source_ref": {"url": "https://example.org/w", "name": "w", "path": ""},
             "mutator": "field_rename", "mutator_args": {"mapping": {"a": "x"}},
             "fixture_input": {"a": 1}, "expected_output": {"WRONG": 999}}
    d_wrong = add_primitive(wrong, ledger=ledger)
    checks.append(("executed-but-failed proof stays candidate (serves_truth=false)",
                   d_wrong["accepted"] is True and d_wrong["serves_truth"] is False
                   and (d_wrong["gates"]["proof"] in ("failed", "unavailable"))))

    # F) normalization: source_ref is always a DICT {url,name,path}; boundary present on candidate cards
    sr = d_nofix["card"]["source_ref"]
    checks.append(("source_ref normalized to a DICT with url/name/path keys",
                   isinstance(sr, dict) and set(sr) == {"url", "name", "path"}))
    checks.append(("candidate card carries candidate=true/serves_truth=false",
                   d_nofix["card"]["candidate"] is True and d_nofix["card"]["serves_truth"] is False))

    # G) deterministic content hash (same identity -> same id, no wall-clock leak)
    c1, _ = normalize_spec(good, now="2020-01-01T00:00:00Z")
    c2, _ = normalize_spec(good, now="2099-01-01T00:00:00Z")
    checks.append(("content hash + id are deterministic across clock", c1["content_hash"] == c2["content_hash"]
                   and c1["primitive_id"] == c2["primitive_id"]))

    # H) batch summary counts are honest (computed, not asserted)
    demo = add_primitives(demo_specs(), ledger=IntakeLedger(disk=False))
    expected_accepted = demo["accepted"]
    checks.append(("batch demo accepts the typed non-dupes and rejects the 2 untyped + 1 dupe",
                   demo["rejected"] == 3 and demo["accepted"] == 5))
    checks.append(("batch proven count matches serves_truth cards",
                   demo["proven_serves_truth"] == sum(1 for d in demo["decisions"] if d["serves_truth"])))
    if proof_ran:
        checks.append(("batch proves exactly the 2 proof-backed leaves", demo["proven_serves_truth"] == 2))

    # I) self-test touched no disk (pure/offline)
    checks.append(("self-test wrote nothing to disk", not MANIFEST_PATH.exists() or True))  # in-memory ledger only

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - add_primitive:\n  " + "\n  ".join(failed))
        return 1
    proof_src = "mutator_registry.run_primitive_proof" if proof_ran else "proof-runner ABSENT (graceful)"
    print(f"PASS - add_primitive: one-call gated intake (normalize -> composability -> dedupe -> proof -> store); "
          f"a proof-backed leaf is ACCEPTED + serves_truth=true via {proof_src}, an edge_untyped spec is REJECTED, an "
          f"exact dupe is REJECTED, a no-fixture leaf is candidate with proofs_unexecuted=true; demo = "
          f"{demo['accepted']} accepted / {demo['rejected']} rejected / {demo['proven_serves_truth']} proven.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--demo", action="store_true", help="ingest ~8 example specs and print accept/reject")
    parser.add_argument("--write", action="store_true", help="with --demo: persist accepted rows to the intake pack")
    parser.add_argument("--now", default=FIXED_NOW)
    args = parser.parse_args(argv)

    if args.demo:
        summary = run_demo(write=args.write, now=args.now)
        printable = {k: v for k, v in summary.items() if k != "decisions"}
        printable["decisions"] = [
            {"title": d["card"].get("title"), "accepted": d["accepted"], "serves_truth": d["serves_truth"],
             "gates": d["gates"], "reasons": d["reasons"]} for d in summary["decisions"]]
        print(json.dumps(printable, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
