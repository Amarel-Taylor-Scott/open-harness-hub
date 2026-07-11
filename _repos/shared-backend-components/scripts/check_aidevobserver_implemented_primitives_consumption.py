#!/usr/bin/env python3
"""Proof: AIDevObserver consumes AST-mined implemented-code primitives."""
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

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH,
    AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND,
    AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY,
)
from src.teleon.observer.registry_search import (  # noqa: E402
    load_edge_foundry_primitives,
    load_implemented_code_primitive_count,
    registry_search_response,
    search_edge_foundry_primitives,
)


def _card_source_kind(hit: dict) -> str:
    card = hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else hit
    return str(card.get("source_kind") or hit.get("source_kind") or "")


def _card_contract(hit: dict) -> dict:
    card = hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else hit
    return card.get("contract") if isinstance(card.get("contract"), dict) else {}


def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    path = _resource(AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH)
    check("implemented-code primitive JSONL exists", path.exists(), str(path))

    implemented_count = load_implemented_code_primitive_count()
    check(
        "edge-foundry loader includes implemented-code primitive corpus",
        implemented_count >= 2000,
        f"got {implemented_count}",
    )

    loaded = load_edge_foundry_primitives()
    implemented_cards = [
        card for card in loaded
        if card.get("source_kind") == AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND
    ]
    check("implemented-code records have private/internal visibility",
          implemented_cards and all(
              card.get("surface_visibility") == AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY
              for card in implemented_cards[:50]
          ),
          str(implemented_cards[:1]))
    check("implemented-code cards preserve compact contracts",
          implemented_cards and all((card.get("contract") or {}).get("input") and (card.get("contract") or {}).get("output") for card in implemented_cards[:50]),
          str(implemented_cards[:1]))
    check("implemented-code cards preserve proof requirements",
          implemented_cards and all(card.get("proof_requirements") for card in implemented_cards[:50]),
          str(implemented_cards[:1]))

    query = "effects_for transport observed effect unknown mode"
    public_hits = search_edge_foundry_primitives(query, visibility_scope="public", limit=12)
    check(
        "public primitive search does not expose implemented-code local source rows",
        all(hit.get("source_kind") != AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND for hit in public_hits),
        str(public_hits[:3]),
    )

    local_hits = search_edge_foundry_primitives(query, visibility_scope="local", limit=12)
    implemented_local_hits = [
        hit for hit in local_hits
        if hit.get("source_kind") == AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND
    ]
    check("local/private search returns implemented-code primitive hits", bool(implemented_local_hits), str(local_hits[:5]))
    check("implemented-code hit remains candidate-only",
          bool(implemented_local_hits)
          and all(hit.get("candidate") is True and hit.get("serves_truth") is False for hit in implemented_local_hits),
          str(implemented_local_hits[:2]))

    status, payload = registry_search_response(query, None, 8, visibility_scope="local")
    service_hits = payload.get("hits") or []
    implemented_service_hits = [
        hit for hit in service_hits
        if _card_source_kind(hit) == AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND
    ]
    check("registry service search succeeds", status == 200, str(payload))
    check("registry service reports implemented-code record count",
          int((payload.get("global_primitive_registry") or {}).get("implemented_code_records") or 0) == implemented_count,
          str(payload.get("global_primitive_registry") or {}))
    check("registry service can surface implemented-code reuse cards",
          bool(implemented_service_hits),
          str(service_hits[:5]))
    check("service reuse cards expose input/output edges",
          bool(implemented_service_hits)
          and all(_card_contract(hit).get("input") and _card_contract(hit).get("output") for hit in implemented_service_hits),
          str(implemented_service_hits[:2]))

    print(
        "\n"
        + (
            "PASS - AIDevObserver consumes implemented-code primitive records as private candidate reuse cards."
            if not failures
            else f"{len(failures)} FAILURES: {failures}"
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
