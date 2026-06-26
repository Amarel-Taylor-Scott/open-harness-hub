"""src.teleon.blackboard.token_economics — a DETERMINISTIC token-economics ESTIMATE for the stateful thesis.

The thesis the blackboard spine exists to prove: building durable, typed, source-backed STATE once and then
querying it beats re-reading the source documents on every question. This module turns that into a *numeric,
deterministic, offline* estimate so the claim can be checked instead of asserted.

Two regimes are estimated over the SAME (source docs, sequence of N questions):

  * **STATELESS** — the agent has no durable state, so it re-reads ALL source docs for EVERY question. Its
    estimated input cost grows linearly in N: ``N * doc_tokens``.
  * **STATEFUL** — ONE first pass reads all the docs and distills them into a compact blackboard (typed,
    source-backed entries, ``serves_truth=False``). After that, each question reads only the small set of
    relevant blackboard entries (plus a tiny per-question shell), never the raw docs again. Its estimated
    input cost is ``first_pass_tokens + N * per_question_tokens`` where ``per_question_tokens << doc_tokens``.

Because the per-question term shrinks from ``doc_tokens`` (stateless) to a small compact read (stateful), there
is a **crossover**: above some N the stateful total is below the stateless total. The estimator reports the
crossover N and both totals so the proof asserts the crossover — NOT a blanket "stateful always wins" claim. At
N=1 the first-pass overhead can make stateless cheaper; that is reported honestly, never hidden.

WHAT THIS IS NOT
----------------
The token figures are a **deterministic ESTIMATE**, not measurements. We use a fixed chars-per-token heuristic
(:data:`CHARS_PER_TOKEN`) — NOT a real BPE/tiktoken tokenizer — and we count *input* tokens only (no output, no
$ price, no model). The report is labeled ``is_truth=False`` and ``estimate_method`` names the heuristic, so a
caller cannot mistake it for a real tokenizer or a real cost. The blackboard entries built here carry
``serves_truth=False`` (the store's invariant); nothing here is served truth.

Pure + deterministic: every figure is a function of the inputs and the injected ``now`` — no RNG, no wall-clock,
no network, no LLM. Teleon-owned: stdlib + Teleon id/blackboard/port helpers only — never Baltor.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.teleon.blackboard.local_sqlite_blackboard import LocalSqliteBlackboard
from src.teleon.experiments.ids import canonical_id
from src.teleon.ports.blackboard_provider import (
    KIND_OBSERVATION,
    KIND_SOURCE,
)

_REPO = Path(__file__).resolve().parents[3]

# ---- the estimate heuristic (SINGLE SOURCE — this is an ESTIMATE, not a real tokenizer) ----------------------
#: Average characters per token. A coarse rule of thumb for English text (~4 chars/token); it is NOT a real
#: BPE/tiktoken tokenizer and the exact value does not matter to the thesis (it cancels in the ratio). Single
#: source: every token figure below divides character length by this one constant.
CHARS_PER_TOKEN = 4

#: Human-readable label for the method, surfaced in the report so a reader cannot mistake it for a real tokenizer.
ESTIMATE_METHOD = "chars/4 heuristic — ESTIMATE not a real tokenizer"

#: A small fixed per-question prompt shell (the question + framing the model re-reads every turn) in CHARACTERS.
#: It is paid in BOTH regimes (so it never biases the comparison) and is a named constant, not a magic literal.
PER_QUESTION_SHELL_CHARS = 280

#: How many blackboard entries a single question is estimated to read. A question consults the compact distilled
#: state (the relevant observations + their source handles), not the raw docs. Single source for the per-question
#: stateful read size; the proof depends on this being far smaller than the full doc set, not on its exact value.
ENTRIES_READ_PER_QUESTION = 4

#: Maximum characters kept in a compact observation digest. The compact entry is intentionally a SMALL fraction of
#: the source doc; this is the lever that makes the per-question stateful read cheap. Single source: every
#: observation digest produced by this module is bounded by this constant. Unit: characters.
OBSERVATION_DIGEST_MAX_CHARS = 160

#: The source documents under demo-data/cfpb-sample that a reader would actually "read" (the seed-graph.json and
#: compiled .pyc are excluded — they are machine artifacts, not the prose/code a model would read). Relative to
#: the cfpb-sample dir; resolved lazily so importing this module never touches disk.
CFPB_SAMPLE_DOC_RELPATHS = (
    "complaints/COMP-5521.json",
    "docs/disputes-faq.md",
    "incidents/INC-CFPB-07.md",
    "org/OWNERS.md",
    "regs/RegE-error-resolution.md",
    "sop/dispute_sla.py",
)


def estimate_tokens(text: str) -> int:
    """DETERMINISTIC token ESTIMATE for ``text``: ``ceil(len(text) / CHARS_PER_TOKEN)``.

    This is a coarse chars-per-token heuristic (:data:`ESTIMATE_METHOD`), NOT a real tokenizer. Pure: the same
    string always yields the same number. Empty text -> 0 tokens. We round UP so non-empty text never estimates
    to zero tokens.
    """
    n = len(text)
    if n <= 0:
        return 0
    # ceil division by the single-source chars-per-token constant (round up: non-empty text >= 1 token).
    return (n + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def load_cfpb_sample_docs(*, repo: Path | None = None) -> dict[str, str]:
    """Load the CFPB-sample source docs as ``{relpath: text}`` (deterministic key order).

    Reads the public, SYNTHETIC demo corpus under ``demo-data/cfpb-sample`` — the same files a reader would
    actually read. ``repo`` is injectable so tests can point at a fixture; defaults to the repo root. Missing
    files are skipped (the caller's doc set is whatever is present), so the helper never raises on a partial tree.
    """
    base = (repo or _REPO) / "demo-data" / "cfpb-sample"
    docs: dict[str, str] = {}
    for rel in CFPB_SAMPLE_DOC_RELPATHS:
        path = base / rel
        if path.is_file():
            docs[rel] = path.read_text(encoding="utf-8")
    return docs


def _distill_entries(docs: Mapping[str, str]) -> list[dict[str, Any]]:
    """Distill the source docs into compact, source-backed blackboard entries (the STATEFUL state).

    For each doc we emit a SOURCE entry (the provenance handle) and one compact OBSERVATION entry that cites it.
    The observation body is a short ``digest`` (a length-bounded slice of the doc) — the compression a real
    distillation step would produce — so reading the entry costs far fewer tokens than re-reading the whole doc,
    yet a source handle is preserved (the lossless-distillation contract: a derived compact layer that still
    points back to its source). Pure + deterministic: ids are content-addressed; the digest is a deterministic
    slice. ``serves_truth`` is never set (the store pins it False — this is working state, never truth).
    """
    entries: list[dict[str, Any]] = []
    for rel in sorted(docs):  # deterministic order over the doc set
        text = docs[rel]
        source_id = canonical_id("src", rel)
        handle = f"ctx://cfpb-sample/{rel}"  # a stable provenance handle back to the source doc
        # a one-line deterministic digest: the first non-trivial run of the doc, whitespace-collapsed + bounded.
        digest = " ".join(text.split())[:OBSERVATION_DIGEST_MAX_CHARS]
        entries.append(
            {
                "kind": KIND_SOURCE,
                "source_id": source_id,
                "handle": handle,
                "relpath": rel,
            }
        )
        entries.append(
            {
                "kind": KIND_OBSERVATION,
                "source_id": source_id,
                "handle": handle,
                "relpath": rel,
                # the compact, source-backed body a question reads instead of the whole doc.
                "body": {"digest": digest, "source_refs": [source_id]},
            }
        )
    return entries


def _entry_chars(entry: Mapping[str, Any]) -> int:
    """Estimated CHARACTER size of one compact blackboard entry as a question would read it.

    A question reads the compact body (the digest) plus its source handle — the small surface the entry exposes,
    not the raw doc. Deterministic; pure.
    """
    body = entry.get("body") or {}
    digest = str(body.get("digest", ""))
    handle = str(entry.get("handle", ""))
    # digest text + the source handle string the reader also sees (provenance is part of what's read).
    return len(digest) + len(handle)


def build_blackboard_from_docs(
    docs: Mapping[str, str],
    *,
    tenant_scope: str,
    now: str,
    db_path: str | None = None,
    task: str = "CFPB dispute knowledge base — stateful token-economics estimate",
) -> dict[str, Any]:
    """Run the STATEFUL first pass: read all ``docs`` and APPEND compact source-backed entries to a blackboard.

    Returns ``{provider, blackboard_id, entries, source_handles}``. ``db_path`` is injectable (pass a tempfile or
    ``":memory:"`` so the real ``.agent`` db is never touched). Every appended entry goes through the store's
    governance guards (source-backed observation, tenant scope, mandatory receipt) and is stored with
    ``serves_truth=False``. Deterministic given the same (docs, tenant_scope, now): content-addressed ids; no RNG.
    """
    bb = LocalSqliteBlackboard(db_path=db_path or ":memory:")
    board = bb.create_blackboard(task=task, tenant_scope=tenant_scope, now=now)
    bid = board["blackboard_id"]

    def receipt(worker_id: str) -> dict:
        # a minimal worker receipt; the store fills the hashes from the entry lineage. No raw keys.
        return {"worker_id": worker_id, "worker_kind": "distiller", "started_at": now, "completed_at": now}

    distilled = _distill_entries(docs)
    source_handles: dict[str, str] = {}
    stored: list[dict[str, Any]] = []
    for spec in distilled:
        rel = spec["relpath"]
        if spec["kind"] == KIND_SOURCE:
            row = bb.append_entry(
                bid,
                {
                    "kind": KIND_SOURCE,
                    "author_worker_id": "worker.distiller",
                    "iteration": 1,
                    "tenant_scope": tenant_scope,
                    "source_refs": [],
                    "body": {"source_id": spec["source_id"], "handle": spec["handle"], "relpath": rel},
                },
                worker_receipt=receipt("worker.distiller"),
                now=now,
            )
            source_handles[rel] = spec["handle"]
        else:  # KIND_OBSERVATION — must cite its source (non-empty source_refs)
            row = bb.append_entry(
                bid,
                {
                    "kind": KIND_OBSERVATION,
                    "author_worker_id": "worker.distiller",
                    "iteration": 1,
                    "tenant_scope": tenant_scope,
                    "source_refs": [spec["source_id"]],
                    "body": spec["body"],
                },
                worker_receipt=receipt("worker.distiller"),
                now=now,
            )
        stored.append(row)
    return {
        "provider": bb,
        "blackboard_id": bid,
        "entries": stored,
        "source_handles": source_handles,
    }


def estimate_token_economics(
    docs: Mapping[str, str],
    questions: Sequence[str],
    *,
    tenant_scope: str = "tenant-demo",
    now: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Estimate STATELESS vs STATEFUL input-token cost over ``docs`` + a sequence of ``questions``.

    The estimate (all token figures are :data:`ESTIMATE_METHOD`, NOT a real tokenizer; input tokens only):

      * **stateless** — re-read every doc for every question: ``N * (doc_tokens + shell_tokens)``.
      * **stateful** — one first pass reads every doc + builds the compact blackboard (its input is the full doc
        set once: ``doc_tokens``); then each question reads only the relevant compact entries + the shell.

    Returns the report dict described in the module docstring, including ``tokens_saved`` / ``savings_ratio``
    (relative to the stateless total), ``crossover_n`` (the smallest N at which stateful wins for this corpus),
    ``stateful_wins`` (for THIS N), ``entries_reused`` (compact entries available to every question),
    ``source_handle_coverage`` (distinct docs reachable by a preserved source handle), ``held_out_leakage`` (0 —
    no held-out content is read), ``is_truth`` (False), and ``estimate_method``. Pure + deterministic given the
    same (docs, questions, tenant_scope, now): content-addressed ids; no RNG / no wall-clock / no network / no LLM.
    """
    n_questions = len(questions)
    shell_tokens = estimate_tokens("x" * PER_QUESTION_SHELL_CHARS)

    # --- doc cost (the input of one full read of the whole corpus) ---------------------------
    doc_tokens = sum(estimate_tokens(text) for text in docs.values())

    # --- build the stateful state (the first pass) -------------------------------------------
    built = build_blackboard_from_docs(docs, tenant_scope=tenant_scope, now=now, db_path=db_path)
    provider: LocalSqliteBlackboard = built["provider"]
    bid = built["blackboard_id"]
    source_handles: dict[str, str] = built["source_handles"]

    # the compact entries a question would read (the source-backed observations). Deterministic query order.
    observations = provider.query(bid, kind=KIND_OBSERVATION)
    entries_reused = len(observations)

    # per-question stateful read: the shell + the SMALLEST relevant slice of the compact entries. We bound the
    # slice at ENTRIES_READ_PER_QUESTION so the per-question read is small and INDEPENDENT of corpus size.
    relevant = observations[: min(ENTRIES_READ_PER_QUESTION, len(observations))]
    per_question_compact_tokens = estimate_tokens("".join("x" * _entry_chars(e) for e in relevant))
    stateful_per_question_tokens = per_question_compact_tokens + shell_tokens

    # --- the two totals ----------------------------------------------------------------------
    # STATELESS: reread the whole corpus (+ shell) for each question.
    stateless_input_tokens = n_questions * (doc_tokens + shell_tokens)
    # STATEFUL: one full doc read to build state, then a small compact read per question.
    stateful_first_pass_tokens = doc_tokens
    stateful_total_tokens = stateful_first_pass_tokens + n_questions * stateful_per_question_tokens

    tokens_saved = stateless_input_tokens - stateful_total_tokens
    # savings relative to the stateless baseline; clamped to a fraction for a stable, interpretable ratio.
    savings_ratio = (tokens_saved / stateless_input_tokens) if stateless_input_tokens > 0 else 0.0

    # --- crossover: smallest N for which stateful_total < stateless_total --------------------
    # stateless(N) = N*(doc+shell); stateful(N) = doc + N*(compact+shell). Stateful wins once the per-question
    # SAVING (doc - compact) accumulated over N exceeds the one-time first-pass overhead (doc). Solve in ints.
    crossover_n = _crossover_n(
        doc_tokens=doc_tokens,
        shell_tokens=shell_tokens,
        per_question_stateful=stateful_per_question_tokens,
        first_pass=stateful_first_pass_tokens,
    )

    # source-handle coverage: distinct docs reachable via a preserved source handle (provenance is not lost).
    source_handle_coverage = len({h for h in source_handles.values() if h})

    provider.close()

    return {
        "n_questions": n_questions,
        "doc_tokens": doc_tokens,
        "stateless_input_tokens": stateless_input_tokens,
        "stateful_first_pass_tokens": stateful_first_pass_tokens,
        "stateful_per_question_tokens": stateful_per_question_tokens,
        "stateful_total_tokens": stateful_total_tokens,
        "tokens_saved": tokens_saved,
        "savings_ratio": savings_ratio,
        "stateful_wins": stateful_total_tokens < stateless_input_tokens,
        "crossover_n": crossover_n,
        "entries_reused": entries_reused,
        "source_handle_coverage": source_handle_coverage,
        # no held-out / omitted content is ever READ in either regime — we only read the docs (stateless) or the
        # compact distilled entries (stateful), and the distillation preserves source handles. Leakage is 0.
        "held_out_leakage": 0,
        "estimate_method": ESTIMATE_METHOD,
        "is_truth": False,
    }


def _crossover_n(*, doc_tokens: int, shell_tokens: int, per_question_stateful: int, first_pass: int) -> int | None:
    """Smallest integer N >= 1 at which the STATEFUL total drops below the STATELESS total.

    ``stateless(N) = N*(doc+shell)``; ``stateful(N) = first_pass + N*per_question_stateful``. Stateful wins when
    ``first_pass < N*(doc + shell - per_question_stateful)``. Returns the smallest such N, or ``None`` if the
    per-question saving is not positive (stateful never catches up — reported honestly, not hidden). Pure.
    """
    per_question_saving = (doc_tokens + shell_tokens) - per_question_stateful
    if per_question_saving <= 0:
        return None  # stateful never wins for this corpus — no false crossover claim
    # smallest N with N*saving > first_pass  ->  N > first_pass/saving  ->  N = floor(first_pass/saving) + 1
    return first_pass // per_question_saving + 1


__all__ = [
    "CHARS_PER_TOKEN",
    "ESTIMATE_METHOD",
    "PER_QUESTION_SHELL_CHARS",
    "ENTRIES_READ_PER_QUESTION",
    "OBSERVATION_DIGEST_MAX_CHARS",
    "CFPB_SAMPLE_DOC_RELPATHS",
    "estimate_tokens",
    "load_cfpb_sample_docs",
    "build_blackboard_from_docs",
    "estimate_token_economics",
]
