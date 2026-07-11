"""src.teleon.monitoring — cross-surface heartbeats + the monitoring/resolution flywheel.

Ping every surface (the local_service_registry health URLs), classify a failure (transient blip vs
persistent break), and PROPOSE a governed resolution (retry / restart / reheal / escalate) — never
auto-destroy (the owner approves destructive actions; the flywheel proposes + records, like the
self-healing seam and the exploration ladder). Tie-in: a persistent SOURCE break routes to
self_healing.reheal; a persistent SERVICE break proposes a restart; an unresolvable one escalates.
"""
from .flywheel import (Flywheel, HeartbeatResult, ResolutionProposal, classify_failure,
                       STATUS_HEALTHY, STATUS_TRANSIENT, STATUS_PERSISTENT,
                       ACTION_NONE, ACTION_RETRY, ACTION_RESTART, ACTION_REHEAL, ACTION_ESCALATE,
                       PERSISTENT_AFTER, urllib_pinger)

__all__ = ["Flywheel", "HeartbeatResult", "ResolutionProposal", "classify_failure",
           "STATUS_HEALTHY", "STATUS_TRANSIENT", "STATUS_PERSISTENT", "ACTION_NONE", "ACTION_RETRY",
           "ACTION_RESTART", "ACTION_REHEAL", "ACTION_ESCALATE", "PERSISTENT_AFTER", "urllib_pinger"]
