"""observability/tracing — see the layer README + _repos/shared-backend-components/architecture/project_spine.json for what belongs here.

Exposes the OBSERVABILITY PROVIDER seam: ContextOperationSpan/SpanTree records, the ObservabilityProvider
port, and the wired local stub. Providers DESCRIBE; Baltor proofs/receipts stay the authority.
"""
from src.baltor.observability.tracing.provider import (  # noqa: F401
    BaltorLocalObservability,
    ContextOperationSpan,
    ObservabilityProvider,
    SpanTree,
)

__all__ = ["ContextOperationSpan", "SpanTree", "ObservabilityProvider", "BaltorLocalObservability"]
