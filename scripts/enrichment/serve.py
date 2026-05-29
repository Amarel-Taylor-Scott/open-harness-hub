#!/usr/bin/env python3
"""CEaaS SERVE — render one governed corpus into the agent consumption surfaces.

This is **M3** of the north-star wave: *serve a governed corpus into an agent via
the consumption surfaces.* The build/monitor product (OHH) mints + scores a
governed object once; CEaaS serves that **same** object into whatever the user's
agent ingests. Per the CEaaS dogfood case study
(``docs/case-studies/ceaas-context-for-claude-code.md`` §3) and the standards
audit's drift-#1 remediation (``docs/strategy/standards-conformance-audit.md`` §3
— *"Implement … emit_llms_txt … the deterministic and cheap one … is the natural
first cut"*), this module ships the two **freezable / contract** surfaces:

  1. ``emit_llms_txt(corpus)``  — the no-integration surface. Renders the governed
     corpus as a spec-conformant ``llms.txt`` (links-only) or ``llms-full.txt``
     (content inlined) string. Download it or paste it into any agent; works on
     any subscription. This is the ``deliver.llms_txt`` processor the catalog
     (``catalog/processors/deliver/emit-llms-txt.yaml``) declared but never
     implemented — the dangling impl the audit flagged.
  2. ``serve_descriptor(corpus, tools)`` — the MCP-style serving descriptor: the
     tool/resource manifest an MCP client (Claude Code / Cursor / cline) would
     mount. This is the ``deliver.mcp_serve`` *contract* — a **dict, the
     skeleton**, NOT a live server. The live MCP endpoint that actually answers
     ``tools/call`` over stdio is the **seam** (see ``SERVE_SEAMS``); we emit the
     descriptor honestly and mark the wire as unbuilt.

And the tier-selection glue:

  3. ``negotiate_tier(request)`` — pick ``raw`` / ``compressed`` / ``hyper_efficient``
     from a budget/latency hint by actually running ``tier_pipeline.run`` on the
     corpus content and choosing the **densest tier that fits the budget** (or the
     latency-shaped tier when latency is the binding hint). The chosen tier ships
     the **measured fidelity record** straight from the tier pipeline's *separate*
     evaluator — never self-graded.

``run(corpus, tools, request)`` ties all three together into one serving result.

What is REAL here vs. the SEAM (honest, per the change-verification contract,
``docs/codex/change-verification-contract.md`` — *"real vs spec; no invented
metrics/authority; mark offline-fixture vs live-seam clearly"*):

  * REAL: the llms.txt rendering + spec-conformance, the tier negotiation logic
    (it calls the real ``tier_pipeline``, which calls the real structural
    compressor + the real separate fidelity evaluator), and the descriptor's
    structure/provenance carriage. All deterministic, pure-stdlib, no network.
  * SEAM (not faked): the *live* MCP server endpoint (the process that speaks
    JSON-RPC over stdio); per-request *metering*; the *learned*-compression and
    *memory/cache* hyper-efficient mechanisms (those live behind
    ``tier_pipeline.HYPER_EFFICIENT_SEAMS``); and freshness/CDC re-serving. The
    descriptor declares these as ``seams`` so a consumer can see the contract is
    a skeleton, not a running wire.

The CORPUS shape (a plain dict — no new dependency, no new class):
    {
      "corpus_id":   str,                 # stable id of the governed object
      "title":       str,                 # human title (becomes the llms.txt H1)
      "summary":     str,                 # one-line blockquote summary (optional)
      "license":     str,                 # SPDX id (optional; carried as provenance)
      "documents": [                      # the governed slices
        {
          "doc_id":     str,
          "title":      str,
          "url":        str,              # canonical/source link (the provenance anchor)
          "content":    str,              # full-fidelity text (the raw tier source)
          "section":    str,              # optional llms.txt section bucket (default "Docs")
          "notes":      str,              # optional one-line note for the link
          "lifecycle":  str,              # optional: experimental|active|… (carried through)
          "provenance": {...},            # optional per-doc provenance (signer/source/updated…)
        }, ...
      ],
      "provenance": {                     # optional corpus-level provenance
        "signer":  str,                   # accountable oracle/publisher (or None)
        "source":  str,                   # where the corpus came from
        "updated": str,                   # last-refresh marker (string; no clock read here)
        "freshness": str,                 # e.g. "tracks main" / "CDC" (a seam note, honest)
      },
    }

Runtime contract (declared per
``docs/architecture/component-execution-and-runtime-routing.md`` §4; surfaced as
``RUNTIME`` and asserted in the self-test):

  * ``process_kind   = deliver.serve``  — composite serving/rendering step.
  * ``deterministic  = true``  — same (corpus, tools, request) → byte-identical
    llms.txt + identical descriptor + identical negotiated tier & fidelity. No
    clocks, RNG, env reads, network, or filesystem writes. (The composed tier
    pipeline is itself deterministic; this layer adds none.)
  * ``idempotent     = true``  — pure function of its arguments; re-serving is
    stable.
  * ``side_effects   = none``  — emits strings/dicts; reads nothing, writes
    nothing. (The ``deliver.*`` *process_kind* normally implies an external
    push; here we emit only the **artifact + descriptor**, so the side-effect is
    deferred to the SEAM that actually serves. Stated honestly.)
  * ``streaming      = false`` — whole corpus in, whole surface out.
  * ``latency_budget_ms = None`` — rendering/negotiation is bulk/offline refinery
    work → routes to the **cpu** pool (scale-to-zero eligible), NOT **burst**.
    (The negotiation *consumes* a latency hint to pick a tier; it does not itself
    have an interactive budget.)
  * ``trust_boundary = local`` — operates only on content already inside the
    governed corpus; runs in the standard container, not the sandbox.
  * ``on_error       = raise`` — bad input raises ``TypeError`` / ``ValueError``;
    we never silently emit a malformed surface.

Public API:
    from scripts.enrichment.serve import (
        emit_llms_txt, negotiate_tier, serve_descriptor, run,
    )
    text = emit_llms_txt(corpus)                       # llms.txt string
    full = emit_llms_txt(corpus, full=True)            # llms-full.txt (content inlined)
    neg  = negotiate_tier({"corpus": corpus, "budget_tokens": 2000})
    desc = serve_descriptor(corpus, tools)             # MCP-style descriptor dict
    out  = run(corpus, tools=tools, request={"budget_tokens": 2000})

CLI / self-test:
    python3 scripts/enrichment/serve.py
    python3 -m scripts.enrichment.serve
"""
from __future__ import annotations

from typing import Any

# Make the repo root importable when this file is run *directly*
# (``python3 scripts/enrichment/serve.py``). The repo intentionally has no
# top-level ``scripts/__init__.py`` (namespace package run via ``-m`` from the
# root), so a direct-file invocation has only THIS file's directory on
# ``sys.path`` and ``import scripts`` fails. This module's job is to COMPOSE the
# real ``scripts.enrichment.tier_pipeline`` + ``scripts.emit.mcp_server`` helpers,
# so it must import them. Prepending the repo root (this file is
# ``<root>/scripts/enrichment/serve.py`` → root is two parents up) keeps the
# clean package-qualified imports working under BOTH ``-m`` and direct
# invocation. Stdlib only; no-op under ``-m`` (already on path). Mirrors the
# identical guard in ``tier_pipeline.py``.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Compose the REAL tier pipeline (raw→compressed→hyper-efficient + measured
# fidelity). We REUSE its tier-name constants as the single source of truth so
# the negotiated-tier vocabulary can't drift from the pipeline's keys
# (No-Magic-Values). We also REUSE its ``count_tokens`` as the ONE token proxy.
from scripts.enrichment import tier_pipeline
from scripts.enrichment.tier_pipeline import (
    DERIVED_TIERS,
    TIER_COMPRESSED,
    TIER_HYPER_EFFICIENT,
    TIER_ORDER,
    TIER_RAW,
    count_tokens,
)

# REUSE the repo's MCP tool-name normalizer so descriptor tool names match the
# names the real MCP emitter (``scripts/emit/mcp_server.py``) produces. One
# definition of "how a component id becomes an MCP tool name", imported.
from scripts.emit.mcp_server import mcp_name

# ── Constants (single source of truth; No-Magic-Values) ──────────────────────

#: process_kind for this composite serving step (open vocab per SPEC §16 /
#: routing doc §4). ``deliver.*`` family — same prefix the catalog uses for the
#: two surfaces this module implements (``deliver.llms_txt`` / ``deliver.mcp_serve``).
PROCESS_KIND = "deliver.serve"

#: The MCP protocol revision this descriptor is shaped for. Mirrors the pin the
#: real emitter uses (``scripts/emit/mcp_server.py`` docstring) so the contract
#: and the eventual live server agree on the wire version. One pin, referenced.
MCP_PROTOCOL_VERSION = "2025-11-25"

#: Default llms.txt section bucket for documents that don't name one. The
#: llms.txt spec groups links under ``##`` headers; "Docs" is the conventional
#: primary bucket.
DEFAULT_SECTION = "Docs"

#: Section name the spec treats specially: links a verbose agent MAY skip.
#: Rendered LAST, after all other sections, per the convention.
OPTIONAL_SECTION = "Optional"

#: When a request gives no budget/latency hint at all, serve the safe default:
#: full fidelity (``raw``). An agent that asked for nothing gets the source of
#: truth, not a silently-lossy tier.
DEFAULT_TIER = TIER_RAW

#: Latency-hint → tier mapping (honest, coarse, stated). A *tight* latency budget
#: favors the densest/cheapest-to-emit tier (fewer tokens → faster downstream
#: model call); a *loose* one can afford raw. These are selection *hints*, not
#: measured per-tier serve latencies (we have not measured those — that's a
#: meter seam), so the mapping is deliberately a small, documented step function.
LATENCY_FAST_MS = 200      # "interactive" — pick the densest tier
LATENCY_RELAXED_MS = 2000  # "batch-ish" — raw is fine above this

#: Honest record of what is a running wire vs. a contract skeleton. Carried in
#: the descriptor + the serving result so the seam is visible to any consumer,
#: never buried in prose. (The hyper-efficient *mechanism* seams live on the tier
#: pipeline itself — ``tier_pipeline.HYPER_EFFICIENT_SEAMS`` — and are surfaced
#: through the tier record, so they are not duplicated here.)
SERVE_SEAMS: tuple[str, ...] = (
    "live MCP endpoint — this descriptor is the tool/resource CONTRACT (a dict an "
    "MCP client would mount); the process that actually speaks JSON-RPC tools/call "
    "over stdio is not started here. Wire it with scripts/emit/mcp_server.py's "
    "generated server stub (dist/mcp/server.py) pointed at these handlers.",
    "metering — per-request token/fidelity metering (the recurring-revenue meter) "
    "is declared in the descriptor's billing block but not enforced here; it is the "
    "CEaaS meter seam (services/registry.yaml enrichment service is status: planned).",
    "freshness/CDC — re-serving when the governed corpus changes (the recurring "
    "obligation that makes the live tier non-freezable) is a seam; this call serves "
    "a point-in-time snapshot of the corpus passed in.",
)

#: Declared runtime-routing manifest for this component. deterministic +
#: idempotent + side_effects=none + no latency budget + local trust boundary →
#: the cheap **cpu** pool (scale-to-zero eligible). Asserted in the self-test so
#: the declaration can't silently rot. Mirrors ``tier_pipeline.RUNTIME``.
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


# ── Corpus access helpers (tolerant readers over the dict contract) ──────────


def _require_corpus(corpus: Any) -> dict[str, Any]:
    """Validate the corpus is the dict contract; raise on a malformed shape.

    Honest failure (``on_error: raise``): a serving surface built from a
    malformed corpus is worse than no surface, so we refuse rather than emit
    something plausible-but-wrong.
    """
    if not isinstance(corpus, dict):
        raise TypeError(f"corpus must be a dict, got {type(corpus).__name__}")
    if "corpus_id" not in corpus or not str(corpus.get("corpus_id", "")).strip():
        raise ValueError("corpus must carry a non-empty 'corpus_id'")
    docs = corpus.get("documents", [])
    if not isinstance(docs, list):
        raise TypeError("corpus['documents'] must be a list")
    return corpus


def _documents(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the corpus documents as dicts, skipping non-dict entries."""
    return [d for d in corpus.get("documents", []) if isinstance(d, dict)]


def _doc_content(doc: dict[str, Any]) -> str:
    """Full-fidelity text of one document (tolerant of the common key spellings)."""
    for key in ("content", "text", "body"):
        val = doc.get(key)
        if isinstance(val, str):
            return val
    return ""


def _corpus_provenance(corpus: dict[str, Any]) -> dict[str, Any]:
    """Corpus-level provenance block, with honest defaults.

    Provenance is the moat (``docs/design/value-propositions.md``); we always
    emit the block so a consumer can see what IS and ISN'T attested. ``signer:
    None`` honestly means "no accountable oracle signature on this corpus", not
    "trusted".
    """
    prov = corpus.get("provenance")
    prov = dict(prov) if isinstance(prov, dict) else {}
    prov.setdefault("signer", None)
    prov.setdefault("source", None)
    prov.setdefault("updated", None)
    # freshness is a SEAM note by default: a point-in-time snapshot is NOT a live
    # CDC-tracked tier. Stated honestly so nobody reads a frozen serve as "fresh".
    prov.setdefault("freshness", "point-in-time snapshot (live CDC re-serve is a seam)")
    return prov


def _aggregate_tiers(corpus: dict[str, Any], *, language: str | None = None) -> dict[str, Any]:
    """Run the tier pipeline **per document** and aggregate to a corpus view.

    Why per-document, not over a concatenated blob: a governed corpus is a *set*
    of heterogeneous documents (code, prose, config). ``tier_pipeline.run`` —
    correctly, per its ``on_error=raise`` contract — auto-detects ONE language
    and ``ast.parse``s the whole input when that language is Python; feeding it a
    blob that mixes a Python file with a prose paragraph makes it (rightly) raise
    a ``SyntaxError`` on the prose. The right composition is therefore to refine
    each document on its own (each gets the correct language + graceful prose
    degradation the pipeline already guarantees) and then sum the results:

      * ``tokens_by_tier`` — the **sum** of every document's proxy-token count at
        that tier. Monotone non-increasing across ``TIER_ORDER`` because it holds
        per document (each pipeline run guarantees it) and a sum of non-increasing
        sequences is non-increasing.
      * ``fidelity_by_tier`` — the **token-weighted mean** of each document's
        measured fidelity at that derived tier, weighted by the document's *raw*
        tokens (a big doc's fidelity counts proportionally more). Still the
        *separate* evaluator's number, never self-graded; weighting just rolls the
        per-doc measurements up to one corpus figure honestly. Empty corpus → 1.0
        (nothing to lose).
      * ``per_document`` — the full per-doc tier result, so the rollup is
        auditable (a consumer can see which document dragged a tier's fidelity).

    Deterministic: documents are processed in their given order; the rollup is a
    fixed left-to-right fold.
    """
    docs = _documents(corpus)
    tokens_by_tier: dict[str, int] = {tier: 0 for tier in TIER_ORDER}
    # token-weighted fidelity accumulators per derived tier
    fid_weighted: dict[str, float] = {tier: 0.0 for tier in DERIVED_TIERS}
    raw_weight = 0
    per_document: list[dict[str, Any]] = []

    for doc in docs:
        content = _doc_content(doc)
        if not content:
            continue
        doc_lang = doc.get("language") or language
        result = tier_pipeline.run(content, language=doc_lang)
        for tier in TIER_ORDER:
            tokens_by_tier[tier] += result["tokens_by_tier"][tier]
        doc_raw = result["tokens_by_tier"][TIER_RAW]
        raw_weight += doc_raw
        for tier in DERIVED_TIERS:
            fid_weighted[tier] += result["fidelity_by_tier"][tier] * doc_raw
        per_document.append({
            "doc_id": str(doc.get("doc_id") or "").strip() or None,
            "tokens_by_tier": result["tokens_by_tier"],
            "fidelity_by_tier": result["fidelity_by_tier"],
            "fidelity_detail": result["fidelity_detail"],
            "language": result["language"],
        })

    # Roll the token-weighted sums up to a mean. Empty/zero-token corpus → 1.0
    # (there is nothing to lose, so fidelity is trivially perfect — honest, not
    # a divide-by-zero or a fabricated low score).
    fidelity_by_tier: dict[str, float] = {}
    for tier in DERIVED_TIERS:
        fidelity_by_tier[tier] = (
            1.0 if raw_weight == 0 else round(fid_weighted[tier] / raw_weight, 6)
        )

    return {
        "tokens_by_tier": tokens_by_tier,
        "fidelity_by_tier": fidelity_by_tier,
        "per_document": per_document,
    }


# ── (1) llms.txt / llms-full.txt emitter ──────────────────────────────────────


def _escape_inline(text: str) -> str:
    """Collapse a value to a single safe line for a markdown link/notes slot.

    llms.txt link list items are one-liners (``- [name](url): notes``), so a
    multi-line title/note would break the list. Deterministic: newlines/tabs →
    spaces, runs of whitespace collapsed, trimmed.
    """
    return " ".join(str(text).split())


def emit_llms_txt(corpus: Any, *, full: bool = False) -> str:
    """Render the governed corpus as a spec-conformant ``llms.txt`` string.

    Implements the ``llms.txt`` standard (llmstxt.org): a markdown file an LLM
    can consume directly, with a **fixed, ordered** structure:

      1. an H1 with the corpus **name/title** (the only REQUIRED element);
      2. an optional blockquote (``> …``) with a one-line **summary**;
      3. zero or more info paragraphs (here: the provenance line — signer +
         freshness — so the consumption surface itself carries the moat);
      4. zero or more ``##`` **sections**, each a markdown list of
         ``- [name](url): notes`` links. Documents are bucketed by their
         ``section`` field (default ``"Docs"``); an ``"Optional"`` section is
         emitted LAST per the spec (links a verbose agent may skip).

    Args:
      corpus: the governed-corpus dict (see module docstring for the shape).
      full:   when ``True``, emit ``llms-full.txt`` semantics — the same skeleton
        but with each document's **full content inlined** under its link (the
        freezable, no-integration *content* surface). When ``False`` (default),
        emit links-only ``llms.txt`` (the index surface).

    Returns:
      A single ``str`` ending in a newline. Deterministic for a given corpus.

    Raises:
      TypeError/ValueError: on a malformed corpus (``on_error: raise``).

    HONEST: this is the REAL ``deliver.llms_txt`` surface (the audit's natural
    first cut). It is *freezable* — a downloaded ``llms.txt`` cannot stay current
    with a changing corpus; keeping it fresh is the recurring/CDC seam, noted in
    the emitted provenance line.
    """
    corpus = _require_corpus(corpus)
    title = _escape_inline(corpus.get("title") or corpus.get("corpus_id"))
    lines: list[str] = [f"# {title}"]

    summary = corpus.get("summary")
    if summary:
        lines.append("")
        lines.append(f"> {_escape_inline(summary)}")

    # Provenance info paragraph — the consumption surface carries the moat.
    prov = _corpus_provenance(corpus)
    signer = prov.get("signer")
    signer_str = f"signed by {signer}" if signer else "unsigned (no accountable oracle signature)"
    lines.append("")
    lines.append(
        f"Governed corpus `{corpus['corpus_id']}` — {signer_str}; "
        f"freshness: {_escape_inline(prov.get('freshness'))}."
    )

    # Bucket documents into sections, preserving first-seen section order so the
    # output is deterministic and stable. The special "Optional" bucket is held
    # back and appended last per the llms.txt convention.
    section_order: list[str] = []
    buckets: dict[str, list[dict[str, Any]]] = {}
    for doc in _documents(corpus):
        section = _escape_inline(doc.get("section") or DEFAULT_SECTION) or DEFAULT_SECTION
        if section not in buckets:
            buckets[section] = []
            section_order.append(section)
        buckets[section].append(doc)

    # Stable ordering: non-Optional sections in first-seen order, then Optional.
    ordered_sections = [s for s in section_order if s != OPTIONAL_SECTION]
    if OPTIONAL_SECTION in buckets:
        ordered_sections.append(OPTIONAL_SECTION)

    for section in ordered_sections:
        lines.append("")
        lines.append(f"## {section}")
        for doc in buckets[section]:
            name = _escape_inline(doc.get("title") or doc.get("doc_id") or "document")
            url = _escape_inline(doc.get("url") or "")
            note = _escape_inline(doc.get("notes") or "")
            link = f"[{name}]({url})" if url else name
            item = f"- {link}: {note}" if note else f"- {link}"
            lines.append(item)
            if full:
                # llms-full.txt: inline the full content as a fenced block under
                # the link so a no-integration agent gets the actual source of
                # truth, not just a pointer. Fence chosen to avoid clashing with
                # the doc's own backticks would require scanning; we use a long
                # tilde fence which markdown treats as a code fence and which
                # passes through content containing ``` unharmed.
                content = _doc_content(doc)
                if content:
                    lines.append("")
                    lines.append("~~~~")
                    lines.append(content.rstrip("\n"))
                    lines.append("~~~~")
                    lines.append("")

    text = "\n".join(lines).rstrip("\n") + "\n"
    return text


# ── (2) Tier negotiation ───────────────────────────────────────────────────────


def _coerce_int(value: Any, name: str) -> int | None:
    """Coerce an optional numeric hint to int; raise on a non-numeric value."""
    if value is None:
        return None
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        raise TypeError(f"{name} must be a number, got bool")
    if isinstance(value, (int, float)):
        return int(value)
    raise TypeError(f"{name} must be a number or None, got {type(value).__name__}")


def negotiate_tier(request: Any) -> dict[str, Any]:
    """Pick the tier to serve from a budget/latency hint, with measured fidelity.

    The request dict carries the corpus and at most two hints:

      ``corpus``        — the governed-corpus dict (REQUIRED).
      ``budget_tokens`` — optional int: the most tokens the agent will spend on
        this corpus. We pick the **densest tier that still fits** when raw is too
        big, and the **least-lossy tier that fits** otherwise (prefer raw when it
        fits the budget, since raw is the source of truth).
      ``latency_ms``    — optional int: a latency hint. A *tight* budget
        (``<= LATENCY_FAST_MS``) favors the densest tier (fewer tokens → faster
        downstream); a *loose* one (``>= LATENCY_RELAXED_MS``) is happy with raw.
      ``language``      — optional language hint forwarded to the tier pipeline.

    Selection precedence: an explicit ``budget_tokens`` is the binding constraint
    (a hard ceiling); ``latency_ms`` only shapes the choice *within* what fits;
    with neither hint we serve ``DEFAULT_TIER`` (raw — the safe, lossless default).

    Returns a dict:
      {
        "tier":            str,            # one of TIER_ORDER
        "reason":          str,            # human-readable why-this-tier
        "tokens":          int,            # proxy tokens of the chosen tier
        "tokens_by_tier":  {tier: int},    # all tiers' tokens (auditable)
        "fidelity":        float | None,   # MEASURED fidelity of the chosen tier
                                           # (None for raw — it IS the reference)
        "fidelity_record": {...} | None,   # the separate evaluator's full result
        "budget_tokens":   int | None,     # echoed hint
        "latency_ms":      int | None,     # echoed hint
        "fits_budget":     bool,           # did the chosen tier fit the budget?
      }

    The fidelity number comes STRAIGHT from ``tier_pipeline`` (the *separate*
    ``verify.compression_fidelity`` evaluator) — a served tier never grades its
    own quality. Deterministic.

    Raises:
      TypeError/ValueError: on a malformed request/corpus (``on_error: raise``).
    """
    if not isinstance(request, dict):
        raise TypeError(f"request must be a dict, got {type(request).__name__}")
    corpus = _require_corpus(request.get("corpus"))
    budget = _coerce_int(request.get("budget_tokens"), "budget_tokens")
    latency = _coerce_int(request.get("latency_ms"), "latency_ms")
    if budget is not None and budget < 0:
        raise ValueError("budget_tokens must be >= 0")
    if latency is not None and latency < 0:
        raise ValueError("latency_ms must be >= 0")

    # Refine each document on its own and roll up — NOT a concatenated blob (a
    # mixed code+prose blob would make the single-language structural compressor
    # raise; see _aggregate_tiers). tokens_by_tier is summed; fidelity_by_tier is
    # the token-weighted mean of the SEPARATE evaluator's per-doc scores.
    agg = _aggregate_tiers(corpus, language=request.get("language"))
    tokens_by_tier: dict[str, int] = agg["tokens_by_tier"]
    fidelity_by_tier: dict[str, float] = agg["fidelity_by_tier"]

    # Decide the tier.
    if budget is not None:
        # Hard ceiling. Prefer the LEAST-lossy tier that fits (raw first), since
        # raw is the source of truth. TIER_ORDER is least-lossy-first.
        chosen = None
        for tier in TIER_ORDER:
            if tokens_by_tier[tier] <= budget:
                chosen = tier
                break
        if chosen is None:
            # Even the densest tier overflows the budget — serve the densest one
            # (best effort) and report fits_budget=False honestly. We do NOT
            # silently truncate; over-budget is the caller's signal to raise the
            # budget or accept a partial. (Truncation/eviction is a seam.)
            chosen = TIER_ORDER[-1]  # hyper_efficient — the smallest
            fits = False
            reason = (
                f"budget {budget} tok is below even the densest tier "
                f"({chosen}={tokens_by_tier[chosen]} tok); serving densest, over budget"
            )
        else:
            fits = True
            if chosen == TIER_RAW:
                reason = f"raw ({tokens_by_tier[TIER_RAW]} tok) fits budget {budget}; serving source of truth"
            else:
                reason = (
                    f"raw ({tokens_by_tier[TIER_RAW]} tok) exceeds budget {budget}; "
                    f"densest least-lossy tier that fits is {chosen} ({tokens_by_tier[chosen]} tok)"
                )
        # Within what fits, a TIGHT latency hint pushes one step denser if denser
        # also fits — fewer tokens means a faster downstream model call.
        if fits and latency is not None and latency <= LATENCY_FAST_MS:
            idx = TIER_ORDER.index(chosen)
            for tier in TIER_ORDER[idx + 1:]:
                if tokens_by_tier[tier] <= budget:
                    chosen = tier
            if chosen != TIER_ORDER[idx]:
                reason += f"; tight latency {latency}ms → densest fitting tier {chosen}"
    elif latency is not None:
        # No token ceiling, only a latency shape.
        if latency <= LATENCY_FAST_MS:
            chosen = TIER_HYPER_EFFICIENT
            reason = f"tight latency {latency}ms (<= {LATENCY_FAST_MS}) → densest tier {chosen}"
        elif latency >= LATENCY_RELAXED_MS:
            chosen = TIER_RAW
            reason = f"relaxed latency {latency}ms (>= {LATENCY_RELAXED_MS}) → full-fidelity raw"
        else:
            chosen = TIER_COMPRESSED
            reason = f"mid latency {latency}ms → balanced compressed tier"
    else:
        chosen = DEFAULT_TIER
        reason = "no budget/latency hint → safe default (raw, source of truth)"

    fits_budget = budget is None or tokens_by_tier[chosen] <= budget
    fidelity = fidelity_by_tier.get(chosen)  # None for raw (the reference)
    # The fidelity record for a derived tier is the auditable rollup: the
    # corpus-level weighted score PLUS each document's own measured score at that
    # tier, so a consumer can see which doc dragged the number. None for raw.
    record: dict[str, Any] | None = None
    if chosen in DERIVED_TIERS:
        record = {
            "tier": chosen,
            "fidelity": fidelity,
            "method": "token-weighted mean of per-document verify.compression_fidelity (separate evaluator)",
            "per_document": [
                {"doc_id": d["doc_id"], "fidelity": d["fidelity_by_tier"][chosen]}
                for d in agg["per_document"]
            ],
        }
    return {
        "tier": chosen,
        "reason": reason,
        "tokens": tokens_by_tier[chosen],
        "tokens_by_tier": tokens_by_tier,
        "fidelity": fidelity,
        "fidelity_record": record,
        "budget_tokens": budget,
        "latency_ms": latency,
        "fits_budget": fits_budget,
    }


# ── (3) MCP-style serving descriptor ───────────────────────────────────────────


def _tool_descriptor(tool: Any) -> dict[str, Any]:
    """Map one tool definition to an MCP Tool object (matching the repo emitter).

    Accepts either an already-shaped MCP tool dict (``{"name", "inputSchema",
    …}``) or a hub component-ish dict (``{"id"|"name", "description",
    "parameters", …}``) and normalizes to the shape
    ``scripts/emit/mcp_server.py`` produces, so this descriptor's tools are
    interchangeable with the real emitter's. Carries an ``ohh:`` ``_meta`` block
    so an MCP host can make authorization decisions.
    """
    if not isinstance(tool, dict):
        raise TypeError(f"each tool must be a dict, got {type(tool).__name__}")
    component_id = tool.get("id") or tool.get("name") or "tool"
    name = mcp_name(str(component_id)) if "id" in tool else _escape_inline(tool.get("name") or "tool")
    schema = tool.get("inputSchema") or tool.get("parameters") or {
        "type": "object", "additionalProperties": False,
    }
    desc: dict[str, Any] = {
        "name": name,
        "title": tool.get("title") or _escape_inline(tool.get("name") or name),
        "description": _escape_inline(tool.get("description") or ""),
        "inputSchema": schema,
        "_meta": {
            "ohh:componentId": component_id,
            "ohh:trustBoundary": tool.get("trust_boundary"),
            "ohh:capability": tool.get("capability", []),
        },
    }
    if tool.get("returns") or tool.get("outputSchema"):
        desc["outputSchema"] = tool.get("outputSchema") or tool.get("returns")
    return desc


def serve_descriptor(corpus: Any, tools: Any = None) -> dict[str, Any]:
    """Build the MCP-style serving descriptor for a governed corpus + its tools.

    This is the **contract / skeleton** an MCP client would mount: the
    ``resources`` it can read (the governed corpus, one resource per document,
    each carrying its provenance + per-tier fidelity from the tier pipeline) and
    the ``tools`` it can call. It is a **dict, not a live server** — the process
    that answers ``tools/call`` / ``resources/read`` over stdio is the SEAM (see
    ``SERVE_SEAMS``; wire it with the generated ``dist/mcp/server.py`` stub).

    Args:
      corpus: the governed-corpus dict.
      tools:  optional iterable of tool definitions (hub-component dicts or
        already-shaped MCP tool dicts). Defaults to no tools.

    Returns a dict shaped like an MCP ``initialize`` + ``tools/list`` +
    ``resources/list`` view, with hub provenance carried throughout:
      {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "serverInfo":      {"name", "corpusId", ...},
        "capabilities":    {"resources": {...}, "tools": {...}},
        "resources":       [ {uri, name, description, _meta:{provenance, fidelity_by_tier}}... ],
        "tools":           [ MCP Tool objects ],
        "provenance":      {...},               # corpus-level provenance (the moat)
        "tiers":           [TIER_ORDER...],      # tiers this corpus can be served at
        "fidelity_by_tier":{tier: float},        # MEASURED, from the tier pipeline
        "billing":         {...},                # metering CONTRACT (a seam)
        "seams":           [SERVE_SEAMS...],     # honest: what is contract vs wire
        "runtime":         RUNTIME,
      }

    Deterministic. Raises TypeError/ValueError on malformed input.
    """
    corpus = _require_corpus(corpus)
    prov = _corpus_provenance(corpus)

    # Measure the corpus's per-tier fidelity via the real tier pipeline, per
    # document then rolled up (the same aggregation negotiate_tier uses), so a
    # client sees the served quality contract — the SEPARATE-evaluator number,
    # never self-graded.
    agg = _aggregate_tiers(corpus)
    fidelity_by_tier: dict[str, float] = agg["fidelity_by_tier"]

    # One MCP resource per governed document. The resource URI namespaces the
    # corpus + doc so a client can address a single slice; each resource carries
    # its own provenance + lifecycle so authorization/citation survives mounting.
    resources: list[dict[str, Any]] = []
    for doc in _documents(corpus):
        doc_id = str(doc.get("doc_id") or "").strip() or "doc"
        resource: dict[str, Any] = {
            "uri": f"ceaas://{corpus['corpus_id']}/{doc_id}",
            "name": _escape_inline(doc.get("title") or doc_id),
            "description": _escape_inline(doc.get("notes") or ""),
            "mimeType": "text/markdown",
            "_meta": {
                "ohh:docId": doc_id,
                "ohh:sourceUrl": doc.get("url"),
                "ohh:lifecycle": doc.get("lifecycle"),
                "ohh:provenance": doc.get("provenance"),
            },
        }
        resources.append(resource)

    tool_list: list[dict[str, Any]] = []
    if tools:
        for tool in tools:
            tool_list.append(_tool_descriptor(tool))

    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "serverInfo": {
            "name": "ceaas-corpus-server",
            "corpusId": corpus["corpus_id"],
            "title": _escape_inline(corpus.get("title") or corpus["corpus_id"]),
            "license": corpus.get("license"),
        },
        "capabilities": {
            # The corpus is read-only fuel; the live server would set
            # listChanged when CDC re-serves (the freshness seam).
            "resources": {"listChanged": False, "subscribe": False},
            "tools": {"listChanged": False},
        },
        "resources": resources,
        "tools": tool_list,
        # ── the moat: provenance carried on the serving contract ──
        "provenance": prov,
        # ── tier contract: which tiers + their MEASURED fidelity (separate eval) ──
        "tiers": list(TIER_ORDER),
        "fidelity_by_tier": fidelity_by_tier,
        # ── metering CONTRACT (declared, not enforced — a seam) ──
        "billing": {
            "model": "per-request token+fidelity metering",
            "freezable_tiers": [TIER_RAW, TIER_COMPRESSED],   # downloadable → one-time
            "recurring_tiers": [TIER_HYPER_EFFICIENT],        # live/fresh → recurring
            "enforced": False,  # HONEST: the meter is the seam, not wired here
        },
        # ── honest seam ledger ──
        "seams": list(SERVE_SEAMS),
        "runtime": dict(RUNTIME),
    }


# ── Public entrypoint (ties the three surfaces together) ───────────────────────


def run(
    corpus: Any,
    *,
    tools: Any = None,
    request: Any = None,
    full: bool = False,
) -> dict[str, Any]:
    """Serve a governed corpus across all three surfaces in one call.

    Args:
      corpus:  the governed-corpus dict.
      tools:   optional tool definitions for the MCP descriptor.
      request: optional negotiation request (budget/latency hints). When omitted,
        a no-hint request is used (negotiates to the safe ``raw`` default). The
        corpus is injected automatically, so callers pass only the hints.
      full:    when ``True``, the emitted ``llms_txt`` is ``llms-full.txt``
        (content inlined).

    Returns a dict:
      {
        "corpus_id":   str,
        "llms_txt":    str,                  # the freezable no-integration surface
        "negotiation": {...},                # negotiate_tier() result
        "descriptor":  {...},                # serve_descriptor() result (MCP contract)
        "provenance":  {...},                # corpus-level provenance (the moat)
        "seams":       [...],                # honest: live MCP wire / meter / CDC
        "runtime":     {...},
      }

    Deterministic, pure, no side effects (emits artifacts; does not push them —
    the push is the SEAM).
    """
    corpus = _require_corpus(corpus)
    req: dict[str, Any] = dict(request) if isinstance(request, dict) else {}
    req["corpus"] = corpus  # the negotiator needs the corpus; inject it

    llms = emit_llms_txt(corpus, full=full)
    negotiation = negotiate_tier(req)
    descriptor = serve_descriptor(corpus, tools)

    return {
        "corpus_id": corpus["corpus_id"],
        "llms_txt": llms,
        "negotiation": negotiation,
        "descriptor": descriptor,
        "provenance": _corpus_provenance(corpus),
        "seams": list(SERVE_SEAMS),
        "runtime": dict(RUNTIME),
    }


# ── Self-test (proves the three surfaces on a small governed corpus) ───────────

# A small but REAL governed corpus: a couple of code docs (so the tier pipeline
# has structure to compress) plus a prose doc, an "Optional" section, a corpus
# signer + a per-doc source link. Code content is dense enough that raw >
# compressed in tokens, so tier negotiation has a real choice to make.
_SAMPLE_CORPUS: dict[str, Any] = {
    "corpus_id": "ohh-serve-demo",
    "title": "Open Harness Hub — serving demo corpus",
    "summary": "A tiny governed corpus used to prove the CEaaS serving surfaces.",
    "license": "MIT",
    "provenance": {
        "signer": "openharnesshub.com (demo oracle)",
        "source": "scripts/enrichment/serve.py self-test fixture",
        "updated": "2026-05-29",
        "freshness": "fixture snapshot (live CDC re-serve is a seam)",
    },
    "documents": [
        {
            "doc_id": "tier-planner",
            "title": "Tier budget planner",
            "url": "https://openharnesshub.com/docs/tier-planner",
            "section": "Reference",
            "notes": "How the token budget is planned per tier.",
            "lifecycle": "experimental",
            "content": (
                '"""Token-budget planner for the CEaaS serving path."""\n'
                "from typing import Any\n\n\n"
                "SAFETY_MARGIN = 0.1\n\n\n"
                "def plan_budget(window: int, *, reserve: int = 0) -> int:\n"
                '    """Return the usable token budget for a window."""\n'
                "    usable = window - reserve\n"
                "    usable = int(usable * (1.0 - SAFETY_MARGIN))\n"
                "    if usable < 0:\n"
                '        raise ValueError("reserve exceeds window")\n'
                "    return usable\n\n\n"
                "def fits(text: str, window: int) -> bool:\n"
                '    """True when text fits the planned budget for window."""\n'
                "    budget = plan_budget(window)\n"
                "    return len(text.split()) <= budget\n"
            ),
        },
        {
            "doc_id": "serve-router",
            "title": "Serve router",
            "url": "https://openharnesshub.com/docs/serve-router",
            "section": "Reference",
            "notes": "Routes a request to a tier.",
            "lifecycle": "experimental",
            "content": (
                '"""Route a serving request to a tier."""\n\n\n'
                "def route(budget: int, latency: int) -> str:\n"
                '    """Pick a tier name from budget + latency."""\n'
                "    if latency < 200:\n"
                '        return "hyper_efficient"\n'
                "    if budget < 1000:\n"
                '        return "compressed"\n'
                '    return "raw"\n'
            ),
        },
        {
            "doc_id": "overview",
            "title": "What this corpus is",
            "url": "https://openharnesshub.com/docs/overview",
            "notes": "Plain-language overview.",
            "lifecycle": "active",
            "content": "This corpus is a tiny demo used only to exercise the serving surfaces.\n",
        },
        {
            "doc_id": "changelog",
            "title": "Changelog",
            "url": "https://openharnesshub.com/docs/changelog",
            "section": "Optional",
            "notes": "Release history a verbose agent may skip.",
            "content": "v0: initial demo corpus.\n",
        },
    ],
}

# Tools the descriptor should expose (one already-shaped MCP tool, one
# hub-component-style dict to prove both input shapes normalize correctly).
_SAMPLE_TOOLS: list[dict[str, Any]] = [
    {
        "id": "processor/serve-mcp-corpus",
        "name": "Serve corpus over MCP",
        "description": "Live-serve a governed corpus + tools over MCP.",
        "parameters": {"type": "object", "properties": {"tier": {"type": "string"}}},
        "trust_boundary": "external",
        "capability": ["tool_use", "retrieval"],
    },
    {
        "name": "search_corpus",
        "title": "Search the corpus",
        "description": "Keyword search over the governed corpus.",
        "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}},
    },
]


def _selftest() -> None:
    # ── (1) emit_llms_txt — well-formed llms.txt (links-only). ──
    text = emit_llms_txt(_SAMPLE_CORPUS)
    lines = text.splitlines()

    # H1 with the title is REQUIRED and must be the first line.
    assert lines[0] == "# Open Harness Hub — serving demo corpus", \
        f"llms.txt must open with the H1 title, got {lines[0]!r}"
    # Blockquote summary present.
    assert any(ln.startswith("> ") and "tiny governed corpus" in ln for ln in lines), \
        "llms.txt missing the blockquote summary"
    # Provenance info line present (the moat on the surface) — signer + freshness.
    assert any("Governed corpus `ohh-serve-demo`" in ln and "signed by" in ln for ln in lines), \
        "llms.txt missing the provenance info line"
    # At least one ## section header and the expected link format.
    assert "## Reference" in text, "llms.txt missing the Reference section"
    assert "- [Tier budget planner](https://openharnesshub.com/docs/tier-planner): " in text, \
        "llms.txt link not in the spec '- [name](url): notes' format"
    # The "Optional" section is emitted LAST (after Reference and Docs).
    opt_idx = lines.index("## Optional")
    ref_idx = lines.index("## Reference")
    assert opt_idx > ref_idx, "Optional section must come after the others"
    # The no-section doc landed in the default 'Docs' bucket.
    assert "## Docs" in text, "default-section doc should bucket under 'Docs'"
    # links-only mode does NOT inline content.
    assert "def plan_budget(" not in text, "links-only llms.txt must not inline content"
    # Ends in exactly one trailing newline.
    assert text.endswith("\n") and not text.endswith("\n\n"), "llms.txt newline shape"

    # ── (1b) emit_llms_txt(full=True) — llms-full.txt inlines content. ──
    full_text = emit_llms_txt(_SAMPLE_CORPUS, full=True)
    assert "# Open Harness Hub — serving demo corpus" in full_text
    assert "def plan_budget(" in full_text, "llms-full.txt must inline document content"
    assert "~~~~" in full_text, "llms-full.txt must fence inlined content"
    # full is strictly larger than links-only (it adds the bodies).
    assert len(full_text) > len(text), "llms-full.txt must be larger than llms.txt"

    # ── (2) negotiate_tier — returns a valid tier with a fidelity record. ──
    # No hint → safe default raw, fidelity None (raw is the reference).
    neg_default = negotiate_tier({"corpus": _SAMPLE_CORPUS})
    assert neg_default["tier"] == TIER_RAW, f"no-hint default must be raw, got {neg_default['tier']}"
    assert neg_default["fidelity"] is None, "raw tier has no fidelity delta (it IS the reference)"
    assert neg_default["fits_budget"] is True

    # The tier vocabulary is exactly the pipeline's (no drift).
    assert set(neg_default["tokens_by_tier"]) == set(TIER_ORDER), "token map must cover all tiers"
    raw_tok = neg_default["tokens_by_tier"][TIER_RAW]
    comp_tok = neg_default["tokens_by_tier"][TIER_COMPRESSED]
    hyper_tok = neg_default["tokens_by_tier"][TIER_HYPER_EFFICIENT]
    # The code-heavy corpus must give a real choice: raw > compressed in tokens.
    assert raw_tok > comp_tok, f"expected raw>compressed tokens for code corpus, got {raw_tok}!>{comp_tok}"

    # A budget below raw but >= compressed must pick a DERIVED tier and carry a
    # MEASURED fidelity in [0,1] from the SEPARATE evaluator.
    mid_budget = comp_tok  # exactly fits compressed, below raw
    neg_budget = negotiate_tier({"corpus": _SAMPLE_CORPUS, "budget_tokens": mid_budget})
    assert neg_budget["tier"] in DERIVED_TIERS, \
        f"budget below raw must pick a derived tier, got {neg_budget['tier']}"
    assert neg_budget["tokens"] <= mid_budget, "chosen tier must fit the budget"
    assert neg_budget["fits_budget"] is True
    fid = neg_budget["fidelity"]
    assert isinstance(fid, (int, float)) and 0.0 <= fid <= 1.0, \
        f"derived tier must carry measured fidelity in [0,1], got {fid!r}"
    rec = neg_budget["fidelity_record"]
    assert isinstance(rec, dict) and rec.get("fidelity") == fid, \
        "fidelity_record must carry the chosen tier's measured score"
    # The record is the AUDITABLE per-document rollup: one entry per content
    # document, each with its OWN measured score from the separate evaluator.
    per_doc = {d["doc_id"]: d["fidelity"] for d in rec["per_document"]}
    assert {"tier-planner", "serve-router", "overview", "changelog"} <= set(per_doc), \
        "fidelity_record must break the score down per document"
    # The evaluator is doing REAL work, not returning a constant: a prose doc
    # that loses nothing scores higher than a code doc whose bodies were stripped.
    assert per_doc["overview"] > per_doc["tier-planner"], \
        "separate evaluator must score lossless prose above body-stripped code (it measures, not asserts)"
    # And the corpus score is exactly the token-weighted mean of those per-doc
    # scores (weighted by each doc's raw tokens) — the rollup is honest math.
    agg_docs = _aggregate_tiers(_SAMPLE_CORPUS)["per_document"]
    weights = {d["doc_id"]: d["tokens_by_tier"][TIER_RAW] for d in agg_docs}
    total_w = sum(weights.values())
    expected = round(sum(per_doc[k] * weights[k] for k in per_doc) / total_w, 6)
    assert abs(expected - fid) < 1e-6, f"corpus fidelity must be the token-weighted mean: {expected} != {fid}"

    # A budget below EVEN the densest tier → serve densest, fits_budget False (honest).
    neg_tiny = negotiate_tier({"corpus": _SAMPLE_CORPUS, "budget_tokens": max(0, hyper_tok - 1)})
    assert neg_tiny["tier"] == TIER_HYPER_EFFICIENT, "below-densest budget serves the densest tier"
    assert neg_tiny["fits_budget"] is False, "over-budget must be reported honestly, not hidden"

    # A tight latency hint (no budget) → densest tier.
    neg_fast = negotiate_tier({"corpus": _SAMPLE_CORPUS, "latency_ms": 50})
    assert neg_fast["tier"] == TIER_HYPER_EFFICIENT, "tight latency → densest tier"
    # A relaxed latency hint → raw.
    neg_slow = negotiate_tier({"corpus": _SAMPLE_CORPUS, "latency_ms": 5000})
    assert neg_slow["tier"] == TIER_RAW, "relaxed latency → raw"

    # ── (2b) Empty / no-content corpus degrades honestly, never crashes. ──
    empty_corpus = {"corpus_id": "empty", "title": "Empty", "documents": []}
    neg_empty = negotiate_tier({"corpus": empty_corpus, "budget_tokens": 100})
    assert neg_empty["tokens"] == 0 and neg_empty["fits_budget"] is True
    # No tokens to lose → fidelity is trivially perfect (1.0), not a fabricated low.
    for score in _aggregate_tiers(empty_corpus)["fidelity_by_tier"].values():
        assert score == 1.0, "empty corpus must report perfect fidelity (nothing to lose), honestly"

    # ── (3) serve_descriptor — lists corpus resources + tools with provenance. ──
    desc = serve_descriptor(_SAMPLE_CORPUS, _SAMPLE_TOOLS)
    assert desc["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert desc["serverInfo"]["corpusId"] == "ohh-serve-demo"
    # One resource per document, each addressable + carrying provenance metadata.
    assert len(desc["resources"]) == len(_SAMPLE_CORPUS["documents"]), \
        "descriptor must list one resource per governed document"
    res0 = desc["resources"][0]
    assert res0["uri"] == "ceaas://ohh-serve-demo/tier-planner", "resource URI must namespace corpus+doc"
    assert res0["_meta"]["ohh:sourceUrl"] == "https://openharnesshub.com/docs/tier-planner", \
        "each resource must carry its source-url provenance anchor"
    # Tools listed, both input shapes normalized to MCP Tool objects.
    assert len(desc["tools"]) == 2, "descriptor must list both tools"
    names = {t["name"] for t in desc["tools"]}
    # The hub-component id was normalized via the SAME mcp_name the real emitter uses.
    assert mcp_name("processor/serve-mcp-corpus") in names, "tool name must match the MCP emitter's normalization"
    assert "search_corpus" in names, "already-shaped MCP tool must pass through"
    for t in desc["tools"]:
        assert "inputSchema" in t and isinstance(t["inputSchema"], dict), "every tool needs an inputSchema"
        assert "_meta" in t and "ohh:componentId" in t["_meta"], "every tool carries ohh provenance _meta"
    # Corpus-level provenance (the moat) present, with the signer carried through.
    assert desc["provenance"]["signer"] == "openharnesshub.com (demo oracle)", \
        "descriptor must carry the corpus signer (provenance is the moat)"
    # Per-tier MEASURED fidelity on the descriptor, covering the derived tiers.
    assert set(desc["fidelity_by_tier"]) == set(DERIVED_TIERS), \
        "descriptor fidelity_by_tier must cover the derived tiers (measured, separate eval)"
    for score in desc["fidelity_by_tier"].values():
        assert 0.0 <= score <= 1.0
    # The billing block is a CONTRACT, honestly NOT enforced (the meter is a seam).
    assert desc["billing"]["enforced"] is False, "metering must be declared unenforced (it's a seam)"
    assert TIER_HYPER_EFFICIENT in desc["billing"]["recurring_tiers"]
    # The seam ledger names the live MCP endpoint as unbuilt (honest skeleton).
    assert any("live MCP endpoint" in s for s in desc["seams"]), \
        "descriptor must declare the live MCP endpoint as a seam (it is a contract, not a wire)"

    # ── run() ties them together. ──
    out = run(_SAMPLE_CORPUS, tools=_SAMPLE_TOOLS, request={"budget_tokens": mid_budget})
    for key in ("corpus_id", "llms_txt", "negotiation", "descriptor", "provenance", "seams", "runtime"):
        assert key in out, f"run() result missing {key!r}"
    assert out["corpus_id"] == "ohh-serve-demo"
    assert out["llms_txt"].startswith("# Open Harness Hub"), "run() must carry the llms.txt surface"
    assert out["negotiation"]["tier"] in DERIVED_TIERS, "run() negotiation must honor the budget"
    assert out["descriptor"]["serverInfo"]["corpusId"] == "ohh-serve-demo"

    # ── Determinism: a re-run is byte-identical across all three surfaces. ──
    out2 = run(_SAMPLE_CORPUS, tools=_SAMPLE_TOOLS, request={"budget_tokens": mid_budget})
    assert out2 == out, "serve.run is not deterministic (re-run differed)"
    assert emit_llms_txt(_SAMPLE_CORPUS, full=True) == full_text, "llms-full.txt is not deterministic"

    # ── Runtime manifest is the declared one + self-consistent with routing §4. ──
    rt = out["runtime"]
    assert rt["process_kind"] == PROCESS_KIND
    assert rt["deterministic"] is True and rt["idempotent"] is True
    assert rt["side_effects"] == "none"
    assert rt["streaming"] is False and rt["latency_budget_ms"] is None
    assert rt["trust_boundary"] == "local"
    assert rt["resource_pool"] == "cpu", f"routing pool mismatch: {rt['resource_pool']}"

    # ── on_error=raise: malformed inputs raise, never silently emit. ──
    for bad_call in (
        lambda: emit_llms_txt({"documents": []}),                 # no corpus_id
        lambda: emit_llms_txt("not a dict"),                      # wrong type
        lambda: negotiate_tier({"corpus": _SAMPLE_CORPUS, "budget_tokens": "lots"}),  # non-numeric
        lambda: negotiate_tier({"corpus": _SAMPLE_CORPUS, "budget_tokens": -5}),      # negative
        lambda: serve_descriptor(_SAMPLE_CORPUS, ["not-a-dict-tool"]),                # bad tool
    ):
        raised = False
        try:
            bad_call()
        except (TypeError, ValueError):
            raised = True
        assert raised, "malformed input must raise (on_error=raise), not emit a malformed surface"

    print(
        "PASS — serve: "
        "llms.txt well-formed (H1+summary+provenance line, "
        "sections Reference/Docs/Optional, links-only & full); "
        f"tier negotiation raw={raw_tok}>compressed={comp_tok}>hyper={hyper_tok} tok, "
        f"budget→{neg_budget['tier']} (measured fidelity={fid:.3f}, separate eval), "
        "latency hints → densest/raw; "
        f"descriptor lists {len(desc['resources'])} resources + {len(desc['tools'])} tools with "
        "provenance + per-tier fidelity; metering+live-MCP+CDC marked as seams; "
        "deterministic re-run identical; runtime=cpu pool. "
        "(MCP descriptor is the contract skeleton; live JSON-RPC endpoint is the seam)"
    )


if __name__ == "__main__":
    _selftest()
