"""teleon.observer — the AI-usage observability + optimization layer (a thin FRONT-END over the existing engine).

The Observer watches how a human/agent uses AI and makes it progressively cheaper: it catches reinvention
(grounded in the federation), waste (oversized/duplicate context, frontier-for-trivial), and missed deterministic
paths — then surfaces a notice/question/cheaper-route. It is NOT a new engine; it reuses
`registry.reinvention_guard` (the "this already exists" catch), the registry federation (grounding/the moat), the
`evolution.descent` (the cheaper path), and `economics` ($ wasted).

This package is the SAME engine at different points on the WHEN axis (post-session review -> ambient -> post-action
-> pre-action -> cross-session analytics). `review` is the post-session mode: the non-invasive adoption wedge.
serves_truth=false; findings are governed CANDIDATES a human triages (discovery != trust).
"""
from .review import REVIEW_VERSION, review_session
from .agentic import loop_signals, monitor_step, review_agentic_run

__all__ = ["review_session", "REVIEW_VERSION", "review_agentic_run", "monitor_step", "loop_signals"]
