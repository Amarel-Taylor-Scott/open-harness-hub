"""src.teleon.objectives — capability-level OBJECTIVE policy: prioritize cost / latency / LLM-usage /
determinism / accuracy, measured per implementation (MetricVector) and resolved by a traceable, deterministic
selection. Teleon's logic uses this to pick AND adapt a capability unit's implementation per what the tenant/
task prioritizes — composing above OIPS (inference routing) and the execution-backend selector (backend cost)."""
from src.teleon.objectives.objective import (
    HIGHER_IS_BETTER,
    LOWER_IS_BETTER,
    OBJECTIVE_DIMENSIONS,
    PRESETS,
    CapabilityObjective,
    MetricVector,
    ObjectiveError,
    select,
)
from src.teleon.objectives.telemetry import RunLedger, RunObservation, TelemetryError
from src.teleon.objectives.tenant_binding import (
    DEFAULT_OBJECTIVE_PRESET,
    bound_tenants,
    objective_for_tenant,
)

__all__ = [
    "CapabilityObjective", "MetricVector", "ObjectiveError", "select", "PRESETS",
    "OBJECTIVE_DIMENSIONS", "LOWER_IS_BETTER", "HIGHER_IS_BETTER",
    "RunLedger", "RunObservation", "TelemetryError",
    "objective_for_tenant", "bound_tenants", "DEFAULT_OBJECTIVE_PRESET",
]
