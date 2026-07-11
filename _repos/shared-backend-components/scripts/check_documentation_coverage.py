#!/usr/bin/env python3
"""scripts.check_documentation_coverage — proof: per-section documentation coverage is COMPLETE and HONEST.

Every critical-path section in ``_repos/shared-backend-components/architecture/section_maturity_matrix.json`` MUST be documented to the
section-card standard, and no section may be "green by omission":

1. Every REFERENCE-PATH section resolves to at least one EXISTING doc — either a ``docs[]`` entry in the matrix
   that exists on disk (file OR directory), or a name-matched per-section card under ``_repos/shared-backend-components/docs/`` whose basename
   normalises to the ``section_id``.
2. Every REFERENCE-PATH section that the matrix leaves with an EMPTY ``docs[]`` MUST instead carry a per-section
   card (``_repos/shared-backend-components/docs/section-cards/<section-id>.md``) — so doc presence is provable WITHOUT a matrix edit (the
   matrix ``docs[]`` additions are REPORTED for the main agent to apply, not made here).
3. Every per-section card that exists (a file under ``_repos/shared-backend-components/docs/section-cards/`` named for a ``section_id``) MUST
   contain the three required exact headings — ``## Purpose``, ``## Proof``, ``## Limitations`` — so a card
   can never claim coverage while omitting purpose, proof, or honest limitations. (Long-form architecture
   docs referenced elsewhere are checked for EXISTENCE only, never reformatted.)
4. Every per-section card for a REFERENCE section MUST name the section's REAL ``owner_module`` and at least one
   of its real ``proof_scripts`` (no doc that points at nothing).
5. A NON-reference section is allowed to have an empty ``docs[]`` ONLY IF it records a ``known_gap`` OR an
   opportunity in ``_repos/shared-backend-components/architecture/opportunities.json`` claims it via ``owner_section`` — otherwise its silence
   is unexplained and fails.

Deterministic: pure filesystem + JSON reads, no clock, no RNG, no network.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_documentation_coverage.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_MATRIX = _resource("architecture") / "section_maturity_matrix.json"
_OPPS = _resource("architecture") / "opportunities.json"
_DOCS = _resource("docs")
#: the dedicated directory for per-section cards (decoupled from long-form architecture docs so the proof
#: never forces a rewrite of a doc another lane owns).
_CARDS = _DOCS / "section-cards"

#: the three required exact section-heading strings every per-section card must carry (level-2 headings).
_REQUIRED_HEADINGS = ("Purpose", "Proof", "Limitations")


def _norm(name: str) -> str:
    """Normalise a section_id / doc basename for matching: lower-case, '-' and '_' equivalent."""
    return name.lower().replace("-", "_")


def _card_path(section_id: str) -> Path:
    """The canonical per-section card location for a section (hyphenated, under _repos/shared-backend-components/docs/section-cards/)."""
    return _CARDS / f"{section_id.replace('_', '-')}.md"


def _cards_by_section() -> dict[str, Path]:
    """Map normalised section_id -> its per-section card file (only files under _repos/shared-backend-components/docs/section-cards/)."""
    out: dict[str, Path] = {}
    if _CARDS.is_dir():
        for p in _CARDS.glob("*.md"):
            out[_norm(p.stem)] = p
    return out


def _headings(text: str) -> set[str]:
    """The level-2/3 heading strings in a markdown doc (text after the '## '/'### ' marker)."""
    found: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(.*\S)\s*$", line)
        if m:
            found.add(m.group(1).strip())
    return found


def _card_has_required_headings(text: str) -> list[str]:
    """Return the required headings MISSING from a card (a heading counts if it STARTS with the required word)."""
    heads = _headings(text)
    missing: list[str] = []
    for req in _REQUIRED_HEADINGS:
        # exact heading 'Purpose' OR a heading that begins with the required word (e.g. 'Proof scripts').
        if not any(h == req or h.startswith(req + " ") or h.startswith(req + ":") for h in heads):
            missing.append(req)
    return missing


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    matrix = json.loads(_MATRIX.read_text())
    secs = matrix["sections"]
    cards = _cards_by_section()  # normalised section_id -> _repos/shared-backend-components/docs/section-cards/<id>.md
    opp_owner_sections = {o.get("owner_section") for o in json.loads(_OPPS.read_text())["opportunities"]}

    reference = [s for s in secs if s.get("critical_path_required")]
    nonreference = [s for s in secs if not s.get("critical_path_required")]

    def _resolves(s: dict) -> bool:
        """A section is documented if a matrix docs[] entry exists OR it has a per-section card."""
        if any((_resource(d)).exists() for d in s.get("docs", [])):
            return True
        return _norm(s["section_id"]) in cards

    # ── (1) every reference section resolves to at least one existing doc ──────────────────────────────
    reference_no_doc = [s["section_id"] for s in reference if not _resolves(s)]
    check("every critical-path section resolves to >=1 existing doc (matrix docs[] file/dir OR per-section card)",
          reference_no_doc == [], str(reference_no_doc))

    # ── (2) every reference section with an EMPTY matrix docs[] carries a per-section card ──────────────
    empty_docs_no_card = [
        s["section_id"] for s in reference if not s.get("docs") and _norm(s["section_id"]) not in cards
    ]
    check("every reference section with EMPTY matrix docs[] has a docs/section-cards/<id>.md card",
          empty_docs_no_card == [], str(empty_docs_no_card))

    # ── (3) every per-section card carries the three required exact headings ─────────────────────────
    card_missing_headings: list[str] = []
    for nid, card in cards.items():
        missing = _card_has_required_headings(card.read_text(encoding="utf-8"))
        if missing:
            card_missing_headings.append(f"{card.relative_to(_REPO)} missing {missing}")
    check(f"every per-section card carries the required headings {list(_REQUIRED_HEADINGS)}",
          card_missing_headings == [], str(card_missing_headings[:8]))

    # ── (4) every reference section's card names the real owner_module + >=1 real proof script ──────────
    card_bad_refs: list[str] = []
    for s in reference:
        card = cards.get(_norm(s["section_id"]))
        if card is None:
            continue  # covered by (1)/(2)
        body = card.read_text(encoding="utf-8")
        owner = s.get("owner_module", "")
        proofs = s.get("proof_scripts", [])
        if owner and owner not in body:
            card_bad_refs.append(f"{card.relative_to(_REPO)} omits owner_module {owner}")
        if proofs and not any(ps in body for ps in proofs):
            card_bad_refs.append(f"{card.relative_to(_REPO)} names no real proof script")
    check("every reference section's card names the real owner_module + >=1 real proof script",
          card_bad_refs == [], str(card_bad_refs[:8]))

    # ── (5) a non-reference section's empty docs[] is explained (known_gap OR owner_section opportunity) ─
    nonreference_unexplained: list[str] = []
    for s in nonreference:
        if _resolves(s):
            continue
        if not (bool(s.get("known_gaps")) or (s["section_id"] in opp_owner_sections)):
            nonreference_unexplained.append(s["section_id"])
    check("every non-reference section with no doc is EXPLAINED (known_gap OR an opportunity owns it)",
          nonreference_unexplained == [], str(nonreference_unexplained))

    # ── coverage summary (informational, deterministic) ─────────────────────────────────────────────
    documented_reference = sum(1 for s in reference if _resolves(s))
    print(f"\n  coverage: {documented_reference}/{len(reference)} critical-path sections documented; "
          f"{len(cards)} per-section cards present.")

    ok = not fails
    print("\n" + (
        "PASS — check_documentation_coverage: every critical-path section is documented; every empty-docs "
        "reference section has a per-section card with Purpose/Proof/Limitations naming its real owner + proof; "
        "non-reference silence is explained. No green-by-omission."
        if ok else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: per-section documentation coverage is complete + honest.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
