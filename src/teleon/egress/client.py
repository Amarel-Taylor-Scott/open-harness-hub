"""Runtime egress client.

Workers use this single entry point for outbound HTTP so Teleon can capture
intent, route decision, attempt, graph observation, and payload digest before a
response is consumed downstream.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from src.teleon.egress.ledger import LocalEgressLedger
from src.teleon.egress.policy import DEFAULT_ROUTE_POLICY_ID, decide_route, make_egress_intent
from src.teleon.egress.traffic_graph import LocalEgressGraph, make_egress_observation
from src.teleon.egress.transports import EgressTransportError, UrllibHttpTransport
from src.teleon.experiments.ids import canonical_id, sha256_hex


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _header_summary(headers: dict[str, str] | None) -> dict[str, str]:
    headers = headers or {}
    return {str(k).lower(): "[set]" for k, v in headers.items() if v not in (None, "")}


def _body_hash(body: bytes | None) -> str:
    if not body:
        return "sha256:" + sha256_hex("")
    return "sha256:" + sha256_hex(body.decode("utf-8", errors="replace"))


class EgressBlocked(RuntimeError):
    """Raised when route policy blocks an outbound request before transport."""


class EgressClient:
    """Governed outbound HTTP client with ledger + graph capture."""

    def __init__(
        self,
        *,
        ledger: LocalEgressLedger | None = None,
        graph: LocalEgressGraph | None = None,
        transport: UrllibHttpTransport | None = None,
    ) -> None:
        self.ledger = ledger or LocalEgressLedger()
        self.graph = graph or LocalEgressGraph()
        self.transport = transport or UrllibHttpTransport()

    def request_bytes(
        self,
        *,
        tenant_id: str,
        run_id: str,
        worker_id: str,
        worker_kind: str,
        operation: str,
        url: str,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout_s: int = 30,
        query_text: str = "",
        query_id: str = "",
        tool_name: str = "",
        route_policy_id: str = DEFAULT_ROUTE_POLICY_ID,
        approved_route_refs: set[str] | None = None,
        trace_id: str = "",
        now: str | None = None,
    ) -> dict[str, Any]:
        started_at = now or _now()
        request_summary = {
            "method": method.upper(),
            "headers": _header_summary(headers),
            "body_hash": _body_hash(body),
            "body_bytes": len(body or b""),
        }
        intent = make_egress_intent(
            tenant_id=tenant_id,
            run_id=run_id,
            worker_id=worker_id,
            worker_kind=worker_kind,
            operation=operation,
            destination_url=url,
            method=method,
            query_text=query_text,
            query_id=query_id,
            route_policy_id=route_policy_id,
            request_summary=request_summary,
            requested_at=started_at,
            tool_name=tool_name,
            trace_id=trace_id,
        )
        self.ledger.append_intent(intent)
        decision = decide_route(intent, approved_route_refs=approved_route_refs, now=started_at)
        self.ledger.append_decision(decision)
        if decision["action"] != "allow":
            attempt = self._attempt_record(intent, decision, status="blocked", response_summary={}, completed_at=started_at)
            self.ledger.append_attempt(attempt)
            observation = self._observation(intent, decision, request_summary, {}, status="blocked",
                                            started_at=started_at, completed_at=started_at)
            self.graph.append(observation)
            raise EgressBlocked(decision["reason"])

        try:
            response = self.transport.request(method=method, url=url, body=body, headers=headers, timeout_s=timeout_s)
            completed_at = _now() if now is None else now
            response_summary = {
                "status_code": response.status_code,
                "content_type": response.content_type,
                "bytes": len(response.body),
                "response_hash": "sha256:" + sha256_hex(response.text),
            }
            attempt = self._attempt_record(intent, decision, status="ok", response_summary=response_summary,
                                           completed_at=completed_at)
            self.ledger.append_attempt(attempt)
            observation = self._observation(intent, decision, request_summary, response_summary, status="ok",
                                            started_at=started_at, completed_at=completed_at)
            self.graph.append(observation)
            return {
                "ok": True,
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.body,
                "text": response.text,
                "intent": intent,
                "decision": decision,
                "attempt": attempt,
                "observation": observation,
            }
        except EgressTransportError as exc:
            completed_at = _now() if now is None else now
            response_summary = {"error": str(exc), "response_hash": "sha256:" + sha256_hex(str(exc))}
            attempt = self._attempt_record(intent, decision, status="failed", response_summary=response_summary,
                                           completed_at=completed_at)
            self.ledger.append_attempt(attempt)
            observation = self._observation(intent, decision, request_summary, response_summary, status="failed",
                                            started_at=started_at, completed_at=completed_at)
            self.graph.append(observation)
            raise

    def request_json(self, *, json_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        body = json.dumps(json_payload).encode("utf-8")
        headers = {"content-type": "application/json", **dict(kwargs.pop("headers", {}) or {})}
        result = self.request_bytes(body=body, headers=headers, method=kwargs.pop("method", "POST"), **kwargs)
        try:
            result["json"] = json.loads(result["text"])
        except json.JSONDecodeError:
            result["json"] = {"raw_response": result["text"]}
        return result

    def _attempt_record(
        self,
        intent: dict[str, Any],
        decision: dict[str, Any],
        *,
        status: str,
        response_summary: dict[str, Any],
        completed_at: str,
    ) -> dict[str, Any]:
        response_hash = response_summary.get("response_hash") or "sha256:" + sha256_hex(response_summary)
        return {
            "schema_version": "EgressAttempt",
            "attempt_id": canonical_id("ega", intent["intent_id"], decision["decision_id"], status, completed_at),
            "intent_id": intent["intent_id"],
            "decision_id": decision["decision_id"],
            "tenant_id": intent["tenant_id"],
            "run_id": intent["run_id"],
            "worker_id": intent["worker_id"],
            "route_policy_id": decision["route_policy_id"],
            "transport_kind": decision["transport_kind"],
            "status": status,
            "response_hash": response_hash,
            "response_summary": response_summary,
            "completed_at": completed_at,
            "serves_truth": False,
        }

    def _observation(
        self,
        intent: dict[str, Any],
        decision: dict[str, Any],
        request_summary: dict[str, Any],
        response_summary: dict[str, Any],
        *,
        status: str,
        started_at: str,
        completed_at: str,
    ) -> dict[str, Any]:
        return make_egress_observation(
            tenant_id=intent["tenant_id"],
            run_id=intent["run_id"],
            worker_id=intent["worker_id"],
            worker_kind=intent["worker_kind"],
            query_text=intent["query_text_redacted"],
            operation=intent["operation"],
            destination_url=intent["destination"]["destination_url"],
            started_at=started_at,
            completed_at=completed_at,
            query_id=intent["query_id"],
            tool_name=intent.get("tool_name", ""),
            request={**request_summary, "route_decision_id": decision["decision_id"]},
            response=response_summary,
            status=status,
            trace_id=intent.get("trace_id", ""),
        )


__all__ = ["EgressBlocked", "EgressClient"]
