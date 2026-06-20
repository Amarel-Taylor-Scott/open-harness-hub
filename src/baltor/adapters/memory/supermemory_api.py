"""adapters/memory/supermemory_api — memory.supermemory_api@candidate: a CONTRACT STUB (no SDK, no network).

This is the CANDIDATE wrapper for the real Supermemory developer API. It is a contract stub on purpose:

  * it NEVER imports the supermemory SDK / package and NEVER makes a network call;
  * with NO credentials configured it raises a clear ``UnavailableProvider`` naming the missing
    ``env://SUPERMEMORY_API_KEY`` credential ref — so the system stays green and the correctness invariant runs offline
    on the emulator / local provider instead;
  * its ``status()`` reports ``unavailable`` WITHOUT raising, so health/catalog checks never crash.

When (later) a real network impl is wired behind this same surface, its outputs MUST still be governed
candidate MemoryArtifacts (claim_status="candidate" + external_source_handle + lineage) — a Supermemory
recall is NEVER a served/canonical fact; Supermemory is NEVER the source of truth. The contract that future
impl must honor is exactly the method surface below + the MemoryArtifact shape from the shared builder.

Stdlib only; offline; deterministic. The shape it WOULD return (had it creds) is documented for the contract.
"""
from __future__ import annotations

from typing import Any

from src.baltor.ports.memory_provider import UnavailableProvider

#: stable provider identity (matches the capability catalog adapter_id).
PROVIDER_ID = "memory.supermemory_api@candidate"

#: the credential this candidate requires — a REF, never a value. Named in the UnavailableProvider it raises.
CREDENTIAL_REF = "env://SUPERMEMORY_API_KEY"

#: status reported by status() when no credential is configured.
_STATUS_UNAVAILABLE = "unavailable"


def _credentials_present() -> bool:
    """True only if the real credential is configured. Checked via the env:// ref WITHOUT logging/echoing its
    value (a missing secret => provider unavailable, never a crash, never a leak). Uses the same posture as the
    LLM gateway's SecretsResolver but does not import it (ports/adapters stay decoupled from the gateway)."""
    import os
    assert CREDENTIAL_REF.startswith("env://")
    return bool(os.environ.get(CREDENTIAL_REF[len("env://"):], ""))


class SupermemoryApiProvider:
    """CANDIDATE Supermemory API wrapper. Satisfies MemoryProviderPort + MemoryProfileProviderPort. With no
    creds, every operation raises UnavailableProvider(env://SUPERMEMORY_API_KEY); status() reports unavailable.
    """

    provider_id = PROVIDER_ID
    credential_ref = CREDENTIAL_REF

    def _require_credentials(self) -> None:
        if not _credentials_present():
            # the correctness invariant NEVER has creds → this is the expected, green, offline-safe failure mode.
            raise UnavailableProvider(self.provider_id, CREDENTIAL_REF,
                                      "candidate contract stub: no network impl wired; use the emulator/local "
                                      "provider for the offline correctness invariant")
        # NOTE: a real network impl would go here LATER, behind this same surface. Until then the stub never
        # reaches network even if a key is set — it raises a clear not-implemented UnavailableProvider so no
        # one accidentally believes a live call happened.
        raise UnavailableProvider(self.provider_id, CREDENTIAL_REF,
                                  "credential present but the live network impl is not wired in this build "
                                  "(contract stub only; never makes network calls)")

    def write(self, request: dict[str, Any]) -> dict[str, Any]:
        """Would POST add(...) to Supermemory and return a governed candidate MemoryArtifact. Stub: raises."""
        self._require_credentials()
        raise AssertionError("unreachable")  # _require_credentials always raises in this stub

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """Would POST search(...) and return candidate MemoryArtifacts. Stub: raises UnavailableProvider."""
        self._require_credentials()
        raise AssertionError("unreachable")

    def profile(self, scope: dict[str, Any]) -> dict[str, Any]:
        """Would GET profile (static/dynamic) as candidate MemoryArtifacts. Stub: raises UnavailableProvider."""
        self._require_credentials()
        raise AssertionError("unreachable")

    def status(self) -> dict[str, Any]:
        """Report liveness WITHOUT raising. Names the env:// credential ref; never echoes a value."""
        has = _credentials_present()
        return {
            "provider_id": self.provider_id,
            "status": _STATUS_UNAVAILABLE,   # candidate stub: unavailable until a live impl is wired
            "has_credentials": has,
            "credential_ref": CREDENTIAL_REF,
            "detail": ("candidate contract stub: no network impl wired (use the emulator/local provider). "
                       f"going live requires {CREDENTIAL_REF}"),
        }


def _self_demo() -> dict[str, Any]:
    """Deterministic offline demo used by the proof: status() is green-unavailable; ops raise UnavailableProvider."""
    p = SupermemoryApiProvider()
    st = p.status()
    raised = False
    cred_named = ""
    try:
        p.search({"tenant_id": "acme", "project": "default", "query": "x"})
    except UnavailableProvider as e:
        raised = True
        cred_named = e.credential_ref
    return {"status": st, "search_raised_unavailable": raised, "credential_named": cred_named,
            "names_correct_ref": cred_named == CREDENTIAL_REF}


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    import json
    print(json.dumps(_self_demo(), indent=2, default=str))
