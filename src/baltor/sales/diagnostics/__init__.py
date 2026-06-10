"""src.baltor.sales.diagnostics — mode-aware sales diagnostics.

A diagnostic runs under a CONFIGURABLE engagement mode (architecture/sales_diagnostic_modes.json) that decides
which authorization bases are permitted and whether a live third-party probe is allowed. The runner enforces the
mode (composing the claim_guard authorization check); the tools themselves never hard-code a posture. Offline +
deterministic; the live-probe path is a labeled seam (no network here).
"""
from .runner import load_modes, resolve_mode, start_diagnostic
from .chatbot_guardrail_audit import audit_transcript, load_risk_rules

__all__ = ["load_modes", "resolve_mode", "start_diagnostic", "audit_transcript", "load_risk_rules"]
