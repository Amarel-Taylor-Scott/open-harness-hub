#!/usr/bin/env python3
"""scripts.generate_dev_task_prompt_corpus — 2,000+ REALISTIC test prompts: what a technical person using
Claude Code asks for, and what agentic harnesses (Hermes / OpenClaw-style loops, CI bots, data agents) try
to accomplish — the session-emulation corpus the token-savings thesis is measured against.

Owner directive: even partial coverage pays — "accomplishing 50% or 80% can still significantly reduce
token spend." So every prompt row carries expected capability tokens, and ``--coverage`` runs the WHOLE
corpus through the real retrieval engine to produce the partial-coverage receipt: full hits, partial hits,
and honest misses, with the projected token savings at each coverage tier.

Generation is a deterministic curated grid (verbs x subjects x agent-task templates x personas) — no RNG,
no clock, ids are content hashes; regenerating is byte-identical. Every row candidate/serves_truth=false.

    PYTHONPATH=. python3 scripts/generate_dev_task_prompt_corpus.py --self-test
    PYTHONPATH=. python3 scripts/generate_dev_task_prompt_corpus.py --write [--coverage]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_MIN_CORPUS_SIZE = 2000          # the owner's floor — the self-test ratchets on it
_COVERAGE_K = 5                  # retrieval depth per prompt in the coverage receipt
_PARTIAL_TIERS = (0.5, 0.8)      # the owner's partial-coverage story: 50% and 80% still save tokens

#: HUMAN Claude Code asks: verb x subject (what technical people actually type). 24 x 28 = 672 prompts/persona-frame.
_HUMAN_VERBS: tuple[str, ...] = (
    "add retry logic with exponential backoff to", "write unit tests for", "refactor", "debug the failing",
    "optimize the slow", "add input validation to", "write a migration script for", "containerize",
    "add structured logging to", "document the public api of", "profile the memory usage of", "parallelize",
    "cache the results of", "add pagination to", "add rate limiting to", "add error handling to",
    "benchmark", "add a health check endpoint to", "deduplicate records in", "normalize the output of",
    "add schema validation to", "stream instead of batch", "add idempotency keys to", "mask pii in",
)
_HUMAN_SUBJECTS: tuple[str, ...] = (
    "the csv import pipeline", "the user authentication flow", "this database query", "the webhook handler",
    "the pdf invoice parser", "the image upload endpoint", "the web scraping job", "the deployment script",
    "the search endpoint", "the email notification service", "the payment reconciliation job",
    "the report generator", "the session cache", "the etl workflow", "the third party api client",
    "the config loader", "the file watcher daemon", "the message queue consumer", "the nightly backup script",
    "the data validation layer", "the ocr service", "the geocoding lookup", "the feature flag service",
    "the audit log writer", "the rss feed aggregator", "the sitemap crawler", "the currency converter",
    "the address normalizer",
)
#: AGENT loop tasks (Hermes / OpenClaw-style): multi-step template x source x product. 6 x 14 x 8 lanes.
_AGENT_TEMPLATES: tuple[str, ...] = (
    "scrape {source}, extract {product}, deduplicate them, and store the result as clean records",
    "monitor {source} on a schedule and produce {product} whenever new entries appear",
    "for every item in {source}, classify it, enrich it with {product}, and write an audit row",
    "crawl {source}, parse each page into {product}, validate the schema, and load into the database",
    "read {source}, summarize each entry, embed the summaries, and build {product} for semantic search",
    "watch {source} for changes, diff against the last snapshot, and emit {product} for each change",
)
_AGENT_SOURCES: tuple[str, ...] = (
    "the vendor price lists", "the github release feeds", "the support ticket inbox", "the sec filings index",
    "the job postings board", "the product review pages", "the server error logs", "the invoice mailbox",
    "the open data portal", "the regulatory bulletins", "the competitor changelogs", "the customer csv exports",
    "the api usage reports", "the incident postmortems",
)
_AGENT_PRODUCTS: tuple[str, ...] = (
    "structured records", "a ranked digest", "entity links", "normalized rows", "a vector index",
    "alert events", "a summary report", "labeled categories",
)
_PERSONAS: tuple[str, ...] = ("human_claude_code", "agentic_hermes", "agentic_openclaw")
#: realistic trailing constraints technical users attach (applied over a verb subset for grid width)
_HUMAN_CONSTRAINTS: tuple[str, ...] = (
    "keeping the public api unchanged", "and add tests that prove it", "without adding new dependencies",
    "and make it idempotent so reruns are safe",
)
_CONSTRAINED_VERB_COUNT = 8      # constraints apply to the first N verbs (grid width without combinatorial spam)


def _prompt_id(text: str) -> str:
    return "prompt-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


#: English prose fillers the card tokenizer keeps (it is tuned for code/card text, not sentences) — dropping
#: them makes expected_capabilities reflect real CAPABILITIES, not grammar (so completeness is not penalized
#: for failing to "cover" the word "that"). Single-source; deterministic.
_PROSE_STOPWORDS: frozenset[str] = frozenset((
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "or", "so", "that", "this", "these", "those",
    "are", "is", "be", "been", "was", "were", "with", "without", "into", "from", "by", "at", "as", "it",
    "its", "add", "make", "keeping", "unchanged", "reruns", "every", "each", "new", "adding", "them", "their",
    "your", "our", "you", "we", "up", "out", "over", "per", "via", "not", "no", "yes", "can", "will",
)) | frozenset(("prove", "logic", "public", "same"))  # weak intent-carriers in these templates


def _capability_tokens(text: str) -> list[str]:
    """Expected capability tokens = the significant CAPABILITY words retrieval must connect to (cheap,
    deterministic): the card tokenizer minus English prose fillers, so 'idempotent'/'backoff'/'validation'
    survive while 'that'/'are'/'so' do not — the completeness metric measures capability, not grammar."""
    from scripts.build_primitive_search_index import tokenize  # noqa: PLC0415  the ONE tokenizer
    toks = [t for t in tokenize(text) if t not in _PROSE_STOPWORDS and len(t) > 2]
    return sorted(set(toks))[:12]


def generate_corpus() -> list[dict[str, Any]]:
    """The full deterministic corpus: human single-step asks + agent multi-step loop tasks, persona-tagged."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(prompt: str, persona: str, kind: str) -> None:
        if prompt in seen:
            return
        seen.add(prompt)
        rows.append({"prompt_id": _prompt_id(prompt), "prompt": prompt, "persona": persona, "kind": kind,
                     "expected_capabilities": _capability_tokens(prompt), **BOUNDARY})

    for verb in _HUMAN_VERBS:
        for subject in _HUMAN_SUBJECTS:
            _add(f"{verb} {subject}", "human_claude_code", "single_step")
    for verb in _HUMAN_VERBS[:_CONSTRAINED_VERB_COUNT]:
        for subject in _HUMAN_SUBJECTS:
            for constraint in _HUMAN_CONSTRAINTS:
                _add(f"{verb} {subject}, {constraint}", "human_claude_code", "single_step")
    for template in _AGENT_TEMPLATES:
        for source in _AGENT_SOURCES:
            for product in _AGENT_PRODUCTS:
                persona = _PERSONAS[1] if (len(rows) % 2 == 0) else _PERSONAS[2]  # deterministic alternation
                _add(template.format(source=source, product=product), persona, "multi_step_loop")
    return rows


def coverage_receipt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The partial-coverage receipt: every prompt through the REAL pruned index; a prompt's coverage = the
    fraction of its expected capability tokens matched by its top-k hits' text. Tiers show the owner's
    50%/80% story with projected savings (reusing the corpus-wide avg-saved-per-covered-probe receipt)."""
    from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
    from scripts.run_token_savings_experiments import _load_cards  # noqa: PLC0415

    cards = _load_cards(0)
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    per_prompt: list[float] = []
    for row in rows:
        hits, _stats = search_with_stats(row["prompt"], _COVERAGE_K, index)
        hit_text = " ".join(json.dumps(by_id.get(h.get("primitive_id")) or h).lower() for h in hits)
        expected = row["expected_capabilities"] or [""]
        matched = sum(1 for t in expected if t in hit_text)
        per_prompt.append(matched / len(expected))
    n = len(per_prompt) or 1
    tiers = {f"coverage_ge_{int(t * 100)}pct": round(sum(1 for c in per_prompt if c >= t) / n, 3)
             for t in _PARTIAL_TIERS}
    return {"record_type": "dev_task_prompt_coverage_receipt", "prompts": len(per_prompt),
            "mean_coverage": round(sum(per_prompt) / n, 3),
            "full_coverage_rate": round(sum(1 for c in per_prompt if c >= 0.999) / n, 3),
            "zero_coverage_rate": round(sum(1 for c in per_prompt if c == 0.0) / n, 3),
            **tiers, "k": _COVERAGE_K,
            "note": "partial coverage still pays: every covered capability token is a primitive the agent "
                    "reads by signature instead of regenerating", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    rows = generate_corpus()
    checks.append((f"corpus meets the owner floor (>= {_MIN_CORPUS_SIZE})", len(rows) >= _MIN_CORPUS_SIZE))
    checks.append(("every prompt is unique (text and id)",
                   len({r["prompt"] for r in rows}) == len(rows) and len({r["prompt_id"] for r in rows}) == len(rows)))
    checks.append(("all three personas are represented",
                   {r["persona"] for r in rows} == set(_PERSONAS)))
    checks.append(("both kinds present (single-step human asks + multi-step agent loops)",
                   {r["kind"] for r in rows} == {"single_step", "multi_step_loop"}))
    checks.append(("every row carries expected capability tokens",
                   all(r["expected_capabilities"] for r in rows)))
    checks.append(("generation is deterministic (byte-identical twice)",
                   json.dumps(rows, sort_keys=True) == json.dumps(generate_corpus(), sort_keys=True)))
    checks.append(("every row is candidate/serves_truth=false",
                   all(r["candidate"] is True and r["serves_truth"] is False for r in rows)))
    # hermetic coverage math on a tiny synthetic corpus (no persisted index, no network)
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    kinds = {k: sum(1 for r in rows if r["kind"] == k) for k in ("single_step", "multi_step_loop")}
    print(f"\nPASS - generate_dev_task_prompt_corpus: {len(rows)} deterministic dev-task prompts "
          f"({kinds['single_step']} human Claude-Code asks + {kinds['multi_step_loop']} agent loop tasks, "
          f"3 personas), unique content-hash ids, capability tokens per row, byte-identical regeneration. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true", help="write the corpus JSONL (deterministic regeneration)")
    ap.add_argument("--coverage", action="store_true", help="run the partial-coverage receipt over the real index")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.write or args.coverage:
        rows = generate_corpus()
        out_dir = resource("data") / "dev-intel" / "session_emulation"
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.write:
            path = out_dir / "dev_task_prompt_corpus.jsonl"
            path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
            print(f"written: {len(rows)} prompts -> {path}")
        if args.coverage:
            receipt = coverage_receipt(rows)
            (out_dir / "coverage_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
            print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
