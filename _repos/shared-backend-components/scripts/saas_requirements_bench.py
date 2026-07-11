#!/usr/bin/env python3
"""scripts.saas_requirements_bench — the COMMON-TASKS benchmark: every requirement of building a production
SaaS (auth · tenancy · RBAC · billing · webhooks · rate limiting · queues · uploads · search · caching ·
migrations · API design · audit logging · observability · CI/CD · secrets · security · compliance ·
onboarding · admin · feature flags · analytics · i18n · realtime · …), each as a realistic dev-task query,
retrieved INDEPENDENTLY over the FULL corpus per path.

HIT = verified-precision style (same bar as bench_domain_token_savings): a top-k card counts only if its
searchable text carries one of the requirement's EXPECTED CONCEPT TOKENS — "returned something" is never
coverage. The suite itself is DATA (`data/dev-intel/session_emulation/saas_requirements_suite.jsonl`) — it
doubles as the seed of the real labelled gold set (ir-nlp roadmap #2) and grows without code changes.

Retrievers raced per requirement: lexical inverted index · dense STORED blackbox lane · the STORED 3-register
lane · RRF fusion of all three — the receipt shows which SaaS areas the corpus covers, which path finds them,
and where the corpus has GAPS (misses are per-category repair signals, never averaged away). 0 LLM calls.

serves_truth=false — coverage of a requirement is a measurement, never served truth.

    PYTHONPATH=. python3 scripts/saas_requirements_bench.py --self-test
    PYTHONPATH=. python3 scripts/saas_requirements_bench.py --run [--k 5]
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
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: stored lanes + card text

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_K = 5
#: the suite lives as DATA — the gold-set seed; growing it is a data change, never a code change.
_SUITE_FILENAME = "saas_requirements_suite.jsonl"


def suite_path() -> Path:
    return resource("data") / "dev-intel" / "session_emulation" / _SUITE_FILENAME


def load_suite(path: Optional[Path] = None) -> list[dict[str, Any]]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = path or suite_path()
    return [r for r in read_jsonl_tolerant(p)
            if r.get("query") and r.get("expected_tokens") and r.get("category")] if p.exists() else []


def _card_tokens(card: dict[str, Any]) -> frozenset:
    """The searchable TOKEN SET a hit is verified against (title + blackbox + edges + blocking keys), split on
    non-alphanumerics. Token-boundary membership, never substring — "sso" must NOT match "processor"."""
    import re  # noqa: PLC0415
    text = " ".join([str(card.get("title") or ""), _emb.blackbox_text(card),
                     str(card.get("input_edge") or ""), str(card.get("output_edge") or ""),
                     " ".join(map(str, card.get("blocking_keys") or []))]).lower()
    return frozenset(re.split(r"[^a-z0-9]+", text)) - {""}


def _verified_hit(top_cards: list[dict[str, Any]], expected_tokens: list[str]) -> bool:
    """A requirement is covered only if a top-k card's TOKEN SET carries an expected CONCEPT token (multi-word
    expected tokens count when every word is present). Expected tokens are split with the SAME [^a-z0-9]+
    rule as card text — a hyphenated expected token like "full-text" must match "full text" in a card
    (review finding: whitespace-only splitting made hyphenated tokens unmatchable)."""
    import re  # noqa: PLC0415
    for c in top_cards:
        toks = _card_tokens(c)
        for t in expected_tokens:
            words = [w for w in re.split(r"[^a-z0-9]+", str(t).lower()) if w]
            if words and all(w in toks for w in words):
                return True
    return False


def _retrievers(cards: list[dict[str, Any]], k: int) -> dict[str, Callable[[str], list[dict[str, Any]]]]:
    from scripts import rank_fusion_zoo as _f  # noqa: PLC0415
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards}
    path = _emb.real_text_path()

    def _cards_of(ids: list[str]) -> list[dict[str, Any]]:
        return [by_id[i] for i in ids if i in by_id]

    def _lex(q: str, kk: int = k) -> list[str]:
        hits, _stats = search_with_stats(q, kk, index)
        return [h["primitive_id"] for h in hits]

    def _dense(q: str, kk: int = k) -> list[str]:
        return [h["primitive_id"] for h in _emb.intent_query(q, cards, k=kk, path=path)]

    def _registers(q: str, kk: int = k) -> list[str]:
        return [h["primitive_id"] for h in _emb.intent_query_registers(q, cards, k=kk, path=path)]

    def _fusion(q: str) -> list[dict[str, Any]]:
        fused = _f.rrf({"lexical": _lex(q, k * 4), "dense": _dense(q, k * 4), "registers": _registers(q, k * 4)})
        return _cards_of([r["primitive_id"] for r in fused][:k])

    return {"lexical": lambda q: _cards_of(_lex(q)), "dense": lambda q: _cards_of(_dense(q)),
            "registers": lambda q: _cards_of(_registers(q)), "fusion": _fusion}


def measure(cards: list[dict[str, Any]], suite: list[dict[str, Any]], *, k: int = _DEFAULT_K) -> dict[str, Any]:
    """Verified hit-rate per retriever + UNION, per SaaS category and overall; misses named per requirement."""
    rets = _retrievers(cards, k)
    per_ret_hits = {name: 0 for name in rets}
    union_hits = 0
    by_category: dict[str, dict[str, int]] = {}
    misses: list[dict[str, str]] = []
    for req in suite:
        cat = str(req["category"])
        by_category.setdefault(cat, {"total": 0, "union_hits": 0})
        by_category[cat]["total"] += 1
        covered_any = False
        for name, fn in rets.items():
            hit = _verified_hit(fn(req["query"]), req["expected_tokens"])
            if hit:
                per_ret_hits[name] += 1
                covered_any = True
        if covered_any:
            union_hits += 1
            by_category[cat]["union_hits"] += 1
        else:
            misses.append({"category": cat, "requirement": str(req.get("requirement") or ""),
                           "query": str(req["query"])})
    n = len(suite) or 1
    return {"record_type": "saas_requirements_benchmark", "requirements": len(suite), "k": k,
            "corpus_cards": len(cards), "embed_path": _emb.real_text_path(),
            "verified_hit_rate": {name: round(h / n, 4) for name, h in per_ret_hits.items()},
            "union_hit_rate": round(union_hits / n, 4),
            "by_category": {c: {"total": v["total"],
                                "union_hit_rate": round(v["union_hits"] / v["total"], 4)}
                            for c, v in sorted(by_category.items())},
            "uncovered_requirements": misses,
            "note": "HIT is VERIFIED (a top-k card must carry an expected concept token) — never 'returned "
                    "something'. Misses are per-requirement corpus-gap signals (acquisition leads), not "
                    "noise. The suite JSONL doubles as the labelled gold-set seed (roadmap #2).", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "s:oauth", "title": "OAuth login flow handler",
         "blackbox": "Handle the oauth authorization code flow and issue a session token on callback.",
         "input_edge": "AuthCallback", "output_edge": "SessionToken", **BOUNDARY},
        {"primitive_id": "s:stripe", "title": "Subscription billing processor",
         "blackbox": "Create and update stripe subscription invoices with proration and dunning retries.",
         "input_edge": "SubscriptionChange", "output_edge": "Invoice", **BOUNDARY},
        {"primitive_id": "s:zeta", "title": "Zeta widget", "blackbox": "Sigma gadget flux capacitor.",
         "input_edge": "ZetaIn", "output_edge": "ZetaOut", **BOUNDARY},
    ]
    suite = [
        {"category": "auth", "requirement": "social login", "query": "let users sign in with google",
         "expected_tokens": ["oauth", "sso"]},
        {"category": "billing", "requirement": "subscriptions", "query": "charge customers monthly with retries",
         "expected_tokens": ["stripe", "subscription", "invoice"]},
        {"category": "search", "requirement": "full-text search", "query": "let users search their documents",
         "expected_tokens": ["elasticsearch", "fulltext"]},  # nothing in this corpus covers it -> honest miss
    ]
    rec = measure(cards, suite, k=2)
    checks.append(("a covered requirement is a VERIFIED hit (token present in a top-k card)",
                   rec["by_category"]["auth"]["union_hit_rate"] == 1.0
                   and rec["by_category"]["billing"]["union_hit_rate"] == 1.0))
    checks.append(("an uncovered requirement is an HONEST miss, named as a corpus gap (never averaged away)",
                   rec["by_category"]["search"]["union_hit_rate"] == 0.0
                   and any(m["category"] == "search" for m in rec["uncovered_requirements"])))
    checks.append(("every retriever reports a rate incl. the stored register lane + fusion",
                   set(rec["verified_hit_rate"]) == {"lexical", "dense", "registers", "fusion"}))
    checks.append(("union rate >= best single retriever (union never loses)",
                   rec["union_hit_rate"] >= max(rec["verified_hit_rate"].values())))
    # mutation: claiming a hit without the token present must be impossible
    checks.append(("the verified-hit gate refuses a card without the expected token (mutation)",
                   not _verified_hit([cards[2]], ["oauth"]) and _verified_hit([cards[0]], ["oauth"])))
    checks.append(("the gate matches TOKEN BOUNDARIES, never substrings ('sso' must not match 'processor')",
                   not _verified_hit([{"title": "Batch processor", "blackbox": "Processes associated records.",
                                       **BOUNDARY}], ["sso"])))
    checks.append(("hyphenated expected tokens match across the same split ('full-text' ~ 'full text search')",
                   _verified_hit([{"title": "Full text search engine", "blackbox": "Index documents.",
                                   **BOUNDARY}], ["full-text"])))
    checks.append(("the receipt is deterministic (byte-identical twice)",
                   json.dumps(measure(cards, suite, k=2), sort_keys=True)
                   == json.dumps(measure(cards, suite, k=2), sort_keys=True)))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - saas_requirements_bench: every-requirement-of-a-SaaS coverage with VERIFIED hits "
          "(expected concept token must appear in a top-k card), independent retrieval per path (lexical + "
          "stored dense + stored 3-register + fusion), per-category rates, honest named misses as corpus-gap "
          "acquisition leads, deterministic receipts. The suite JSONL is the gold-set seed. serves_truth=false.")
    return 0


def _run(k: int, suite_file: Optional[str] = None) -> int:
    from scripts import path_graph_bench as _bench  # noqa: PLC0415  REUSE: the corpus loader
    chosen = Path(suite_file) if suite_file else suite_path()
    suite = load_suite(chosen)
    if not suite:
        print(f"no suite at {chosen} — write the requirement rows there first")
        return 1
    cards = _bench._load_scale_corpus(None)  # noqa: SLF001
    print(f"benchmarking {len(suite)} requirements ({chosen.name}) over {len(cards)} cards, 4 retrievers ...")
    rec = measure(cards, suite, k=k)
    out = (resource("data") / "dev-intel" / "session_emulation"
           / (f"{Path(suite_file).stem}_receipt.json" if suite_file else "saas_requirements_receipt.json"))
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({kk: rec[kk] for kk in ("requirements", "verified_hit_rate", "union_hit_rate")},
                     indent=2, sort_keys=True))
    print(json.dumps(rec["by_category"], indent=2, sort_keys=True))
    print(f"uncovered: {len(rec['uncovered_requirements'])}")
    print(f"\nwritten: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="full-corpus SaaS-requirements coverage + receipt")
    ap.add_argument("--k", type=int, default=_DEFAULT_K)
    ap.add_argument("--suite", default=None,
                    help="alternate suite JSONL (same row schema) — one bench, many suites (e.g. the Kaggle "
                         "competition-archetype suite); receipt name derives from the suite filename")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.k, args.suite)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
