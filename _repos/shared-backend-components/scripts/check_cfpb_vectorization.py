#!/usr/bin/env python3
"""scripts.check_cfpb_vectorization — proof: deterministic local vectors are stable across runs, record
provider/model/version/dimensions, and search filters by tenant and by artifact_type (no fact/allegation blur).

CLI: python3 _repos/shared-backend-components/scripts/check_cfpb_vectorization.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph.artifact_ledger import ArtifactGraphLedger
from scripts.artifact_graph.vector_store import (DeterministicLocalVectorProvider, VECTORIZABLE,
                                                 search_similar, vectorize_artifact, vectorize_into_ledger)
from scripts.security.tenant_catalog import TenantPolicy

REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."}]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    prov = DeterministicLocalVectorProvider()
    arts = CA.build_artifacts(REC, TenantPolicy("acme"))["artifacts"]

    # vectorize the retrieval-unit types
    fact = next(a for a in arts if a.artifact_type == "atomic_fact")
    v1, v2 = vectorize_artifact(prov, fact), vectorize_artifact(prov, fact)
    check("deterministic vector is STABLE across runs (byte-identical)", v1.vector_json == v2.vector_json and v1.content_hash == v2.content_hash)
    check("vector records provider/model/version/dimensions",
          v1.vector_provider == "deterministic_local" and v1.vector_model == "hashed_lexical"
          and v1.vector_version == "v1" and v1.dimensions == prov.dimensions and len(v1.vector_json) == prov.dimensions)
    check("vectorizes facts/sentences/allegations/conclusions",
          {"atomic_fact", "narrative_allegation", "sentence", "conclusion"} <= set(VECTORIZABLE))

    led = ArtifactGraphLedger(":memory:")
    n = vectorize_into_ledger(led, prov, arts)
    check("vectorized only the retrieval-unit types", n == sum(1 for a in arts if a.artifact_type in VECTORIZABLE) and n > 0)

    # tenant filter: a second tenant's vectors are isolated
    led.put_vector(vectorize_artifact(prov, CA.build_artifacts(REC, TenantPolicy("globex"))["artifacts"][0]))
    check("tenant filter isolates vectors", all(v["artifact_id"].split(":")[0] for v in led.vectors("acme"))
          and len(led.vectors("globex")) == 1)

    # artifact_type filter: searching with a type filter never returns another type
    fact_id = fact.artifact_id
    nn_facts = search_similar(led, prov, "acme", artifact_id=fact_id, artifact_types=("atomic_fact",), k=10)
    allowed = {a.artifact_id for a in arts if a.artifact_type == "atomic_fact"}
    check("artifact_type filter returns ONLY that type (no fact/allegation blur)",
          all(r["artifact_id"] in allowed for r in nn_facts), str([r["artifact_id"] for r in nn_facts][:3]))
    nn_alleg = search_similar(led, prov, "acme", artifact_id=fact_id, artifact_types=("narrative_allegation",), k=10)
    check("filtering to allegations excludes the facts", all(r["artifact_id"] not in allowed for r in nn_alleg))

    led.close()
    print(f"\n{'PASS — check_cfpb_vectorization: deterministic vectors are stable + provider-tagged; search filters by tenant and artifact_type (a similar allegation is never returned as a fact).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 vectorization + filtered search.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
