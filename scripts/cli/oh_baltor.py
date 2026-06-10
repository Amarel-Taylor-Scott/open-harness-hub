#!/usr/bin/env python3
"""``oh-ce`` — the Open Harness Hub open-funnel developer CLI (M5).

The no-account, works-with-the-agent-you-already-run surface. This is the
**open funnel + consumption surface** for verified corpora described in the
north-star (``docs/codex/north-star.md`` §"The execution sequence", M5 done bar:
*"a dev installs, builds a governed harness, pulls a verified corpus, runs it
against their own agent — no account."*) and the positioning thesis
(``docs/strategy/north-star.md``: *OHH = the open, governed harness funnel; the
verified-context service is the business; the wedge = "we verify your docs are
RIGHT, not just current."*).

It is a **thin front end** over the already-shipped, already-self-tested backend.
It owns **no** product logic of its own — every subcommand imports and delegates:

  * ``serve <corpus.json> [--tier T] [--full] [--descriptor|--llms|--both]``
      Emit the **consumption surfaces** for a governed corpus, ready to drop into
      Claude Code / Codex / Cursor:
        - ``llms.txt`` / ``llms-full.txt`` via ``scripts.enrichment.serve.emit_llms_txt``
          — the REAL ``deliver.llms_txt`` surface (no integration, paste-anywhere).
        - the MCP **serve descriptor** via ``scripts.enrichment.serve.serve_descriptor``
          — the tool/resource CONTRACT an MCP client would mount. (The live
          JSON-RPC endpoint is a declared SEAM; see ``serve.SERVE_SEAMS``.)
      With ``--tier`` it also prints the tier-negotiation record (which tier fits
      and its MEASURED fidelity) from ``serve.negotiate_tier`` — the separate
      evaluator's number, never self-graded.

  * ``verify <claim> --sources <sources.json> [--min-independent N]``
      Run the deterministic multi-source corroborator
      (``scripts.processors.assurance.multi_source_corroborate.run``) on a claim
      and the sources it is HANDED, and print the verdict
      (corroborated / single-source / contradicted / uncorroborated) + the
      independent-publisher counts. This is the change-verification ≥2-source bar
      as a one-line developer tool — the "is this claim actually RIGHT?" wedge.

  * ``tiers <corpus.json> [--language L]``
      Show the raw / compressed / hyper-efficient **token counts + measured
      fidelity** for a corpus via ``scripts.enrichment.tier_pipeline`` (rolled up
      per document, the same way ``serve`` does). The CEaaS density story,
      runnable offline.

Honest scope (per the change-verification contract,
``docs/codex/change-verification-contract.md`` — *real vs. seam; no invented
metrics*):

  * REAL: every number printed is computed by the imported backend modules
    (token counts from the one ``count_tokens`` proxy; fidelity from the
    *separate* ``verify.compression_fidelity`` evaluator; verdicts from the
    deterministic corroborator). The CLI adds **no** scoring of its own.
  * SEAM (not faked): the **live MCP server** (this CLI emits the descriptor — a
    dict — not a running JSON-RPC wire); **live source fetching** for ``verify``
    (the corroborator scores only the sources it is handed — retrieval is a
    separate external component); per-request **metering**; **CDC re-serving**.
    These are surfaced through the backend's own seam ledgers and noted in
    ``--help`` / stderr, never hidden.

Runtime contract (declared per
``docs/architecture/component-execution-and-runtime-routing.md`` §4; surfaced as
``RUNTIME`` and asserted in the self-test):

  * ``process_kind   = cli.oh_ce`` — an operator/consumption front end.
  * ``deterministic  = true``  — same (inputs, flags) → byte-identical stdout. No
    clocks, RNG, env reads, or network. (The composed backend is itself
    deterministic; this layer adds none.)
  * ``idempotent     = true``  — re-running produces the same output.
  * ``side_effects   = "read/emit"``  — reads the small JSON inputs it is pointed
    at and writes to **stdout only**; it makes no network calls and performs no
    hidden filesystem writes. (Honest: a ``read`` of the named input file + an
    ``emit`` to stdout — nothing else.)
  * ``streaming      = false`` — whole input in, whole surface out.
  * ``latency_budget_ms = None`` — an interactive dev tool, not a hot serving
    path; the work it composes is bulk/offline refinery work (cpu pool).
  * ``trust_boundary = local`` — operates on local files + already-governed
    corpus content; no sandbox needed.
  * ``on_error       = raise`` — bad input raises (surfaced as a clean stderr
    message + non-zero exit); we never emit a malformed surface silently.

CLI / self-test:
    python3 scripts/cli/oh_ce.py --selftest        # proves all three subcommands
    python3 -m scripts.cli.oh_ce --selftest
    python3 -m scripts.cli.oh_ce serve corpus.json --tier --budget-tokens 2000
    python3 -m scripts.cli.oh_ce verify "the limit is USD 10,000" --sources s.json
    python3 -m scripts.cli.oh_ce tiers corpus.json
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# Make the repo root importable when this file is run *directly*
# (``python3 scripts/cli/oh_ce.py``). The CLI's whole job is to COMPOSE the
# shipped ``scripts.*`` backend modules, so it must import them; a direct-file
# invocation only has THIS file's directory on ``sys.path`` and ``import
# scripts`` would fail. Prepending the repo root (this file is
# ``<root>/scripts/cli/oh_ce.py`` → root is two parents up) keeps the clean
# package-qualified imports working under BOTH ``-m`` and direct invocation.
# Stdlib only; no-op under ``-m`` (already on path). Mirrors the identical guard
# in ``scripts/enrichment/serve.py`` and ``tier_pipeline.py``.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# ── Import the shipped backend (do NOT reimplement) ──────────────────────────
# M3 serving surfaces (llms.txt + MCP descriptor + tier negotiation).
from scripts.enrichment import serve as serve_mod
from scripts.enrichment.serve import (
    emit_llms_txt,
    negotiate_tier,
    serve_descriptor,
)

# M3 base tier pipeline + its canonical tier vocabulary / token proxy. We REUSE
# TIER_ORDER / count_tokens as the single source of truth so the CLI's tier
# language can't drift from the pipeline's keys (No-Magic-Values).
from scripts.enrichment import tier_pipeline
from scripts.enrichment.tier_pipeline import TIER_ORDER, count_tokens

# M1 corroboration (the verify wedge).
from scripts.processors.assurance import multi_source_corroborate

# ── Constants (single source of truth; No-Magic-Values) ──────────────────────

#: process_kind for this front end (open vocab per SPEC §16 / routing doc §4).
PROCESS_KIND = "cli.oh_ce"

#: The CLI program name (used in argparse + the descriptor banner).
PROG = "oh-ce"

#: Declared runtime-routing manifest. deterministic + idempotent + local trust
#: boundary + reads-a-file/writes-stdout → side_effects "read/emit" (NOT "none":
#: it does read the named input). Asserted in the self-test so it can't rot.
#: Mirrors the shape of ``serve.RUNTIME`` / ``tier_pipeline.RUNTIME``.
RUNTIME: dict[str, Any] = {
    "process_kind": PROCESS_KIND,
    "deterministic": True,
    "idempotent": True,
    "side_effects": "read/emit",  # reads the named JSON input; writes stdout only
    "streaming": False,
    "latency_budget_ms": None,
    "trust_boundary": "local",
    "on_error": "raise",
    "resource_pool": "cpu",  # the composed refinery work routes to the cheap pool
}

#: ``serve`` output-surface selectors. Default emits BOTH so a dev gets the
#: paste-anywhere artifact AND the MCP mount contract in one call.
SURFACE_LLMS = "llms"
SURFACE_DESCRIPTOR = "descriptor"
SURFACE_BOTH = "both"

#: Exit codes (small, documented; usable as CI/pipeline gates).
EXIT_OK = 0
#: ``verify`` returns this when the claim is NOT corroborated — so a dev can gate
#: a pipeline on "this claim is established by >= N independent publishers".
EXIT_NOT_CORROBORATED = 2
#: A malformed input / usage error (the ``on_error: raise`` path, surfaced clean).
EXIT_USAGE = 1


# ── Small IO helpers (read-only; stdout-only) ────────────────────────────────


def _load_json(path: str, *, what: str) -> Any:
    """Read + parse a small JSON input file. Raises ValueError on a bad path/JSON.

    The CLI's only read side effect. Honest failure (``on_error: raise``): a bad
    input becomes a clean ValueError (surfaced as a stderr message + non-zero
    exit by ``main``), never a silently-empty surface.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ValueError(f"{what} file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} file is not valid JSON ({path}): {exc}") from exc


def _dump_json(obj: Any) -> str:
    """Deterministic JSON for stdout: stable key order, UTF-8, 2-space indent."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)


# ── Subcommand: serve ────────────────────────────────────────────────────────


def cmd_serve(args: argparse.Namespace, *, out: Any) -> int:
    """Emit the consumption surfaces for a governed corpus.

    Delegates entirely to ``scripts.enrichment.serve``:
      * ``emit_llms_txt(corpus, full=...)`` → the ``llms.txt`` / ``llms-full.txt``
        artifact (the REAL ``deliver.llms_txt`` surface), printed verbatim so a
        dev can pipe it straight to a file.
      * ``serve_descriptor(corpus)`` → the MCP serve-descriptor CONTRACT (a dict;
        the live wire is a declared SEAM), printed as deterministic JSON.
      * ``negotiate_tier({...})`` → (only with ``--tier``) the chosen tier + its
        MEASURED fidelity (separate evaluator), printed as JSON.

    ``--llms`` / ``--descriptor`` / ``--both`` select the surface(s); default
    ``--both``. Returns EXIT_OK.
    """
    corpus = _load_json(args.corpus, what="corpus")

    surface = args.surface
    emitted_llms = False

    if surface in (SURFACE_LLMS, SURFACE_BOTH):
        # The artifact goes to stdout verbatim (no JSON wrapping) so it can be
        # redirected straight into an llms.txt / llms-full.txt file.
        text = emit_llms_txt(corpus, full=args.full)
        out.write(text)
        if not text.endswith("\n"):
            out.write("\n")
        emitted_llms = True

    if surface in (SURFACE_DESCRIPTOR, SURFACE_BOTH):
        descriptor = serve_descriptor(corpus)
        if emitted_llms:
            # Separate the two surfaces with a fenced banner so a human reading
            # combined stdout can tell where the artifact ends and the (JSON)
            # MCP contract begins. (When only one surface is requested, no banner
            # — keeps single-surface output clean for piping.)
            out.write("\n# --- MCP serve descriptor (contract; live wire is a SEAM) ---\n")
        out.write(_dump_json(descriptor))
        out.write("\n")

    if args.tier:
        request: dict[str, Any] = {"corpus": corpus}
        if args.budget_tokens is not None:
            request["budget_tokens"] = args.budget_tokens
        if args.latency_ms is not None:
            request["latency_ms"] = args.latency_ms
        if args.language:
            request["language"] = args.language
        negotiation = negotiate_tier(request)
        out.write("\n# --- tier negotiation (measured fidelity, separate evaluator) ---\n")
        out.write(_dump_json(negotiation))
        out.write("\n")

    return EXIT_OK


# ── Subcommand: verify ───────────────────────────────────────────────────────


def cmd_verify(args: argparse.Namespace, *, out: Any) -> int:
    """Corroborate a claim against the sources it is HANDED; print the verdict.

    Delegates to ``multi_source_corroborate.run``. The sources file is a JSON
    list of source records (each a string, or a dict carrying ``text`` +
    ``source_id``/``publisher`` for independence keying). Prints the full result
    (verdict + independent counts + supporting/contradicting ids) as JSON.

    HONEST: this scores ONLY the sources handed in — live web/browser retrieval
    of independent sources is a SEPARATE external component (a seam), not done
    here. Returns EXIT_OK when corroborated, else EXIT_NOT_CORROBORATED (usable
    as a CI/pipeline gate).
    """
    sources = _load_json(args.sources, what="sources")
    result = multi_source_corroborate.run(
        args.claim, sources, min_independent=args.min_independent
    )
    out.write(_dump_json(result))
    out.write("\n")
    return EXIT_OK if result["verdict"] == "corroborated" else EXIT_NOT_CORROBORATED


# ── Subcommand: tiers ────────────────────────────────────────────────────────


def _corpus_tier_rollup(corpus: Any, *, language: str | None = None) -> dict[str, Any]:
    """Roll the tier pipeline up over a corpus's documents (raw/compressed/hyper).

    Mirrors ``serve._aggregate_tiers``' composition rule — refine each document
    on its own (so a mixed code+prose corpus never makes the single-language
    structural compressor raise) and SUM the token counts / token-weight the
    fidelity — but is kept here rather than importing the private helper, so the
    ``tiers`` subcommand stays decoupled from ``serve``'s internals while still
    reusing the PUBLIC ``tier_pipeline.run`` + the shared ``count_tokens`` proxy
    and ``TIER_ORDER`` vocabulary (the single sources of truth).

    Returns a JSON-friendly dict:
      {
        "corpus_id": str | None,
        "tiers": [TIER_ORDER...],
        "tokens_by_tier": {tier: int},          # SUM across documents
        "fidelity_by_tier": {derived_tier: float},  # token-weighted mean (separate eval)
        "reduction_by_tier": {derived_tier: float},  # 1 - tokens/raw_tokens (audit)
        "document_count": int,
        "per_document": [ {doc_id, tokens_by_tier, fidelity_by_tier}... ],
      }
    """
    if not isinstance(corpus, dict):
        raise TypeError(f"corpus must be a dict, got {type(corpus).__name__}")
    documents = corpus.get("documents", [])
    if not isinstance(documents, list):
        raise TypeError("corpus['documents'] must be a list")

    tokens_by_tier: dict[str, int] = {tier: 0 for tier in TIER_ORDER}
    derived = tuple(t for t in TIER_ORDER if t != TIER_ORDER[0])  # all but raw
    fid_weighted: dict[str, float] = {tier: 0.0 for tier in derived}
    raw_weight = 0
    per_document: list[dict[str, Any]] = []

    for doc in documents:
        if not isinstance(doc, dict):
            continue
        content = ""
        for key in ("content", "text", "body"):
            val = doc.get(key)
            if isinstance(val, str):
                content = val
                break
        if not content:
            continue
        doc_lang = doc.get("language") or language
        result = tier_pipeline.run(content, language=doc_lang)
        for tier in TIER_ORDER:
            tokens_by_tier[tier] += result["tokens_by_tier"][tier]
        doc_raw = result["tokens_by_tier"][TIER_ORDER[0]]
        raw_weight += doc_raw
        for tier in derived:
            fid_weighted[tier] += result["fidelity_by_tier"][tier] * doc_raw
        per_document.append({
            "doc_id": str(doc.get("doc_id") or "").strip() or None,
            "tokens_by_tier": result["tokens_by_tier"],
            "fidelity_by_tier": result["fidelity_by_tier"],
        })

    fidelity_by_tier: dict[str, float] = {
        tier: (1.0 if raw_weight == 0 else round(fid_weighted[tier] / raw_weight, 6))
        for tier in derived
    }
    raw_total = tokens_by_tier[TIER_ORDER[0]]
    reduction_by_tier: dict[str, float] = {
        tier: (0.0 if raw_total == 0 else round(1.0 - tokens_by_tier[tier] / raw_total, 6))
        for tier in derived
    }

    return {
        "corpus_id": str(corpus.get("corpus_id") or "").strip() or None,
        "tiers": list(TIER_ORDER),
        "tokens_by_tier": tokens_by_tier,
        "fidelity_by_tier": fidelity_by_tier,
        "reduction_by_tier": reduction_by_tier,
        "document_count": len(per_document),
        "per_document": per_document,
    }


def cmd_tiers(args: argparse.Namespace, *, out: Any) -> int:
    """Show raw/compressed/hyper-efficient token counts + measured fidelity.

    Delegates to ``tier_pipeline.run`` per document and rolls up (see
    ``_corpus_tier_rollup``). Prints the rollup as deterministic JSON. Every
    number is the backend's — token counts from the one ``count_tokens`` proxy,
    fidelity from the *separate* evaluator. Returns EXIT_OK.
    """
    corpus = _load_json(args.corpus, what="corpus")
    rollup = _corpus_tier_rollup(corpus, language=args.language)
    out.write(_dump_json(rollup))
    out.write("\n")
    return EXIT_OK


# ── argparse wiring ──────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser. Kept separate so the self-test can drive it."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Open Harness Hub open-funnel CLI — emit verified-corpus consumption "
            "surfaces (serve), corroborate a claim (verify), or show token/fidelity "
            "tiers (tiers). Offline, no account; reads small JSON, writes stdout. "
            "Live MCP wire + live source fetch + metering are SEAMS (see --help)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--selftest", action="store_true",
        help="Run the offline self-test (proves all three subcommands) and exit.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # ── serve ──
    p_serve = sub.add_parser(
        "serve",
        help="Emit the consumption surfaces (llms.txt and/or the MCP descriptor) "
             "for a governed corpus, ready to drop into your agent.",
        description="Emit llms.txt / llms-full.txt (the deliver.llms_txt surface) "
                    "and/or the MCP serve descriptor (the mount CONTRACT; the live "
                    "JSON-RPC wire is a SEAM). With --tier, also print the "
                    "tier-negotiation record (chosen tier + MEASURED fidelity).",
    )
    p_serve.add_argument("corpus", help="Path to the governed-corpus JSON file.")
    surface_grp = p_serve.add_mutually_exclusive_group()
    surface_grp.add_argument(
        "--llms", dest="surface", action="store_const", const=SURFACE_LLMS,
        help="Emit only the llms.txt artifact (clean for piping to a file).",
    )
    surface_grp.add_argument(
        "--descriptor", dest="surface", action="store_const", const=SURFACE_DESCRIPTOR,
        help="Emit only the MCP serve descriptor (the mount contract).",
    )
    surface_grp.add_argument(
        "--both", dest="surface", action="store_const", const=SURFACE_BOTH,
        help="Emit both surfaces (default).",
    )
    p_serve.set_defaults(surface=SURFACE_BOTH)
    p_serve.add_argument(
        "--full", action="store_true",
        help="Emit llms-full.txt (inline each document's full content) instead of "
             "links-only llms.txt.",
    )
    p_serve.add_argument(
        "--tier", action="store_true",
        help="Also print the tier-negotiation record (which tier fits + its "
             "measured fidelity from the separate evaluator).",
    )
    p_serve.add_argument(
        "--budget-tokens", dest="budget_tokens", type=int, default=None,
        help="Token budget hint for --tier negotiation (a hard ceiling).",
    )
    p_serve.add_argument(
        "--latency-ms", dest="latency_ms", type=int, default=None,
        help="Latency hint (ms) for --tier negotiation (shapes the choice).",
    )
    p_serve.add_argument(
        "--language", default=None,
        help="Optional language hint forwarded to the tier pipeline (e.g. python).",
    )

    # ── verify ──
    p_verify = sub.add_parser(
        "verify",
        help="Corroborate a claim against a JSON list of sources; print the verdict.",
        description="Run the deterministic multi-source corroborator on a claim and "
                    "the sources it is HANDED (it does NOT fetch — live retrieval is a "
                    "separate component / SEAM). Exit 0 if corroborated, else 2 — "
                    "usable as a pipeline gate.",
    )
    p_verify.add_argument("claim", help="The claim text to corroborate.")
    p_verify.add_argument(
        "--sources", required=True,
        help="Path to a JSON list of source records (strings, or "
             "{\"text\": ..., \"source_id\": ...} dicts). Independence is by source id.",
    )
    p_verify.add_argument(
        "--min-independent", dest="min_independent", type=int,
        default=multi_source_corroborate.DEFAULT_MIN_INDEPENDENT,
        help="Minimum independent agreeing publishers for 'corroborated' "
             f"(default {multi_source_corroborate.DEFAULT_MIN_INDEPENDENT}).",
    )

    # ── tiers ──
    p_tiers = sub.add_parser(
        "tiers",
        help="Show raw/compressed/hyper-efficient token counts + measured fidelity.",
        description="Run the tier pipeline over a corpus's documents and roll up the "
                    "token counts (summed) + fidelity (token-weighted mean, from the "
                    "separate evaluator). The CEaaS density story, offline.",
    )
    p_tiers.add_argument("corpus", help="Path to the governed-corpus JSON file.")
    p_tiers.add_argument(
        "--language", default=None,
        help="Optional language hint forwarded to the tier pipeline (e.g. python).",
    )

    return parser


_DISPATCH = {
    "serve": cmd_serve,
    "verify": cmd_verify,
    "tiers": cmd_tiers,
}


def main(argv: list[str] | None = None, *, out: Any = None) -> int:
    """CLI entrypoint. Returns a process exit code; writes only to ``out`` (stdout).

    ``out`` is injectable so the self-test can capture stdout. ``on_error:
    raise`` is honored as a clean message: a malformed input (ValueError/
    TypeError) becomes a stderr line + EXIT_USAGE, never a traceback-as-output or
    a silent malformed surface.
    """
    if out is None:
        out = sys.stdout
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.command:
        parser.print_help(out)
        return EXIT_OK

    handler = _DISPATCH[args.command]
    try:
        return handler(args, out=out)
    except (TypeError, ValueError) as exc:
        # on_error=raise, surfaced cleanly: the dev sees what was malformed, the
        # process exits non-zero, and stdout is NOT polluted with a half-surface.
        print(f"{PROG} {args.command}: error: {exc}", file=sys.stderr)
        return EXIT_USAGE


# ── Self-test (proves each subcommand produces correct output) ───────────────
#
# Tiny REAL fixtures (no network, no files): a governed corpus with one code doc
# (so the tiers have real structure to compress and the token order is strict)
# plus a prose doc, and a corroboration claim + sources covering the corroborated
# AND contradicted verdicts. The self-test drives ``main`` exactly as a shell
# would (argv in, exit code out, stdout captured) so it proves the REAL CLI path,
# not just the helper functions.

import io  # noqa: E402  (stdlib; only needed by the self-test)
import os  # noqa: E402
import tempfile  # noqa: E402

_SELFTEST_CORPUS: dict[str, Any] = {
    "corpus_id": "oh-ce-selftest",
    "title": "oh-ce self-test corpus",
    "summary": "A tiny governed corpus used to prove the open-funnel CLI offline.",
    "license": "MIT",
    "provenance": {
        "signer": "openharnesshub.com (selftest oracle)",
        "source": "scripts/cli/oh_ce.py self-test fixture",
        "updated": "2026-05-29",
    },
    "documents": [
        {
            "doc_id": "budget",
            "title": "Token budget planner",
            "url": "https://openharnesshub.com/docs/budget",
            "section": "Reference",
            "notes": "How the token budget is planned.",
            "content": (
                '"""Token-budget planner."""\n'
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
                '    """True when text fits the planned budget."""\n'
                "    return len(text.split()) <= plan_budget(window)\n"
            ),
        },
        {
            "doc_id": "overview",
            "title": "What this corpus is",
            "url": "https://openharnesshub.com/docs/overview",
            "notes": "Plain-language overview.",
            "content": "This corpus is a tiny demo used only to exercise the CLI.\n",
        },
    ],
}

_SELFTEST_CLAIM = "The daily wire-transfer limit is USD 10,000 per account."

# Two DISTINCT publishers agreeing → corroborated (exit 0).
_SELFTEST_SOURCES_OK: list[dict[str, Any]] = [
    {"source_id": "reuters", "text": "Reuters: the daily wire-transfer limit is USD 10,000."},
    {"source_id": "central-bank", "text": "Per the regulator, the wire transfer limit is $10,000 daily."},
]

# One independent publisher asserts a DIFFERENT value → contradicted (exit 2).
_SELFTEST_SOURCES_CONFLICT: list[dict[str, Any]] = [
    {"source_id": "reuters", "text": "Reuters: the daily wire-transfer limit is USD 10,000."},
    {"source_id": "planted-memo", "text": "URGENT: the daily wire-transfer limit is now USD 50,000."},
]


def _run_cli(argv: list[str]) -> tuple[int, str]:
    """Drive ``main`` with a captured stdout; return (exit_code, stdout_text)."""
    buf = io.StringIO()
    code = main(argv, out=buf)
    return code, buf.getvalue()


def _selftest() -> int:
    # Write the fixtures to a private temp dir (the ONLY filesystem touch — the
    # CLI's contract is "reads a small JSON input"; we give it real files to read,
    # then clean them up, so nothing leaks into the repo).
    tmp = tempfile.mkdtemp(prefix="oh_ce_selftest_")
    corpus_path = os.path.join(tmp, "corpus.json")
    sources_ok_path = os.path.join(tmp, "sources_ok.json")
    sources_conflict_path = os.path.join(tmp, "sources_conflict.json")
    try:
        with open(corpus_path, "w", encoding="utf-8") as fh:
            json.dump(_SELFTEST_CORPUS, fh)
        with open(sources_ok_path, "w", encoding="utf-8") as fh:
            json.dump(_SELFTEST_SOURCES_OK, fh)
        with open(sources_conflict_path, "w", encoding="utf-8") as fh:
            json.dump(_SELFTEST_SOURCES_CONFLICT, fh)

        # ── (a) serve --llms : a well-formed llms.txt artifact. ──
        code, llms = _run_cli(["serve", corpus_path, "--llms"])
        assert code == EXIT_OK, f"serve --llms exit {code}"
        lines = llms.splitlines()
        assert lines[0] == "# oh-ce self-test corpus", \
            f"llms.txt must open with the H1 title, got {lines[0]!r}"
        assert any(ln.startswith("> ") and "tiny governed corpus" in ln for ln in lines), \
            "llms.txt missing the blockquote summary"
        # The moat on the surface: the provenance/signer line is carried through.
        assert any("Governed corpus `oh-ce-selftest`" in ln and "signed by" in ln for ln in lines), \
            "llms.txt missing the provenance info line"
        assert "## Reference" in llms, "llms.txt missing the Reference section"
        assert "- [Token budget planner](https://openharnesshub.com/docs/budget): " in llms, \
            "llms.txt link not in the spec '- [name](url): notes' format"
        # links-only must NOT inline document bodies.
        assert "def plan_budget(" not in llms, "links-only llms.txt must not inline content"
        # It must be byte-identical to the backend's own emitter (no CLI mangling).
        assert llms == emit_llms_txt(_SELFTEST_CORPUS) , \
            "serve --llms must print the backend emit_llms_txt output verbatim"

        # ── (a2) serve --full : llms-full.txt inlines the document bodies. ──
        code, full = _run_cli(["serve", corpus_path, "--llms", "--full"])
        assert code == EXIT_OK
        assert "def plan_budget(" in full, "serve --full (llms-full.txt) must inline content"
        assert len(full) > len(llms), "llms-full.txt must be larger than links-only llms.txt"

        # ── (a3) serve --descriptor : the MCP serve-descriptor CONTRACT (JSON). ──
        code, desc_out = _run_cli(["serve", corpus_path, "--descriptor"])
        assert code == EXIT_OK
        descriptor = json.loads(desc_out)  # must be parseable JSON on its own
        assert descriptor == serve_descriptor(_SELFTEST_CORPUS), \
            "serve --descriptor must print serve_descriptor() verbatim"
        assert descriptor["serverInfo"]["corpusId"] == "oh-ce-selftest"
        # one MCP resource per governed document, carrying provenance.
        assert len(descriptor["resources"]) == len(_SELFTEST_CORPUS["documents"])
        # the live MCP endpoint is honestly declared a SEAM, not faked as a wire.
        assert any("live MCP endpoint" in s for s in descriptor["seams"]), \
            "descriptor must declare the live MCP endpoint as a seam"

        # ── (a4) serve --tier : the tier-negotiation record with MEASURED fidelity. ──
        # A budget below raw but at/above compressed must pick a DERIVED tier and
        # carry a measured fidelity in [0,1] (the separate evaluator's number).
        roll = _corpus_tier_rollup(_SELFTEST_CORPUS)
        comp_tok = roll["tokens_by_tier"][TIER_ORDER[1]]  # compressed
        code, tier_out = _run_cli(
            ["serve", corpus_path, "--descriptor", "--tier", "--budget-tokens", str(comp_tok)]
        )
        assert code == EXIT_OK
        # stdout carries the descriptor JSON + a tier-negotiation block; pull the
        # negotiation JSON out from after its banner and parse it.
        marker = "# --- tier negotiation"
        assert marker in tier_out, "serve --tier must emit the tier-negotiation block"
        neg_json = tier_out.split(marker, 1)[1].split("\n", 1)[1]
        negotiation = json.loads(neg_json)
        assert negotiation["tier"] in (TIER_ORDER[1], TIER_ORDER[2]), \
            f"budget below raw must pick a derived tier, got {negotiation['tier']}"
        assert negotiation["tokens"] <= comp_tok and negotiation["fits_budget"] is True
        fid = negotiation["fidelity"]
        assert isinstance(fid, (int, float)) and 0.0 <= fid <= 1.0, \
            f"derived tier must carry measured fidelity in [0,1], got {fid!r}"

        # ── (b) verify : the verdict is CORRECT for both the agree + conflict cases. ──
        # Two distinct agreeing publishers → corroborated → exit 0.
        code, vout = _run_cli(["verify", _SELFTEST_CLAIM, "--sources", sources_ok_path])
        result = json.loads(vout)
        assert result["verdict"] == "corroborated", \
            f"two distinct agreeing publishers must corroborate, got {result['verdict']}"
        assert result["agreeing_independent"] == 2
        assert code == EXIT_OK, f"corroborated must exit {EXIT_OK}, got {code}"
        # It must equal the backend corroborator's own output (no CLI massaging).
        assert result == multi_source_corroborate.run(
            _SELFTEST_CLAIM, _SELFTEST_SOURCES_OK,
            min_independent=multi_source_corroborate.DEFAULT_MIN_INDEPENDENT,
        ), "verify must print the backend corroborator output verbatim"

        # One independent contradicting publisher → contradicted → exit 2 (gate).
        code, vout2 = _run_cli(["verify", _SELFTEST_CLAIM, "--sources", sources_conflict_path])
        result2 = json.loads(vout2)
        assert result2["verdict"] == "contradicted", \
            f"a conflicting independent source must contradict, got {result2['verdict']}"
        assert result2["contradicting_source_ids"] == ["planted-memo"]
        assert code == EXIT_NOT_CORROBORATED, \
            f"non-corroborated must exit {EXIT_NOT_CORROBORATED} (the gate), got {code}"

        # --min-independent raises the bar: 2 agreeing with bar=3 → single-source → exit 2.
        code, vout3 = _run_cli(
            ["verify", _SELFTEST_CLAIM, "--sources", sources_ok_path, "--min-independent", "3"]
        )
        result3 = json.loads(vout3)
        assert result3["verdict"] == "single-source", \
            f"2 agreeing with bar=3 must be single-source, got {result3['verdict']}"
        assert code == EXIT_NOT_CORROBORATED, "single-source must hit the non-corroborated gate"

        # ── (c) tiers : token counts MONOTONE non-increasing + fidelity in [0,1]. ──
        code, tiers_out = _run_cli(["tiers", corpus_path])
        assert code == EXIT_OK
        rollup = json.loads(tiers_out)
        tok = rollup["tokens_by_tier"]
        raw_t = tok[TIER_ORDER[0]]
        comp_t = tok[TIER_ORDER[1]]
        hyper_t = tok[TIER_ORDER[2]]
        # Monotone non-increasing across the tier order (the orderable property).
        assert raw_t >= comp_t >= hyper_t, \
            f"tiers tokens must be monotone non-increasing, got {raw_t}>={comp_t}>={hyper_t}"
        # The code-bearing corpus gives a STRICT reduction (raw > compressed) — proof
        # the compression tier is doing real work, not a passthrough.
        assert raw_t > comp_t, \
            f"code corpus must give a strict raw>compressed reduction, got {raw_t}!>{comp_t}"
        # Fidelity present for both derived tiers, each a measured number in [0,1].
        for tier in (TIER_ORDER[1], TIER_ORDER[2]):
            score = rollup["fidelity_by_tier"][tier]
            assert isinstance(score, (int, float)) and 0.0 <= score <= 1.0, \
                f"{tier} fidelity must be in [0,1], got {score!r}"
        # reduction_by_tier is the honest 1 - tokens/raw audit number.
        assert abs(rollup["reduction_by_tier"][TIER_ORDER[1]] - (1.0 - comp_t / raw_t)) < 1e-6
        assert rollup["document_count"] == 2

        # ── Determinism: re-running every subcommand is byte-identical stdout. ──
        for argv in (
            ["serve", corpus_path, "--llms"],
            ["serve", corpus_path, "--descriptor"],
            ["verify", _SELFTEST_CLAIM, "--sources", sources_ok_path],
            ["tiers", corpus_path],
        ):
            first = _run_cli(argv)
            second = _run_cli(argv)
            assert first == second, f"non-deterministic stdout for {argv!r}"

        # ── on_error=raise, surfaced cleanly: a missing file → EXIT_USAGE, empty stdout. ──
        missing = os.path.join(tmp, "does_not_exist.json")
        code, miss_out = _run_cli(["tiers", missing])
        assert code == EXIT_USAGE, f"missing input must exit {EXIT_USAGE}, got {code}"
        assert miss_out == "", "a usage error must NOT pollute stdout with a half-surface"

        # ── Runtime manifest is the declared one + self-consistent with routing §4. ──
        assert RUNTIME["process_kind"] == PROCESS_KIND
        assert RUNTIME["deterministic"] is True and RUNTIME["idempotent"] is True
        assert RUNTIME["side_effects"] == "read/emit"
        assert RUNTIME["streaming"] is False and RUNTIME["latency_budget_ms"] is None
        assert RUNTIME["trust_boundary"] == "local"
        assert RUNTIME["resource_pool"] == "cpu", f"routing pool mismatch: {RUNTIME['resource_pool']}"

    finally:
        # Clean up the temp fixtures — leave NO trace (no hidden writes survive).
        for path in (corpus_path, sources_ok_path, sources_conflict_path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass

    print(
        "PASS — oh-ce CLI: "
        "serve --llms emits a well-formed llms.txt (H1+summary+provenance line, "
        "Reference section, spec link format; --full inlines bodies) byte-identical "
        "to emit_llms_txt; serve --descriptor emits the MCP contract (live wire = seam) "
        "verbatim from serve_descriptor; serve --tier picks a derived tier with measured "
        f"fidelity (separate eval); verify corroborates 2 distinct publishers (exit {EXIT_OK}) "
        f"and flags a conflicting source as contradicted (exit {EXIT_NOT_CORROBORATED}), bar "
        f"configurable; tiers shows tokens raw={raw_t}>compressed={comp_t}>=hyper={hyper_t} "
        "(monotone, strict raw>compressed) + per-tier fidelity in [0,1]; deterministic "
        "stdout; bad input → clean exit, empty stdout; runtime=cpu pool. "
        "(live MCP wire + live source fetch + metering are declared SEAMS)"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
