"""src.teleon.verticals — concrete vertical pipelines built on the Teleon compiler + Baltor governance.

provider_directory: a repeatable, cost-efficient provider/practice directory freshness pipeline (the healthcare-admin
adjacent vertical — directory data only, NOT insurance). Deterministic-first (NPI checksum, normalization, matching,
source-agreement confidence resolve the bulk; an LLM is the last rung for the ambiguous residual); governed (every change
is a serves_truth=false candidate scored by confidence; high-confidence auto-updates, conflicts go to human review; full
provenance/audit trail; honest-MISSING). Synthetic/public metadata only.
"""

__all__ = ["provider_directory"]
