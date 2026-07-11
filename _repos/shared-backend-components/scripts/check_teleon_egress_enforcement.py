#!/usr/bin/env python3
"""Proof for Teleon's governed egress enforcement path.

The egress graph proves searchable observations. This check proves the runtime
path in front of it: covered workers and inference adapters use EgressClient,
raw HTTP is isolated to the approved transport adapter, route decisions are
ledgered, blocked routes do not fall through, and egress evidence never serves
truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
else:
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.teleon.egress import EgressBlocked, EgressClient, EgressLedgerRejected, LocalEgressGraph, LocalEgressLedger
from src.teleon.egress.transports import EgressTransportResponse

REPO = Path(_REPO_ROOT)
COVERED_EGRESS_CALLERS = (
    _resource("scripts") / "context_workers" / "workers" / "tool_adapters.py",
    _resource("scripts") / "context_workers" / "workers" / "node_research.py",
    _resource("src/teleon/inference/adapters.py"),
)
APPROVED_TRANSPORT = _resource("src/teleon/egress/transports.py")
FORBIDDEN_IMPORT_ROOTS = {"requests", "httpx", "aiohttp"}
FORBIDDEN_QUALIFIED_IMPORTS = {"urllib.request", "urllib.error"}
FORBIDDEN_CALLS = {
    "urllib.request.Request",
    "urllib.request.urlopen",
    "requests.get",
    "requests.post",
    "requests.request",
    "httpx.get",
    "httpx.post",
    "httpx.request",
    "aiohttp.ClientSession",
}


class _StubTransport:
    transport_kind = "stub_http"

    def request(
        self,
        *,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout_s: int = 30,
    ) -> EgressTransportResponse:
        del method, url, body, headers, timeout_s
        return EgressTransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=b'{"ok": true, "source": "stub"}',
        )


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return ""


def _raw_http_violations(path: Path) -> list[str]:
    """Forbidden raw-network imports/calls in a file. Does NOT require EgressClient — a deterministic worker
    (chunker, keyword, graph) legitimately makes no outbound call; this is the deny-by-default backstop."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in FORBIDDEN_QUALIFIED_IMPORTS or name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                    problems.append(f"{path.relative_to(REPO)}:{node.lineno} forbidden import {name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in {"urllib", "urllib.request", "urllib.error"}:
                problems.append(f"{path.relative_to(REPO)}:{node.lineno} forbidden urllib import-from {module}")
            if module.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                problems.append(f"{path.relative_to(REPO)}:{node.lineno} forbidden import-from {module}")
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name in FORBIDDEN_CALLS:
                problems.append(f"{path.relative_to(REPO)}:{node.lineno} forbidden raw network call {name}")
    return problems


def _static_violations(path: Path) -> list[str]:
    """A COVERED egress caller must BOTH make no raw network call AND route via EgressClient."""
    problems = _raw_http_violations(path)
    if "EgressClient" not in path.read_text(encoding="utf-8"):
        problems.append(f"{path.relative_to(REPO)} missing EgressClient usage")
    return problems


def _deny_by_default_violations() -> list[str]:
    """Deny-by-default backstop: NO worker file (egressing or not) may make a raw outbound HTTP call — raw
    network stays isolated to the approved transport. A NEW worker doing requests.get(...) fails the proof
    even though it is not in the 3-file covered-caller allowlist (the gap the old hardcoded scan missed)."""
    problems: list[str] = []
    workers_dir = _resource("scripts") / "context_workers" / "workers"
    for f in sorted(workers_dir.rglob("*.py")):
        if "__pycache__" not in f.parts:
            problems.extend(_raw_http_violations(f))
    return problems


def _raw_transport_is_isolated() -> list[str]:
    problems: list[str] = []
    raw = APPROVED_TRANSPORT.read_text(encoding="utf-8")
    if "urllib.request.urlopen" not in raw or "urllib.request.Request" not in raw:
        problems.append("approved transport does not own the stdlib urllib call surface")
    for caller in COVERED_EGRESS_CALLERS:
        problems.extend(_static_violations(caller))
    return problems


def _run_allowed_request() -> tuple[dict[str, Any], LocalEgressLedger, LocalEgressGraph]:
    ledger = LocalEgressLedger(":memory:")
    graph = LocalEgressGraph(":memory:")
    client = EgressClient(ledger=ledger, graph=graph, transport=_StubTransport())
    result = client.request_json(
        tenant_id="tenant-egress-proof",
        run_id="run-egress-proof",
        worker_id="worker-proof",
        worker_kind="proof_worker",
        operation="proof.service_json",
        url="https://registry.example.gov/search?token=redact-me&q=license",
        json_payload={"q": "licensed employment agency", "token": "redact-me"},
        headers={"Authorization": "Bearer proof-token"},
        timeout_s=5,
        query_text="licensed employment agency authoritative registry lookup",
        tool_name="egress.proof",
        route_policy_id="direct_public_internet",
        now="2026-06-14T00:00:00Z",
    )
    return result, ledger, graph


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    static_problems = _raw_transport_is_isolated()
    check("covered workers route HTTP through EgressClient", not static_problems, "; ".join(static_problems))

    deny = _deny_by_default_violations()
    check("deny-by-default: NO worker file makes a raw outbound HTTP call (not just the 3 covered callers)",
          not deny, "; ".join(deny))

    result, ledger, graph = _run_allowed_request()
    intents = ledger.records("intents")
    decisions = ledger.records("decisions")
    attempts = ledger.records("attempts")
    events = graph.search_events(tenant_id="tenant-egress-proof", text="licensed employment")
    serialized = json.dumps({"result": result, "events": events, "intents": intents}, sort_keys=True, default=str)

    check("allowed request returns parsed JSON through approved transport", result["json"].get("ok") is True)
    check("ledger appends one intent, decision, and attempt", len(intents) == len(decisions) == len(attempts) == 1)
    check("route decision allows direct public internet", decisions[0]["action"] == "allow"
          and decisions[0]["route_policy_id"] == "direct_public_internet")
    check("ledger and graph records remain truth-free",
          all(record["serves_truth"] is False for record in [*intents, *decisions, *attempts, *events]))
    check("graph captures the allowed attempt", len(events) == 1 and events[0]["status"] == "ok")
    check("secret-like request data is redacted from captured evidence",
          "redact-me" not in serialized and "Bearer proof-token" not in serialized, serialized)

    tampered = dict(intents[0])
    tampered["worker_id"] = "tampered-worker"
    check("ledger rejects same intent id with different content", _raises_ledger(lambda: ledger.append_intent(tampered)))

    blocked_ledger = LocalEgressLedger(":memory:")
    blocked_graph = LocalEgressGraph(":memory:")
    blocked_client = EgressClient(ledger=blocked_ledger, graph=blocked_graph, transport=_StubTransport())
    blocked = _raises_blocked(lambda: blocked_client.request_json(
        tenant_id="tenant-egress-proof",
        run_id="run-egress-blocked",
        worker_id="worker-proof",
        worker_kind="proof_worker",
        operation="proof.service_json",
        url="https://registry.example.gov/search",
        json_payload={"q": "license"},
        query_text="license registry over vpn",
        tool_name="egress.proof",
        route_policy_id="approved_vpn_exit",
        now="2026-06-14T00:00:01Z",
    ))
    blocked_decisions = blocked_ledger.records("decisions")
    blocked_attempts = blocked_ledger.records("attempts")
    blocked_events = blocked_graph.search_events(tenant_id="tenant-egress-proof", text="license registry")
    check("approval-required routes block without explicit approval", blocked)
    check("blocked route is still ledgered and graphed",
          blocked_decisions[0]["action"] == "blocked"
          and blocked_attempts[0]["status"] == "blocked"
          and blocked_events[0]["status"] == "blocked")

    # EVERY non-default route blocks without an approval ref — derived from the taxonomy so it cannot drift
    # (the bug this catches: browser_pool_render was default_allowed=false yet allowed without approval).
    from src.teleon.egress.policy import ALLOWED_TRANSPORT_KIND, approval_required_route_ids, decide_route, make_egress_intent
    approval_routes = approval_required_route_ids()
    ungated = []
    for rid in sorted(approval_routes):
        intent = make_egress_intent(tenant_id="t", run_id="r", worker_id="w", worker_kind="proof",
                                    operation="probe", destination_url="https://registry.example.gov/x",
                                    route_policy_id=rid, requested_at="2026-06-14T00:00:00Z")
        d = decide_route(intent, now="2026-06-14T00:00:01Z", approved_route_refs=set())
        if d["action"] != "blocked":
            ungated.append(rid)
    check("every non-default route blocks without an approval ref (taxonomy-derived; browser_pool_render incl.)",
          not ungated and len(approval_routes) >= 4, f"ungated={ungated} routes={sorted(approval_routes)}")
    check("allowed decision's transport_kind is single-sourced from the approved transport (no parallel literal)",
          decisions[0]["transport_kind"] == ALLOWED_TRANSPORT_KIND)

    print("\n" + ("PASS - check_teleon_egress_enforcement: NO worker file makes a raw outbound HTTP call "
                  "(deny-by-default); the covered callers route through EgressClient; every non-default route "
                  "blocks without an explicit approval ref (taxonomy-derived, no drift); raw HTTP is isolated to "
                  "the approved transport; decisions/attempts/graph observations are append-only and truth-free."
                  if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


def _raises_ledger(fn) -> bool:
    try:
        fn()
        return False
    except EgressLedgerRejected:
        return True


def _raises_blocked(fn) -> bool:
    try:
        fn()
        return False
    except EgressBlocked:
        return True


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
