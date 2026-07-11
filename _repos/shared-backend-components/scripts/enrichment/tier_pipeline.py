#!/usr/bin/env python3
"""Baltor tier orchestrator — compose the REAL processors into the three tiers.

This is the implementation the Context-Enrichment-as-a-Service spec
(``_repos/baltor/context/strategy/context-enrichment-service.md`` §"Status") names as the thing
that makes Baltor real: *"the tier pipeline (raw→compressed→hyper-efficient,
hosted + downloadable) on the shared workers."* It takes one governed object's
content and refines it into the three token-efficiency tiers, then — for every
non-raw tier — calls the **separate** fidelity evaluator so each tier ships a
*measured* quality delta, never self-graded.

It owns **no** compression logic of its own. The tiers are assembled from the
already-shipped, already-self-tested processors so the same components the
build/monitor product (OHH) mints are the components the enrichment product
(Baltor) sells:

  * **raw**            — hosted full fidelity (passthrough; the source of truth).
  * **compressed**     — ``scripts.processors.compression.structural_compress.run``
                         (``compress.structural``): strip function/method bodies,
                         keep signatures + structure. Repomix-style, ~70% on code,
                         structure-lossless.
  * **hyper_efficient**— a *further* distilled / denser form. **v1 (pragmatic,
                         stated honestly):** the structural compression run again
                         with docstrings dropped, then a deterministic
                         dedupe + whitespace-collapse pass. This is a token-only
                         reduction (it never *adds* tokens), which is what makes
                         the tier ordering provable. It is **NOT** the eventual
                         mechanism — see "Seams" below.

Per the Baltor spec's three-SKU table, the eventual hyper-efficient tier is
*"distilled facts + cache-shaped packaging"* (``memory/*`` extraction +
``cache/*`` prefix-shaping, where provider prompt-cache compounds the savings),
optionally fed by the *learned* compressor (``summarize.llmlingua`` / LLMLingua-2).
None of those exist as shipped code yet; this module wires the real structural
path now and leaves clean seams for them (see ``_hyper_efficient`` /
``HYPER_EFFICIENT_SEAMS``).

Runtime contract (declared per
``_repos/shared-backend-components/context/architecture/component-execution-and-runtime-routing.md`` §4; surfaced as
``RUNTIME`` and asserted in the self-test):

  * ``process_kind   = enrich.tier_pipeline`` — composite CPU step.
  * ``deterministic  = true``  — same input → byte-identical tiers + identical
    fidelity scores. No clocks, RNG, env reads, network, or filesystem writes.
    (Both wrapped processors are themselves deterministic; this orchestrator
    adds no nondeterminism.)
  * ``idempotent     = true``  — the structural compressor is a fixed point, so
    re-deriving a tier from its own text is stable; ``run`` is a pure function of
    its arguments.
  * ``side_effects   = none``  — pure function; reads nothing, writes nothing.
  * ``streaming      = false`` — whole-content in, whole tier set out.
  * ``latency_budget_ms = None`` — bulk/offline refinery work, not interactive →
    routes to the **cpu** pool (scale-to-zero eligible), NOT **burst**.
  * ``trust_boundary = local`` — operates only on content already inside the
    governed corpus; runs in the standard container, not the sandbox.
  * ``on_error       = raise`` — bad input raises ``TypeError`` (delegated to the
    wrapped processors); we never silently swallow.

Honest scope: the *learned*-compression and *memory/cache* mechanisms are seams,
not yet implemented. What is real and verified here is the composition + the
measured per-tier fidelity from the separate evaluator.

Public API:
    from scripts.enrichment.tier_pipeline import run
    out = run("...source...", language="python")
    # -> {
    #   "raw": str, "compressed": str, "hyper_efficient": str,
    #   "fidelity_by_tier": {"compressed": float, "hyper_efficient": float},
    #   "tokens_by_tier":   {"raw": int, "compressed": int, "hyper_efficient": int},
    #   ... (see run() docstring for the full, auditable shape)
    # }

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/enrichment/tier_pipeline.py
    python3 -m scripts.enrichment.tier_pipeline
"""
from __future__ import annotations

import re
from typing import Any

# Make the repo root importable when this file is run *directly*
# (``python3 _repos/shared-backend-components/scripts/enrichment/tier_pipeline.py``). The repo intentionally has
# no top-level ``_repos/shared-backend-components/scripts/__init__.py`` (it is a namespace package run via
# ``-m`` from the root), so a direct-file invocation has only THIS file's
# directory on ``sys.path`` and ``import scripts`` fails. Unlike the leaf
# processors this orchestrator's whole job is to COMPOSE ``scripts.processors.*``,
# so it cannot be self-contained — it must import them. Prepending the repo root
# (this file is ``<root>/scripts/enrichment/tier_pipeline.py`` → root is two
# parents up) keeps the clean package-qualified imports below working under BOTH
# ``-m`` and direct invocation. Stdlib only; no-op under ``-m`` (already on path).
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Compose the REAL shared-backend processors (they exist and are self-tested):
#   compress.structural        — strip bodies, keep signatures (the Compressed tier)
#   verify.compression_fidelity — separate evaluator (the measured delta per tier)
# We also REUSE structural_compress.count_tokens as the single token PROXY rather
# than defining a parallel tokenizer (No-Magic-Values: one definition, imported).
from scripts.processors.compression import structural_compress
from scripts.processors.verify import compression_fidelity_check

count_tokens = structural_compress.count_tokens

# ── Tier names (single source of truth; No-Magic-Values) ─────────────────────
#
# These three strings are the tier vocabulary used by the result keys, the
# fidelity map, the token map, and the runtime manifest. Defined ONCE here and
# referenced everywhere so a rename can't drift across the dict shape.

TIER_RAW = "raw"
TIER_COMPRESSED = "compressed"
TIER_HYPER_EFFICIENT = "hyper_efficient"

#: All tiers, coarsest-fidelity-last — the order the pipeline reports them in and
#: the order whose token counts must be monotone non-increasing.
TIER_ORDER: tuple[str, ...] = (TIER_RAW, TIER_COMPRESSED, TIER_HYPER_EFFICIENT)

#: The non-raw tiers — the ones that get a *measured* fidelity score (raw is the
#: reference, so scoring raw-against-raw is trivially 1.0 and not reported).
DERIVED_TIERS: tuple[str, ...] = (TIER_COMPRESSED, TIER_HYPER_EFFICIENT)

#: Honest record of what the hyper-efficient tier WILL be vs. what v1 IS. Carried
#: in the result so the seam is visible to any consumer, not buried in prose.
HYPER_EFFICIENT_SEAMS: tuple[str, ...] = (
    "learned compression — summarize.llmlingua (LLMLingua-2): token-classification "
    "compression, 2-5x (general 5-20x); plugs in as an alternative/added Compressed "
    "mechanism before this distillation pass.",
    "memory extraction — memory/* (Mem0/Hindsight): distil facts/observations rather "
    "than shrink surface form; the spec's true hyper-efficient mechanism.",
    "cache-shaped packaging — cache/*: pack the distilled tier onto a cacheable "
    "prefix so the provider prompt cache (~90% off input at a high hit rate) "
    "compounds the savings. This is where Baltor value compounds.",
)

#: process_kind for this composite step (open vocab per SPEC §16 / routing doc §4).
PROCESS_KIND = "enrich.tier_pipeline"

#: Declared runtime-routing manifest for this component. Mirrors the field→pool
#: mapping in _repos/shared-backend-components/context/architecture/component-execution-and-runtime-routing.md §4:
#: deterministic + idempotent + side_effects=none + no latency budget + local
#: trust boundary → the cheap **cpu** pool (scale-to-zero eligible). Asserted in
#: the self-test so the declaration can't silently rot.
RUNTIME: dict[str, Any] = {
    "process_kind": PROCESS_KIND,
    "deterministic": True,
    "idempotent": True,
    "side_effects": "none",
    "streaming": False,
    "latency_budget_ms": None,
    "trust_boundary": "local",
    "on_error": "raise",
    "resource_pool": "cpu",  # inferred per routing-doc §4 from the signals above
}


# ── Tier builders ─────────────────────────────────────────────────────────────


def _compressed(content: str, *, language: str | None) -> dict[str, Any]:
    """The Compressed tier: structural body-stripping via the REAL processor.

    Pure delegation to ``compress.structural`` (keep_docstrings=True — keep the
    signature *and* its leading docstring, the structural promise). Returns that
    processor's full result dict (``compressed``/``tokens_*``/``ratio``/…).
    """
    return structural_compress.run(content, language=language, keep_docstrings=True)


# A run of >=2 consecutive blank lines (after normalizing trailing whitespace).
_BLANK_RUN_RE = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")


def _dedupe_and_collapse(text: str) -> str:
    """Deterministic dedupe + whitespace collapse (token-only reduction).

    Three passes, all of which can only *remove* tokens (never add), which is
    what guarantees ``hyper_efficient`` tokens ``<=`` ``compressed`` tokens:

      1. strip trailing whitespace on every line (drops stray punctuation tokens
         the proxy would otherwise count);
      2. collapse runs of consecutive *identical* non-blank lines to one — after
         body-stripping, many sibling defs become an identical ``    ...`` line;
         a single marker conveys the same structure (dedupe);
      3. collapse runs of >=2 blank lines to a single blank line (whitespace).

    Deterministic and order-stable: a fixed left-to-right fold, no sorting of
    content, no set iteration over text. Preserves the input's final-newline
    shape so re-running is stable.
    """
    had_final_nl = text.endswith("\n")
    # Pass 1: strip trailing whitespace per line.
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Pass 2: collapse consecutive identical *non-blank* lines to one.
    deduped: list[str] = []
    for ln in lines:
        if ln != "" and deduped and deduped[-1] == ln:
            continue
        deduped.append(ln)

    out = "\n".join(deduped)
    # Pass 3: collapse >=2 blank lines to exactly one.
    out = _BLANK_RUN_RE.sub("\n\n", out)
    # Trim leading/trailing blank lines, then restore the original final-NL shape.
    out = out.strip("\n")
    if had_final_nl and out:
        out += "\n"
    return out


def _hyper_efficient(content: str, *, language: str | None) -> dict[str, Any]:
    """The Hyper-efficient tier — v1 (pragmatic; stated honestly).

    **v1 mechanism:** structural compression with docstrings *dropped*
    (``keep_docstrings=False`` — denser than the Compressed tier, which keeps
    them), followed by ``_dedupe_and_collapse``. Both steps are strictly
    token-reducing, so this tier is always ``<=`` the Compressed tier in tokens —
    the orderable, provable behavior the self-test asserts.

    **What it is NOT (the seam):** the spec's hyper-efficient tier is *distilled
    facts + cache-shaped packaging* (``memory/*`` + ``cache/*``), optionally fed
    by the *learned* compressor (``summarize.llmlingua``). Those mechanisms are
    not yet shipped; see ``HYPER_EFFICIENT_SEAMS``. v1 deliberately reuses the
    one real compression component we have rather than inventing an unverified
    one, and leaves the contract (``run`` shape, tier keys) unchanged for the
    upgrade.

    Returns a result dict shaped like the structural processor's, with the dense
    text under ``compressed`` plus recomputed token/ratio fields and a ``seams``
    note. (Computing ratio off the SAME ``count_tokens`` proxy keeps one
    definition of "token" across the whole pipeline.)
    """
    structural = structural_compress.run(content, language=language, keep_docstrings=False)
    dense = _dedupe_and_collapse(structural["compressed"])

    tokens_in = count_tokens(content)
    tokens_out = count_tokens(dense)
    ratio = 0.0 if tokens_in == 0 else round(1.0 - (tokens_out / tokens_in), 6)
    return {
        "compressed": dense,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "ratio": ratio,
        "language": structural["language"],
        "definitions_stripped": structural["definitions_stripped"],
        "method": "v1: compress.structural(keep_docstrings=False) + dedupe/whitespace-collapse",
        "seams": list(HYPER_EFFICIENT_SEAMS),
    }


# ── Public entrypoint ─────────────────────────────────────────────────────────


def run(content: str, *, language: str | None = None) -> dict[str, Any]:
    """Refine ``content`` into the three Baltor tiers, with measured fidelity.

    Args:
      content:  the governed object's full-fidelity text. Required, ``str``.
      language: optional language hint forwarded to ``compress.structural``
        (``"python"`` / ``"js"`` / ``"ts"`` / ``"text"`` / …). When omitted, the
        structural processor auto-detects from the content.

    Returns a dict whose **headline keys are exactly the four the orchestrator
    contract names** plus auditable detail:

      ``raw``              — the passthrough source of truth (== ``content``).
      ``compressed``       — the Compressed-tier text (structural body-strip).
      ``hyper_efficient``  — the Hyper-efficient-tier text (v1, see above).
      ``fidelity_by_tier`` — ``{tier: float in [0,1]}`` for each DERIVED tier,
                             scored by the **separate** evaluator
                             (``verify.compression_fidelity``) against ``raw``.
      ``tokens_by_tier``   — ``{tier: int}`` proxy-token count for every tier
                             (raw included); monotone non-increasing across
                             ``TIER_ORDER`` for code (the orderable property).
      ``fidelity_detail``  — full evaluator result per derived tier (verdict,
                             retained/dropped signals, per-class recall) so the
                             score is auditable, not a black box.
      ``language``         — the language the structural processor actually used.
      ``runtime``          — the declared routing manifest (``RUNTIME``).
      ``tiers``            — ordered tier names (``TIER_ORDER``) for consumers.

    Raises:
      TypeError: on non-``str`` ``content`` (delegated to the wrapped
        processors — the ``on_error: raise`` contract).

    Deterministic, pure, no side effects.
    """
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")

    raw = content
    compressed_res = _compressed(content, language=language)
    hyper_res = _hyper_efficient(content, language=language)

    tier_text = {
        TIER_RAW: raw,
        TIER_COMPRESSED: compressed_res["compressed"],
        TIER_HYPER_EFFICIENT: hyper_res["compressed"],
    }

    # Measured fidelity per DERIVED tier from the SEPARATE evaluator — raw is the
    # reference both tiers are graded against, so a compressor can never grade its
    # own homework (the whole point of compression_fidelity_check living apart).
    fidelity_by_tier: dict[str, float] = {}
    fidelity_detail: dict[str, dict[str, Any]] = {}
    for tier in DERIVED_TIERS:
        result = compression_fidelity_check.run(raw, tier_text[tier])
        fidelity_by_tier[tier] = result["fidelity"]
        fidelity_detail[tier] = result

    tokens_by_tier = {tier: count_tokens(tier_text[tier]) for tier in TIER_ORDER}

    return {
        # ── the four headline keys the orchestrator contract names ──
        TIER_RAW: raw,
        TIER_COMPRESSED: tier_text[TIER_COMPRESSED],
        TIER_HYPER_EFFICIENT: tier_text[TIER_HYPER_EFFICIENT],
        "fidelity_by_tier": fidelity_by_tier,
        "tokens_by_tier": tokens_by_tier,
        # ── auditable detail / provenance ──
        "fidelity_detail": fidelity_detail,
        "language": compressed_res["language"],
        "tiers": list(TIER_ORDER),
        "runtime": dict(RUNTIME),
    }


# ── Self-test (proves the composition on a real multi-function sample) ────────

# A real multi-function Python module: substantive bodies (the case structural
# compression is *for*), a module docstring, imports, a decorator, a multi-line
# signature, methods, AND repeated structure (sibling getters) so the
# hyper-efficient dedupe pass has something real to collapse.
_PY_SAMPLE = '''\
"""Token-budget planner for the Baltor serving path."""
import math
from typing import Any


DEFAULT_BUDGET = 8000
SAFETY_MARGIN = 0.1


def plan_budget(window: int, *, reserve: int = 0) -> int:
    """Return the usable token budget for a window."""
    usable = window - reserve
    usable = int(usable * (1.0 - SAFETY_MARGIN))
    if usable < 0:
        raise ValueError("reserve exceeds window")
    return usable


class TierStore:
    """Holds the three tiers for one governed object."""

    def __init__(self, object_id: str) -> None:
        self.object_id = object_id
        self._raw = ""
        self._compressed = ""
        self._hyper = ""

    def set_raw(self, text: str) -> None:
        self._raw = text

    def set_compressed(self, text: str) -> None:
        self._compressed = text

    def set_hyper(self, text: str) -> None:
        self._hyper = text

    def fits(
        self,
        tier: str,
        window: int,
    ) -> bool:
        # multi-line signature above must survive the structural tier
        budget = plan_budget(window)
        text = getattr(self, "_" + tier, "")
        return len(text.split()) <= budget
'''


def _selftest() -> None:
    out = run(_PY_SAMPLE, language="python")

    # ── Headline contract: the four named keys + the two maps are present. ──
    for key in (TIER_RAW, TIER_COMPRESSED, TIER_HYPER_EFFICIENT,
                "fidelity_by_tier", "tokens_by_tier"):
        assert key in out, f"missing headline key: {key!r}"

    raw_t = out["tokens_by_tier"][TIER_RAW]
    comp_t = out["tokens_by_tier"][TIER_COMPRESSED]
    hyper_t = out["tokens_by_tier"][TIER_HYPER_EFFICIENT]

    # ── Tokens STRICTLY decrease raw > compressed >= hyper_efficient. ──
    # Strict raw>compressed holds because the sample's bodies dwarf signatures
    # (the case structural compression is for); hyper<=compressed is guaranteed
    # by construction (docstrings dropped + token-only dedupe/collapse).
    assert raw_t > comp_t, f"expected raw>compressed tokens, got {raw_t} !> {comp_t}"
    assert comp_t >= hyper_t, f"expected compressed>=hyper tokens, got {comp_t} < {hyper_t}"
    # And the hyper tier must be a STRICT further reduction here (docstrings +
    # repeated sibling setters give it real tokens to drop) — proving it's a
    # distinct, denser tier, not a copy of Compressed.
    assert hyper_t < comp_t, f"expected hyper<compressed (denser tier), got {hyper_t} !< {comp_t}"

    # ── raw passthrough is exactly the input. ──
    assert out[TIER_RAW] == _PY_SAMPLE, "raw tier must be the unchanged input"

    # ── Compressed tier kept signatures, dropped bodies (sanity on the real proc). ──
    comp_text = out[TIER_COMPRESSED]
    for needle in ("def plan_budget(window: int, *, reserve: int = 0) -> int:",
                   "class TierStore:", "def fits("):
        assert needle in comp_text, f"compressed tier lost signature: {needle!r}"
    assert "usable = window - reserve" not in comp_text, "compressed tier kept a body line"

    # ── Hyper tier is denser: docstrings gone, structure still parses-ish. ──
    hyper_text = out[TIER_HYPER_EFFICIENT]
    assert '"""Return the usable token budget for a window."""' not in hyper_text, \
        "hyper tier should have dropped function docstrings"
    assert "def plan_budget(" in hyper_text, "hyper tier lost the signatures"

    # ── Fidelity reported in [0,1] for EACH derived tier. ──
    fid = out["fidelity_by_tier"]
    assert set(fid) == set(DERIVED_TIERS), f"fidelity must cover exactly {DERIVED_TIERS}"
    for tier, score in fid.items():
        assert isinstance(score, (int, float)), f"{tier} fidelity not numeric: {score!r}"
        assert 0.0 <= score <= 1.0, f"{tier} fidelity out of [0,1]: {score}"
    # The structural Compressed tier should preserve signatures well → decent
    # fidelity; assert it's clearly non-trivial (not a gutted score).
    assert fid[TIER_COMPRESSED] >= 0.5, \
        f"structural compressed fidelity unexpectedly low: {fid[TIER_COMPRESSED]}"

    # ── Determinism: a re-run is byte-identical (all tiers + all scores). ──
    out2 = run(_PY_SAMPLE, language="python")
    assert out2 == out, "tier pipeline is not deterministic (re-run differed)"

    # ── _dedupe_and_collapse is itself idempotent + token-only (defensive). ──
    once = _dedupe_and_collapse(hyper_text)
    assert _dedupe_and_collapse(once) == once, "dedupe/collapse is not idempotent"
    assert count_tokens(once) <= count_tokens(hyper_text), "collapse added tokens"

    # ── Runtime manifest is the declared one and self-consistent w/ the routing doc. ──
    rt = out["runtime"]
    assert rt["deterministic"] is True and rt["idempotent"] is True
    assert rt["side_effects"] == "none"
    assert rt["streaming"] is False and rt["latency_budget_ms"] is None
    assert rt["trust_boundary"] == "local"
    # deterministic + idempotent + side_effects=none + no latency budget + local
    # trust boundary ⇒ the cheap cpu pool (NOT burst/gpu/sandbox) per routing §4.
    assert rt["resource_pool"] == "cpu", f"routing pool mismatch: {rt['resource_pool']}"

    # ── Non-str input raises (on_error=raise, delegated to the processors). ──
    raised = False
    try:
        run(123)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str content must raise TypeError"

    # ── Graceful degradation: prose has no code structure → tiers collapse to
    #    raw==compressed in tokens; the pipeline must NOT crash and fidelity must
    #    still be reported in range (honest about where the order is only >=).
    prose = "This is a plain paragraph. It carries no code structure whatsoever.\n"
    pout = run(prose)
    p = pout["tokens_by_tier"]
    assert p[TIER_RAW] >= p[TIER_COMPRESSED] >= p[TIER_HYPER_EFFICIENT], \
        "prose token order must be non-increasing"
    for score in pout["fidelity_by_tier"].values():
        assert 0.0 <= score <= 1.0

    print(
        "PASS — tier_pipeline: "
        f"tokens raw={raw_t} > compressed={comp_t} > hyper={hyper_t}; "
        f"fidelity compressed={fid[TIER_COMPRESSED]:.3f} "
        f"hyper={fid[TIER_HYPER_EFFICIENT]:.3f} (both in [0,1], separate evaluator); "
        "deterministic re-run identical; runtime=cpu pool; "
        "prose degrades gracefully. (hyper tier is v1 — LLMLingua/memory/cache seams noted)"
    )


if __name__ == "__main__":
    _selftest()
