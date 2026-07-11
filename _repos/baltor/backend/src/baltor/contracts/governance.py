"""contracts/governance — governed claim-status vocabulary (single source).

The load-bearing rule across Baltor: memory / research-agent / extractor output is a CANDIDATE, never a
served fact. The token for that status was previously defined independently in several modules
(ports.memory_provider, ports.research_agent_provider, contextops.extractor_snippets), inviting drift.
It lives here ONCE; everything imports it. ``contracts`` is the lowest layer (ports/adapters/runtime may
import it), so this is the boundary-safe home. Changing the token here changes it everywhere — no magic value.
"""
from __future__ import annotations

#: the claim_status a not-yet-promoted artifact carries — a proposal/evidence signal, never a served fact.
CANDIDATE_CLAIM_STATUS = "candidate"

__all__ = ["CANDIDATE_CLAIM_STATUS"]
