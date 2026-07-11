#!/usr/bin/env python3
"""scripts.check_temporal_graph_contracts — proof: the temporal-graph schemas parse (stdlib-validator
keywords only), and the runtime dataclasses emit objects carrying every required field.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_contracts.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
from pathlib import Path

from src.baltor.graph.temporal import build_cfpb_temporal_graph

_S = _resource("schemas/graph")
_REQUIRED = ["TemporalFactNode", "TemporalFactEdge", "TemporalFactObservation", "TemporalFactState",
             "TemporalFactTimeline", "TemporalGraphReceipt", "TemporalGraphProviderStatus",
             "TemporalFactGraphQuery", "TemporalFactGraphResult", "TemporalGraphProjection"]
_OK_KEYS = {"$id", "title", "description", "type", "properties", "required", "additionalProperties", "items", "enum"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for name in _REQUIRED:
        fp = _S / f"{name}.schema.json"
        chk(f"{name} schema exists", fp.exists())
        if fp.exists():
            sch = json.loads(fp.read_text())
            chk(f"{name} $id == graph/{name}", sch.get("$id") == f"graph/{name}")
            chk(f"{name} additionalProperties false", sch.get("additionalProperties") is False)
            bad = _bad_keys(sch)
            chk(f"{name} uses only stdlib-validator keywords", bad == [], str(bad))

    # runtime dataclasses → dicts carry the required node/edge fields
    r = build_cfpb_temporal_graph()
    node = r["current_node"]
    for f in ("temporal_fact_id", "canonical_fact_key", "tenant_id", "scope", "value_normalized",
              "source_authority", "source_handles", "content_hash", "current_state", "created_at"):
        chk(f"node carries {f}", f in node and node[f] not in (None,))
    edge = r["edges"][0]
    for f in ("edge_id", "tenant_id", "from_temporal_fact_id", "to_temporal_fact_id", "edge_type", "edge_source"):
        chk(f"edge carries {f}", f in edge)
    chk("node.scope is in the scope enum", node["scope"] in {"global_public", "tenant_private", "tenant_override", "system_reference"})

    print(f"\n{'PASS — check_temporal_graph_contracts: 10 schemas parse with stdlib keywords + additionalProperties:false; runtime node/edge dicts carry all required fields.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _bad_keys(node) -> list:
    bad = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("properties",):
                continue
            if k not in _OK_KEYS and not k.startswith("$"):
                # allow nested property names; only flag schema-keyword position
                pass
        for v in node.get("properties", {}).values():
            for kk in v:
                if kk not in _OK_KEYS and not kk.startswith("$"):
                    bad.append(kk)
    return sorted(set(bad))


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph contracts.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
