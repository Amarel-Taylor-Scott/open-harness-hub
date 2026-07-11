"""src/baltor/experiments/boundary_approval — RE-EXPORT SHIM (lossless extraction → Teleon).

The human-approval gate for BOUNDARY EXPANSION now lives in its canonical Teleon home
``src.teleon.experiments.boundary_approval`` (boundary approvals are a Teleon-owned surface per
_repos/shared-backend-components/architecture/portfolio_dependency_law.json + the Teleon Agent Capability Gateway). This shim re-exports its
full accessed surface (``mint_human_approval_receipt`` / ``gate_boundary_expansion`` / ``BOUNDARY_KINDS``) so
check_eval_promotion_io (``from src.baltor.experiments import boundary_approval as BA``) keeps working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.experiments.boundary_approval import (
    BOUNDARY_KINDS,
    gate_boundary_expansion,
    mint_human_approval_receipt,
)

__all__ = ["mint_human_approval_receipt", "gate_boundary_expansion", "BOUNDARY_KINDS"]
