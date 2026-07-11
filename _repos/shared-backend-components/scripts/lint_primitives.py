#!/usr/bin/env python3
"""scripts.lint_primitives — the "primitive smell detector" node of the primitive-OS pipeline (2026-07-08),
grounded in the 2026 agent-skill research cluster (SkillReducer analyzed 55,315 skills → >60% non-actionable
body, 26.4% missing routing; the SKILL.md-smells study found >99% of real skills carry ≥1 smell;
SWE-Skills-Bench found 39/49 skills gave ZERO lift and some added +451% tokens). The lesson: **a primitive is
a liability until it is evaluated, typed, and lean** — so audit BEFORE accumulating.

This lints OUR OWN executable-pack cards (the live source, via executable_pack_pool_sync.PACK_MODULES) for
the smells that apply to a code-primitive card, scores each 0-100, and — critically — reports the SCHEMA-LEVEL
gaps our card shape has against the formal-primitive-package standard (Formal Skill / SkVM / SWE-Skills-Bench):
no verifier link, no declared failure_modes, no permission manifest, no marginal-utility evidence, no
model/harness/runtime compatibility. It is the "lint" gate of candidate→validated→certified→production; it
does not promote anything (serves_truth=false), it tells us honestly where our 141 cards stand.

    python3 scripts/lint_primitives.py --self-test
    python3 scripts/lint_primitives.py --report          # lint the live pool, print the receipt
    python3 scripts/lint_primitives.py --report --worst 15
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.primitive_package_contract import FORMAL_FIELDS, formalize_card  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
LINT_RULESET_VERSION = "primitive-lint-v1"

# ── token/size thresholds (chars; a rough token proxy at ~4 chars/token) ─────────────────────────────────────
_BLOAT_WARN = 4000      # ~1000 tokens of body — start watching
_BLOAT_HEAVY = 9000     # ~2250 tokens — SkillReducer's "reference injection" danger zone
_ROUTING_MIN = 40       # a "when to use" description shorter than this is not actionable
#: side-effect markers → a primitive that touches these needs a PERMISSION MANIFEST (which our schema lacks)
_SIDE_EFFECT_RE = re.compile(r"\b(subprocess|os\.system|socket|urllib|httpx|requests|shutil\.rmtree|"
                             r"__import__|eval\(|exec\()")
#: the fields a FORMAL primitive package should carry (single source: primitive_package_contract.FORMAL_FIELDS,
#: SkVM / Formal Skill / SWE-Skills-Bench). A card that has been through formalize_card() carries them all;
#: a RAW card carries none — the gap the contract closes.
FORMAL_PACKAGE_FIELDS = FORMAL_FIELDS


# ── per-card smell checks: (name, weight, is_smell(card) -> bool) ────────────────────────────────────────────
def _is_python_code(card: dict[str, Any]) -> bool:
    return (card.get("language") == "python") and bool(card.get("executable_body"))


def _body_unparseable(card: dict[str, Any]) -> bool:
    if not _is_python_code(card):
        return False
    try:
        ast.parse(card["executable_body"])
        return False
    except SyntaxError:
        return True


def _bloat_weight(card: dict[str, Any]) -> int:
    n = len(card.get("executable_body") or "")
    return 15 if n > _BLOAT_HEAVY else (6 if n > _BLOAT_WARN else 0)


SMELL_CHECKS: tuple[tuple[str, int, Callable[[dict[str, Any]], bool]], ...] = (
    ("missing_routing_description", 25,
     lambda c: len((c.get("blackbox") or "").strip()) < _ROUTING_MIN),
    ("missing_io_typing", 20, lambda c: not (c.get("input_edge") and c.get("output_edge"))),
    ("missing_title", 10, lambda c: not (c.get("title") or "").strip()),
    ("composite_without_plan", 12,
     lambda c: c.get("kind") == "primitive_group" and not c.get("plan_steps")),
    ("no_executable_body", 30, lambda c: not (c.get("executable_body") or "").strip()),
    ("body_unparseable", 30, _body_unparseable),
    ("missing_candidate_boundary", 15, lambda c: c.get("serves_truth") is not False),
    ("undeclared_side_effect_no_permission_manifest", 15,
     lambda c: bool(_SIDE_EFFECT_RE.search(c.get("executable_body") or ""))),
)


def lint_card(card: dict[str, Any]) -> dict[str, Any]:
    """Score ONE card 0-100; list the smells it triggers. Deterministic, pure."""
    smells: list[str] = []
    penalty = 0
    for name, weight, is_smell in SMELL_CHECKS:
        if is_smell(card):
            smells.append(name)
            penalty += weight
    penalty += _bloat_weight(card)
    if _bloat_weight(card):
        smells.append("token_bloat_warn" if _bloat_weight(card) == 6 else "token_bloat_heavy")
    score = max(0, 100 - penalty)
    return {"primitive_id": card.get("primitive_id"), "impl_name": card.get("impl_name"),
            "record_type": card.get("record_type"), "kind": card.get("kind"),
            "quality_score": score, "smells": smells,
            "body_chars": len(card.get("executable_body") or ""), **BOUNDARY}


def load_live_cards() -> list[dict[str, Any]]:
    """The live source of truth: every registered pack's all_cards() (not a stale file)."""
    from scripts.executable_pack_pool_sync import PACK_MODULES
    cards: list[dict[str, Any]] = []
    for modname in PACK_MODULES:
        mod = importlib.import_module(modname)
        cards.extend(mod.all_cards())
    return cards


def lint_corpus(cards: list[dict[str, Any]], *, formalize: bool = True) -> dict[str, Any]:
    """Lint every card; roll up distribution + per-smell counts + the corpus-level SCHEMA gaps.
    formalize=True (default) runs cards through the formal-package contract first (the production path);
    formalize=False lints the RAW cards (used to prove the detector still detects absence)."""
    if formalize:
        cards = [formalize_card(c) for c in cards]
    linted = [lint_card(c) for c in cards]
    n = len(linted) or 1
    by_smell: dict[str, int] = {}
    for lc in linted:
        for s in lc["smells"]:
            by_smell[s] = by_smell.get(s, 0) + 1
    scores = [lc["quality_score"] for lc in linted]
    buckets = {"90-100": 0, "70-89": 0, "50-69": 0, "0-49": 0}
    for s in scores:
        buckets["90-100" if s >= 90 else "70-89" if s >= 70 else "50-69" if s >= 50 else "0-49"] += 1
    # corpus-level: which FORMAL-package fields does the schema carry at all?
    schema_gaps = [f for f in FORMAL_PACKAGE_FIELDS
                   if not any(f in c for c in cards)]
    worst = sorted(linted, key=lambda lc: (lc["quality_score"], lc["impl_name"] or ""))[:20]
    return {"record_type": "primitive_lint_receipt", "ruleset_version": LINT_RULESET_VERSION,
            "n_cards": len(cards), "mean_quality_score": round(sum(scores) / n, 2),
            "min_score": min(scores) if scores else None, "max_score": max(scores) if scores else None,
            "score_distribution": buckets, "smells_by_count": dict(sorted(by_smell.items(),
                                                                          key=lambda kv: -kv[1])),
            "schema_level_gaps_all_cards_missing": schema_gaps,
            "schema_gap_meaning": "fields the formal-primitive-package standard (Formal Skill/SkVM/"
                                  "SWE-Skills-Bench) expects that our card schema does not yet carry — the "
                                  "extend-the-schema backlog, not a per-card defect",
            "worst_cards": worst, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    good = {"primitive_id": "p1", "impl_name": "clean_fn", "language": "python", "kind": "primitive",
            "title": "A clean primitive", "input_edge": "In", "output_edge": "Out",
            "blackbox": "Atomic primitive that does a well-described thing you would use when X happens.",
            "executable_body": "def clean_fn(x):\n    return x.strip()\n", "serves_truth": False}
    lc = lint_card(good)
    checks.append(("a clean card scores 100 with no smells", lc["quality_score"] == 100 and not lc["smells"]))
    # mutation: strip routing description -> the routing smell fires and score drops by exactly its weight
    bad = dict(good, blackbox="too short")
    lb = lint_card(bad)
    checks.append(("removing routing description fires missing_routing_description (-25)",
                   "missing_routing_description" in lb["smells"] and lb["quality_score"] == 75))
    checks.append(("unparseable body is caught (-30)",
                   "body_unparseable" in lint_card(dict(good, executable_body="def f(:\n bad"))["smells"]))
    checks.append(("missing IO typing fires (-20)",
                   "missing_io_typing" in lint_card(dict(good, output_edge=""))["smells"]))
    checks.append(("side-effect body without a permission manifest is flagged",
                   "undeclared_side_effect_no_permission_manifest"
                   in lint_card(dict(good, executable_body="import subprocess\ndef f():\n subprocess.run(1)"
                                     ))["smells"]))
    checks.append(("composite without plan_steps is flagged",
                   "composite_without_plan"
                   in lint_card(dict(good, kind="primitive_group", plan_steps=[]))["smells"]))
    # corpus roll-up over the LIVE pool (the honest audit of our own cards)
    cards = load_live_cards()
    rec = lint_corpus(cards, formalize=True)
    checks.append(("lints the live pool (>=100 cards), mean score computed, distribution sums to n",
                   rec["n_cards"] >= 100 and 0 <= rec["mean_quality_score"] <= 100
                   and sum(rec["score_distribution"].values()) == rec["n_cards"]))
    raw = lint_corpus(cards, formalize=False)
    checks.append(("RAW cards miss the formal-package fields; formalize_card CLOSES the gap (the contract wire)",
                   "verifier_id" in raw["schema_level_gaps_all_cards_missing"]
                   and "failure_modes" in raw["schema_level_gaps_all_cards_missing"]
                   and rec["schema_level_gaps_all_cards_missing"] == []))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - lint_primitives: {len(SMELL_CHECKS)} smell checks + token-bloat + corpus schema-gap "
          f"audit. The lint gate of candidate->validated; scores our own cards, never promotes. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--worst", type=int, default=10)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.report:
        rec = lint_corpus(load_live_cards())
        rec["worst_cards"] = rec["worst_cards"][:args.worst]
        print(json.dumps(rec, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
