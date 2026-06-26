#!/usr/bin/env python3
"""src.baltor.distillation.retention_report — the InformationRetentionReport builder.

The lossless law (``docs/codex/lossless-distillation.md``) says a distilled artifact may be smaller /
cleaner / compressed / optimized, but the SYSTEM must retain raw + source + intermediates + **all source
handles** + held-out + rejected + lineage + receipts + a rollback target. This module turns "is this one
transform lossless?" into a checkable verdict: given the input artifacts and the output artifacts of a
single transform (plus the held-out / rejected / superseded lists and a few lineage signals), it produces
an :class:`InformationRetentionReport` whose ``safe_to_promote`` is True ONLY when nothing truth-bearing
was lost.

It is the dual of the optimizer's regression gate: the harness asks "did THIS candidate regress?"; the
retention report asks "did the system, taken as a whole, keep everything?" — counts in/out, computes
``source_handle_coverage`` over the served set, counts omitted / held-out / rejected, flags orphaned
inputs (dropped without being held-out/rejected/superseded — a silent loss) and orphaned outputs
(fabricated — appeared without a surviving input lineage), counts ``dropped_source_handle_count``
(handles present on an input fact but missing on its surviving output — the canonical compression sin),
and records whether raw rehydration passed and lineage is complete.

A LOSSY transform on truth-bearing facts is never safe to promote. A transform MAY be declared lossy ONLY
if it is explicitly allowed (a non-truth surface — e.g. whitespace/text-surface compression that does not
touch facts/handles/warnings); declaring it does not waive the source-handle / held-out / lineage rules.

This builder is PURE (dict-in → report-out): no store, no clock, no RNG, no I/O. The same inputs always
yield the same report (``report_id`` is content-addressed). It is deliberately decoupled from the Lane-B
store so it can be exercised standalone; the apply-proofs feed it the REAL outputs of the existing CFPB /
optimization / ingestion flows to show those flows already satisfy the law.

Identity of an artifact = its ``artifact_id`` (falls back to ``fact_id``). A source handle = any of
``source_handles`` (list) or a single ``source_handle``. A fact is "truth-bearing" when its
``claim_status``/``claim_type`` marks it a fact (not an allegation/derived-signal/source excerpt) — those
are the ones whose handles MUST survive.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterable, Mapping

#: claim statuses / types that carry CERTIFIED truth — their source handles must never be dropped.
TRUTH_CLAIM_STATUSES = frozenset({"fact"})
#: claim statuses / types that are explicitly NOT certified truth (held-out by nature, handle loss tolerated
#: only because they should not be SERVED in the first place — but losing their lineage is still a sin).
NON_TRUTH_CLAIM_STATUSES = frozenset(
    {"unverified_allegation", "narrative_allegation", "derived_signal", "source", "source_excerpt", "context_object"}
)


def _aid(a: Mapping) -> str:
    """Stable identity of an artifact: ``artifact_id`` then ``fact_id``."""
    return str(a.get("artifact_id") or a.get("fact_id") or "")


def _handles(a: Mapping) -> list:
    """All source handles on an artifact (list form or single ``source_handle``)."""
    hs = a.get("source_handles")
    if hs:
        return [h for h in hs if h]
    sh = a.get("source_handle")
    return [sh] if sh else []


def _is_truth(a: Mapping) -> bool:
    """A truth-bearing fact: claim_status/claim_type marks it a fact AND it is not an allegation type."""
    status = str(a.get("claim_status") or "")
    ctype = str(a.get("claim_type") or "")
    atype = str(a.get("artifact_type") or "")
    if status in NON_TRUTH_CLAIM_STATUSES or ctype in NON_TRUTH_CLAIM_STATUSES or atype in NON_TRUTH_CLAIM_STATUSES:
        return False
    return status in TRUTH_CLAIM_STATUSES or ctype in TRUTH_CLAIM_STATUSES or atype in ("atomic_fact", "conclusion")


@dataclass
class InformationRetentionReport:
    """The verdict that one transform kept everything the law requires.

    ``safe_to_promote`` is the single gate downstream reads; it is True ONLY when raw rehydration passed,
    lineage is complete, no source handle was dropped from a surviving fact, there are no orphaned (silently
    dropped) inputs or fabricated outputs, and any lossy transform was BOTH declared and allowed.
    """

    report_id: str
    transform_type: str
    input_count: int
    output_count: int
    served_count: int
    source_handle_coverage: float        # fraction of SERVED truth-bearing outputs carrying >=1 source handle
    omitted_count: int                   # inputs not in the output AND not held_out/rejected/superseded (explained)
    held_out_count: int
    rejected_count: int
    superseded_count: int
    orphaned_input_ids: list             # inputs that vanished with NO explanation (silent loss) — must be []
    orphaned_output_ids: list            # outputs with no surviving input lineage (fabricated) — must be []
    dropped_source_handle_count: int     # handles present on an input fact, missing on its surviving output — must be 0
    raw_rehydration_passed: bool
    lineage_complete: bool
    lossy_transform_declared: bool
    lossy_transform_allowed: bool
    safe_to_promote: bool
    notes: list = field(default_factory=list)
    schema_version: str = "InformationRetentionReport"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "transform_type": self.transform_type,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "served_count": self.served_count,
            "source_handle_coverage": round(self.source_handle_coverage, 4),
            "omitted_count": self.omitted_count,
            "held_out_count": self.held_out_count,
            "rejected_count": self.rejected_count,
            "superseded_count": self.superseded_count,
            "orphaned_input_ids": list(self.orphaned_input_ids),
            "orphaned_output_ids": list(self.orphaned_output_ids),
            "dropped_source_handle_count": self.dropped_source_handle_count,
            "raw_rehydration_passed": self.raw_rehydration_passed,
            "lineage_complete": self.lineage_complete,
            "lossy_transform_declared": self.lossy_transform_declared,
            "lossy_transform_allowed": self.lossy_transform_allowed,
            "safe_to_promote": self.safe_to_promote,
            "notes": list(self.notes),
        }


class InformationRetentionReportBuilder:
    """Build an :class:`InformationRetentionReport` for ONE transform from its in/out artifacts + signals.

    Pure: no store, no clock, no RNG. ``report_id`` is content-addressed so the verdict is reproducible.
    """

    def build(
        self,
        *,
        transform_type: str,
        inputs: Iterable[Mapping],
        outputs: Iterable[Mapping],
        served: Iterable[Mapping] | None = None,
        held_out: Iterable[Mapping] | None = None,
        rejected: Iterable[Mapping] | None = None,
        superseded: Iterable[Mapping] | None = None,
        raw_rehydration_passed: bool = True,
        lineage_complete: bool = True,
        lossy_transform_declared: bool = False,
        lossy_transform_allowed: bool = False,
    ) -> InformationRetentionReport:
        inputs = list(inputs)
        outputs = list(outputs)
        served = list(served) if served is not None else list(outputs)
        held_out = list(held_out or [])
        rejected = list(rejected or [])
        superseded = list(superseded or [])
        notes: list[str] = []

        in_by_id = {_aid(a): a for a in inputs if _aid(a)}
        out_by_id = {_aid(a): a for a in outputs if _aid(a)}
        held_ids = {_aid(a) for a in held_out if _aid(a)}
        rejected_ids = {_aid(a) for a in rejected if _aid(a)}
        superseded_ids = {_aid(a) for a in superseded if _aid(a)}
        explained_ids = held_ids | rejected_ids | superseded_ids

        # ── orphaned INPUTS: vanished from output AND not held-out/rejected/superseded → silent loss ──
        orphaned_input_ids = sorted(
            iid for iid in in_by_id if iid not in out_by_id and iid not in explained_ids
        )
        # an input is "omitted" if it's not in output but IS explained (held-out/rejected/superseded).
        omitted_count = sum(1 for iid in in_by_id if iid not in out_by_id and iid in explained_ids)

        # ── orphaned OUTPUTS: appeared with no surviving input lineage → fabrication ──
        # an output is lineaged if its id was an input, OR it cites a parent/derived_from/support that is an input.
        def _lineage_refs(a: Mapping) -> set:
            refs: set = set()
            for k in ("parent_artifact_id", "parent"):
                v = a.get(k)
                if v:
                    refs.add(str(v))
            for k in ("derived_from", "supports", "supporting_artifact_ids", "baseline_artifact_ids"):
                v = a.get(k)
                if isinstance(v, (list, tuple)):
                    refs.update(str(x) for x in v)
            return refs

        in_handles_index = {h for a in inputs for h in _handles(a)}
        orphaned_output_ids = sorted(
            oid
            for oid, a in out_by_id.items()
            if oid not in in_by_id
            and not (_lineage_refs(a) & set(in_by_id))
            # an output handle that resolves to an input handle also counts as lineaged (handle == source)
            and not (set(_handles(a)) & in_handles_index)
            and not any(str(h).split("#")[0] in {str(ih).split("#")[0] for ih in in_handles_index} for h in _handles(a))
        )

        # ── dropped source handles: a SURVIVING truth-bearing output that lost a handle its input carried ──
        dropped_source_handle_count = 0
        for oid, oa in out_by_id.items():
            ia = in_by_id.get(oid)
            if ia is None:
                continue
            if not (_is_truth(ia) or _is_truth(oa)):
                continue
            in_h, out_h = set(_handles(ia)), set(_handles(oa))
            if in_h and not (in_h <= out_h):
                dropped_source_handle_count += len(in_h - out_h)

        # ── source-handle coverage over the SERVED truth-bearing set (must be 100% to promote) ──
        served_truth = [a for a in served if _is_truth(a)]
        served_count = len(served)
        with_handle = sum(1 for a in served_truth if _handles(a))
        source_handle_coverage = (with_handle / len(served_truth)) if served_truth else 1.0

        # explanatory notes
        if orphaned_input_ids:
            notes.append(f"orphaned (silently dropped) inputs: {orphaned_input_ids}")
        if orphaned_output_ids:
            notes.append(f"orphaned (fabricated) outputs: {orphaned_output_ids}")
        if dropped_source_handle_count:
            notes.append(f"{dropped_source_handle_count} source handle(s) dropped from surviving facts")
        if source_handle_coverage < 1.0:
            notes.append(f"served source-handle coverage below 100%: {round(source_handle_coverage, 4)}")
        if lossy_transform_declared and not lossy_transform_allowed:
            notes.append("transform declared lossy but loss is not allowed (truth-bearing)")

        safe_to_promote = (
            bool(raw_rehydration_passed)
            and bool(lineage_complete)
            and not orphaned_input_ids
            and not orphaned_output_ids
            and dropped_source_handle_count == 0
            and source_handle_coverage >= 1.0
            and ((not lossy_transform_declared) or bool(lossy_transform_allowed))
        )

        body = {
            "t": transform_type,
            "in": sorted(in_by_id),
            "out": sorted(out_by_id),
            "served": sorted(_aid(a) for a in served if _aid(a)),
            "held": sorted(held_ids),
            "rej": sorted(rejected_ids),
            "sup": sorted(superseded_ids),
            "drop": dropped_source_handle_count,
            "orph_in": orphaned_input_ids,
            "orph_out": orphaned_output_ids,
            "rehydr": bool(raw_rehydration_passed),
            "lin": bool(lineage_complete),
            "lossy": (bool(lossy_transform_declared), bool(lossy_transform_allowed)),
        }
        report_id = "retreport-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]

        return InformationRetentionReport(
            report_id=report_id,
            transform_type=transform_type,
            input_count=len(in_by_id),
            output_count=len(out_by_id),
            served_count=served_count,
            source_handle_coverage=source_handle_coverage,
            omitted_count=omitted_count,
            held_out_count=len(held_ids),
            rejected_count=len(rejected_ids),
            superseded_count=len(superseded_ids),
            orphaned_input_ids=orphaned_input_ids,
            orphaned_output_ids=orphaned_output_ids,
            dropped_source_handle_count=dropped_source_handle_count,
            raw_rehydration_passed=bool(raw_rehydration_passed),
            lineage_complete=bool(lineage_complete),
            lossy_transform_declared=bool(lossy_transform_declared),
            lossy_transform_allowed=bool(lossy_transform_allowed),
            safe_to_promote=safe_to_promote,
            notes=notes,
        )


def build_retention_report(**kwargs) -> InformationRetentionReport:
    """Module-level convenience wrapper around :meth:`InformationRetentionReportBuilder.build`."""
    return InformationRetentionReportBuilder().build(**kwargs)
