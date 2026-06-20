"""src.teleon.self_healing — detect when a capability SILENTLY breaks because an external source
changed, and heal it (the owner's pain: scrapers / fact-checkers that keep running but return
garbage when a site or source-API moves). Built ON the proven self-heal engine
(src.teleon.purpose_tasks.purpose_task: provision / run_current / evaluate_health / adapt /
rollback) — this is the SOURCE-CHANGE trigger + the benchmark-as-health-check that engine lacked.
"""
from .reheal import (HealOutcome, benchmark_health, reheal_on_source_change,
                     capabilities_depending_on, HEAL_STATUS_HEALTHY, HEAL_STATUS_HEALED,
                     HEAL_STATUS_DEGRADED, HEAL_STATUS_NO_BENCHMARK, NEXT_RUNG)

__all__ = ["HealOutcome", "benchmark_health", "reheal_on_source_change", "capabilities_depending_on",
           "HEAL_STATUS_HEALTHY", "HEAL_STATUS_HEALED", "HEAL_STATUS_DEGRADED",
           "HEAL_STATUS_NO_BENCHMARK", "NEXT_RUNG"]
