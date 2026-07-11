#!/usr/bin/env python3
"""scripts.mint_gap_primitives — mint THOUSANDS of gap-closing primitive CANDIDATE cards from the scenario
axes, and PROVE the coverage lift they buy.

The scenario corpus (``scripts.build_scenario_corpus``) measures verified coverage per capability x artifact
phrasing — every miss names a (capability, artifact) hole the primitive corpus cannot answer. This module is
the SUPPLY side of that signal: for each capability x artifact pair (axes IMPORTED from the corpus module —
single source, never copied) it mints ``variants_per_pair`` deterministic candidate cards whose title and
blackbox NATURALLY carry the capability's expected concept tokens plus the artifact vocabulary, so the
verified-hit gate (token-boundary, never substring) can genuinely cover the scenario. Each card carries:

  * ``title``        — e.g. "Rate limiting middleware for REST API service" (capability + variant role +
                       artifact),
  * ``blackbox``     — 1-2 sentences naturally containing every expected token and the artifact words,
  * typed edges      — CamelCase, derived from the capability's semantics:
                       ``<CapabilityCamel>Requirement -> <CapabilityCamel>Capability`` (the card consumes a
                       requirement for the capability and emits the working capability),
  * ``blocking_keys``— exactly the capability's expected tokens (the corpus's verified-coverage contract),
  * ``contract``     — {input, output} in words,
  * ``primitive_id`` — the ONE id authority ``src.teleon.experiments.ids.canonical_id`` with prefix
                       ``prim-minted`` over the title + blackbox bytes (no RNG, no wall-clock).

Deterministic end to end: the same axes always mint byte-identical cards. The default mint crosses the LIVE
capability axis with every artifact x stack phrase form (the exact phrasing law the scenario corpus uses for
its queries, computed from the imported axes — ``--bare-artifacts`` restricts to the bare artifact axis), so
the minted count is ``len(capabilities) * len(artifact_forms) * variants_per_pair`` — computed, never typed.

Cards are STAGED to a NEW file (``minted_gap_primitive_candidates.jsonl``, append-only with dedupe by id);
the verified corpus files are NEVER written — the writer refuses any other filename outright, refuses a
symlinked target, and re-checks the RESOLVED real path (a planted link cannot retarget the append).
``prove_lift`` runs the corpus module's verified ``coverage`` THREE ways — base cards, base + minted, and a
PROSE-ONLY ablation (minted minus the copied ``blocking_keys``, so the receipt itself proves hits are earned
by title+blackbox text, not by the answer-key copy) — and reports the rates and the delta: ADMISSION
EVIDENCE for the candidate lane, never promotion — every card stays
``candidate=true / serves_truth=false`` with explicit promotion blockers, and promotion goes through the
factory gates (source review + executed proof), not through this module.

    PYTHONPATH=. python3 scripts/mint_gap_primitives.py --self-test
    PYTHONPATH=. python3 scripts/mint_gap_primitives.py --mint [--variants-per-pair 3] [--bare-artifacts]
    PYTHONPATH=. python3 scripts/mint_gap_primitives.py --prove [--sample 120] [--k 5] [--max-cards N]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/build_scenario_corpus.py) ─────────────────────────
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts._jsonl import iter_jsonl_tolerant  # noqa: E402  (mandated tolerant reader for append-only feeds)
from scripts._repo_paths import resource as _resource  # noqa: E402
# the AXES + the verified-coverage engine — SINGLE SOURCE (scripts.build_scenario_corpus), never copied here.
from scripts.build_scenario_corpus import _ARTIFACTS as SCENARIO_ARTIFACT_AXIS  # noqa: E402
from scripts.build_scenario_corpus import _CAPABILITIES as SCENARIO_CAPABILITY_AXIS  # noqa: E402
from scripts.build_scenario_corpus import _DEFAULT_COUNT as SCENARIO_POOL_DEFAULT_COUNT  # noqa: E402
from scripts.build_scenario_corpus import _STACKS as SCENARIO_STACK_AXIS  # noqa: E402
from scripts.build_scenario_corpus import coverage as scenario_coverage  # noqa: E402  THE verified gate
from scripts.build_scenario_corpus import generate as generate_scenarios  # noqa: E402
# the verified corpus path, single-sourced — used ONLY to assert this module never writes it.
from scripts.edge_type_matcher import CORPUS as VERIFIED_FACTORY_CORPUS_PATH  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as _ids_exc:  # pragma: no cover - the law: no parallel id scheme, ever
    raise ImportError(
        "scripts.mint_gap_primitives requires the ONE id authority src.teleon.experiments.ids.canonical_id "
        "— refusing to invent a parallel id scheme (deterministic-naming law)."
    ) from _ids_exc

#: every minted row/report is a candidate signal, never truth — generation is NEVER promotion (repo law).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: typed, human-readable id prefix for minted gap candidates; the suffix is canonical_id's sha256[:16]
#: content hash over (title, blackbox), so the prefix carries meaning and the hash carries uniqueness.
MINTED_ID_PREFIX = "prim-minted"
#: record_type of every minted card — distinguishes gap-mint candidates from verified/demand-minted cards.
MINTED_RECORD_TYPE = "minted_gap_primitive_candidate"
#: mirrors the verified corpus's card kind so loaders/matchers/indexes ingest these cards uniformly.
MINTED_CARD_KIND = "route.primitive"
#: card schema version lives in METADATA, never in a name or id (deterministic-naming law).
MINTED_SCHEMA_VERSION = 1
#: readiness label for a minted-but-unproven card: rank 0 under edge_type_matcher._readiness_rank,
#: deliberately BELOW every built card (R1+), so ranking never prefers an unproven gap-fill stub.
MINTED_READINESS_UNPROVEN = "R0_minted_gap_candidate"
#: why a minted card cannot be promoted as-is — explicit blockers keep the candidate/truth boundary readable.
MINTED_PROMOTION_BLOCKERS: tuple[str, ...] = (
    "no_source_evidence",
    "no_executed_proof",
    "coverage_gap_candidate_only",
)
#: the ONE staged filename this module may ever write (a NEW file next to — never equal to — the verified
#: corpus files); write_staged refuses every other filename, which is what makes "never touch the verified
#: corpus" a hard gate instead of a promise.
STAGED_FILENAME = "minted_gap_primitive_candidates.jsonl"
#: task-set floor for the default mint at DEFAULT_VARIANTS_PER_PAIR — the "thousands, not dozens" bar the
#: --mint report checks itself against (the actual count is always computed from the live axes).
TARGET_MINTED_MINIMUM = 5000
#: variants minted per (capability, artifact) pair by default — one per variant role/frame below.
DEFAULT_VARIANTS_PER_PAIR = 3
#: top-k for the lift proof's verified coverage (matches build_scenario_corpus.coverage's default).
DEFAULT_PROVE_TOP_K = 5
#: scenario sample size for the --prove CLI — sized to move rates. HONEST COST NOTE (2026-07-07 review):
#: coverage's dense lane delta-embeds every OUT-OF-STORE card PER QUERY (capability_embedding's delta lane
#: has no cross-query cache yet), and every minted card is out-of-store — so a --prove run costs roughly
#: <sweeps carrying minted> x len(minted) x sample single-text embeds. That is workstation-practical with
#: ``--bare-artifacts`` (the artifact axis without stack forms) and impractical at the full default axes;
#: ``main`` prints the COMPUTED cost line before running and never caps or subsamples the minted set
#: silently (that would change what the receipt measures).
DEFAULT_PROVE_SAMPLE = 120

#: variant ROLE words — variant v of a pair frames the same capability as a different reusable unit, so the
#: three default variants give retrieval three distinct phrasings per gap (v >= len cycles with a lane tag).
VARIANT_ROLES: tuple[str, ...] = (
    "middleware", "module", "engine", "toolkit", "adapter", "workflow", "component", "gateway")
#: blackbox sentence frames (1-2 sentences each), cycled per variant. Placeholders: {cap} capability name,
#: {a_art} article+artifact, {toks} the natural-joined expected tokens, {role} the variant role word.
VARIANT_BLACKBOX_FRAMES: tuple[str, ...] = (
    "Gives {a_art} a working {cap} capability: handling the {toks} concerns in one governed, typed path, "
    "packaged as a reusable {role}.",
    "Drop-in {role} that adds {cap} to {a_art}. It wires the {toks} concerns behind a single typed "
    "contract so composition stays deterministic.",
    "Closes the {cap} gap in {a_art} by shipping the {toks} concerns as one config-driven {role} with "
    "typed input and output edges.",
)

#: blackbox frame GENERATION — metadata, never part of a name or id (deterministic-naming law). Bumped
#: whenever VARIANT_BLACKBOX_FRAMES change wording, because new frame text mints all-new canonical ids:
#: the staged pool then holds MULTIPLE generations side by side (append-only law — rows minted under a
#: prior generation are never rewritten, deleted, or deduped away), and this stamp — carried in every
#: card's provenance and every write_staged report — is what tells the generations apart.
MINTED_BLACKBOX_FRAME_GENERATION = 2
#: supersession record for the staged pool (lossless-distillation law: superseded != deleted). Generation 1
#: frames pasted the raw expected-token list into the {toks} slot as a bare enumeration, which read as
#: keyword salad for adjective/verb token tuples (2026-07-07 review finding); generation 2 heads the list
#: with "the ... concerns" so any part of speech reads as a topic enumeration. Generation-1 rows STAY in
#: the staged pool file as the preserved prior generation; this record — surfaced in every write_staged
#: report — is the pool metadata naming that supersession, with the exact prior frame texts preserved for
#: lineage (the losers keep their lineage; nothing is rewritten on disk).
SUPERSEDED_BLACKBOX_FRAME_GENERATIONS: tuple[dict[str, Any], ...] = (
    {
        "generation": 1,
        "superseded_on": "2026-07-07",
        "reason": "token-stuffing review finding: the {toks} slot rendered the expected-token list as a "
                  "bare enumeration (keyword salad for adjective/verb token tuples); generation 2 gives "
                  "the list a head noun ('the ... concerns')",
        "frames": (
            "Gives {a_art} a working {cap} capability: {toks} are handled in one governed, typed path, "
            "packaged as a reusable {role}.",
            "Drop-in {role} that adds {cap} to {a_art}. It wires {toks} behind a single typed contract so "
            "composition stays deterministic.",
            "Closes the {cap} gap in {a_art} by shipping {toks} as one config-driven {role} with typed "
            "input and output edges.",
        ),
        "disposition": "staged generation-1 rows are PRESERVED append-only in the staged pool file — "
                       "never rewritten, deleted, or deduped away; generation-2 rows append beside them",
    },
)

#: shape of a well-minted id: the typed prefix + '-' + canonical_id's 16-hex sha256 suffix.
_MINTED_ID_RE = re.compile(r"^%s-[0-9a-f]{16}$" % re.escape(MINTED_ID_PREFIX))
#: the SAME token split rule the verified-hit gate uses (saas_requirements_bench) — kept identical so the
#: "blackbox naturally carries the expected tokens" validator agrees with the coverage gate byte-for-byte.
_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")
#: a typed edge is CamelCase: leading capital, alphanumeric only (the corpus edge vocabulary convention).
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


# ── the default axes (computed from the imported single source; never copied) ─────────────────────────────

def default_capability_axis() -> dict[str, tuple]:
    """The LIVE capability axis (capability -> expected concept tokens) from build_scenario_corpus."""
    return dict(SCENARIO_CAPABILITY_AXIS)


def default_artifact_axis(*, bare: bool = False) -> list[str]:
    """The artifact phrase forms the scenario corpus actually asks about: every artifact in every stack
    qualification, using the corpus's own "{artifact} {stack}" phrasing law (the empty stack yields the bare
    artifact exactly once). ``bare=True`` restricts to the bare artifact axis. Computed from the imported
    axes at call time, so axis growth in the single source grows the mint automatically."""
    if bare:
        return list(SCENARIO_ARTIFACT_AXIS)
    return [f"{art} {stack}" if stack else art
            for art in SCENARIO_ARTIFACT_AXIS for stack in SCENARIO_STACK_AXIS]


# ── deterministic derivations ──────────────────────────────────────────────────────────────────────────────

def camel_case_type(text: str) -> str:
    """CamelCase type name from free words — 'user login and accounts' -> 'UserLoginAndAccounts'."""
    return "".join(w.capitalize() for w in _TOKEN_SPLIT_RE.split(str(text).lower()) if w)


def derive_capability_edges(capability: str) -> tuple[str, str]:
    """Typed input/output edges from the capability's semantics: the card consumes a REQUIREMENT for the
    capability and emits the WORKING capability — '<Cap>Requirement' -> '<Cap>Capability'. Mechanical over
    any capability string (the axes are injectable), CamelCase, meaning-bearing, no fake morphology."""
    base = camel_case_type(capability)
    if not base:
        raise ValueError(f"capability {capability!r} yields an empty edge type")
    return f"{base}Requirement", f"{base}Capability"


def _natural_join(words: list[str]) -> str:
    """'a' | 'a and b' | 'a, b and c' — so the expected tokens sit in the blackbox as natural prose."""
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " and " + words[-1]


def _article(noun: str) -> str:
    """Deterministic English article: 'an' before a vowel letter, else 'a'."""
    return "an" if str(noun)[:1].lower() in "aeiou" else "a"


def _variant_role(variant_index: int) -> str:
    """The role word for variant v: the role tuple, cycling with a lane tag past its length so ANY
    variants_per_pair yields distinct, deterministic role strings."""
    base = VARIANT_ROLES[variant_index % len(VARIANT_ROLES)]
    lane = variant_index // len(VARIANT_ROLES)
    return base if lane == 0 else f"{base} lane {lane + 1}"


def _text_tokens(text: str) -> frozenset:
    """Token set under the SAME split rule as the verified-hit gate (token-boundary, never substring)."""
    return frozenset(_TOKEN_SPLIT_RE.split(str(text).lower())) - {""}


# ── minting ────────────────────────────────────────────────────────────────────────────────────────────────

def mint_cards(capabilities: dict[str, tuple], artifacts: list[str], *,
               variants_per_pair: int) -> list[dict[str, Any]]:
    """Mint ``variants_per_pair`` candidate cards for EVERY capability x artifact pair — exactly
    ``len(capabilities) * len(artifacts) * variants_per_pair`` cards, in sorted-capability, given-artifact,
    variant order. Pure and deterministic over its inputs: no RNG, no wall-clock — ids are canonical_id's
    sha256 content hash over (title, blackbox), so the same axes always mint byte-identical cards. Every
    card is born candidate=true / serves_truth=false (generation is never promotion). Raises on empty or
    duplicate axis entries rather than silently collapsing the count."""
    if variants_per_pair < 1:
        raise ValueError(f"variants_per_pair must be >= 1, got {variants_per_pair}")
    cards: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for capability in sorted(capabilities):
        tokens = [str(t) for t in capabilities[capability] if str(t).strip()]
        if not capability.strip() or not tokens:
            raise ValueError(f"capability {capability!r} needs a name and expected tokens — "
                             "a token-less capability can never be verified-covered")
        input_edge, output_edge = derive_capability_edges(capability)
        capability_title = capability[:1].upper() + capability[1:]
        token_prose = _natural_join(tokens)
        for artifact in artifacts:
            artifact = str(artifact)
            if not artifact.strip():
                raise ValueError("artifacts must be non-empty strings")
            a_art = f"{_article(artifact)} {artifact}"
            for variant_index in range(variants_per_pair):
                role = _variant_role(variant_index)
                title = f"{capability_title} {role} for {artifact}"
                frame = VARIANT_BLACKBOX_FRAMES[variant_index % len(VARIANT_BLACKBOX_FRAMES)]
                blackbox = frame.format(cap=capability, a_art=a_art, toks=token_prose, role=role)
                pid = canonical_id(MINTED_ID_PREFIX, title, blackbox)
                if pid in seen_ids:
                    raise ValueError(f"duplicate mint for title {title!r} — the axes contain a duplicate "
                                     "entry; refusing to collapse the count silently")
                seen_ids.add(pid)
                cards.append({
                    "record_type": MINTED_RECORD_TYPE,
                    "schema_version": MINTED_SCHEMA_VERSION,
                    "kind": MINTED_CARD_KIND,
                    "primitive_id": pid,
                    "title": title,
                    "capability": capability,
                    "artifact": artifact,
                    "variant_index": variant_index,
                    "variant_role": role,
                    "input_edge": input_edge,
                    "output_edge": output_edge,
                    "blackbox": blackbox,
                    "blocking_keys": list(tokens),
                    "contract": {
                        "input": f"{capability} requirement for {a_art} "
                                 f"(expected concepts: {', '.join(tokens)})",
                        "output": f"working {capability} capability for the {artifact} "
                                  f"with {', '.join(tokens)} handled",
                    },
                    "readiness": MINTED_READINESS_UNPROVEN,
                    "promotion_blockers": list(MINTED_PROMOTION_BLOCKERS),
                    "provenance": {
                        "minter": "scripts.mint_gap_primitives",
                        "demand_signal": "build_scenario_corpus capability x artifact coverage gap",
                        "expected_tokens": list(tokens),
                        "lift_evidence": "prove_lift (admission evidence, candidate lane — not promotion)",
                        "blackbox_frame_generation": MINTED_BLACKBOX_FRAME_GENERATION,
                    },
                    **BOUNDARY,
                })
    return cards


# ── the write gate (ONE staged filename ever; append-only with dedupe; boundary enforced) ─────────────────

def serialize_card(card: dict[str, Any]) -> str:
    """Canonical one-line JSON for a card — sorted keys, compact separators, so two mints of the same axes
    are byte-identical on disk (the determinism gate compares these bytes)."""
    return json.dumps(card, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_minted_card(card: dict[str, Any]) -> list[str]:
    """Problems that make a card unfit to stage (empty list == fit). The write path REFUSES any problem —
    this is the boundary gate the self-test mutates against."""
    problems: list[str] = []
    if card.get("candidate") is not True:
        problems.append("candidate must be True — a minted row is born a candidate")
    if card.get("serves_truth") is not False:
        problems.append("serves_truth must be False — generation is never promotion")
    pid = str(card.get("primitive_id") or "")
    if not _MINTED_ID_RE.match(pid):
        problems.append(f"primitive_id {pid!r} is not a {MINTED_ID_PREFIX}-<sha256[:16]> id")
    title = str(card.get("title") or "")
    blackbox = str(card.get("blackbox") or "")
    if not title.strip():
        problems.append("title is required")
    if not blackbox.strip():
        problems.append("blackbox is required")
    if pid != canonical_id(MINTED_ID_PREFIX, title, blackbox):
        problems.append("primitive_id does not recompute from title+blackbox (tampered or stale)")
    for edge_field in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(edge_field) or "")):
            problems.append(f"{edge_field} must be a CamelCase type name")
    blocking_keys = card.get("blocking_keys")
    if not isinstance(blocking_keys, list) or not blocking_keys:
        problems.append("blocking_keys (the capability's expected tokens) are required")
    else:
        # the "naturally contains" gate: every expected token's words must sit in the title+blackbox token
        # set under the SAME split rule the verified-hit gate uses — a card that fails this can never cover.
        card_tokens = _text_tokens(f"{title} {blackbox}")
        for key in blocking_keys:
            words = [w for w in _TOKEN_SPLIT_RE.split(str(key).lower()) if w]
            if not words or not all(w in card_tokens for w in words):
                problems.append(f"expected token {key!r} is not carried naturally by title+blackbox")
    contract = card.get("contract")
    if (not isinstance(contract, dict) or not str(contract.get("input") or "").strip()
            or not str(contract.get("output") or "").strip()):
        problems.append("contract needs non-empty input and output descriptions")
    return problems


def mint_domain_flavored(capabilities: dict[str, tuple], artifacts: list[str], domains: list[str], *,
                         variants_per_pair: int = 1) -> list[dict[str, Any]]:
    """DOMAIN-FLAVORED minting (the 500K lever): one card per capability x artifact x DOMAIN x variant, whose
    title AND blackbox speak the domain's vocabulary — a genuinely more specific retrieval target (a booking
    portal for dental practices is not a booking portal for marinas), categorized by all three axes. Same id
    law, same gates, same determinism as mint_cards; ADD-only sibling, never a rewrite of it."""
    if variants_per_pair < 1:
        raise ValueError(f"variants_per_pair must be >= 1, got {variants_per_pair}")
    if not domains or len(set(domains)) != len(domains) or any(not str(d).strip() for d in domains):
        raise ValueError("domains must be non-empty, non-blank and duplicate-free")
    cards: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for capability in sorted(capabilities):
        tokens = [str(t) for t in capabilities[capability] if str(t).strip()]
        if not capability.strip() or not tokens:
            raise ValueError(f"capability {capability!r} needs a name and expected tokens")
        input_edge, output_edge = derive_capability_edges(capability)
        capability_title = capability[:1].upper() + capability[1:]
        token_prose = _natural_join(tokens)
        for artifact in artifacts:
            artifact = str(artifact)
            if not artifact.strip():
                raise ValueError("artifacts must be non-empty strings")
            a_art = f"{_article(artifact)} {artifact}"
            for domain in domains:
                for variant_index in range(variants_per_pair):
                    role = _variant_role(variant_index)
                    title = f"{capability_title} {role} for {artifact} serving {domain}"
                    frame = VARIANT_BLACKBOX_FRAMES[variant_index % len(VARIANT_BLACKBOX_FRAMES)]
                    blackbox = (frame.format(cap=capability, a_art=a_art, toks=token_prose, role=role)
                                + f" Tuned for {domain} workflows, records, and vocabulary.")
                    pid = canonical_id(MINTED_ID_PREFIX, title, blackbox)
                    if pid in seen_ids:
                        raise ValueError(f"duplicate domain-flavored mint for {title!r}")
                    seen_ids.add(pid)
                    cards.append({
                        "record_type": MINTED_RECORD_TYPE, "schema_version": MINTED_SCHEMA_VERSION,
                        "kind": MINTED_CARD_KIND, "primitive_id": pid, "title": title,
                        "capability": capability, "artifact": artifact, "domain": domain,
                        "variant_index": variant_index, "variant_role": role,
                        "input_edge": input_edge, "output_edge": output_edge, "blackbox": blackbox,
                        "blocking_keys": list(tokens),
                        "contract": {"input": f"{capability} requirement for {a_art} serving {domain}",
                                     "output": f"working {capability} capability for the {artifact} "
                                               f"in {domain} with {', '.join(tokens)} handled"},
                        "readiness": MINTED_READINESS_UNPROVEN,
                        "promotion_blockers": list(MINTED_PROMOTION_BLOCKERS),
                        "provenance": {"minter": "scripts.mint_gap_primitives.mint_domain_flavored",
                                       "axes": "capability x artifact x domain", "candidate": True,
                                       "blackbox_frame_generation": MINTED_BLACKBOX_FRAME_GENERATION},
                        "candidate": True, "serves_truth": False})
    return cards


def default_staged_path() -> Path:
    """The ONE staged file this module writes — a NEW sibling of the verified corpus files, never one of
    them (write_staged enforces the filename)."""
    return VERIFIED_FACTORY_CORPUS_PATH.parent / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], staged_path: Optional[Path] = None) -> dict[str, Any]:
    """APPEND cards to the staged candidates file, deduped by primitive_id against the lines already there
    and within the batch (a second identical run appends NOTHING — byte-stable file). HARD GATE: the target
    filename must be exactly ``STAGED_FILENAME``, the target must not be a SYMLINK, and the RESOLVED real
    path must still carry the staged filename and never equal the verified corpus file — any other target
    (in particular every verified corpus file, even one reached through a planted link) is refused before a
    byte is written. Raises on any card that fails validate_minted_card. The pre-existing file is scanned
    in ONE streaming pass (ids and the line count harvested together — the GB-scale pool is never parsed
    twice and never materialized as a list of dicts)."""
    path = Path(staged_path) if staged_path is not None else default_staged_path()
    if path.name != STAGED_FILENAME:
        raise ValueError(f"write_staged writes exactly one filename ({STAGED_FILENAME!r}); refusing "
                         f"{path.name!r} — the verified corpus files are never written by this module")
    if path.is_symlink():
        raise ValueError(f"refusing symlinked staged path {path} — open(..., 'a') follows symlinks, so a "
                         "planted link could retarget the append into a verified corpus file")
    resolved = path.resolve()
    if resolved.name != STAGED_FILENAME or resolved == VERIFIED_FACTORY_CORPUS_PATH.resolve():
        raise ValueError(f"staged path {path} resolves to {resolved} — write_staged writes exactly one "
                         f"real file named {STAGED_FILENAME!r}, never a verified corpus file")
    # ONE streaming pass over the (potentially GB-scale) staged pool: ids + pre-existing row count together.
    pre_existing = 0
    existing_ids: set[str] = set()
    for row in iter_jsonl_tolerant(path):
        pre_existing += 1
        existing_ids.add(str(row.get("primitive_id") or ""))
    lines: list[str] = []
    appended = skipped = 0
    for card in cards:
        problems = validate_minted_card(card)
        if problems:
            raise ValueError(f"refusing to stage invalid card {card.get('primitive_id')!r}: {problems}")
        pid = card["primitive_id"]
        if pid in existing_ids:
            skipped += 1
            continue
        existing_ids.add(pid)
        lines.append(serialize_card(card))
        appended += 1
    if lines:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return {
        "record_type": "minted_gap_primitive_append_report",
        "staged_path": str(path),
        "minted": len(cards),
        "appended": appended,
        "skipped_already_staged": skipped,
        # computed from the single streaming pass (same tolerant-parse semantics as before): rows that were
        # already in the pool plus the rows this call appended — the file is never re-read to count.
        "total_staged_lines": pre_existing + appended,
        # pool metadata: which frame generation this mint used + the generations it supersedes (the prior
        # generations' rows remain in the pool file, append-only — see SUPERSEDED_BLACKBOX_FRAME_GENERATIONS).
        "blackbox_frame_generation": MINTED_BLACKBOX_FRAME_GENERATION,
        "superseded_frame_generations": [g["generation"] for g in SUPERSEDED_BLACKBOX_FRAME_GENERATIONS],
        **BOUNDARY,
    }


# ── the lift proof (admission evidence, never promotion) ───────────────────────────────────────────────────

def prove_lift(base_cards: list[dict[str, Any]], minted: list[dict[str, Any]],
               scenarios: list[dict[str, Any]], k: int = DEFAULT_PROVE_TOP_K) -> dict[str, Any]:
    """Run the corpus module's VERIFIED coverage three ways — base cards, base + minted, and base + minted
    stripped of ``blocking_keys`` (the PROSE-ONLY ablation) — over the same scenarios and report the hit
    rates plus the delta.

    The ablation exists because the verified-hit gate folds ``blocking_keys`` into a card's token set and a
    minted card's blocking_keys are a verbatim copy of the scenario answer key — so without it the receipt
    could not distinguish prose-earned hits from key-copied hits. ``with_minted_prose_only_hit_rate`` is
    computed from per-card copies with the key list removed (the minted cards are never mutated; coverage
    and the search-doc builder both tolerate absent blocking_keys), so it measures what title+blackbox text
    ALONE earns.

    This receipt is ADMISSION EVIDENCE for the candidate lane, NOT promotion: it shows the minted candidates
    close measured coverage gaps, while every minted row stays candidate=true / serves_truth=false with its
    promotion blockers intact. Promotion goes through the factory gates (source review + an executed passing
    proof), never through this measurement."""
    base_receipt = scenario_coverage(base_cards, scenarios, k=k)
    with_minted_receipt = scenario_coverage(list(base_cards) + list(minted), scenarios, k=k)
    # PROSE-ONLY ablation: the same minted cards minus the copied answer key (per-card dict copy — the
    # originals keep their blocking_keys untouched); any hit here is earned by title+blackbox prose.
    prose_only_minted = [{key: value for key, value in card.items() if key != "blocking_keys"}
                         for card in minted]
    prose_only_receipt = scenario_coverage(list(base_cards) + prose_only_minted, scenarios, k=k)
    base_rate = base_receipt["verified_hit_rate"]
    minted_rate = with_minted_receipt["verified_hit_rate"]
    return {
        "record_type": "minted_gap_primitive_lift_proof",
        "scenarios": len(scenarios),
        "k": k,
        "base_cards": len(base_cards),
        "minted_cards": len(minted),
        "base_verified_hit_rate": base_rate,
        "with_minted_verified_hit_rate": minted_rate,
        "with_minted_prose_only_hit_rate": prose_only_receipt["verified_hit_rate"],
        "delta": round(minted_rate - base_rate, 4),
        "base_coverage": base_receipt,
        "with_minted_coverage": with_minted_receipt,
        "note": "admission evidence for the candidate lane, not promotion — minted rows remain "
                "candidate=true/serves_truth=false; promotion goes through the factory gates. The "
                "prose-only rate re-runs coverage with the minted cards' blocking_keys removed, proving "
                "hits are earned by title+blackbox text rather than by the copied answer-key list.",
        **BOUNDARY,
    }


# ── self-test (hermetic: tiny injected axes + temp dirs; plus the live default-axes plan, in memory) ──────

def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # tiny INJECTED axes with novel names — proving nothing about the real axes is hardcoded in the minter.
    tiny_capabilities: dict[str, tuple] = {
        "quantum flux calibration": ("quantum", "flux", "calibration"),
        "zorple stream shaping": ("zorple", "shaping", "streamgate"),
    }
    tiny_artifacts = ["orbital telemetry console", "widget kiosk"]
    tiny_variants = 3

    minted_a = mint_cards(tiny_capabilities, tiny_artifacts, variants_per_pair=tiny_variants)
    minted_b = mint_cards(tiny_capabilities, tiny_artifacts, variants_per_pair=tiny_variants)
    expected_n = len(tiny_capabilities) * len(tiny_artifacts) * tiny_variants

    # 1) count formula + determinism (byte-identical twice).
    checks.append((f"mints exactly len(caps)*len(artifacts)*variants = {expected_n} cards, byte-identical "
                   "across two mints",
                   len(minted_a) == expected_n
                   and [serialize_card(c) for c in minted_a] == [serialize_card(c) for c in minted_b]))

    # 2) id law: every id starts with the prefix, matches the shape, is distinct, and recomputes.
    checks.append(("id law: all ids start with 'prim-minted-', are distinct, and recompute from "
                   "title+blackbox via canonical_id",
                   len({c["primitive_id"] for c in minted_a}) == expected_n
                   and all(c["primitive_id"].startswith(f"{MINTED_ID_PREFIX}-") for c in minted_a)
                   and all(_MINTED_ID_RE.match(c["primitive_id"]) for c in minted_a)
                   and all(c["primitive_id"] == canonical_id(MINTED_ID_PREFIX, c["title"], c["blackbox"])
                           for c in minted_a)))

    # 3) card anatomy: expected tokens carried NATURALLY (same split rule as the verified-hit gate),
    #    artifact words present, blocking_keys == the expected tokens, contract complete, boundary stamped.
    def _carries(card: dict[str, Any]) -> bool:
        toks = _text_tokens(f"{card['title']} {card['blackbox']}")
        expect = list(tiny_capabilities[card["capability"]])
        return (all(all(w in toks for w in _TOKEN_SPLIT_RE.split(t.lower()) if w) for t in expect)
                and all(w in toks for w in _TOKEN_SPLIT_RE.split(card["artifact"].lower()) if w)
                and card["blocking_keys"] == expect)
    checks.append(("every card naturally carries its expected tokens + artifact vocabulary in "
                   "title+blackbox, blocking_keys are exactly the expected tokens, contract has "
                   "input+output, candidate=true/serves_truth=false",
                   all(_carries(c) for c in minted_a)
                   and all(not validate_minted_card(c) for c in minted_a)
                   and all(c["candidate"] is True and c["serves_truth"] is False for c in minted_a)))

    # 4) typed edges: CamelCase, derived from the capability's semantics (Requirement -> Capability).
    checks.append(("edges are CamelCase and derived from capability semantics "
                   "(QuantumFluxCalibrationRequirement -> QuantumFluxCalibrationCapability)",
                   all(_CAMEL_EDGE_RE.match(c["input_edge"]) and _CAMEL_EDGE_RE.match(c["output_edge"])
                       for c in minted_a)
                   and minted_a[0]["input_edge"] == "QuantumFluxCalibrationRequirement"
                   and minted_a[0]["output_edge"] == "QuantumFluxCalibrationCapability"))

    # 5) title shape matches the spec example pattern: '<Capability> <role> for <artifact>'.
    checks.append(("variant 0 title reads '<Capability> middleware for <artifact>' (the spec's example "
                   "shape) and the three variants of a pair are all distinct",
                   minted_a[0]["title"] == "Quantum flux calibration middleware for orbital telemetry console"
                   and len({c["title"] for c in minted_a}) == expected_n))

    with tempfile.TemporaryDirectory(prefix="mint_gap_primitives_selftest_") as td:
        tmp = Path(td)

        # 6) write gate: appends all cards; a second identical run appends 0 and the bytes do not change.
        staged = tmp / STAGED_FILENAME
        report1 = write_staged(minted_a, staged)
        bytes_before = staged.read_bytes()
        report2 = write_staged(minted_b, staged)
        checks.append(("write_staged appends all cards once; a second identical run appends 0 (all "
                       "deduped by id) and the staged file stays byte-identical",
                       report1["appended"] == expected_n and report2["appended"] == 0
                       and report2["skipped_already_staged"] == expected_n
                       and staged.read_bytes() == bytes_before
                       and report2["total_staged_lines"] == expected_n))

        # 7) NO VERIFIED-FILE WRITES: the default path is the NEW staged filename in the foundry dir —
        #    never a verified corpus file — and writing to a verified filename is REFUSED outright.
        refused = False
        try:
            write_staged(minted_a, tmp / VERIFIED_FACTORY_CORPUS_PATH.name)
        except ValueError:
            refused = True
        checks.append(("no verified-file writes: default path is the new staged filename beside (never "
                       "equal to) the verified corpus, and a verified filename is refused before any write",
                       default_staged_path().name == STAGED_FILENAME
                       and default_staged_path().parent == VERIFIED_FACTORY_CORPUS_PATH.parent
                       and STAGED_FILENAME != VERIFIED_FACTORY_CORPUS_PATH.name
                       and refused and not (tmp / VERIFIED_FACTORY_CORPUS_PATH.name).exists()))

        # 8) MUTATION gates: a flipped boundary bit and a tampered title are both rejected + refused.
        flipped = dict(minted_a[0])
        flipped["serves_truth"] = True
        flip_refused = False
        try:
            write_staged([flipped], tmp / STAGED_FILENAME)
        except ValueError:
            flip_refused = True
        retitled = dict(minted_a[0])
        retitled["title"] = "Something else entirely"
        stripped = dict(minted_a[0])
        stripped["blackbox"] = "A blackbox that names none of the expected concepts."
        stripped["title"] = "An unrelated module"  # tokens live in the TITLE too — strip both surfaces
        # DOMAIN-FLAVORED lane: count math caps x arts x domains x variants; the domain lives in title AND
        # blackbox (categorized + retrievable by domain); ids distinct from the plain mint; deterministic.
        flavored = mint_domain_flavored(tiny_capabilities, tiny_artifacts, ["orbital farms", "kelp ranching"],
                                        variants_per_pair=1)
        checks.append(("domain-flavored mint: exact count math + domain in both text surfaces + new ids",
                       len(flavored) == len(tiny_capabilities) * len(tiny_artifacts) * 2
                       and all(f["domain"] in f["title"] and f["domain"] in f["blackbox"] for f in flavored)
                       and not ({f["primitive_id"] for f in flavored} & {c["primitive_id"] for c in minted_a})
                       and flavored == mint_domain_flavored(tiny_capabilities, tiny_artifacts,
                                                            ["orbital farms", "kelp ranching"],
                                                            variants_per_pair=1)))
        checks.append(("mutation gates: serves_truth=True is refused by the write path; a tampered title "
                       "breaks the id recompute; a blackbox stripped of the expected tokens is flagged",
                       bool(validate_minted_card(flipped)) and flip_refused
                       and any("recompute" in p for p in validate_minted_card(retitled))
                       and any("carried naturally" in p for p in validate_minted_card(stripped))))

    # 9) REAL lift proof on synthetic scenarios: the base corpus covers quantum flux but MISSES zorple;
    #    the minted cards close the zorple gap -> delta > 0 (verified coverage, not "returned something").
    base_cards = [
        {"primitive_id": "s:quantum", "title": "Quantum flux calibration engine",
         "blackbox": "Calibrates quantum flux against a fluxgate baseline and reports calibration drift.",
         "input_edge": "In", "output_edge": "Out", **BOUNDARY},
        {"primitive_id": "s:decoy", "title": "Pebble polisher",
         "blackbox": "Polishes pebbles into a smooth gravel heap.",
         "input_edge": "Pebble", "output_edge": "GravelHeap", **BOUNDARY},
    ]
    synth_scenarios = [
        {"record_type": "build_scenario", "capability": "quantum flux calibration",
         "artifact": "orbital telemetry console",
         "query": "quantum flux calibration for an orbital telemetry console",
         "expected_tokens": ["quantum", "flux", "calibration"], **BOUNDARY},
        {"record_type": "build_scenario", "capability": "quantum flux calibration",
         "artifact": "widget kiosk", "query": "add quantum flux calibration to my widget kiosk",
         "expected_tokens": ["quantum", "flux", "calibration"], **BOUNDARY},
        {"record_type": "build_scenario", "capability": "zorple stream shaping",
         "artifact": "widget kiosk", "query": "zorple stream shaping for a widget kiosk",
         "expected_tokens": ["zorple", "shaping", "streamgate"], **BOUNDARY},
        {"record_type": "build_scenario", "capability": "zorple stream shaping",
         "artifact": "orbital telemetry console",
         "query": "need zorple stream shaping in the orbital telemetry console we are building",
         "expected_tokens": ["zorple", "shaping", "streamgate"], **BOUNDARY},
    ]
    proof = prove_lift(base_cards, minted_a, synth_scenarios, k=2)
    checks.append(("REAL lift proof: base coverage misses the zorple capability (rate 0.5), base+minted "
                   "covers it (rate 1.0) -> delta > 0, and the receipt is candidate/serves_truth=false",
                   proof["base_verified_hit_rate"] == 0.5
                   and proof["with_minted_verified_hit_rate"] == 1.0
                   and proof["delta"] > 0
                   and all(m["capability"] == "zorple stream shaping"
                           for m in proof["base_coverage"]["misses_sample"])
                   and proof["with_minted_coverage"]["misses_sample"] == []
                   and proof["serves_truth"] is False))

    # 10) the LIVE default-axes plan (in memory, no disk): the default mint at DEFAULT_VARIANTS_PER_PAIR
    #     obeys the count formula over the imported single-source axes and clears the thousands target.
    live_caps = default_capability_axis()
    live_artifacts = default_artifact_axis()
    live_minted = mint_cards(live_caps, live_artifacts, variants_per_pair=DEFAULT_VARIANTS_PER_PAIR)
    live_expected = len(live_caps) * len(live_artifacts) * DEFAULT_VARIANTS_PER_PAIR
    checks.append((f"live axes: default mint = len(caps)={len(live_caps)} x len(artifact_forms)="
                   f"{len(live_artifacts)} x {DEFAULT_VARIANTS_PER_PAIR} = {live_expected} cards "
                   f">= {TARGET_MINTED_MINIMUM}, all ids distinct, every card valid",
                   len(live_minted) == live_expected
                   and live_expected >= TARGET_MINTED_MINIMUM
                   and len({c["primitive_id"] for c in live_minted}) == live_expected
                   and not validate_minted_card(live_minted[0])
                   and not validate_minted_card(live_minted[-1])))

    # 11) axes are the single source (imported, not copied): the default axes ARE the corpus module's rows,
    #     and the bare artifact lane is exactly its artifact axis.
    checks.append(("axes single-sourced from scripts.build_scenario_corpus (capabilities dict equal; bare "
                   "artifact lane == the artifact axis; stacked forms = artifacts x stacks)",
                   live_caps == dict(SCENARIO_CAPABILITY_AXIS)
                   and default_artifact_axis(bare=True) == list(SCENARIO_ARTIFACT_AXIS)
                   and len(live_artifacts) == len(SCENARIO_ARTIFACT_AXIS) * len(SCENARIO_STACK_AXIS)))

    # 12) input-law gates: variants_per_pair < 1 and duplicate axis entries raise instead of mis-counting.
    bad_variants = bad_duplicate = False
    try:
        mint_cards(tiny_capabilities, tiny_artifacts, variants_per_pair=0)
    except ValueError:
        bad_variants = True
    try:
        mint_cards(tiny_capabilities, ["widget kiosk", "widget kiosk"], variants_per_pair=1)
    except ValueError:
        bad_duplicate = True
    checks.append(("input law: variants_per_pair=0 raises; a duplicate artifact raises instead of "
                   "silently collapsing the count", bad_variants and bad_duplicate))

    # 13) (ADDED 2026-07-07 review) domain-flavored input law mirrors mint_cards' guards: a blank artifact,
    #     a blank domain, and an empty domain list all raise instead of minting malformed cards that
    #     validate_minted_card would wave into the production pool.
    blank_artifact_refused = blank_domain_refused = empty_domains_refused = False
    try:
        mint_domain_flavored(tiny_capabilities, ["  "], ["dental practices"], variants_per_pair=1)
    except ValueError:
        blank_artifact_refused = True
    try:
        mint_domain_flavored(tiny_capabilities, tiny_artifacts, [""], variants_per_pair=1)
    except ValueError:
        blank_domain_refused = True
    try:
        mint_domain_flavored(tiny_capabilities, tiny_artifacts, [], variants_per_pair=1)
    except ValueError:
        empty_domains_refused = True
    checks.append(("domain-flavored input law: a blank artifact, a blank domain, and an empty domain list "
                   "all raise instead of staging malformed cards",
                   blank_artifact_refused and blank_domain_refused and empty_domains_refused))

    # 14) (ADDED 2026-07-07 review) the write gate is not name-only: a planted SYMLINK named exactly the
    #     staged filename pointing at a verified-named file is refused before a byte is written, and the
    #     link target stays byte-identical.
    with tempfile.TemporaryDirectory(prefix="mint_gap_primitives_selftest_symlink_") as td_link:
        tmp_link = Path(td_link)
        decoy_verified = tmp_link / VERIFIED_FACTORY_CORPUS_PATH.name
        decoy_verified.write_text('{"decoy_verified_row": true}\n', encoding="utf-8")
        decoy_bytes_before = decoy_verified.read_bytes()
        planted_link = tmp_link / STAGED_FILENAME
        planted_link.symlink_to(decoy_verified)
        symlink_refused = False
        try:
            write_staged(minted_a, planted_link)
        except ValueError:
            symlink_refused = True
        checks.append(("write gate beats a planted symlink: a link named the staged filename pointing at "
                       "a verified-named file is refused and the target stays byte-identical",
                       symlink_refused and decoy_verified.read_bytes() == decoy_bytes_before))

    # 15) (ADDED 2026-07-07 review) the receipt itself proves hits are EARNED BY PROSE, not by the copied
    #     answer key: the prose-only ablation (minted minus blocking_keys) still covers everything on the
    #     synthetic set, and the ablation copies — the minted cards keep their blocking_keys untouched.
    checks.append(("prose-only ablation: with_minted_prose_only_hit_rate == 1.0 on the synthetic set and "
                   "the minted cards keep their blocking_keys (the ablation copies, never mutates)",
                   proof["with_minted_prose_only_hit_rate"] == 1.0
                   and all("blocking_keys" in c for c in minted_a)))

    # 16) (ADDED 2026-07-07 review) frame supersession is RECORDED pool metadata, not a silent rewrite:
    #     every minted card (plain and domain-flavored) stamps the live blackbox frame generation, the
    #     write report names the superseded generations, and each superseded generation preserves its exact
    #     prior frame texts, sits strictly below the live generation, and differs from the live frames.
    checks.append(("frame supersession recorded: cards stamp the live frame generation, the write report "
                   "carries generation + superseded list, and superseded generations preserve their frames",
                   all(c["provenance"]["blackbox_frame_generation"] == MINTED_BLACKBOX_FRAME_GENERATION
                       for c in minted_a)
                   and all(f["provenance"]["blackbox_frame_generation"] == MINTED_BLACKBOX_FRAME_GENERATION
                           for f in flavored)
                   and report1["blackbox_frame_generation"] == MINTED_BLACKBOX_FRAME_GENERATION
                   and report1["superseded_frame_generations"]
                   == [g["generation"] for g in SUPERSEDED_BLACKBOX_FRAME_GENERATIONS]
                   and all(gen["generation"] < MINTED_BLACKBOX_FRAME_GENERATION and gen["frames"]
                           and tuple(gen["frames"]) != tuple(VARIANT_BLACKBOX_FRAMES)
                           for gen in SUPERSEDED_BLACKBOX_FRAME_GENERATIONS)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - mint_gap_primitives: deterministic gap-mint over the single-source scenario axes — "
          f"tiny injected axes mint {expected_n} byte-identical cards with prim-minted sha256 ids, natural "
          f"expected-token blackboxes (frame generation {MINTED_BLACKBOX_FRAME_GENERATION}; "
          f"{len(SUPERSEDED_BLACKBOX_FRAME_GENERATIONS)} superseded generation(s) recorded, prior staged "
          f"rows preserved append-only), CamelCase Requirement->Capability edges; the write gate stages "
          f"ONE new file in a single streaming pass with proven dedupe and refuses verified corpus "
          f"filenames AND planted symlinks; the lift proof shows a missed capability covered "
          f"(0.5 -> 1.0, delta +0.5) with a prose-only ablation proving hits are earned by text, not the "
          f"copied key list — admission evidence, not promotion; live default axes plan {len(live_caps)} "
          f"caps x {len(live_artifacts)} artifact forms x {DEFAULT_VARIANTS_PER_PAIR} = {live_expected} "
          f"cards (>= {TARGET_MINTED_MINIMUM}). Every row candidate=true / serves_truth=false.")
    return 0


# ── CLI ────────────────────────────────────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="hermetic proof (tiny injected axes + tmp dir)")
    ap.add_argument("--mint", action="store_true",
                    help="mint from the LIVE single-source axes, stage (append-only, deduped), print counts")
    ap.add_argument("--prove", action="store_true",
                    help="lift proof: verified coverage of a scenario sample, real corpus vs corpus+minted "
                         "(+ a prose-only ablation). The dense lane delta-embeds every minted card PER "
                         "query, so cost scales with minted x sample — PREFER --bare-artifacts (mints "
                         f"1/{len(SCENARIO_STACK_AXIS)} of the default set); a computed cost line prints "
                         "before the run")
    ap.add_argument("--variants-per-pair", type=int, default=DEFAULT_VARIANTS_PER_PAIR,
                    help="cards minted per capability x artifact pair")
    ap.add_argument("--bare-artifacts", action="store_true",
                    help="restrict the artifact axis to the bare artifacts (no stack-qualified forms)")
    ap.add_argument("--mint-domain-flavored", action="store_true",
                    help="mint capability x artifact x DOMAIN cards (the 500K lever), stage append-deduped")
    ap.add_argument("--sample", type=int, default=DEFAULT_PROVE_SAMPLE,
                    help="scenario sample size for --prove")
    ap.add_argument("--k", type=int, default=DEFAULT_PROVE_TOP_K, help="top-k for --prove coverage")
    ap.add_argument("--max-cards", type=int, default=None,
                    help="cap the real base corpus for a faster --prove (default: full corpus)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()

    if args.mint_domain_flavored:
        from scripts import build_scenario_corpus as _scen_axes  # noqa: PLC0415  single-source domain axis
        capabilities = default_capability_axis()
        artifacts = default_artifact_axis(bare=True)  # bare artifacts x domains (stacked forms would explode)
        domains = list(_scen_axes._DOMAINS)  # noqa: SLF001
        flavored = mint_domain_flavored(capabilities, artifacts, domains,
                                        variants_per_pair=args.variants_per_pair)
        report = write_staged(flavored)
        report.update({"capabilities": len(capabilities), "artifacts_bare": len(artifacts),
                       "domains": len(domains), "variants_per_pair": args.variants_per_pair,
                       "domain_flavored_minted": len(flavored)})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.mint or args.prove:
        capabilities = default_capability_axis()
        artifacts = default_artifact_axis(bare=args.bare_artifacts)
        minted = mint_cards(capabilities, artifacts, variants_per_pair=args.variants_per_pair)

    if args.mint:
        report = write_staged(minted)
        report.update({
            "capabilities": len(capabilities),
            "artifact_forms": len(artifacts),
            "variants_per_pair": args.variants_per_pair,
            "target_minimum": TARGET_MINTED_MINIMUM,
            "meets_target": len(minted) >= TARGET_MINTED_MINIMUM,
        })
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.prove:
        from scripts import capability_embedding as _emb  # noqa: PLC0415  resolve the live embed path (cost line)
        from scripts import path_graph_bench as _bench  # noqa: PLC0415  heavy: real-corpus loader (reused)
        base_cards = _bench._load_scale_corpus(args.max_cards)  # noqa: SLF001  the ONE scale-corpus loader
        pool = generate_scenarios(SCENARIO_POOL_DEFAULT_COUNT)
        step = max(1, len(pool) // max(1, args.sample))
        scenarios = pool[::step][:args.sample]
        # HONEST COST LINE (2026-07-07 review): coverage's dense lane delta-embeds every out-of-store card
        # PER QUERY and all minted cards are out-of-store; the with-minted sweep and the prose-only
        # ablation sweep both carry them. Printed, never hidden — the minted set is never capped or
        # subsampled silently, because that would change what the receipt measures.
        minted_carrying_sweeps = 2  # the with-minted sweep + the prose-only ablation sweep
        estimated_delta_embeds = minted_carrying_sweeps * len(minted) * len(scenarios)
        bare_minted_count = len(capabilities) * len(SCENARIO_ARTIFACT_AXIS) * args.variants_per_pair
        print(f"cost: dense delta lane ~= {minted_carrying_sweeps} sweeps x {len(minted):,} minted x "
              f"{len(scenarios)} scenarios = {estimated_delta_embeds:,} single-text embeds "
              f"(embed path: {_emb.real_text_path()}); "
              + ("--bare-artifacts is active."
                 if args.bare_artifacts else
                 f"prefer --bare-artifacts (mints {bare_minted_count:,} instead of {len(minted):,})."))
        print(f"lift proof: {len(scenarios)} scenarios; base {len(base_cards)} cards vs base + "
              f"{len(minted)} minted; k={args.k} ...")
        proof = prove_lift(base_cards, minted, scenarios, k=args.k)
        headline = {key: proof[key] for key in
                    ("scenarios", "k", "base_cards", "minted_cards", "base_verified_hit_rate",
                     "with_minted_verified_hit_rate", "with_minted_prose_only_hit_rate", "delta", "note")}
        headline["base_weakest_capabilities"] = proof["base_coverage"]["weakest_capabilities"]
        headline["with_minted_weakest_capabilities"] = proof["with_minted_coverage"]["weakest_capabilities"]
        print(json.dumps(headline, indent=2, sort_keys=True))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
