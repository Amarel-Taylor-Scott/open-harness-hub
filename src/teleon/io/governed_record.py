"""src.teleon.io.governed_record — the ONE thin base every RUNTIME record extends.

The repo already standardizes a lot: the catalog COMPONENT envelope (schemas/_common.schema.json
`$defs/envelope`) aligns to EU AI Act / NIST AI RMF / ISO 42001 / DPV; events project to
CloudEvents 1.0 (io/event_io.py); the compiler emits OTel attrs; everything validates against JSON
Schema 2020-12. What was missing is a single base for the ~70 RUNTIME records that already share a
convention by hand — ModelInvocationReceipt, CompiledRuntimeUnit, TeleonRunReceipt, HealOutcome,
the lift result, worker claims — each carrying `schema_version` + `is_truth:false` + provenance,
but minted ad hoc. This is that base: one helper to MINT and VALIDATE the governed-record envelope,
OTel-correlatable, so new records adopt it by default and old ones migrate incrementally.

THE ENVELOPE (a thin global shape that records EXTEND with their own payload keys):
  schema_version : str  — "<Name>.v<N>" (the record's own contract id; the discriminator)
  is_truth       : bool — pinned False on model/agent/candidate output (the standing law); a
                          deterministic, verified, human-approved record MAY set True explicitly
  provenance     : {produced_by, produced_at, source_hash?, inputs?}  — who/when/from-what (lineage)
  trace          : {trace_id?, span_id?}  — OTel correlation (the compiler's convention, repo-wide)
  created_at     : str  — ISO/epoch handle (passed in — deterministic, no clock here)

Pure + deterministic (timestamps/ids injected — never a clock/random). stdlib only. src/teleon only
(no src.baltor import). Records keep being plain dicts (the repo's portability strength — no
Pydantic) — this just gives the shared keys ONE producer + ONE validator.
"""
from __future__ import annotations

from typing import Any

ENVELOPE_VERSION = "GovernedRecord.v1"
TRUTH_LAW_DEFAULT = False                 # model/agent/candidate output is NEVER truth (the standing law)
_RESERVED = ("schema_version", "is_truth", "provenance", "trace", "created_at", "envelope")


def mint_record(schema_version: str, payload: dict | None = None, *, produced_by: str,
                created_at: str, is_truth: bool = TRUTH_LAW_DEFAULT,
                source_hash: str | None = None, inputs: list | None = None,
                trace_id: str | None = None, span_id: str | None = None,
                extra_provenance: dict | None = None) -> dict:
    """Mint a governed runtime record: the shared envelope + the record's payload. Deterministic
    (created_at/ids injected). `payload` keys must not collide with the reserved envelope keys."""
    if not schema_version or "." not in schema_version:
        raise ValueError(f"schema_version must look like '<Name>.v<N>', got {schema_version!r}")
    payload = dict(payload or {})
    clash = [k for k in payload if k in _RESERVED]
    if clash:
        raise ValueError(f"payload keys collide with the envelope: {clash}")
    provenance = {"produced_by": produced_by, "produced_at": created_at}
    if source_hash is not None:
        provenance["source_hash"] = source_hash
    if inputs is not None:
        provenance["inputs"] = list(inputs)
    if extra_provenance:
        provenance.update(extra_provenance)
    record = {"envelope": ENVELOPE_VERSION, "schema_version": schema_version,
              "is_truth": bool(is_truth), "provenance": provenance, "created_at": created_at}
    trace = {k: v for k, v in (("trace_id", trace_id), ("span_id", span_id)) if v is not None}
    if trace:
        record["trace"] = trace
    record.update(payload)
    return record


def validate_record(record: Any, *, require_truth_false: bool = False) -> list[str]:
    """Return a list of envelope problems ([] = valid). `require_truth_false` enforces the standing
    law for record classes that must never claim truth (model/agent/candidate output)."""
    problems: list[str] = []
    if not isinstance(record, dict):
        return [f"record must be a dict, got {type(record).__name__}"]
    sv = record.get("schema_version")
    if not isinstance(sv, str) or "." not in sv:
        problems.append("schema_version missing or not '<Name>.v<N>'")
    if not isinstance(record.get("is_truth"), bool):
        problems.append("is_truth missing or not a bool")
    elif require_truth_false and record["is_truth"] is not False:
        problems.append("is_truth must be False for this record class (the standing law)")
    prov = record.get("provenance")
    if not isinstance(prov, dict) or not prov.get("produced_by") or not prov.get("produced_at"):
        problems.append("provenance missing produced_by/produced_at (lineage required)")
    if not record.get("created_at"):
        problems.append("created_at missing (the time handle)")
    trace = record.get("trace")
    if trace is not None and not isinstance(trace, dict):
        problems.append("trace must be an object {trace_id?, span_id?} when present")
    return problems


def is_governed(record: Any) -> bool:
    """True iff the record already carries the governed envelope (for incremental migration checks)."""
    return isinstance(record, dict) and record.get("envelope") == ENVELOPE_VERSION and not validate_record(record)


# ---------------------------------------------------------------- self-test (offline, deterministic)

def _self_test() -> int:
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    rec = mint_record("ModelInvocationReceipt.v1", {"selected_model": "gemma", "latency_ms": 12},
                      produced_by="oips", created_at="epoch:1700000000",
                      source_hash="sha256:abc", trace_id="t1", span_id="s1")
    ck("mints the envelope + payload", rec["schema_version"] == "ModelInvocationReceipt.v1"
       and rec["selected_model"] == "gemma" and rec["envelope"] == ENVELOPE_VERSION)
    ck("is_truth defaults to False (the standing law)", rec["is_truth"] is False)
    ck("provenance carries produced_by/at + source_hash (lineage)",
       rec["provenance"]["produced_by"] == "oips" and rec["provenance"]["source_hash"] == "sha256:abc")
    ck("OTel trace correlation carried (the compiler's repo-wide convention)",
       rec["trace"] == {"trace_id": "t1", "span_id": "s1"})
    ck("a freshly minted record validates clean", validate_record(rec, require_truth_false=True) == [])
    ck("is_governed recognizes it", is_governed(rec))

    ck("deterministic: same inputs → identical record",
       mint_record("X.v1", {"a": 1}, produced_by="p", created_at="t")
       == mint_record("X.v1", {"a": 1}, produced_by="p", created_at="t"))

    # honesty + guards
    ck("a payload key colliding with the envelope is REJECTED (no silent overwrite of governance)",
       _raises(lambda: mint_record("X.v1", {"is_truth": True}, produced_by="p", created_at="t")))
    ck("a bad schema_version is REJECTED", _raises(lambda: mint_record("nodots", produced_by="p", created_at="t")))
    truthy = mint_record("VerifiedFact.v1", {"fact": "x"}, produced_by="rail", created_at="t", is_truth=True)
    ck("an explicit verified record MAY set is_truth=True (a deterministic/verified class)",
       truthy["is_truth"] is True and validate_record(truthy) == [])
    ck("require_truth_false flags a truthy record for a never-truth class",
       "is_truth must be False for this record class (the standing law)"
       in validate_record(truthy, require_truth_false=True))
    ck("a record missing provenance fails validation (lineage is required)",
       "provenance missing produced_by/produced_at (lineage required)"
       in validate_record({"schema_version": "X.v1", "is_truth": False, "created_at": "t"}))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"governed_record: {len(checks) - len(failed)}/{len(checks)} — the ONE thin base runtime "
            "records extend (schema_version + is_truth + provenance + OTel trace), minted + validated, "
            "stdlib-only, records stay plain dicts.")
    return 1 if failed else 0


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except (ValueError, TypeError):
        return True


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
