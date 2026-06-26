#!/usr/bin/env python3
"""scripts.check_stateful_vs_stateless_token_economics — PROOF: the stateful-blackboard thesis, in numbers.

The thesis: building durable, typed, source-backed STATE once (a blackboard) and then querying it beats
re-reading the source documents on every question. This proof turns that into a DETERMINISTIC, OFFLINE token
ESTIMATE over the bundled SYNTHETIC CFPB-sample corpus + a sequence of follow-up questions, and asserts the
**crossover** — above a small N the stateful total input-token estimate drops below the stateless one — rather
than a blanket "stateful always wins" claim.

Honest framing baked into the assertions (no overclaim):
  * the figures are a chars/4 HEURISTIC, NOT a real tokenizer, and INPUT tokens only — the report is labeled
    ``is_truth=False`` and ``estimate_method`` names the heuristic; both are asserted here;
  * the N=1 degenerate case (first-pass overhead can make stateless cheaper) is handled honestly — the proof
    asserts the crossover N, and that stateful does NOT necessarily win at N=1;
  * no held-out / omitted source content is read in either regime (``held_out_leakage == 0``), and the
    distillation PRESERVES source handles (``source_handle_coverage > 0``).

Asserts:
  A. CROSSOVER (the thesis): for the CFPB doc set + 5 follow-up questions, ``stateful_total_tokens <
     stateless_input_tokens`` (stateful wins as N grows); ``0 < savings_ratio < 1``; ``tokens_saved > 0``;
     a positive crossover_n is reported and the case-N is at/above it.
  B. HONEST N=1: at N=1 the estimator does NOT claim a blanket win — it reports ``stateful_wins`` per-N and a
     ``crossover_n``; the proof asserts the crossover (the smallest N where stateful wins), not "always wins".
  C. DETERMINISTIC / REPRODUCIBLE: the same (docs, questions, now) -> byte-identical report numbers (re-run);
     pure (no RNG / no wall-clock leaking in).
  D. PROVENANCE PRESERVED: ``source_handle_coverage > 0`` (every distilled doc keeps a source handle) and
     ``held_out_leakage == 0`` (no omitted content is read).
  E. NO OVERCLAIM: ``is_truth is False`` and ``estimate_method`` names it an ESTIMATE / not a real tokenizer.
  F. NO LIVE LLM / NO BALTOR IMPORT / NO RAW KEYS: the module + this proof do not import any LLM/network client,
     do not import src.baltor (line-anchored), and contain no raw API key literals.

Deterministic + offline. stdlib only. Builds the blackboard in an in-memory sqlite db (never the real .agent db).
Exit 0/1. _REPO = parents[1]; sys.path.insert. No raw keys/secrets.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.blackboard.token_economics import (  # noqa: E402
    ESTIMATE_METHOD,
    OBSERVATION_DIGEST_MAX_CHARS,
    estimate_token_economics,
    estimate_tokens,
    load_cfpb_sample_docs,
)

_NOW = "2026-01-01T00:00:00Z"

#: the 5 follow-up questions over the CFPB-sample corpus (the same questions a reviewer would ask the docs).
_QUESTIONS = (
    "How long do we have to resolve an EFT dispute?",
    "Which document is the authoritative source for the timeline?",
    "Is the disputes FAQ stale or superseded?",
    "Who owns EFT dispute handling?",
    "What is the extended window with provisional credit?",
)

# the source files this proof reads (the module + this script) — must not import an LLM/network client or
# src.baltor, and must carry no raw keys.
_SOURCE_FILES = [
    _REPO / "src" / "teleon" / "blackboard" / "token_economics.py",
    _REPO / "scripts" / "check_stateful_vs_stateless_token_economics.py",
]

# crude raw-key detectors (provider key prefixes); env:// refs / the word in prose are fine.
_KEY_PATTERNS = [re.compile(p) for p in (r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{12,}", r"AIza[0-9A-Za-z_\-]{20,}")]

# live-LLM / network client imports that an OFFLINE deterministic estimator must NOT pull in (line-anchored).
_LLM_NET_IMPORT = re.compile(
    r"^[ \t]*(?:import|from)[ \t]+(?:openai|anthropic|httpx|requests|urllib\.request|aiohttp|tiktoken)\b",
    re.MULTILINE,
)
_BALTOR_IMPORT = re.compile(r"^[ \t]*(?:import|from)[ \t]+src\.baltor\b", re.MULTILINE)


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    docs = load_cfpb_sample_docs()
    check("setup: CFPB-sample docs loaded (the synthetic corpus to 'read')", len(docs) >= 5,
          f"loaded {len(docs)} docs")

    rep = estimate_token_economics(docs, _QUESTIONS, now=_NOW)

    # ---- A. CROSSOVER (the thesis) ------------------------------------------------------
    check("A: stateful_total_tokens < stateless_input_tokens for CFPB + 5 questions (stateful wins as N grows)",
          rep["stateful_total_tokens"] < rep["stateless_input_tokens"],
          f"stateful={rep['stateful_total_tokens']} stateless={rep['stateless_input_tokens']}")
    check("A: tokens_saved > 0", rep["tokens_saved"] > 0, f"saved={rep['tokens_saved']}")
    check("A: savings_ratio in (0, 1) (a fraction, not >1 or negative)",
          0.0 < rep["savings_ratio"] < 1.0, f"ratio={rep['savings_ratio']}")
    check("A: tokens_saved == stateless - stateful (the report is internally consistent)",
          rep["tokens_saved"] == rep["stateless_input_tokens"] - rep["stateful_total_tokens"])
    check("A: stateful_total == first_pass + N*per_question (the cost model is what it claims)",
          rep["stateful_total_tokens"]
          == rep["stateful_first_pass_tokens"] + rep["n_questions"] * rep["stateful_per_question_tokens"])
    check("A: per-question stateful read is far smaller than re-reading the whole corpus (compact state)",
          rep["stateful_per_question_tokens"] < rep["doc_tokens"],
          f"per_q={rep['stateful_per_question_tokens']} doc={rep['doc_tokens']}")
    check("A: a positive crossover_n is reported, and this case's N is at/above it",
          isinstance(rep["crossover_n"], int) and rep["crossover_n"] >= 1
          and rep["n_questions"] >= rep["crossover_n"],
          f"crossover_n={rep['crossover_n']} N={rep['n_questions']}")
    check("A: stateful_wins is True for this N (consistent with the totals)",
          rep["stateful_wins"] is True and rep["stateful_wins"]
          == (rep["stateful_total_tokens"] < rep["stateless_input_tokens"]))

    # ---- B. HONEST N=1 (no blanket claim) ------------------------------------------------
    rep1 = estimate_token_economics(docs, _QUESTIONS[:1], now=_NOW)
    # the degenerate case is handled HONESTLY: the report tells the truth about whether stateful wins at N=1,
    # and the win is consistent with the totals (we do NOT assert it always wins — that would be an overclaim).
    check("B: N=1 report is internally honest (stateful_wins matches whether stateful_total < stateless)",
          rep1["stateful_wins"] == (rep1["stateful_total_tokens"] < rep1["stateless_input_tokens"]))
    check("B: the proof asserts the CROSSOVER, not 'always wins' — crossover_n is reported (>= 1)",
          isinstance(rep1["crossover_n"], int) and rep1["crossover_n"] >= 1, f"crossover_n={rep1['crossover_n']}")
    # for THIS corpus the first-pass overhead means N=1 does not yet win (crossover_n > 1) — assert that the
    # crossover is honestly above 1 here, i.e. the win is earned by N growing, not asserted blindly at N=1.
    check("B: N=1 does NOT win for this corpus (first-pass overhead) — crossover is honestly > 1",
          rep1["crossover_n"] is not None and rep1["crossover_n"] > 1 and rep1["stateful_wins"] is False,
          f"crossover_n={rep1['crossover_n']} n1_wins={rep1['stateful_wins']}")
    # and: at exactly the crossover N the stateful total IS below the stateless total (the boundary holds).
    n_star = rep1["crossover_n"]
    rep_star = estimate_token_economics(docs, _QUESTIONS[:1] * n_star, now=_NOW)
    check("B: at N == crossover_n the stateful total is below the stateless total (the crossover is real)",
          rep_star["stateful_total_tokens"] < rep_star["stateless_input_tokens"],
          f"@N={n_star}: stateful={rep_star['stateful_total_tokens']} stateless={rep_star['stateless_input_tokens']}")

    # ---- C. DETERMINISTIC / REPRODUCIBLE -------------------------------------------------
    rep_again = estimate_token_economics(docs, _QUESTIONS, now=_NOW)
    check("C: same (docs, questions, now) -> identical report (reproducible / deterministic)", rep == rep_again)
    check("C: estimate_tokens is pure (same text -> same estimate)",
          estimate_tokens("the sanction took effect on 2026-04-15")
          == estimate_tokens("the sanction took effect on 2026-04-15"))
    check("C: estimate_tokens('') == 0 (empty text costs nothing)", estimate_tokens("") == 0)
    # the digest cap is a single-source constant; any change to it is a seam and must be asserted here.
    check("C: digest max-chars is exported as OBSERVATION_DIGEST_MAX_CHARS and is positive",
          isinstance(OBSERVATION_DIGEST_MAX_CHARS, int) and OBSERVATION_DIGEST_MAX_CHARS > 0,
          f"OBSERVATION_DIGEST_MAX_CHARS={OBSERVATION_DIGEST_MAX_CHARS}")

    # ---- D. PROVENANCE PRESERVED ---------------------------------------------------------
    check("D: source_handle_coverage > 0 (every distilled doc keeps a source handle)",
          rep["source_handle_coverage"] > 0, f"coverage={rep['source_handle_coverage']}")
    check("D: source_handle_coverage covers the whole doc set (no doc loses its handle)",
          rep["source_handle_coverage"] == len(docs),
          f"coverage={rep['source_handle_coverage']} docs={len(docs)}")
    check("D: held_out_leakage == 0 (no omitted/held-out content is read in either regime)",
          rep["held_out_leakage"] == 0, f"leakage={rep['held_out_leakage']}")
    check("D: entries_reused > 0 (compact state exists for questions to reuse)",
          rep["entries_reused"] > 0, f"entries_reused={rep['entries_reused']}")

    # ---- E. NO OVERCLAIM (labeled estimate, not truth, not a real tokenizer) -------------
    check("E: report is labeled is_truth=False (a blackboard estimate is never served truth)",
          rep["is_truth"] is False)
    check("E: estimate_method names it an ESTIMATE / not a real tokenizer (no overclaim)",
          rep["estimate_method"] == ESTIMATE_METHOD
          and "ESTIMATE" in rep["estimate_method"] and "not a real tokenizer" in rep["estimate_method"],
          f"method={rep['estimate_method']!r}")

    # ---- F. no live LLM / no baltor import / no raw keys ---------------------------------
    for f in _SOURCE_FILES:
        text = f.read_text(encoding="utf-8")
        check(f"F: {f.name} imports no live LLM / network client (offline + deterministic)",
              not _LLM_NET_IMPORT.search(text))
        check(f"F: {f.name} does not import src.baltor", not _BALTOR_IMPORT.search(text))
        leaked = [p.pattern for p in _KEY_PATTERNS if p.search(text)]
        check(f"F: {f.name} contains no raw API key literal", not leaked, f"matched {leaked}")

    # ---- headline numbers (for the run log) ----------------------------------------------
    print(
        "\n  headline (CFPB + {n}Q): stateless={sl} tok  vs  stateful={sf} tok  "
        "(first_pass={fp} + {n}x{pq})  saved={sv} tok  savings_ratio={sr:.3f}  crossover_n={cx}".format(
            n=rep["n_questions"],
            sl=rep["stateless_input_tokens"],
            sf=rep["stateful_total_tokens"],
            fp=rep["stateful_first_pass_tokens"],
            pq=rep["stateful_per_question_tokens"],
            sv=rep["tokens_saved"],
            sr=rep["savings_ratio"],
            cx=rep["crossover_n"],
        )
    )

    print("\n" + (
        "PASS — check_stateful_vs_stateless_token_economics: build-state-once-and-query beats reread-every-time. "
        "For the CFPB-sample corpus + 5 follow-up questions the STATEFUL total input-token ESTIMATE "
        f"({rep['stateful_total_tokens']}) is below the STATELESS one ({rep['stateless_input_tokens']}) — "
        f"savings_ratio {rep['savings_ratio']:.3f}, crossover at N={rep['crossover_n']}. The proof asserts the "
        "CROSSOVER (stateless can be cheaper at N=1 due to first-pass overhead — reported honestly), the figures "
        "are a chars/4 HEURISTIC labeled is_truth=False / 'not a real tokenizer' (no overclaim), provenance is "
        "preserved (source_handle_coverage>0) and held_out_leakage==0. Reproducible; no live LLM; no src.baltor; "
        "no raw keys."
        if not fails else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_stateful_vs_stateless_token_economics.py --self-test")
    raise SystemExit(0)
