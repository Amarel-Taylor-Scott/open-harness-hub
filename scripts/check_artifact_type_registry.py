#!/usr/bin/env python3
"""scripts.check_artifact_type_registry — proof: the governed artifact-type registry holds its contract.

Proves the required artifact types exist, the four claim-shaped types (atomic_fact / narrative_allegation /
conclusion / emotion_signal) have DISTINCT governance defaults (no silent conflation), and every
model-dependent artifact type requires processor metadata.

CLI: python3 scripts/check_artifact_type_registry.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime import artifact_types as AT


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("all required artifact types are registered",
          all(t in AT.REGISTRY for t in AT.REQUIRED_TYPES),
          str([t for t in AT.REQUIRED_TYPES if t not in AT.REGISTRY]))

    keys = {t: AT.get(t).governance_key() for t in AT.CLAIM_SHAPED}
    check("atomic_fact / narrative_allegation / conclusion / emotion_signal have DISTINCT governance",
          len(set(keys.values())) == len(AT.CLAIM_SHAPED), str(keys))

    af, na, co, em = (AT.get(t) for t in AT.CLAIM_SHAPED)
    check("atomic_fact is promotion-eligible + usable as fact", af.promotion_eligible_default and af.can_be_used_as_fact)
    check("narrative_allegation is source-grounded but NOT a fact / NOT promotion-eligible",
          na.source_grounded and not na.can_be_used_as_fact and not na.promotion_eligible_default and na.requires_human_review)
    check("conclusion is derived, requires human review, NOT a certified fact",
          co.derived and co.requires_human_review and not co.can_be_used_as_fact)
    check("emotion_signal is model-dependent, NOT promotion-eligible, NOT a fact",
          em.model_dependent and not em.promotion_eligible_default and not em.can_be_used_as_fact)

    md_types = [t for t, s in AT.REGISTRY.items() if s.model_dependent]
    check("model-dependent types exist (emotion_signal/sentiment_vector/embedding)",
          {"emotion_signal", "sentiment_vector", "embedding"} <= set(md_types), str(md_types))
    check("EVERY model-dependent artifact type requires processor metadata",
          all(AT.requires_processor_metadata(t) for t in md_types))
    check("source-grounded raw types are NOT model-dependent",
          not any(AT.get(t).model_dependent for t in ("source_record", "source_field", "sentence", "atomic_fact")))

    print(f"\n{'PASS — check_artifact_type_registry: required types present; the four claim-shaped types are governed distinctly; model-dependent artifacts require processor metadata.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: governed artifact-type registry contract.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
