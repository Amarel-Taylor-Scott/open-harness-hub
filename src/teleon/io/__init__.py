"""src.teleon.io — shared command/work I/O projectors for the Shared I/O Spine.

Pure functions that project a durable-runtime task record (the FleetLedger CapabilityTask shape) into the typed
work-I/O contracts: WorkItem (= CapabilityTask), WorkerClaim, AckNackReceipt, DeadLetterEntry, IdempotencyKey.
They take plain dicts, so this module imports NOTHING from src.baltor — the durable runtime (currently in
src/baltor/workers, extracting toward src/teleon) keeps producing these shapes; this layer just names them.
"""
from .work_io import (project_work_item, project_worker_claim, project_ack_nack_receipt,
                      project_dead_letter, project_idempotency_key, WORK_ITEM_CORE_FIELDS)
from .event_io import project_event_envelope, redact_secrets
from .inference_io import make_inference_request, project_route_decision

__all__ = ["project_work_item", "project_worker_claim", "project_ack_nack_receipt",
           "project_dead_letter", "project_idempotency_key", "WORK_ITEM_CORE_FIELDS",
           "project_event_envelope", "redact_secrets",
           "make_inference_request", "project_route_decision"]
