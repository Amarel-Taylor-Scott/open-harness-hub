"""src.baltor.purpose_tasks.runtime_binding — RE-EXPORT SHIM (lossless extraction -> Teleon).

PurposeTask is a Teleon concept (purpose/capability-provisioned self-adapting execution units; _repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status, step 3). The whole subsystem now lives in src.teleon.purpose_tasks; this shim re-exports its full accessed surface so the check_purpose_task_* / check_runtime_class_binding / check_adaptation_ladder / check_octs_conformance proofs keep working with NO duplicate runtime. Baltor -> Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.purpose_tasks.runtime_binding import (
    bind, bind_allowed, class_record, class_vendor_backends, eligible_backends_for_classes,
    is_known_class, local_fallback_backend, offline_default_backend, resolve_for_spec,
)

__all__ = ["bind", "bind_allowed", "resolve_for_spec", "eligible_backends_for_classes",
           "offline_default_backend", "class_record", "is_known_class", "class_vendor_backends",
           "local_fallback_backend"]
