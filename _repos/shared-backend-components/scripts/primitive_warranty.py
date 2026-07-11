#!/usr/bin/env python3
"""scripts.primitive_warranty — the shippable, EXPIRING WARRANTY object that binds a primitive's PROVEN
scope to a hard expiry (2026-07-08). The data already existed — `primitive_benchmark_taxonomy.bench_primitive`
measures the economics, `schemas/environments/EnvironmentRunReceipt.schema.json` records a run, and
`primitive_lifecycle` gates candidate->validated->certified->production — but none of them produced a
single object a caller can hold that says "this primitive is warranted to do X, was NOT tested on Y, may
fail as Z, is allowed these data classes / side effects, at this accuracy/latency, and this warranty
EXPIRES on <date>." This module is that object plus its "no warranty, no production" gate.

Why expiry: a primitive that never re-proves silently drifts (a bounded-external dependency changes, a
schema version rolls, a model behind it moves). The warranty horizon is COMPUTED from determinism + risk —
a D0_pure/safe primitive cannot drift so its warranty lasts a year; a D2_bounded_external or regulated one
expires fast and must re-prove. The warranty ATTESTS what was measured; `check_warranty_valid` re-checks
the attestation is coherent and unexpired; `warranty_gate` says whether a card is production-eligible (a
candidate/validated card never is; a valid warranty is NECESSARY, not SUFFICIENT).

This module mints NOTHING as truth: every warranty is candidate=true, serves_truth=false. VERSION lives in
the `schema_version` metadata field, never in a name or id.

    python3 scripts/primitive_warranty.py --self-test
    python3 scripts/primitive_warranty.py --emit     # a real warranty over the scalar-standardization kernel
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_warranty requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RECORD_TYPE = "primitive_warranty"
#: VERSION of the warranty object itself — metadata, never encoded into an id/name (naming law §2).
WARRANTY_SCHEMA_VERSION = "primitive-warranty-policy-v1"
_DATA_SUBDIR = "data/dev-intel/primitive_warranties"
WARRANTIES_FILENAME = "warranties.jsonl"
_SECONDS_PER_DAY = 86400  # unit constant for the day->epoch horizon math (single source)

#: Base warranty horizon (days) by determinism level. RATIONALE: a purer primitive cannot silently drift —
#: D0_pure has no external dependency, so its measured scope stays true far longer; a stochastic primitive
#: can change its behavior between two runs, so its warranty expires fast and must re-prove. Single source;
#: extend a row, never a parallel literal. Ordering mirrors primitive_lifecycle's determinism ladder.
DETERMINISM_WARRANTY_DAYS: dict[str, int] = {
    "D0_pure": 365,
    "D1_seeded": 180,
    "D2_bounded_external": 90,
    "D3_hybrid": 30,
    "D4_stochastic": 7,
}
DEFAULT_WARRANTY_DAYS = 30  # unknown/undeclared determinism -> conservative horizon

#: Risk multiplier on the horizon. RATIONALE: a regulated/high-risk primitive must re-prove more often, so
#: its warranty expires SOONER; a quarantined one is never warranted (0 days -> expired at issue).
RISK_WARRANTY_MULTIPLIER: dict[str, float] = {
    "safe": 1.0,
    "low": 1.0,
    "review required": 0.5,
    "medium": 0.5,
    "high": 0.25,
    "regulated": 0.25,
    "quarantined": 0.0,
}
DEFAULT_RISK_MULTIPLIER = 0.5  # unknown risk -> halve the horizon (conservative)

#: Data classes that shorten a warranty the same way a regulated risk tier does (PII/PHI/financial/secret).
SENSITIVE_DATA_CLASSES = frozenset({"pii", "phi", "phi_regulated", "regulated", "financial", "pci", "secret"})
SENSITIVE_DATA_MULTIPLIER = 0.25  # touching sensitive data -> re-prove often

#: Accuracy band width below the measured oracle rate that the warranty PROMISES as its floor.
ACCURACY_TOLERANCE = 0.05
#: A production-gating warranty must promise at least this accuracy floor; below it, re-prove (not warrantable).
MIN_WARRANTY_ACCURACY_FLOOR = 0.5

#: Keys that MUST be present-and-non-null for a warranty to be checkable at all (a blank {} fails every one).
WARRANTY_REQUIRED_FIELDS: tuple[str, ...] = (
    "record_type", "warranty_id", "primitive_id", "schema_version",
    "tested_on", "expected_accuracy_range", "attested_accuracy",
    "expires_after_days", "issued_at", "expires_at", "evidence_refs",
)
#: Lifecycle stages that MAY reach production (a candidate/validated/deprecated/quarantined card never can).
PRODUCTION_ELIGIBLE_STAGES = frozenset({"certified", "production"})


# ── time helpers (injected clock only — NO wall-clock in any library/self-test path) ───────────────────────────
def _to_epoch(value: Any) -> float:
    """Normalize an epoch number OR an ISO-8601 string to absolute epoch seconds (UTC). Timezone-stable:
    the result does not depend on the machine's local timezone, so it is deterministic under test."""
    if isinstance(value, bool):  # bool is an int subclass — reject it as a time
        raise TypeError("bool is not a time value")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        d = _dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        return d.timestamp()
    raise TypeError(f"unsupported time value: {type(value).__name__}")


def _to_iso(epoch: float) -> str:
    """Absolute epoch seconds -> canonical ISO-8601 UTC string (the shippable, human-readable time surface)."""
    return _dt.datetime.fromtimestamp(float(epoch), _dt.timezone.utc).isoformat()


# ── horizon computation (COMPUTED from determinism + risk + data sensitivity; never hardcoded per-primitive) ────
def compute_expires_after_days(determinism_level: Optional[str], risk_tier: Optional[str],
                               data_classes: Optional[list[str]] = None) -> int:
    """Warranty horizon in days = base(determinism) x min(risk_multiplier, data_sensitivity_multiplier).
    D0_pure/safe -> a full year; D2_bounded_external or regulated/sensitive -> shorter; quarantined -> 0."""
    base = DETERMINISM_WARRANTY_DAYS.get(determinism_level or "", DEFAULT_WARRANTY_DAYS)
    risk_mult = RISK_WARRANTY_MULTIPLIER.get(risk_tier or "", DEFAULT_RISK_MULTIPLIER)
    data_mult = (SENSITIVE_DATA_MULTIPLIER
                 if any((dc or "").lower() in SENSITIVE_DATA_CLASSES for dc in (data_classes or []))
                 else 1.0)
    return max(0, int(round(base * min(risk_mult, data_mult))))


# ── field derivations (each COMPUTED from card/bench/fixtures; honest about the unknown) ────────────────────────
def _normalize_fixtures(fixtures: Any, bench_result: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Split fixture families/standards into (passed, failed). A fixture may be a family/standard name string
    or a dict carrying its own pass flag; when a fixture declares no flag, the bench's oracle pass rate decides."""
    default_pass = float(bench_result.get("oracle_pass_rate", 0.0)) >= 1.0
    passed: list[str] = []
    failed: list[str] = []
    for fx in fixtures or []:
        if isinstance(fx, dict):
            name = fx.get("family") or fx.get("standard") or fx.get("name") or fx.get("id")
            ok = fx.get("passed", fx.get("pass", default_pass))
        else:
            name, ok = str(fx), default_pass
        if not name:
            continue
        (passed if ok else failed).append(str(name))
    return sorted(set(passed)), sorted(set(failed))


def _card_data_classes(card: dict[str, Any]) -> list[str]:
    pm = card.get("permission_manifest") or {}
    raw = (card.get("data_classes_allowed") or pm.get("data_classes")
           or card.get("data_classes") or [])
    return sorted({str(c) for c in raw})


def _side_effects_allowed(card: dict[str, Any]) -> list[str]:
    """What state changes the primitive is warranted to make. A side-effect-free primitive -> read_only only;
    an unknown one warrants nothing (honest — do not imply a permission that was never proven)."""
    if card.get("side_effects_allowed") is not None:
        return sorted({str(s) for s in card["side_effects_allowed"]})
    pm = card.get("permission_manifest") or {}
    sef = pm.get("side_effect_free", card.get("side_effect_free"))
    if sef is True:
        return ["read_only"]
    if sef is False:
        return sorted({str(s) for s in (pm.get("side_effects_allowed") or ["read"])})
    return []  # unknown -> warrant nothing


def _human_review_required(card: dict[str, Any], bench_result: dict[str, Any],
                           data_classes: list[str]) -> list[str]:
    """The cases in which a human MUST review this primitive's output before it is trusted — computed from
    risk tier, sensitive data classes, security-gate status, side effects, and determinism budget."""
    cases: list[str] = []
    if (card.get("risk_tier") or "").lower() in {"high", "regulated", "quarantined"}:
        cases.append(f"high_risk_tier:{card.get('risk_tier')}")
    for dc in data_classes:
        if dc.lower() in SENSITIVE_DATA_CLASSES:
            cases.append(f"regulated_data_class:{dc}")
    if bench_result.get("security_gate_status") not in (None, "pass"):
        cases.append(f"security_gate:{bench_result.get('security_gate_status')}")
    pm = card.get("permission_manifest") or {}
    if pm.get("side_effect_free") is False:
        cases.append("side_effecting_action")
    if (card.get("determinism_level") or "") in ("D3_hybrid", "D4_stochastic"):
        cases.append(f"nondeterministic_output:{card.get('determinism_level')}")
    return sorted(set(cases))


def _known_failure_modes(card: dict[str, Any], bench_result: dict[str, Any],
                         failed_fixtures: list[str]) -> list[str]:
    modes: list[str] = [str(m) for m in (card.get("failure_modes") or [])]
    modes += [f"fails_on:{f}" for f in failed_fixtures]
    if float(bench_result.get("semantic_entropy", 0.0)) > 0.0:
        modes.append("nondeterministic_replay")
    rate = float(bench_result.get("oracle_pass_rate", 1.0))
    if rate < 1.0:
        modes.append(f"partial_oracle_pass:{round(rate, 4)}")
    return sorted(set(modes))


def _evidence_refs(card: dict[str, Any], bench_result: dict[str, Any],
                   lifecycle: Any) -> list[dict[str, str]]:
    """Handles a caller can follow back to the proof: the benchmark, its artifact hash, the verifier, the
    provenance, the lifecycle stage, the security-gate verdict, and any EnvironmentRunReceipt id."""
    prov = card.get("provenance") if isinstance(card.get("provenance"), dict) else {}
    lc = lifecycle if isinstance(lifecycle, dict) else {}
    lc_prov = lc.get("provenance") if isinstance(lc.get("provenance"), dict) else {}
    refs: list[dict[str, str]] = []

    def add(kind: str, value: Any) -> None:
        if value:
            refs.append({"kind": kind, "value": str(value)})

    add("benchmark_id", bench_result.get("benchmark_id"))
    add("benchmark_artifact_hash", bench_result.get("artifact_hash"))
    add("security_gate_status", bench_result.get("security_gate_status"))
    add("verifier_id", card.get("verifier_id"))
    add("provenance_artifact_hash", prov.get("artifact_hash") or lc_prov.get("artifact_hash"))
    add("lifecycle_stage", _lifecycle_stage(lifecycle, card))
    add("environment_run_receipt_id",
        bench_result.get("environment_run_receipt_id") or lc.get("receipt_id"))
    # deterministic order (sets/dicts never leak iteration order into the row)
    return sorted(refs, key=lambda r: (r["kind"], r["value"]))


def _lifecycle_stage(lifecycle: Any, card: dict[str, Any]) -> str:
    """Resolve the lifecycle stage from a stage string, a promote() decision, a truth-serving result, or a
    raw card — whichever the caller passed as `lifecycle`."""
    if isinstance(lifecycle, str):
        return lifecycle
    if isinstance(lifecycle, dict):
        card_in = lifecycle.get("card") if isinstance(lifecycle.get("card"), dict) else {}
        return (lifecycle.get("lifecycle_stage") or card_in.get("lifecycle_stage")
                or lifecycle.get("to") or card.get("lifecycle_stage") or "candidate")
    return card.get("lifecycle_stage", "candidate")


# ── 1. build_warranty ──────────────────────────────────────────────────────────────────────────────────────────
def build_warranty(card: dict[str, Any], bench_result: dict[str, Any], fixtures: Any, lifecycle: Any, *,
                   issued_at: Any) -> dict[str, Any]:
    """Assemble the shippable warranty. Every field is COMPUTED from (card, bench_result, fixtures, lifecycle);
    `issued_at` is an injected clock (epoch or ISO-8601) — this function never reads the wall clock, so it is
    pure and byte-identical across calls with the same inputs. Candidate-only; serves_truth=false."""
    primitive_id = card.get("primitive_id") or "unknown_primitive"
    passed, failed = _normalize_fixtures(fixtures, bench_result)
    declared_oos = sorted({str(x) for x in (card.get("not_tested_on") or card.get("out_of_scope") or [])})
    not_tested_on = sorted(set(declared_oos) | set(failed))  # declared out-of-scope + anything that failed
    data_classes = _card_data_classes(card)

    measured = round(float(bench_result.get("oracle_pass_rate", 0.0)), 4)
    acc_lo = round(max(0.0, measured - ACCURACY_TOLERANCE), 4)
    acc_hi = round(min(1.0, measured), 4)
    latency_lo = bench_result.get("latency_p50_ms")
    latency_hi = bench_result.get("latency_p99_ms", bench_result.get("latency_p95_ms"))

    stage = _lifecycle_stage(lifecycle, card)
    days = compute_expires_after_days(card.get("determinism_level"), card.get("risk_tier"), data_classes)
    issued_epoch = _to_epoch(issued_at)
    expires_epoch = issued_epoch + days * _SECONDS_PER_DAY
    issued_iso = _to_iso(issued_epoch)
    expires_iso = _to_iso(expires_epoch)

    supported_schema_versions = sorted({str(v) for v in (
        card.get("supported_schema_versions") or ([card["schema_version"]] if card.get("schema_version") else []))})

    warranty = {
        "record_type": RECORD_TYPE,
        "warranty_id": canonical_id("warranty", primitive_id, WARRANTY_SCHEMA_VERSION, issued_iso,
                                    str(bench_result.get("benchmark_id") or bench_result.get("artifact_hash") or "")),
        "primitive_id": primitive_id,
        "schema_version": WARRANTY_SCHEMA_VERSION,           # VERSION lives here (metadata), never in the id
        "lifecycle_stage": stage,
        "determinism_level": card.get("determinism_level"),
        "risk_tier": card.get("risk_tier"),
        "tested_on": passed,                                 # fixture families/standards that PASSED
        "not_tested_on": not_tested_on,                      # declared out-of-scope + failed families
        "known_failure_modes": _known_failure_modes(card, bench_result, failed),
        "data_classes_allowed": data_classes,
        "side_effects_allowed": _side_effects_allowed(card),
        "expected_accuracy_range": [acc_lo, acc_hi],
        "attested_accuracy": measured,                       # the measured oracle rate the range attests
        "expected_latency_range": [latency_lo, latency_hi],
        "latency_unit": "ms",
        "supported_schema_versions": supported_schema_versions,
        "human_review_required": _human_review_required(card, bench_result, data_classes),
        "expires_after_days": days,
        "issued_at": issued_iso,
        "expires_at": expires_iso,
        "evidence_refs": _evidence_refs(card, bench_result, lifecycle),
        **BOUNDARY,
    }
    return warranty


# ── 2. check_warranty_valid — the "no warranty, no production" validity gate ────────────────────────────────────
def check_warranty_valid(warranty: dict[str, Any], now: Any) -> dict[str, Any]:
    """Is this warranty valid AT `now`? INVALID if expired (now >= expires_at), missing a required field, the
    accuracy range is malformed / unmet / below the production floor, or its scope is empty. Returns
    {valid: bool, reasons: [...]}. A blank/{} warranty fails every required-field check."""
    reasons: list[str] = []
    if not isinstance(warranty, dict) or not warranty:
        return {"valid": False, "reasons": ["empty_or_non_dict_warranty"]}

    for k in WARRANTY_REQUIRED_FIELDS:
        if warranty.get(k) is None:
            reasons.append(f"missing_field:{k}")

    # expiry — only checkable once both time fields are present
    if warranty.get("issued_at") is not None and warranty.get("expires_at") is not None:
        try:
            now_e = _to_epoch(now)
            iss_e = _to_epoch(warranty["issued_at"])
            exp_e = _to_epoch(warranty["expires_at"])
            if now_e >= exp_e:
                reasons.append("expired")
            elif now_e < iss_e:
                reasons.append("not_yet_valid")
        except (TypeError, ValueError) as exc:
            reasons.append(f"unparseable_time:{exc}")

    # scope must not be empty (a warranty for nothing warrants nothing)
    if warranty.get("tested_on") is not None and not warranty.get("tested_on"):
        reasons.append("empty_tested_on_scope")

    # accuracy range: well-formed, the attested value inside it, and its floor high enough to gate production
    rng = warranty.get("expected_accuracy_range")
    if not (isinstance(rng, (list, tuple)) and len(rng) == 2 and all(isinstance(x, (int, float)) for x in rng)):
        reasons.append("accuracy_range_malformed")
    else:
        lo, hi = float(rng[0]), float(rng[1])
        if not (0.0 <= lo <= hi <= 1.0):
            reasons.append("accuracy_range_malformed")
        else:
            att = warranty.get("attested_accuracy")
            if isinstance(att, (int, float)) and not (lo <= float(att) <= hi):
                reasons.append("accuracy_range_unmet")
            if lo < MIN_WARRANTY_ACCURACY_FLOOR:
                reasons.append(f"accuracy_below_floor:{lo}")

    return {"valid": not reasons, "reasons": sorted(set(reasons))}


# ── 3. warranty_gate — production eligibility (valid warranty is NECESSARY, not SUFFICIENT) ─────────────────────
def warranty_gate(card: dict[str, Any], warranty: Any, now: Any) -> bool:
    """Production-eligibility boolean. A candidate/validated (or deprecated/quarantined) card is NEVER
    production-eligible regardless of its warranty; a certified/production card is eligible ONLY with a
    warranty that is present, matches this primitive, and is valid at `now`."""
    stage = card.get("lifecycle_stage", "candidate")
    if stage not in PRODUCTION_ELIGIBLE_STAGES:
        return False
    if not isinstance(warranty, dict) or not warranty:
        return False
    if warranty.get("primitive_id") != card.get("primitive_id"):
        return False
    return bool(check_warranty_valid(warranty, now)["valid"])


# ── 4. persist (append, candidate-only) ─────────────────────────────────────────────────────────────────────────
def persist_warranty(warranty: dict[str, Any], out_path: Optional[Path] = None) -> Path:
    """Append the warranty to the candidate-only warranties.jsonl staging file. Never overwrites; never
    promotes (the row stays candidate=true, serves_truth=false)."""
    out_path = out_path or (resource(_DATA_SUBDIR) / WARRANTIES_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    row = {**warranty, **BOUNDARY}  # re-stamp the boundary so a hand-edited input can never persist as truth
    with out_path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return out_path


# ── a real warranty over the scalar-standardization kernel (no placeholder; reuses the shipped bench) ──────────
def scalar_kernel_warranty(*, issued_at: Any) -> dict[str, Any]:
    """Build a REAL warranty for the scalar-standardization primitive from its REAL benchmark receipt and a
    SLSA provenance record — the end-to-end proof that this layer works on shipped data, not a fixture."""
    from scripts.primitive_benchmark_taxonomy import scalar_kernel_receipt  # noqa: PLC0415
    from scripts.primitive_lifecycle import build_provenance  # noqa: PLC0415
    bench = scalar_kernel_receipt()
    card = {
        "primitive_id": bench["primitive_id"],
        "pack_module": "scripts.scalar_standardization_primitives",
        "impl_name": "standardize_scalar",
        "determinism_level": "D0_pure",
        "risk_tier": "safe",
        "lifecycle_stage": "certified",
        "verifier_id": "scalar_standardization_primitives::_self_test",
        "schema_version": "scalar-standardization-v1",
        "permission_manifest": {"side_effect_free": True, "network_access": False, "permission_class": "pure"},
        "failure_modes": ["ambiguous_range_input", "locale_specific_decimal_separator"],
        "data_classes_allowed": ["public_metadata"],
        "not_tested_on": ["free_text_paragraphs", "binary_blobs"],
        "provenance": {"contract_version": "v1"},
    }
    prov = build_provenance(card, source_files=["scripts/scalar_standardization_primitives.py"])
    fixtures = [
        {"family": "unit_conversion", "passed": True},
        {"family": "currency_parse", "passed": True},
        {"family": "percent_and_basis_points", "passed": True},
        {"family": "boolean_coercion", "passed": True},
        {"family": "unicode_name_passthrough", "passed": True},
    ]
    return build_warranty(card, bench, fixtures, {"lifecycle_stage": "certified", "provenance": prov},
                          issued_at=issued_at)


# ── self-test (OFFLINE · DETERMINISTIC · MUTATION-GATED) ────────────────────────────────────────────────────────
#: a fixed injected clock (~2025-06-15T14:26:40Z) — NO wall-clock, NO Date.now (naming/verify laws)
_FIXED_ISSUED_AT = 1_750_000_000.0


def _fake_card(stage: str = "certified", *, determinism: str = "D0_pure", risk: str = "safe",
               data_classes: Optional[list[str]] = None) -> dict[str, Any]:
    return {
        "primitive_id": "prim:test:normalize_phone",
        "determinism_level": determinism,
        "risk_tier": risk,
        "lifecycle_stage": stage,
        "verifier_id": "phone_pack::_self_test",
        "schema_version": "phone-normalize-v3",
        "permission_manifest": {"side_effect_free": True, "network_access": False},
        "failure_modes": ["extension_dropped"],
        "data_classes_allowed": data_classes if data_classes is not None else ["public_metadata"],
        "not_tested_on": ["e164_extensions"],
        "provenance": {"artifact_hash": "artifact-fake-phone"},
    }


def _fake_bench(oracle: float = 1.0, entropy: float = 0.0) -> dict[str, Any]:
    return {
        "benchmark_id": "det_bench::phone_pack", "artifact_hash": "bench-fake-phone",
        "oracle_pass_rate": oracle, "semantic_entropy": entropy,
        "latency_p50_ms": 0.12, "latency_p95_ms": 0.31, "latency_p99_ms": 0.44,
        "security_gate_status": "pass",
    }


def _fake_fixtures() -> list[dict[str, Any]]:
    return [
        {"family": "us_nanp", "passed": True},
        {"family": "e164_international", "passed": True},
        {"family": "vanity_letters", "passed": False},  # a failed family -> not_tested_on + known_failure_modes
    ]


def _mutation_gate() -> bool:
    """Verify-the-verifier: prove the expiry assertion actually bites. A defective checker that IGNORES
    expiry would wrongly pass an expired warranty; the REAL checker rejects it. If the real checker ever
    stops checking expiry this returns False and the self-test exits 1."""
    w = build_warranty(_fake_card(), _fake_bench(), _fake_fixtures(),
                       {"lifecycle_stage": "certified"}, issued_at=_FIXED_ISSUED_AT)
    after_expiry = _to_epoch(w["expires_at"]) + 1.0

    def _buggy_ignores_expiry(warranty: dict[str, Any], now: Any) -> dict[str, Any]:
        return {"valid": True, "reasons": []}  # the injected defect

    real = check_warranty_valid(w, after_expiry)["valid"]        # correct: False (expired)
    buggy = _buggy_ignores_expiry(w, after_expiry)["valid"]      # defect:  True
    return real is False and buggy is True


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    card = _fake_card()
    bench = _fake_bench()
    fixtures = _fake_fixtures()
    lifecycle = {"lifecycle_stage": "certified"}
    w = build_warranty(card, bench, fixtures, lifecycle, issued_at=_FIXED_ISSUED_AT)

    checks.append(("build: candidate-only row, warranty record_type + id, correct primitive_id",
                   w["record_type"] == RECORD_TYPE and w["primitive_id"] == "prim:test:normalize_phone"
                   and w["warranty_id"].startswith("warranty-")
                   and w["candidate"] is True and w["serves_truth"] is False))
    checks.append(("VERSION lives in schema_version metadata — NOT in the id/name (no .vN / @N)",
                   w["schema_version"] == WARRANTY_SCHEMA_VERSION
                   and ".v" not in w["warranty_id"] and "@" not in w["warranty_id"]))
    checks.append(("tested_on = PASSED families; not_tested_on = declared out-of-scope + FAILED families",
                   w["tested_on"] == ["e164_international", "us_nanp"]
                   and "vanity_letters" in w["not_tested_on"] and "e164_extensions" in w["not_tested_on"]))
    checks.append(("known_failure_modes carries card modes + a fails_on:<failed family>",
                   "extension_dropped" in w["known_failure_modes"]
                   and "fails_on:vanity_letters" in w["known_failure_modes"]))
    checks.append(("expected_accuracy_range=[measured-tol, measured]; attested_accuracy stored",
                   w["expected_accuracy_range"] == [0.95, 1.0] and w["attested_accuracy"] == 1.0))
    checks.append(("expected_latency_range from bench p50..p99 (ms); supported_schema_versions from card",
                   w["expected_latency_range"] == [0.12, 0.44] and w["latency_unit"] == "ms"
                   and w["supported_schema_versions"] == ["phone-normalize-v3"]))
    checks.append(("data_classes_allowed + side_effects_allowed computed (side-effect-free -> read_only)",
                   w["data_classes_allowed"] == ["public_metadata"] and w["side_effects_allowed"] == ["read_only"]))
    checks.append(("evidence_refs link bench + verifier + provenance + lifecycle, deterministically ordered",
                   {r["kind"] for r in w["evidence_refs"]} >= {"benchmark_id", "verifier_id",
                   "provenance_artifact_hash", "lifecycle_stage"}
                   and w["evidence_refs"] == sorted(w["evidence_refs"], key=lambda r: (r["kind"], r["value"]))))

    # horizon: D0_pure + safe -> a full year; expires_at = issued + days
    checks.append(("expires_after_days computed from determinism+risk (D0_pure/safe -> 365)",
                   w["expires_after_days"] == 365
                   and abs(_to_epoch(w["expires_at"]) - (_FIXED_ISSUED_AT + 365 * _SECONDS_PER_DAY)) < 1e-6))
    d2_days = compute_expires_after_days("D2_bounded_external", "regulated", ["public_metadata"])
    sens_days = compute_expires_after_days("D0_pure", "safe", ["phi"])
    checks.append(("D2/regulated horizon SHORTER than D0/safe; sensitive data class also shortens it",
                   d2_days < 365 and 0 < sens_days < 365))

    exp_e = _to_epoch(w["expires_at"])
    checks.append(("VALID at issued_at", check_warranty_valid(w, _FIXED_ISSUED_AT)["valid"] is True))
    checks.append(("VALID just before expiry (expires_at - 1s)",
                   check_warranty_valid(w, exp_e - 1.0)["valid"] is True))
    inv = check_warranty_valid(w, exp_e + 1.0)
    checks.append(("INVALID just after expiry — reason 'expired' (the mutation-sensitive assertion)",
                   inv["valid"] is False and "expired" in inv["reasons"]))
    checks.append(("INVALID exactly AT expires_at (now >= expires_at)",
                   check_warranty_valid(w, exp_e)["valid"] is False))

    # missing / blank warranty rejected by BOTH the checker and the gate
    blank = check_warranty_valid({}, _FIXED_ISSUED_AT)
    checks.append(("blank {} warranty rejected by checker (missing required fields)",
                   blank["valid"] is False and any(r.startswith("missing_field") or
                   r == "empty_or_non_dict_warranty" for r in blank["reasons"])))
    checks.append(("blank / missing warranty rejected by the gate",
                   warranty_gate(card, {}, _FIXED_ISSUED_AT) is False
                   and warranty_gate(card, None, _FIXED_ISSUED_AT) is False))

    # accuracy: tampered range unmet; low-accuracy bench below the production floor
    tampered = {**w, "expected_accuracy_range": [0.6, 0.7]}  # attested 1.0 falls OUTSIDE [0.6,0.7]
    checks.append(("tampered accuracy range -> 'accuracy_range_unmet'",
                   "accuracy_range_unmet" in check_warranty_valid(tampered, _FIXED_ISSUED_AT)["reasons"]))
    low = build_warranty(card, _fake_bench(oracle=0.3), fixtures, lifecycle, issued_at=_FIXED_ISSUED_AT)
    checks.append(("low-accuracy warranty (floor unmet) is INVALID",
                   check_warranty_valid(low, _FIXED_ISSUED_AT)["valid"] is False
                   and any(r.startswith("accuracy_below_floor") for r in
                           check_warranty_valid(low, _FIXED_ISSUED_AT)["reasons"])))

    # the gate: lifecycle boundary + valid warranty (necessary, not sufficient)
    checks.append(("gate: certified card + VALID warranty -> production-eligible (True)",
                   warranty_gate(card, w, _FIXED_ISSUED_AT) is True))
    checks.append(("gate: candidate/validated card NEVER production-eligible, even with a valid warranty",
                   warranty_gate(_fake_card("candidate"), w, _FIXED_ISSUED_AT) is False
                   and warranty_gate(_fake_card("validated"), w, _FIXED_ISSUED_AT) is False))
    checks.append(("gate: certified card + EXPIRED warranty -> not eligible (no warranty, no production)",
                   warranty_gate(card, w, exp_e + 1.0) is False))
    checks.append(("gate: warranty for a DIFFERENT primitive is rejected",
                   warranty_gate({**card, "primitive_id": "prim:test:other"}, w, _FIXED_ISSUED_AT) is False))

    # quarantined risk -> 0-day horizon -> expired at issue -> never warranted
    q = build_warranty(_fake_card(risk="quarantined"), bench, fixtures, lifecycle, issued_at=_FIXED_ISSUED_AT)
    checks.append(("quarantined risk -> expires_after_days 0 -> INVALID at issue (never warranted)",
                   q["expires_after_days"] == 0 and check_warranty_valid(q, _FIXED_ISSUED_AT)["valid"] is False))

    # determinism gate: building twice is byte-identical
    w2 = build_warranty(card, bench, fixtures, lifecycle, issued_at=_FIXED_ISSUED_AT)
    checks.append(("DETERMINISTIC: build twice -> byte-identical",
                   json.dumps(w, sort_keys=True) == json.dumps(w2, sort_keys=True)))

    # mutation gate: the expiry assertion actually bites
    checks.append(("MUTATION-GATED: a checker that ignores expiry is caught by the expiry assertion",
                   _mutation_gate() is True))

    # a REAL warranty over the shipped scalar kernel (no placeholder) — and it gates + persists candidate-only
    real_w = scalar_kernel_warranty(issued_at=_FIXED_ISSUED_AT)
    checks.append(("REAL scalar-kernel warranty: valid, production-eligible, candidate-only",
                   check_warranty_valid(real_w, _FIXED_ISSUED_AT)["valid"] is True
                   and real_w["serves_truth"] is False
                   and warranty_gate({"primitive_id": real_w["primitive_id"], "lifecycle_stage": "certified"},
                                     real_w, _FIXED_ISSUED_AT) is True))

    # persistence: append + round-trip, candidate-only, into a temp file (no pollution of the real staging file)
    import tempfile  # noqa: PLC0415
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / WARRANTIES_FILENAME
        persist_warranty(w, out_path=p)
        persist_warranty(real_w, out_path=p)
        rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    checks.append(("persist: appends candidate-only rows that round-trip from warranties.jsonl",
                   len(rows) == 2 and all(r["candidate"] is True and r["serves_truth"] is False for r in rows)
                   and rows[0]["warranty_id"] == w["warranty_id"]))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + " - primitive_warranty: shippable EXPIRING warranty "
          f"(schema_version={WARRANTY_SCHEMA_VERSION}) — tested_on/not_tested_on/known_failure_modes, "
          "data-class + side-effect scope, accuracy/latency ranges, human-review cases, horizon computed from "
          "determinism+risk, 'no warranty, no production' gate; deterministic + mutation-gated; serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Shippable, expiring primitive warranty layer (candidate-only).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true",
                    help="build + persist a REAL warranty over the scalar-standardization kernel")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.emit:
        # wall clock ONLY here at the CLI edge (never in a library/self-test path) — a real warranty is issued now
        issued = _dt.datetime.now(_dt.timezone.utc).isoformat()
        w = scalar_kernel_warranty(issued_at=issued)
        path = persist_warranty(w)
        valid = check_warranty_valid(w, issued)
        print(json.dumps(w, indent=2, sort_keys=True))
        print(f"\nvalid={valid['valid']} reasons={valid['reasons']}  ->  appended to {path}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
