"""contextops — the Baltor ContextOps Verification Foundry runtime home (lean core).

DETECT fragile/conflicting/stale/under-supported context -> bounded agents DISCOVER sources & methods ->
convert to DETERMINISTIC SourceRecipes + VerificationRecipes + sandboxed extractor candidates -> reliability
+ cross-source confirmation -> a visible cost ladder. THE INVARIANT: agents DISCOVER and PROPOSE; Baltor
STORES, VERIFIES, RECONCILES, PROVES, CONSUMES. Contracts live under schemas/contextops/*.v1; the typed ports
live under src/baltor/ports/research_agent_provider.py. See prompts/baltor-contextops-verification-foundry.md."""

from src.baltor.contextops.triage import (  # noqa: F401
    TRIAGE_LANES,
    ContextTriageClassifier,
    ContextTriageResult,
)

__all__ = ["ContextTriageClassifier", "ContextTriageResult", "TRIAGE_LANES"]
