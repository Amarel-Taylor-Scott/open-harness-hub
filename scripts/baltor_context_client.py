#!/usr/bin/env python3
"""Small local client for the Baltor context gateway.

This module is intentionally dependency-free so Claude Code commands, hooks,
local memory sync scripts, and future SDK wrappers can share the same gateway
contract without copying URL/path logic.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._config import CONTEXT_GATEWAY_RUNTIME_SETTINGS
from scripts.db.runtime_settings import runtime_setting


CONTEXT_GATEWAY_RUNTIME_NAMESPACE = "baltor.context_gateway.runtime"

def _context_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_GATEWAY_RUNTIME_NAMESPACE,
        definitions=CONTEXT_GATEWAY_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_BASE_URL = _context_setting("gateway_base_url")
DEFAULT_TIMEOUT_SECONDS = int(_context_setting("client_timeout_seconds"))

PATH_STATUS = "/api/context-gateway/status"
PATH_SEARCH = "/api/context-gateway/search"
PATH_FETCH = "/api/context-gateway/fetch"
PATH_TRACE = "/api/context-gateway/trace"
PATH_CONNECTORS = "/api/context-gateway/connectors"
PATH_GLOSSARY = "/api/context-gateway/glossary"
PATH_HEARTBEAT = "/api/debug/heartbeat"
PATH_QUEUE_HEALTH = "/api/admin-dashboard/queue-health"


@dataclass(frozen=True)
class BaltorContextClient:
    """Thin HTTP client for bounded local context gateway operations."""

    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    def http_json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = urllib.parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def status(self) -> dict[str, Any]:
        return self.http_json(PATH_STATUS)

    def search(self, query: str, *, run_id: str = "", token_budget: int = 3000, task_type: str = "code_change") -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "task_type": task_type,
            "token_budget": token_budget,
        }
        if run_id:
            payload["run_id"] = run_id
        return self.http_json(PATH_SEARCH, payload)

    def fetch(self, handle: str, *, run_id: str = "", max_tokens: int = 1500) -> dict[str, Any]:
        query = {"handle": handle, "max_tokens": str(max_tokens)}
        if run_id:
            query["run_id"] = run_id
        return self.http_json(PATH_FETCH + "?" + urllib.parse.urlencode(query))

    def trace(self) -> dict[str, Any]:
        return self.http_json(PATH_TRACE)

    def connectors(self) -> dict[str, Any]:
        return self.http_json(PATH_CONNECTORS)

    def glossary(self, *, run_id: str = "", term: str = "", max_packets: int = 20) -> dict[str, Any]:
        payload: dict[str, Any] = {"max_packets": max_packets}
        if run_id:
            payload["run_id"] = run_id
        if term:
            payload["term"] = term
        return self.http_json(PATH_GLOSSARY, payload)

    def heartbeat(self, *, run_id: str = "") -> dict[str, Any]:
        path = PATH_HEARTBEAT
        if run_id:
            path += "?" + urllib.parse.urlencode({"run_id": run_id})
        return self.http_json(path)

    def queue_health(self) -> dict[str, Any]:
        return self.http_json(PATH_QUEUE_HEALTH)
