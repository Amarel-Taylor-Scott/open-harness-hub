"""src.teleon.tuning — the SELF-TUNING layer for the Teleon runtime: an append-only ACTION LEDGER + a
contrastive TUNER that learns from it.

The runtime makes selections (model / route / component); each is recorded as an ACTION with its outcome
(passed/failed, cost, latency, tokens) in the append-only, content-addressed ``ActionLedger`` (lossless — failures
are kept; a policy learner must learn from what did NOT work). The ``ContrastiveTuner`` reads that ledger and, by
contrasting SUCCESSFUL vs FAILED choices in SIMILAR contexts, PROPOSES selection-policy deltas ("in context X,
prefer model A over B").

GOVERNED: the tuner proposes, it never auto-applies a destructive change (``apply_delta`` refuses without explicit
human approval and is lossless when approved). Deterministic + offline; serves_truth=false. Teleon-layer — never
imports src.baltor.
"""
from src.teleon.tuning.action_ledger import (
    ACTION_ID_PREFIX,
    LEDGER_SCHEMA_VERSION,
    ActionLedger,
    ActionLedgerRejected,
    ActionRecord,
)
from src.teleon.tuning.tuner import (
    DEFAULT_MIN_PASSRATE_GAP,
    DEFAULT_MIN_SUPPORT,
    POLICY_DELTA_KIND,
    ContrastiveTuner,
    PolicyDelta,
    TunerRefused,
    WIN_COST,
    WIN_RELIABILITY,
)

__all__ = [
    "ActionLedger",
    "ActionLedgerRejected",
    "ActionRecord",
    "ACTION_ID_PREFIX",
    "LEDGER_SCHEMA_VERSION",
    "ContrastiveTuner",
    "PolicyDelta",
    "TunerRefused",
    "DEFAULT_MIN_SUPPORT",
    "DEFAULT_MIN_PASSRATE_GAP",
    "POLICY_DELTA_KIND",
    "WIN_RELIABILITY",
    "WIN_COST",
]
