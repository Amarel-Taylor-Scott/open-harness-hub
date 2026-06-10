"""scripts.repo_intel — GitHub Signal Flywheel / Repo Intelligence Agent (governed intake layer).

Reviews top GitHub repos, classifies them into the right portfolio hub, scores trend + fit + risk, and emits a
governed intake DECISION + a weekly report. Hard law: **discovery is not trust · stars are not proof · trend ≠
fit ≠ activation.** A repo can never become an active skill/tool/harness/template/context/Teleon/Baltor
integration here — the strongest outcome is a *candidate* with a proof_to_promote ladder. Weekly star-growth is
computed from STORED snapshots, never a scraped delta. Reuses scripts/acquisition/github_repo_harvester.py as
the live source adapter (not reinvented); the offline fixture is the golden path.
"""
from .engine import (repo_id, append_snapshot, snapshots_for, compute_trend, classify, trend_score, fit_score,
                     risk, intake_decision, weekly_report, load_fixture, DECISIONS, DEFAULT_STORE)

__all__ = ["repo_id", "append_snapshot", "snapshots_for", "compute_trend", "classify", "trend_score",
           "fit_score", "risk", "intake_decision", "weekly_report", "load_fixture", "DECISIONS", "DEFAULT_STORE"]
