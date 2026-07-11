"""scripts/primitive_scale_plan — the executable route to >=200,000 searchable-staged primitives.

The searchable corpus today is the two READ-ONLY base card files (verified factory cards + primitive edge
cards). Three staged candidate pools already exist on disk (minted gap candidates, template-minted producer
cards, context-foundry drafts). This module PLANS and ASSEMBLES a clearly-labelled searchable-STAGED
extension pool from those candidates, behind six named admission gates, until the combined searchable
total (base + admitted staged) reaches the target — or the pools are exhausted.

Laws honored (candidate/truth boundary · lossless · naming · no-magic-values · determinism):
- every assembled row is stamped ``candidate=true, serves_truth=false, record_type
  searchable_staged_primitive`` + pool provenance — assembly NEVER promotes anything to verified; the
  output is a searchable-STAGED pool, one honest layer above raw candidates and far below promotion;
- LOSSLESS: every original field of an admitted row survives; if a stamped key would overwrite a
  differing original value, the original is preserved under ``original_<key>``;
- ids are NEVER re-minted — admitted rows keep the id their pool minted under its existing scheme;
- all counts are COMPUTED live from the pool files (``ledger()``), never typed into prose or code;
- deterministic: no RNG, no timestamps — assembling twice yields byte-identical output + manifest;
- the verified/base corpus files are READ-ONLY: they are only ever opened for read, and the output-path
  guard refuses to write over ANY registered pool file.

CLI: ``--plan`` (ledger + arithmetic to target) · ``--assemble`` (build the pool + manifest) ·
``--self-test`` (hermetic tmp pools; exact gate-rejection counts; determinism; boundary; lossless;
target-stop; manifest math).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional

from scripts._repo_paths import repo_root, resource

# ---------------------------------------------------------------------------------------------------------
# Constants (single definitions — no value typed twice)
# ---------------------------------------------------------------------------------------------------------

# Owner scale goal (rows): searchable base + admitted staged rows must reach at least this total.
DEFAULT_TARGET_SEARCHABLE_TOTAL = 200_000

# Record type stamped on every assembled row: a SEARCHABLE-STAGED candidate — not verified, not promoted.
SEARCHABLE_STAGED_RECORD_TYPE = "searchable_staged_primitive"

# Fields stamped onto every admitted row (the candidate/truth boundary made explicit on the row itself).
STAGED_ROW_STAMP = (
    ("record_type", SEARCHABLE_STAGED_RECORD_TYPE),
    ("candidate", True),
    ("serves_truth", False),
)
# Provenance key naming the pool an admitted row came from.
STAGED_ROW_POOL_PROVENANCE_KEY = "source_pool"
# Prefix under which a differing original value of a stamped key is preserved (lossless law).
ORIGINAL_FIELD_PRESERVE_PREFIX = "original_"

# Field-extraction key orders (observed shapes across the five pool files — see POOLS id_scheme notes).
ROW_ID_KEYS = ("primitive_id", "id", "card_id")
ROW_TITLE_KEYS = ("title", "name")

# Admission gates in evaluation order; a row is rejected by the FIRST failing gate (so per-gate rejection
# counts partition the stream exactly: admitted + rejected + unparseable == streamed).
ADMISSION_GATE_ORDER = (
    "has_id",
    "has_title",
    "has_text",
    "has_both_edges",
    "id_not_in_searchable",
    "title_text_not_duplicate",
)
# Accounting bucket for lines that are not parseable JSON objects (kept out of the gate names because it
# fires before any gate can run; it still participates in the manifest math).
UNPARSEABLE_BUCKET = "unparseable"

# Pool roles.
POOL_ROLE_SEARCHABLE_BASE = "searchable_base_read_only_reference"
POOL_ROLE_CANDIDATE = "candidate_source"

_DATA = resource("data")
_EDGE_FOUNDRY_DIR = _DATA / "dev-intel" / "aidevobserver_edge_foundry"

# Default output location for the assembled searchable-staged pool + its manifest (same directory as the
# searchable base files it extends; the write-guard below keeps the base files themselves untouchable).
DEFAULT_OUTPUT_PATH = _EDGE_FOUNDRY_DIR / "searchable_extended_pool.jsonl"


def default_manifest_path(output_path: Path) -> Path:
    """Manifest path derived from the pool path (matches the existing *_manifest.json convention)."""
    return output_path.with_name(output_path.stem + "_manifest.json")


# ---------------------------------------------------------------------------------------------------------
# POOLS — the module-level registry of the four pools (paths via scripts._repo_paths.resource("data")).
# `id_scheme` strings are documentation of the EXISTING minting schemes (never re-minted here); all counts
# come from ledger(), never from prose.
# ---------------------------------------------------------------------------------------------------------

POOLS = (
    {
        "pool": "searchable_base",
        "role": POOL_ROLE_SEARCHABLE_BASE,
        "priority": 0,  # not streamed for admission — it is the reference set candidates must not collide with
        "members": (
            ("base_verified_factory_cards",
             _EDGE_FOUNDRY_DIR / "verified_factory_primitive_cards.jsonl"),
            ("base_primitive_edge_cards",
             _EDGE_FOUNDRY_DIR / "primitive_edge_cards.jsonl"),
        ),
        "id_scheme": "prim:vf:<hex20> and prim:<hex20>",
    },
    {
        "pool": "minted_gap_candidates",
        "role": POOL_ROLE_CANDIDATE,
        "priority": 1,  # highest-priority candidate source (richest cards: title+blackbox+both edges)
        "members": (
            ("minted_gap_candidates",
             _EDGE_FOUNDRY_DIR / "minted_gap_primitive_candidates.jsonl"),
        ),
        "id_scheme": "prim-minted-<hex16>",
    },
    {
        "pool": "template_minted_producer_cards_v2",
        "role": POOL_ROLE_CANDIDATE,
        "priority": 2,
        "members": (
            ("template_minted_producer_cards_v2",
             _DATA / "dev-intel" / "domain_token_savings" / "template_minted_producer_cards_v2.jsonl"),
        ),
        "id_scheme": "codefactory-<hex16>",
    },
    {
        "pool": "context_foundry_drafts",
        "role": POOL_ROLE_CANDIDATE,
        "priority": 3,  # lowest priority: drafts carry no prose text yet, so most fail the has_text gate
        "members": (
            ("context_foundry_drafts",
             _DATA / "dev-intel" / "aidevobserver_context_foundry" / "primitive_drafts.jsonl"),
        ),
        "id_scheme": "prim:candidate:<surface>:<slug> (slug-based, not hash-suffixed)",
    },
)


def _base_pools(pools) -> list[dict]:
    return [p for p in pools if p["role"] == POOL_ROLE_SEARCHABLE_BASE]


def _candidate_pools_in_priority_order(pools) -> list[dict]:
    return sorted((p for p in pools if p["role"] == POOL_ROLE_CANDIDATE), key=lambda p: p["priority"])


# ---------------------------------------------------------------------------------------------------------
# Row field extraction (pure; tolerant of the observed per-pool shapes)
# ---------------------------------------------------------------------------------------------------------

def row_id(row: dict) -> str:
    for key in ROW_ID_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def row_title(row: dict) -> str:
    for key in ROW_TITLE_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def row_text(row: dict) -> str:
    """The prose text of a card: blackbox str, or blackbox dict's `does`, or `description`."""
    blackbox = row.get("blackbox")
    if isinstance(blackbox, str) and blackbox.strip():
        return blackbox.strip()
    if isinstance(blackbox, dict):
        does = blackbox.get("does")
        if isinstance(does, str) and does.strip():
            return does.strip()
    description = row.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    return ""


def _edge_value(row: dict, edge_key: str, contract_key: str) -> str:
    value = row.get(edge_key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    contract = row.get("contract")
    if isinstance(contract, dict):
        value = contract.get(contract_key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def row_input_edge(row: dict) -> str:
    return _edge_value(row, "input_edge", "input")


def row_output_edge(row: dict) -> str:
    return _edge_value(row, "output_edge", "output")


def _normalized(text: str) -> str:
    """Case- and whitespace-insensitive normalization for duplicate detection (punctuation preserved)."""
    return " ".join(text.lower().split())


def title_text_hash(row: dict) -> str:
    """Canonical sha256 over normalized title+text — the duplicate-content identity of a card."""
    payload = _normalized(row_title(row)) + "\n" + _normalized(row_text(row))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------------------
# ADMISSION GATES — pure functions, one per named gate (no side effects; context passed in explicitly)
# ---------------------------------------------------------------------------------------------------------

def gate_has_id(row: dict) -> bool:
    return bool(row_id(row))


def gate_has_title(row: dict) -> bool:
    return bool(row_title(row))


def gate_has_text(row: dict) -> bool:
    return bool(row_text(row))


def gate_has_both_edges(row: dict) -> bool:
    return bool(row_input_edge(row)) and bool(row_output_edge(row))


def gate_id_not_in_searchable(row: dict, searchable_ids: set) -> bool:
    """Exact-set membership: the id must not already be searchable (base ids + previously admitted ids —
    the searchable set GROWS as rows are admitted, so a duplicate id can never enter the pool twice)."""
    return row_id(row) not in searchable_ids


def gate_title_text_not_duplicate(row: dict, seen_title_text_hashes: set) -> bool:
    """Normalized title+text hash must be new vs the searchable base AND vs rows already admitted in this
    assembly (within-assembly dedupe)."""
    return title_text_hash(row) not in seen_title_text_hashes


def first_failing_gate(row: dict, searchable_ids: set, seen_title_text_hashes: set) -> Optional[str]:
    """Evaluate the gates in ADMISSION_GATE_ORDER; return the first failing gate name, or None if admitted."""
    if not gate_has_id(row):
        return "has_id"
    if not gate_has_title(row):
        return "has_title"
    if not gate_has_text(row):
        return "has_text"
    if not gate_has_both_edges(row):
        return "has_both_edges"
    if not gate_id_not_in_searchable(row, searchable_ids):
        return "id_not_in_searchable"
    if not gate_title_text_not_duplicate(row, seen_title_text_hashes):
        return "title_text_not_duplicate"
    return None


# ---------------------------------------------------------------------------------------------------------
# Streaming engine (shared by ledger / plan / assemble)
# ---------------------------------------------------------------------------------------------------------

def _iter_jsonl(path: Path) -> Iterator[Optional[dict]]:
    """Yield parsed dict rows; None for a non-blank line that is not a JSON object (counted unparseable)."""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except ValueError:
                yield None
                continue
            yield parsed if isinstance(parsed, dict) else None


def _searchable_reference(pools) -> dict:
    """Scan the READ-ONLY searchable base members once: id set + title/text hash set + per-member counts."""
    ids: set = set()
    hashes: set = set()
    members: list[dict] = []
    for pool in _base_pools(pools):
        for member_name, path in pool["members"]:
            stats = {"member": member_name, "path": _portable_path(path),
                     "rows": 0, "with_id": 0, "with_title_text": 0, UNPARSEABLE_BUCKET: 0}
            for parsed in _iter_jsonl(path):
                stats["rows"] += 1
                if parsed is None:
                    stats[UNPARSEABLE_BUCKET] += 1
                    continue
                identifier = row_id(parsed)
                if identifier:
                    stats["with_id"] += 1
                    ids.add(identifier)
                if row_title(parsed) and row_text(parsed):
                    stats["with_title_text"] += 1
                    hashes.add(title_text_hash(parsed))
            members.append(stats)
    return {"members": members, "ids": ids, "title_text_hashes": hashes}


def _staged_row(row: dict, pool_name: str) -> dict:
    """The assembled output row: ALL original fields preserved (lossless), stamped with the candidate/truth
    boundary + pool provenance. A stamped key that would overwrite a differing original value has that
    original preserved under original_<key>."""
    staged = dict(row)
    stamp = STAGED_ROW_STAMP + ((STAGED_ROW_POOL_PROVENANCE_KEY, pool_name),)
    for key, value in stamp:
        if key in staged and staged[key] != value:
            staged[ORIGINAL_FIELD_PRESERVE_PREFIX + key] = staged[key]
        staged[key] = value
    return staged


def _stream_assembly(pools, target: Optional[int], emit: Optional[Callable[[dict], None]] = None) -> dict:
    """One deterministic pass: seed the searchable reference, then stream candidate pools in priority
    order, admitting rows that pass ALL gates, stopping when base + admitted reaches `target` (or at
    exhaustion when target is None). `emit` receives each admitted STAGED row (None = simulate only)."""
    reference = _searchable_reference(pools)
    searchable_ids: set = reference["ids"]
    seen_hashes: set = reference["title_text_hashes"]
    base_distinct_ids = len(searchable_ids)
    base_hash_count = len(seen_hashes)
    needed = None if target is None else max(0, target - base_distinct_ids)

    pool_stats: list[dict] = []
    admitted_total = 0
    for pool in _candidate_pools_in_priority_order(pools):
        stats = {
            "pool": pool["pool"],
            "priority": pool["priority"],
            "members": [_portable_path(path) for _name, path in pool["members"]],
            "streamed": 0,
            "admitted": 0,
            UNPARSEABLE_BUCKET: 0,
            "rejections": {name: 0 for name in ADMISSION_GATE_ORDER},
        }
        pool_stats.append(stats)
        if needed is not None and admitted_total >= needed:
            continue  # target already reached — pool intentionally left unstreamed (streamed == 0)
        for _member_name, path in pool["members"]:
            for parsed in _iter_jsonl(path):
                if needed is not None and admitted_total >= needed:
                    break
                stats["streamed"] += 1
                if parsed is None:
                    stats[UNPARSEABLE_BUCKET] += 1
                    continue
                failing = first_failing_gate(parsed, searchable_ids, seen_hashes)
                if failing is not None:
                    stats["rejections"][failing] += 1
                    continue
                stats["admitted"] += 1
                admitted_total += 1
                searchable_ids.add(row_id(parsed))
                seen_hashes.add(title_text_hash(parsed))
                if emit is not None:
                    emit(_staged_row(parsed, pool["pool"]))
            if needed is not None and admitted_total >= needed:
                break

    return {
        "schema_version": 1,
        "searchable_base": {
            "members": reference["members"],
            "distinct_ids": base_distinct_ids,
            "title_text_hashes": base_hash_count,
        },
        "target": target,
        "needed_from_candidates": needed,
        "gate_order": list(ADMISSION_GATE_ORDER),
        "pools": pool_stats,
        "admitted_total": admitted_total,
        "projected_searchable_total": base_distinct_ids + admitted_total,
        "stopped_at_target": bool(needed is not None and admitted_total >= needed),
    }


def verify_manifest_math(stats: dict) -> bool:
    """The accounting invariant: per pool, admitted + all gate rejections + unparseable == streamed; and
    the totals recompose. Used by the self-test and asserted after every real assemble."""
    admitted_sum = 0
    for pool in stats["pools"]:
        rejected = sum(pool["rejections"].values()) + pool[UNPARSEABLE_BUCKET]
        if pool["admitted"] + rejected != pool["streamed"]:
            return False
        admitted_sum += pool["admitted"]
    if admitted_sum != stats["admitted_total"]:
        return False
    expected_total = stats["searchable_base"]["distinct_ids"] + stats["admitted_total"]
    return expected_total == stats["projected_searchable_total"]


# ---------------------------------------------------------------------------------------------------------
# Public verbs: ledger / plan / assemble
# ---------------------------------------------------------------------------------------------------------

def ledger(pools=POOLS) -> dict:
    """Computed per-pool counts + gate pass/fail counts at exhaustion (no target stop, nothing written).
    Every number here is computed live from the pool files — never typed."""
    return _stream_assembly(pools, target=None, emit=None)


def plan(target: int = DEFAULT_TARGET_SEARCHABLE_TOTAL, pools=POOLS) -> dict:
    """The ledger plus the arithmetic to target: how many staged rows are needed, which pools supply them
    in priority order, and whether the target is reachable. Derived exactly from the exhaustion ledger
    (admission is order-stable, so truncating at the target cannot change which earlier rows admit)."""
    stats = ledger(pools)
    base = stats["searchable_base"]["distinct_ids"]
    needed = max(0, target - base)
    remaining = needed
    projection = []
    for pool in stats["pools"]:
        take = min(pool["admitted"], remaining)
        projection.append({"pool": pool["pool"], "admissible_at_exhaustion": pool["admitted"],
                           "projected_admitted_at_stop": take})
        remaining -= take
    projected_admitted = needed - remaining
    return {
        "target": target,
        "searchable_base_distinct_ids": base,
        "needed_from_candidates": needed,
        "admissible_total_at_exhaustion": stats["admitted_total"],
        "projection": projection,
        "projected_admitted_at_stop": projected_admitted,
        "projected_searchable_total": base + projected_admitted,
        "target_reachable": remaining == 0,
        "shortfall": remaining,
        "surplus_admissible_beyond_target": max(0, stats["admitted_total"] - needed),
        "ledger": stats,
    }


def _portable_path(path: Path | str) -> str:
    """Repo-relative when possible (machine-independent manifests); plain string otherwise."""
    try:
        return str(Path(path).resolve().relative_to(repo_root()))
    except ValueError:
        return str(path)


def _assert_output_path_safe(path: Path, pools) -> None:
    """The write boundary: never write over ANY registered pool file (the verified/base corpus files and
    the candidate pool files are read-only inputs to this module)."""
    resolved = Path(path).resolve()
    for pool in pools:
        for member_name, member_path in pool["members"]:
            if resolved == Path(member_path).resolve():
                raise ValueError(
                    f"refusing to write over pool file {member_name} at {member_path} — "
                    "pool inputs are read-only for this module")


def assemble(target: Optional[int] = DEFAULT_TARGET_SEARCHABLE_TOTAL, pools=POOLS,
             output_path: Path | str | None = None,
             manifest_path: Path | str | None = None) -> dict:
    """Build the searchable-staged extension pool: stream candidates through the gates in priority order,
    write admitted STAGED rows (lossless + stamped) to `output_path`, stop at target or exhaustion, and
    write a manifest (per-pool counts, per-gate rejections, content hash). Returns the manifest dict.
    Deterministic: byte-identical output + manifest on a re-run over the same pools."""
    out_path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT_PATH
    man_path = Path(manifest_path) if manifest_path is not None else default_manifest_path(out_path)
    _assert_output_path_safe(out_path, pools)
    _assert_output_path_safe(man_path, pools)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    content_hash = hashlib.sha256()
    rows_written = [0]
    tmp_path = out_path.with_name(out_path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        def emit(staged: dict) -> None:
            line = json.dumps(staged, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            content_hash.update(line.encode("utf-8"))
            rows_written[0] += 1

        stats = _stream_assembly(pools, target=target, emit=emit)
    os.replace(tmp_path, out_path)

    manifest = dict(stats)
    manifest.update({
        "record_type": "searchable_extended_pool_manifest",
        "candidate": True,
        "serves_truth": False,
        "generator": "scripts/primitive_scale_plan.py",
        "staged_record_type": SEARCHABLE_STAGED_RECORD_TYPE,
        "target_reached": stats["stopped_at_target"],
        "output": {
            "path": _portable_path(out_path),
            "rows": rows_written[0],
            "sha256": content_hash.hexdigest(),
        },
    })
    if rows_written[0] != stats["admitted_total"]:
        raise AssertionError("rows written diverged from admitted count — accounting bug")
    if not verify_manifest_math(manifest):
        raise AssertionError("manifest math failed: admitted + rejected != streamed")
    man_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------------------------------------
# CLI rendering
# ---------------------------------------------------------------------------------------------------------

def _print_plan(report: dict) -> None:
    stats = report["ledger"]
    print("POOL LEDGER (every count computed live from the pool files — never typed)")
    print("  searchable base (READ-ONLY reference):")
    for member in stats["searchable_base"]["members"]:
        print(f"    {member['member']:<38} rows={member['rows']:>9,}  with_id={member['with_id']:>9,}")
    print(f"    {'distinct searchable ids':<38} {stats['searchable_base']['distinct_ids']:>14,}")
    print(f"    {'title+text duplicate hashes seeded':<38} {stats['searchable_base']['title_text_hashes']:>14,}")
    print("  candidate pools (priority order; gate rejections are first-failing-gate counts):")
    for pool in stats["pools"]:
        print(f"    [{pool['priority']}] {pool['pool']}: streamed={pool['streamed']:,} "
              f"admissible={pool['admitted']:,} {UNPARSEABLE_BUCKET}={pool[UNPARSEABLE_BUCKET]:,}")
        rejected = {name: count for name, count in pool["rejections"].items() if count}
        print(f"        rejections: {rejected if rejected else '{}'}")
    print("ARITHMETIC TO TARGET")
    print(f"  target searchable total          {report['target']:>12,}")
    print(f"  searchable base (distinct ids)   {report['searchable_base_distinct_ids']:>12,}")
    print(f"  needed from candidate pools      {report['needed_from_candidates']:>12,}")
    print(f"  admissible at exhaustion         {report['admissible_total_at_exhaustion']:>12,}")
    for row in report["projection"]:
        print(f"    {row['pool']:<36} admissible={row['admissible_at_exhaustion']:>9,} "
              f"-> projected admitted at stop={row['projected_admitted_at_stop']:>9,}")
    print(f"  projected admitted at stop       {report['projected_admitted_at_stop']:>12,}")
    print(f"  projected searchable total       {report['projected_searchable_total']:>12,}")
    if report["target_reachable"]:
        print(f"  TARGET REACHABLE — surplus admissible beyond target: "
              f"{report['surplus_admissible_beyond_target']:,}")
    else:
        print(f"  TARGET NOT REACHABLE at exhaustion — shortfall: {report['shortfall']:,}")


# ---------------------------------------------------------------------------------------------------------
# Self-test (hermetic: synthetic tmp pools; the real pool files are only existence-checked, never read)
# ---------------------------------------------------------------------------------------------------------

def _write_jsonl(path: Path, rows: Iterable, raw_lines: Iterable[str] = ()) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        for raw in raw_lines:
            handle.write(raw + "\n")


def _self_test() -> int:  # noqa: PLR0915 — a single linear proof script is clearer than fragments
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'ok ' if ok else 'FAIL'} {name}{(' — ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    with tempfile.TemporaryDirectory(prefix="primitive_scale_plan_selftest_") as tmp:
        tmp_dir = Path(tmp)

        # --- synthetic searchable base (READ-ONLY reference) -------------------------------------------
        base_rows = [
            {"primitive_id": "prim:vf:base0000000000000001", "title": "Alpha Base Card",
             "blackbox": "Consumes A and emits B.", "input_edge": "A", "output_edge": "B",
             "candidate": True, "serves_truth": False},
            {"primitive_id": "prim:base0000000000000002", "title": "beta_edge_card",
             "blackbox": {"does": "Calls beta with C and returns D."},
             "input_edge": "C", "output_edge": "D", "candidate": True, "serves_truth": False},
            {"primitive_id": "prim:vf:base0000000000000003", "title": "Gamma Base Card",
             "blackbox": "Consumes E and emits F.", "input_edge": "E", "output_edge": "F",
             "candidate": True, "serves_truth": False},
        ]
        base_path = tmp_dir / "tiny_base.jsonl"
        _write_jsonl(base_path, base_rows)

        # --- synthetic candidate pool 1 (minted-like) — one row per gate + goods + a malformed line ----
        def _minted(identifier, title, text, extra=None, **edges):
            row = {"primitive_id": identifier, "title": title, "blackbox": text,
                   "record_type": "tiny_minted_candidate", "candidate": True, "serves_truth": False}
            row.update(edges)
            row.update(extra or {})
            return row

        good_1 = _minted("prim-minted-good000000000001", "Good One Card", "Turns G into H cleanly.",
                         extra={"custom_marker": "survives_losslessly"},
                         input_edge="G", output_edge="H")
        pool_1_rows = [
            good_1,                                                                     # admit (g1)
            _minted("prim:vf:base0000000000000001", "Dup Id Card", "Different text entirely.",
                    input_edge="I", output_edge="J"),                                   # id_not_in_searchable
            _minted("prim-minted-missingedge00001", "Missing Edge Card", "Has text but only one edge.",
                    input_edge="K"),                                                    # has_both_edges
            _minted("prim-minted-titledup00000001", "  ALPHA   base CARD ", "consumes a AND emits b.",
                    input_edge="L", output_edge="M"),                                   # title_text dup vs base
            _minted("", "No Id Card", "Text present, id missing.",
                    input_edge="N", output_edge="O"),                                   # has_id
            _minted("prim-minted-notitle000000001", "", "Text present, title missing.",
                    input_edge="P", output_edge="Q"),                                   # has_title
            _minted("prim-minted-notext0000000001", "No Text Card", "",
                    input_edge="R", output_edge="S"),                                   # has_text
            _minted("prim-minted-good000000000002", "Good Two Card", "Turns T into U cleanly.",
                    input_edge="T", output_edge="U"),                                   # admit (g2)
            _minted("prim-minted-withindup0000001", "good ONE card", "  turns g INTO h cleanly. ",
                    input_edge="V", output_edge="W"),                                   # within-assembly dup of g1
            # (raw malformed line appended below)                                       # unparseable
            _minted("prim-minted-good000000000003", "Good Three Card", "Turns X into Y cleanly.",
                    input_edge="X", output_edge="Y"),                                   # admit (g3)
            _minted("prim-minted-good000000000001", "Reused Id Card", "Same id as good one, new text.",
                    input_edge="Z", output_edge="AA"),                                  # id dup of admitted g1
        ]
        pool_1_path = tmp_dir / "tiny_minted.jsonl"
        _write_jsonl(pool_1_path, pool_1_rows[:9], raw_lines=["this is not json {"])
        with open(pool_1_path, "a", encoding="utf-8") as handle:
            for row in pool_1_rows[9:]:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

        # --- synthetic candidate pool 2 (producer-like): two good rows ---------------------------------
        pool_2_rows = [
            _minted("codefactory-tinygood00000001", "Producer Good One", "Compiled producer body one.",
                    input_edge="PA", output_edge="PB"),
            _minted("codefactory-tinygood00000002", "Producer Good Two", "Compiled producer body two.",
                    input_edge="PC", output_edge="PD"),
        ]
        pool_2_path = tmp_dir / "tiny_producers.jsonl"
        _write_jsonl(pool_2_path, pool_2_rows)

        # --- synthetic candidate pool 3 (draft-like): contract edges + description text; one no-text ---
        pool_3_rows = [
            {"primitive_id": "prim:candidate:tiny:draft-good", "title": "Draft Good Card",
             "description": "Draft with contract edges and a description.",
             "contract": {"input": "DA", "output": "DB"}, "record_type": "primitive_opportunity",
             "serves_truth": False},
            {"primitive_id": "prim:candidate:tiny:draft-no-text", "title": "Draft No Text Card",
             "contract": {"input": "DC", "output": "DD"}, "record_type": "primitive_opportunity",
             "serves_truth": False},
        ]
        pool_3_path = tmp_dir / "tiny_drafts.jsonl"
        _write_jsonl(pool_3_path, pool_3_rows)

        tmp_pools = (
            {"pool": "tiny_searchable_base", "role": POOL_ROLE_SEARCHABLE_BASE, "priority": 0,
             "members": (("tiny_base", base_path),), "id_scheme": "synthetic"},
            {"pool": "tiny_minted", "role": POOL_ROLE_CANDIDATE, "priority": 1,
             "members": (("tiny_minted", pool_1_path),), "id_scheme": "synthetic"},
            {"pool": "tiny_producers", "role": POOL_ROLE_CANDIDATE, "priority": 2,
             "members": (("tiny_producers", pool_2_path),), "id_scheme": "synthetic"},
            {"pool": "tiny_drafts", "role": POOL_ROLE_CANDIDATE, "priority": 3,
             "members": (("tiny_drafts", pool_3_path),), "id_scheme": "synthetic"},
        )

        base_bytes_before = base_path.read_bytes()
        out_path = tmp_dir / "out" / "searchable_extended_pool.jsonl"

        # 1) exhaustion assemble: exact per-gate rejection counts ----------------------------------------
        manifest = assemble(target=None, pools=tmp_pools, output_path=out_path)  # type: ignore[arg-type]
        pool_1_stats = manifest["pools"][0]
        expected_rejections = {"has_id": 1, "has_title": 1, "has_text": 1, "has_both_edges": 1,
                               "id_not_in_searchable": 2, "title_text_not_duplicate": 2}
        check("exact per-gate rejection counts (pool 1)",
              pool_1_stats["rejections"] == expected_rejections,
              f"got {pool_1_stats['rejections']}")
        check("unparseable line counted (pool 1)", pool_1_stats[UNPARSEABLE_BUCKET] == 1)
        check("pool 1 streamed/admitted", pool_1_stats["streamed"] == 12 and pool_1_stats["admitted"] == 3)
        check("pool 2 fully admitted", manifest["pools"][1]["admitted"] == 2)
        check("pool 3 draft gates (contract edges + description pass; no-text rejected)",
              manifest["pools"][2]["admitted"] == 1
              and manifest["pools"][2]["rejections"]["has_text"] == 1)
        check("manifest math adds up (admitted + rejected == streamed)", verify_manifest_math(manifest))

        # 2) lossless + boundary stamps on the admitted rows ---------------------------------------------
        out_rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
        expected_ids = ["prim-minted-good000000000001", "prim-minted-good000000000002",
                        "prim-minted-good000000000003", "codefactory-tinygood00000001",
                        "codefactory-tinygood00000002", "prim:candidate:tiny:draft-good"]
        check("admission order + ids never re-minted",
              [row["primitive_id"] for row in out_rows] == expected_ids,
              f"got {[row['primitive_id'] for row in out_rows]}")
        first = out_rows[0]
        check("original custom field survives (lossless)", first.get("custom_marker") == "survives_losslessly")
        check("conflicting original record_type preserved under original_record_type",
              first.get(ORIGINAL_FIELD_PRESERVE_PREFIX + "record_type") == "tiny_minted_candidate")
        check("candidate/truth boundary stamped on every row",
              all(row["candidate"] is True and row["serves_truth"] is False
                  and row["record_type"] == SEARCHABLE_STAGED_RECORD_TYPE for row in out_rows))
        check("pool provenance stamped",
              [row[STAGED_ROW_POOL_PROVENANCE_KEY] for row in out_rows]
              == ["tiny_minted"] * 3 + ["tiny_producers"] * 2 + ["tiny_drafts"])

        # 3) determinism: assemble twice -> byte-identical pool + manifest -------------------------------
        pool_bytes_first = out_path.read_bytes()
        manifest_path = default_manifest_path(out_path)
        manifest_bytes_first = manifest_path.read_bytes()
        assemble(target=None, pools=tmp_pools, output_path=out_path)  # type: ignore[arg-type]
        check("determinism: pool byte-identical on re-run", out_path.read_bytes() == pool_bytes_first)
        check("determinism: manifest byte-identical on re-run",
              manifest_path.read_bytes() == manifest_bytes_first)

        # 4) target-stop honored --------------------------------------------------------------------------
        stop_out = tmp_dir / "out" / "stopped_pool.jsonl"
        base_distinct = manifest["searchable_base"]["distinct_ids"]
        stop_manifest = assemble(target=base_distinct + 2, pools=tmp_pools, output_path=stop_out)
        stop_rows = stop_out.read_text(encoding="utf-8").splitlines()
        check("target-stop honored (exactly the needed rows admitted)",
              stop_manifest["admitted_total"] == 2 and len(stop_rows) == 2
              and stop_manifest["stopped_at_target"] is True and stop_manifest["target_reached"] is True)
        check("pools after the stop stay unstreamed",
              stop_manifest["pools"][1]["streamed"] == 0 and stop_manifest["pools"][2]["streamed"] == 0)
        check("manifest math holds under target-stop", verify_manifest_math(stop_manifest))

        # 5) plan() arithmetic matches the assemble behavior --------------------------------------------
        plan_report = plan(target=base_distinct + 2, pools=tmp_pools)
        check("plan projection matches target-stop assemble",
              plan_report["projected_admitted_at_stop"] == 2 and plan_report["target_reachable"] is True
              and plan_report["projection"][0]["projected_admitted_at_stop"] == 2)
        unreachable = plan(target=10_000, pools=tmp_pools)
        check("plan reports honest shortfall when pools cannot reach the target",
              unreachable["target_reachable"] is False
              and unreachable["shortfall"] == 10_000 - base_distinct - manifest["admitted_total"])

        # 6) read-only boundary: base pool untouched + write-guard refuses pool paths -------------------
        check("searchable base file byte-identical after all assembles",
              base_path.read_bytes() == base_bytes_before)
        guard_fired = False
        try:
            assemble(target=None, pools=tmp_pools, output_path=base_path)  # type: ignore[arg-type]
        except ValueError:
            guard_fired = True
        check("write-guard refuses to write over a pool file", guard_fired)

        # 7) content hash in the manifest matches the written bytes -------------------------------------
        recomputed = hashlib.sha256(pool_bytes_first).hexdigest()
        check("manifest sha256 matches pool file bytes", manifest["output"]["sha256"] == recomputed)

    # --- real registry sanity (read-only existence; no real rows are read in the self-test) ------------
    real_members = [(member, path) for pool in POOLS for member, path in pool["members"]]
    check("real POOLS registry paths exist on disk",
          all(Path(path).is_file() for _member, path in real_members),
          f"missing: {[member for member, path in real_members if not Path(path).is_file()]}")

    if failures:
        print(f"\nFAIL - primitive_scale_plan: {len(failures)} check(s) failed: {failures}")
        return 1
    print(f"\nPASS - primitive_scale_plan: {len(ADMISSION_GATE_ORDER)} named admission gates "
          f"({', '.join(ADMISSION_GATE_ORDER)}) proven on hermetic tmp pools — exact per-gate rejection "
          "counts, lossless stamped rows (candidate=true serves_truth=false, ids never re-minted), "
          "byte-identical determinism, read-only pool boundary + write-guard, target-stop, and "
          "manifest math (admitted + rejected == streamed). serves_truth=false.")
    return 0


# ---------------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------------

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--self-test", action="store_true", help="hermetic proof on synthetic tmp pools")
    parser.add_argument("--plan", action="store_true",
                        help="print the computed pool ledger + the arithmetic to target (nothing written)")
    parser.add_argument("--assemble", action="store_true",
                        help="build the searchable-staged extension pool + manifest")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_SEARCHABLE_TOTAL,
                        help="searchable total to reach (base + admitted staged rows)")
    parser.add_argument("--output", default=None, help="override the output pool path")
    parser.add_argument("--manifest", default=None, help="override the manifest path")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.plan:
        _print_plan(plan(target=args.target))
        return 0
    if args.assemble:
        manifest = assemble(target=args.target, output_path=args.output, manifest_path=args.manifest)
        print(json.dumps({key: manifest[key] for key in
                          ("target", "admitted_total", "projected_searchable_total", "target_reached",
                           "output")}, indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
