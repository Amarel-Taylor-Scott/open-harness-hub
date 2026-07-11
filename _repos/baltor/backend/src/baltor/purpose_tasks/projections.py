"""src.baltor.purpose_tasks.projections — RE-EXPORT SHIM (lossless extraction -> Teleon).

PurposeTask is a Teleon concept (purpose/capability-provisioned self-adapting execution units; _repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status, step 3). The whole subsystem now lives in src.teleon.purpose_tasks; this shim re-exports its full accessed surface so the check_purpose_task_* / check_runtime_class_binding / check_adaptation_ladder / check_octs_conformance proofs keep working with NO duplicate runtime. Baltor -> Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.purpose_tasks.projections import (
    CUSTOMER_EVAL_FIELDS, CUSTOMER_RUN_FIELDS, CUSTOMER_SPEC_FIELDS, STAFF_ONLY_FORBIDDEN_IN_CUSTOMER,
    customer_projection, customer_view_is_clean, staff_projection,
)

__all__ = ["staff_projection", "customer_projection", "customer_view_is_clean",
           "CUSTOMER_SPEC_FIELDS", "CUSTOMER_RUN_FIELDS", "STAFF_ONLY_FORBIDDEN_IN_CUSTOMER",
           "CUSTOMER_EVAL_FIELDS"]
