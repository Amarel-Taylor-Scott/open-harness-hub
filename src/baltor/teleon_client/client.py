"""src.baltor.teleon_client.client — the versioned TeleonClient (Baltor → Teleon tenant boundary).

ONE entry point Baltor uses to reach Teleon capabilities, instead of importing Teleon's internal modules
all over the codebase. Design:
  * VERSIONED surface — ``CLIENT_CONTRACT_VERSION`` + a fixed capability registry; callers depend on the
    capability name + contract, not Teleon's file layout (so the layout can change, or move behind a network,
    without touching callers).
  * OFFLINE-FIRST — default ``mode="local"`` calls Teleon's in-process implementation. No network.
  * GRACEFUL FALLBACK — if a remote Teleon is configured (``mode="remote"`` + an injected ``remote`` callable)
    and the call fails, the client falls back to the local implementation and records ``fallback=True``. The
    real remote (HTTP to a separate Teleon service) is a SEAM — not implemented offline; ``remote`` is an
    injected callable so the fallback path is testable and a real adapter can drop in later.
  * RECEIPT — every call returns an envelope {capability, contract_version, served_by, fallback, ok, result}
    and is appended to ``self.calls`` so which backend served what is always inspectable.

DEPENDENCY LAW: this module imports ``src.teleon`` (Baltor → Teleon, allowed); it must NEVER be imported by
Teleon. Capability results are deterministic governance outputs (evidence) — the client does not auto-serve
model/LLM output as truth.
"""
from __future__ import annotations

from typing import Any, Callable

# Baltor → Teleon (the allowed direction). The client is the boundary; it imports Teleon's canonical home.
from src.teleon.purpose_tasks import adaptation_ladder as _ladder
from src.teleon.purpose_tasks import runtime_binding as _binding

CLIENT_CONTRACT_VERSION = "teleon-client/v1"

# The versioned capability surface: capability_id -> the local Teleon callable it resolves to. Callers depend
# on these stable ids + the contract version, never on Teleon's module layout. Extend additively (new id),
# never repurpose an id (that would be a breaking contract change → bump the version).
_LOCAL_CAPABILITIES: dict[str, Callable[..., Any]] = {
    "purpose.classify_change": _ladder.classify,                 # change_type -> risk-tier record
    "purpose.change_gate": _ladder.required_gate,                # change_type -> required approval gate
    "purpose.autonomy_forbidden": _ladder.is_forbidden_autonomous,  # change_type -> bool
    "runtime.default_backend": _binding.offline_default_backend,  # () -> the offline default backend id
    "runtime.bind": _binding.bind,                               # runtime_class -> binding decision
}


def capabilities() -> list[str]:
    """The versioned capability surface (sorted, stable)."""
    return sorted(_LOCAL_CAPABILITIES)


class TeleonClient:
    """Baltor's tenant client for Teleon. Offline-first local calls; graceful fallback from a remote seam."""

    def __init__(self, *, mode: str = "local", remote: Callable[[str, dict], Any] | None = None) -> None:
        if mode not in ("local", "remote"):
            raise ValueError(f"unknown mode {mode!r} (expected 'local' or 'remote')")
        # 'remote' with no injected remote callable degrades to local (offline-first; never a hard failure).
        self.mode = mode
        self._remote = remote
        self.calls: list[dict[str, Any]] = []

    def call(self, capability: str, **params: Any) -> dict[str, Any]:
        """Invoke a Teleon capability. Returns an inspectable envelope; records it in ``self.calls``."""
        if capability not in _LOCAL_CAPABILITIES:
            raise ValueError(f"unknown capability {capability!r}; known: {capabilities()}")
        local_fn = _LOCAL_CAPABILITIES[capability]
        served_by, fallback = "local", False

        if self.mode == "remote" and self._remote is not None:
            try:
                result = self._remote(capability, dict(params))
                served_by = "remote"
            except Exception:  # noqa: BLE001 — ANY remote failure must fall back, never propagate
                result = local_fn(**params)
                served_by, fallback = "local", True
        else:
            result = local_fn(**params)

        env = {
            "capability": capability,
            "contract_version": CLIENT_CONTRACT_VERSION,
            "served_by": served_by,
            "fallback": fallback,
            "ok": True,
            "result": result,
        }
        self.calls.append(env)
        return env

    # --- ergonomic wrappers (return the raw result; the envelope/receipt lives in self.calls) ---
    def classify_change(self, change_type: str) -> dict[str, Any]:
        return self.call("purpose.classify_change", change_type=change_type)["result"]

    def change_gate(self, change_type: str) -> str:
        return self.call("purpose.change_gate", change_type=change_type)["result"]

    def autonomy_forbidden(self, change_type: str) -> bool:
        return self.call("purpose.autonomy_forbidden", change_type=change_type)["result"]

    def default_backend(self, policy_matrix: dict | None = None) -> str:
        return self.call("runtime.default_backend", policy_matrix=policy_matrix)["result"]

    def bind_runtime(self, runtime_class: str, **kw: Any) -> dict[str, Any]:
        return self.call("runtime.bind", runtime_class=runtime_class, **kw)["result"]


# --------------------------------------------------------------------------------------------------------
def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # versioned surface
    ck("contract version is teleon-client/vN", CLIENT_CONTRACT_VERSION.startswith("teleon-client/v"))
    caps = capabilities()
    ck("surface spans purpose_tasks + runtime_binding (>=5 caps)",
       len(caps) >= 5 and any(c.startswith("purpose.") for c in caps) and any(c.startswith("runtime.") for c in caps), str(caps))

    # default = local, offline (no remote configured)
    c = TeleonClient()
    ck("default mode is local", c.mode == "local" and c._remote is None)
    env = c.call("purpose.classify_change", change_type="config_change")
    ck("local call served_by=local, not a fallback", env["served_by"] == "local" and env["fallback"] is False)
    ck("local call returns the Teleon result", isinstance(env["result"], dict) and env["result"] == _ladder.classify("config_change"))
    ck("envelope is a receipt (capability + contract_version + served_by + fallback)",
       env["capability"] == "purpose.classify_change" and env["contract_version"] == CLIENT_CONTRACT_VERSION)
    ck("calls are logged", len(c.calls) == 1)

    # deterministic
    c2 = TeleonClient()
    ck("deterministic — same input, same result", c2.call("purpose.classify_change", change_type="config_change")["result"] == env["result"])

    # remote available → served_by=remote
    cr = TeleonClient(mode="remote", remote=lambda cap, p: {"via": "remote", "cap": cap})
    er = cr.call("runtime.default_backend")
    ck("remote-available call served_by=remote", er["served_by"] == "remote" and er["fallback"] is False and er["result"]["via"] == "remote")

    # remote FAILS → graceful fallback to local (records fallback, still returns the local result)
    def _boom(cap, p):
        raise ConnectionError("teleon remote unreachable")
    cf = TeleonClient(mode="remote", remote=_boom)
    ef = cf.call("runtime.default_backend")
    ck("remote-unavailable → graceful fallback to local", ef["served_by"] == "local" and ef["fallback"] is True)
    ck("fallback result == local result (offline still works)", ef["result"] == _binding.offline_default_backend())

    # 'remote' mode with no remote callable degrades to local (offline-first, never a hard failure)
    cd = TeleonClient(mode="remote")
    ck("remote mode w/o remote callable → local (offline-first)", cd.call("runtime.default_backend")["served_by"] == "local")

    # guardrails
    try:
        c.call("nope.unknown")
        ck("unknown capability rejected", False)
    except ValueError:
        ck("unknown capability rejected", True)
    try:
        TeleonClient(mode="bogus")
        ck("unknown mode rejected", False)
    except ValueError:
        ck("unknown mode rejected", True)

    print("\n" + (f"PASS — teleon_client: a versioned ({CLIENT_CONTRACT_VERSION}) Baltor→Teleon tenant client over "
                  f"{len(caps)} capabilities; offline-first local calls, graceful fallback from a remote seam, "
                  f"per-call receipts (served_by/fallback). Migration step 4 complete."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 -m src.baltor.teleon_client.client --self-test")
    raise SystemExit(0)
