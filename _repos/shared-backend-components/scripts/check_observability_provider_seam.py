#!/usr/bin/env python3
"""scripts.check_observability_provider_seam — proof (C-OBS-1): the ObservabilityProvider seam turns a
stream of context-operation spans into a correct, deterministic SpanTree. The wired adapter is the local
stub (Langfuse/Phoenix/LangSmith are candidate-only). Nesting, count, ordering, correlation, and
held-out propagation all hold; the provider DESCRIBES and never mutates canonical (frozen spans).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_observability_provider_seam.py --self-test
"""
from __future__ import annotations

import argparse
import dataclasses

from src.baltor.observability.tracing.provider import (
    BaltorLocalObservability,
    ContextOperationSpan,
    ObservabilityProvider,
    SpanTree,
)

T0 = "2026-06-06T00:00:00Z"


def _spans() -> list[ContextOperationSpan]:
    return [
        ContextOperationSpan("s2", "s1", "reconciliation.find_contradictions", "ok", "2026-06-06T00:00:02Z",
                             object_ref="obj-runbook", correlation_id="corr-1"),
        ContextOperationSpan("s1", None, "pipeline.run", "ok", "2026-06-06T00:00:01Z", correlation_id="corr-1"),
        ContextOperationSpan("s3", "s1", "verification.check", "held_out", "2026-06-06T00:00:03Z",
                             correlation_id="corr-1", governance={"held_out": True, "claim_status": "allegation"}),
    ]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    prov = BaltorLocalObservability()
    chk("stub satisfies the ObservabilityProvider port", isinstance(prov, ObservabilityProvider))
    chk("wired adapter id is the local stub", prov.adapter_id == "observability.baltor_local_trace@v1", prov.adapter_id)

    tree = prov.record(_spans())
    chk("returns a SpanTree", isinstance(tree, SpanTree))
    chk("span_count counts every span", tree.span_count == 3, str(tree.span_count))
    chk("single real root (s1) chosen", tree.root["span_id"] == "s1", tree.root["span_id"])
    child_ids = {c["span_id"] for c in tree.root["children"]}
    chk("children nest under their parent", child_ids == {"s2", "s3"}, str(child_ids))
    # ordering by (occurred_at, span_id): s2 (00:02) before s3 (00:03)
    chk("children are ordered by time", [c["span_id"] for c in tree.root["children"]] == ["s2", "s3"],
        str([c["span_id"] for c in tree.root["children"]]))
    chk("correlation id propagated", tree.correlation_id == "corr-1", str(tree.correlation_id))
    held = next(c for c in tree.root["children"] if c["span_id"] == "s3")
    chk("held_out flag surfaces on the node", held["held_out"] is True)
    chk("governance filtered to allowed keys only", set(held["governance"]) <= {"held_out", "claim_status"},
        str(held["governance"]))

    # determinism: same input (any order) -> same tree
    import json
    a = json.dumps(prov.record(_spans()).root, sort_keys=True)
    b = json.dumps(prov.record(list(reversed(_spans()))).root, sort_keys=True)
    chk("deterministic regardless of input order", a == b)

    # no canonical mutation: spans are frozen
    frozen_ok = False
    try:
        _spans()[0].operation = "tampered"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        frozen_ok = True
    chk("spans are immutable (provider cannot mutate canonical)", frozen_ok)

    # multi-root -> synthetic root
    multi = prov.record([
        ContextOperationSpan("a", None, "op.a", "ok", T0),
        ContextOperationSpan("b", None, "op.b", "ok", "2026-06-06T00:00:05Z"),
    ])
    chk("multiple top-level spans get a synthetic root", multi.root["span_id"] == "root" and len(multi.root["children"]) == 2)

    print(f"\n{'PASS — check_observability_provider_seam: local stub builds a correct, deterministic, immutable SpanTree; held-out + governance propagate; provider describes, never the authority.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: observability provider seam.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
