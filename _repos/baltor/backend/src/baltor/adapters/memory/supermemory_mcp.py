"""adapters/memory/supermemory_mcp — mcp.supermemory@candidate: a CONTRACT STUB for the memory MCP tools.

The CANDIDATE wrapper for Supermemory's open MCP server (the ``memory`` / ``recall`` / ``context`` tools). Same
posture as the api candidate: it NEVER imports an MCP/Supermemory SDK and NEVER makes a network call. With NO
credentials configured, every tool raises a clear ``UnavailableProvider`` naming ``env://SUPERMEMORY_API_KEY``;
``status()`` reports ``unavailable`` without raising. The correctness invariant runs offline on the emulator / local
provider, exposing the same memory/recall/context tools.

When a real MCP-bridge impl is wired behind this surface, its tool outputs MUST still be governed candidate
MemoryArtifacts (claim_status="candidate" + external_source_handle + lineage) — an MCP recall is NEVER a
served/canonical fact, and Supermemory is NEVER the source of truth.

Stdlib only; offline; deterministic.
"""
from __future__ import annotations

from typing import Any

from src.baltor.ports.memory_provider import UnavailableProvider

#: stable MCP provider identity (matches the capability catalog adapter_id).
PROVIDER_ID = "mcp.supermemory@candidate"

#: the credential this candidate requires — a REF, never a value. Named in the UnavailableProvider it raises.
CREDENTIAL_REF = "env://SUPERMEMORY_API_KEY"

#: the MCP tool names this provider exposes.
TOOLS = ("memory", "recall", "context")

#: status reported by status() when no credential is configured.
_STATUS_UNAVAILABLE = "unavailable"


def _credentials_present() -> bool:
    """True only if the MCP credential is configured (checked via the env:// ref, never logged/echoed)."""
    import os
    assert CREDENTIAL_REF.startswith("env://")
    return bool(os.environ.get(CREDENTIAL_REF[len("env://"):], ""))


class SupermemoryMcpProvider:
    """CANDIDATE Supermemory MCP wrapper. Satisfies MemoryMCPProviderPort. With no creds every tool raises
    UnavailableProvider(env://SUPERMEMORY_API_KEY); status() reports unavailable without raising."""

    provider_id = PROVIDER_ID
    credential_ref = CREDENTIAL_REF

    def tools(self) -> list[str]:
        return list(TOOLS)

    def _require_credentials(self) -> None:
        if not _credentials_present():
            raise UnavailableProvider(self.provider_id, CREDENTIAL_REF,
                                      "candidate MCP contract stub: no bridge wired; use the emulator/local "
                                      "provider for the offline correctness invariant")
        raise UnavailableProvider(self.provider_id, CREDENTIAL_REF,
                                  "credential present but the live MCP bridge is not wired in this build "
                                  "(contract stub only; never makes network calls)")

    def memory(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP ``memory`` tool (remember). Stub: raises UnavailableProvider naming the env:// credential."""
        self._require_credentials()
        raise AssertionError("unreachable")

    def recall(self, request: dict[str, Any]) -> dict[str, Any]:
        """MCP ``recall`` tool (search). Stub: raises UnavailableProvider naming the env:// credential."""
        self._require_credentials()
        raise AssertionError("unreachable")

    def context(self, scope: dict[str, Any]) -> dict[str, Any]:
        """MCP ``context`` tool (profile static/dynamic). Stub: raises UnavailableProvider."""
        self._require_credentials()
        raise AssertionError("unreachable")

    def status(self) -> dict[str, Any]:
        has = _credentials_present()
        return {
            "provider_id": self.provider_id,
            "status": _STATUS_UNAVAILABLE,
            "has_credentials": has,
            "credential_ref": CREDENTIAL_REF,
            "tools": list(TOOLS),
            "detail": ("candidate MCP contract stub: no bridge wired (use the emulator/local provider). "
                       f"going live requires {CREDENTIAL_REF}"),
        }


def _self_demo() -> dict[str, Any]:
    """Deterministic offline demo used by the proof: status() green-unavailable; each tool raises Unavailable."""
    p = SupermemoryMcpProvider()
    st = p.status()
    raised: dict[str, str] = {}
    for tool, call in (("memory", lambda: p.memory({})), ("recall", lambda: p.recall({})),
                       ("context", lambda: p.context({}))):
        try:
            call()
        except UnavailableProvider as e:
            raised[tool] = e.credential_ref
    return {"status": st, "tools": p.tools(), "tools_raised": raised,
            "all_tools_named_ref": all(v == CREDENTIAL_REF for v in raised.values()) and len(raised) == len(TOOLS)}


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    import json
    print(json.dumps(_self_demo(), indent=2, default=str))
