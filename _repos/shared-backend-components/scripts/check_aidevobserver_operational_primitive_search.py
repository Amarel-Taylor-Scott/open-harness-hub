#!/usr/bin/env python3
"""Proof: AIDevObserver can search the wide operational primitive export."""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.observer.registry_search import (  # noqa: E402
    load_operational_primitive_count,
    registry_search_response,
    search_operational_primitives,
)


MANIFEST = _resource("dist") / "primitive-registry-operational-load" / "manifest.json"


def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_records = int((manifest.get("counts") or {}).get("registry_record") or 0)
    operational_count = load_operational_primitive_count()
    check(
        "operational primitive index exposes the generated registry scale",
        operational_count >= int(expected_records * 0.95),
        f"expected near {expected_records}, got {operational_count}",
    )

    csv_hits = search_operational_primitives("parse csv rows", limit=5)
    check(
        "operational search returns registry-backed primitive cards",
        bool(csv_hits) and any(hit.get("source_kind") == "operational_primitive_registry" for hit in csv_hits),
    )
    check(
        "operational hits include input and output edge summaries",
        all((hit.get("contract") or {}).get("input") and (hit.get("contract") or {}).get("output") for hit in csv_hits),
    )
    check(
        "operational hits include deterministic mutation affordances",
        any(hit.get("edge_mutation_options") for hit in csv_hits),
    )
    check(
        "operational hits remain candidate evidence, not served truth",
        all(hit.get("candidate") is True and hit.get("serves_truth") is False for hit in csv_hits),
    )
    check(
        "operational hits do not expose raw canonical source bodies",
        all("canonical_json" not in hit and "source_body" not in hit for hit in csv_hits),
    )

    status, payload = registry_search_response("parse csv rows", None, 8)
    service_hits = payload.get("hits") or []
    check("registry service search succeeds", status == 200)
    check(
        "registry service reports operational record count",
        int((payload.get("global_primitive_registry") or {}).get("operational_records") or 0) == operational_count,
    )
    check(
        "registry service surfaces operational cards to the planner path",
        any((hit.get("reuse_card") or hit).get("source_kind") == "operational_primitive_registry" for hit in service_hits),
    )

    print("\n" + ("PASS — AIDevObserver operational primitive search uses the wide generated registry export."
                  if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    # `--self-test` is accepted explicitly: the default invocation IS the in-process proof
    # (main() runs every assertion and exits non-zero on failure).
    raise SystemExit(main())
