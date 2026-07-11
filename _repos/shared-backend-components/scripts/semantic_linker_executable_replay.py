#!/usr/bin/env python3
"""Proof-bound executable replay of the five receipt-backed recipes.

This is an offline execution benchmark, not a token-savings result.  For each
current deterministic recipe it exercises the real chain:

    trusted recipe search
      -> semantic linker resolve + link_and_assemble
      -> current content-valid receipt lookup
      -> content-addressed implementation lock
      -> safe isolated exact-file materialization
      -> the registered project's existing hidden oracle

Four lanes are persisted in an immutable, resumable JSONL ledger:

``baseline_full_source``
    The registered full reference project is materialized and executed.
``receipt_locked_linker``
    Search, linker, receipt, lock, and exact recipe artifact must all agree
    before the hidden oracle is allowed to count as a passing replay.
``missing_control``
    A deliberately absent capability must remain a linker residual; an
    isolated known-bad artifact is executed only as a negative oracle probe.
``mutated_control``
    Search/link/receipt succeed, then a post-lock artifact mutation must be
    detected and the isolated negative oracle probe must fail.

Repeats are deterministic fixture re-executions.  The report applies the
repository's ``REPORTING_MIN_N`` mechanical cell gate and matched baseline /
linker pairing, but explicitly claims no statistical independence.  There is
no model call and therefore no input/output/total token number.  Every report
is ``candidate=true``, ``serves_truth=false``, ``reportable=false``, and
``headline_eligible=false``.

    PYTHONPATH=. python3 scripts/semantic_linker_executable_replay.py --run
    PYTHONPATH=. python3 scripts/semantic_linker_executable_replay.py --report
    PYTHONPATH=. python3 scripts/semantic_linker_executable_replay.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next(
    (q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
    _here_boot.parents[1],
)
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import contextlib  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
from collections import Counter  # noqa: E402
from pathlib import PurePosixPath  # noqa: E402
from typing import Any, Iterator, Mapping, Sequence  # noqa: E402

from scripts import primitive_search_federation as _search  # noqa: E402
from scripts import semantic_linker_assemble as _assemble  # noqa: E402
from scripts import verified_recipe_receipt_store as _receipts  # noqa: E402
from scripts.reuse_experiment_policy import REPORTING_MIN_N  # noqa: E402


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "semantic-linker-executable-replay/v1"
LOCK_SCHEMA_VERSION = "semantic-linker-recipe-lock/v1"
BENCHMARK_KIND = "offline_receipt_locked_executable_replay"
DEFAULT_LEDGER = Path(resource("data/dev-intel/semantic_linker_executable_replay/runs.jsonl"))
DEFAULT_RECEIPT_DB = _receipts.DEFAULT_DB_PATH
DEFAULT_RECIPE_CARDS = _receipts.DEFAULT_CARD_PATH
REPEAT_DESIGN = "deterministic_fixture_reexecution_pseudo_replication"
STATISTICAL_INDEPENDENCE_CLAIMED = False
TOKEN_ACCOUNTING = "unavailable_no_model_calls"

LANE_BASELINE = "baseline_full_source"
LANE_LINKER = "receipt_locked_linker"
LANE_MISSING = "missing_control"
LANE_MUTATED = "mutated_control"
LANES = (LANE_BASELINE, LANE_LINKER, LANE_MISSING, LANE_MUTATED)


class ReplayIntegrityError(RuntimeError):
    """Raised when a replay artifact, receipt, lock, or ledger is inconsistent."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _source_digest(obj: Any) -> str:
    return _digest(inspect.getsource(obj).encode("utf-8"))


def _file_manifest(files: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "path": name,
            "bytes": len(source.encode("utf-8")),
            "sha256": _digest(source.encode("utf-8")),
        }
        for name, source in sorted(files.items())
    ]


def _artifact_digest(files: Mapping[str, str]) -> str:
    return _digest(_file_manifest(files))


def _safe_relative_path(raw: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise ReplayIntegrityError(f"unsafe materialization path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ReplayIntegrityError(f"unsafe materialization path: {raw!r}")
    return path


@contextlib.contextmanager
def _isolated_materialization(files: Mapping[str, str]) -> Iterator[tuple[Path, dict[str, str]]]:
    """Write exact files into a new non-symlink workspace and verify byte-for-byte readback."""
    with tempfile.TemporaryDirectory(prefix="semantic-linker-replay-") as temp:
        root = Path(temp).resolve()
        for name, source in sorted(files.items()):
            relative = _safe_relative_path(name)
            target = root.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                raise ReplayIntegrityError(f"materialization target already exists: {name}")
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                payload = source.encode("utf-8")
                with os.fdopen(descriptor, "wb", closefd=False) as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                os.close(descriptor)
        readback: dict[str, str] = {}
        for name in sorted(files):
            relative = _safe_relative_path(name)
            target = root.joinpath(*relative.parts)
            if target.is_symlink() or not target.is_file() or root not in target.resolve().parents:
                raise ReplayIntegrityError(f"unsafe materialized file: {name}")
            readback[name] = target.read_text(encoding="utf-8")
        if readback != dict(files):
            raise ReplayIntegrityError("isolated materialization did not round-trip exact source bytes")
        yield root, readback


def _recipe_query(material: Mapping[str, Any]) -> str:
    return str(material["step"]).replace("_", " ")


def _recipe_plan(material: Mapping[str, Any], query: str) -> dict[str, Any]:
    return {
        "name": f"receipt-replay/{material['step']}",
        "steps": [
            {
                "var": "project",
                "capability": query.replace(" ", "."),
                "in": ["declared_config"],
            }
        ],
        "policy": {},
    }


def _search_and_link(
    material: Mapping[str, Any],
    *,
    searcher: _search.PrimitiveSearchFederation,
    query: str | None = None,
) -> dict[str, Any]:
    """Use the actual trusted-recipe search as the linker's retrieval seam."""
    effective_query = query or _recipe_query(material)
    initial = searcher.search_trusted_recipes(effective_query, limit=10)
    cards = list(initial.get("results") or [])

    def retriever(capability_query: str, k: int) -> list[dict[str, Any]]:
        response = searcher.search_trusted_recipes(capability_query, limit=k)
        return [
            {
                "primitive_id": row["primitive_id"],
                "score": row.get("score", 0.0),
                "family": "verified_recipe",
            }
            for row in response.get("results") or []
        ]

    assembly = _assemble.link_and_assemble(
        _recipe_plan(material, effective_query),
        cards=cards,
        retriever=retriever,
    )
    return {"query": effective_query, "search": initial, "cards": cards, "assembly": assembly}


def _receipt_for_lock(
    primitive_id: str,
    *,
    db_path: Path,
) -> dict[str, Any]:
    current = _receipts.trusted_receipts_for([primitive_id], db_path=db_path)
    if len(current) != 1:
        raise ReplayIntegrityError(f"expected one current trusted receipt for {primitive_id}, found {len(current)}")
    return current[0]


def _make_content_lock(
    material: Mapping[str, Any],
    assembly: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    primitive_id = str(material["card"]["primitive_id"])
    if set((assembly.get("lock") or {}).values()) != {primitive_id}:
        raise ReplayIntegrityError(f"assembly did not lock exactly {primitive_id}")
    if assembly.get("n_residual") != 0 or not assembly.get("deterministic_composition"):
        raise ReplayIntegrityError(f"assembly for {primitive_id} was not deterministic and complete")
    exact_files = material["exact_files"]
    artifact_digest = _artifact_digest(exact_files)
    if receipt.get("artifact_digest") != artifact_digest or material.get("artifact_digest") != artifact_digest:
        raise ReplayIntegrityError(f"receipt/current artifact disagreement for {primitive_id}")
    payload = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "primitive_id": primitive_id,
        "assembly_lock": dict(assembly.get("lock") or {}),
        "assembly_artifact_digest": _digest(str(assembly.get("artifact") or "")),
        "receipt_id": receipt["receipt_id"],
        "receipt_digest": receipt["receipt_digest"],
        "identity_digest": receipt["identity_digest"],
        "declaration_digest": receipt["declaration_digest"],
        "contract_digest": receipt["contract_digest"],
        "artifact_digest": artifact_digest,
        "oracle_digest": receipt["oracle_digest"],
        "protocol_digest": receipt["protocol_digest"],
        "artifact_files": _file_manifest(exact_files),
        **BOUNDARY,
    }
    lock_digest = _digest(payload)
    return {
        **payload,
        "lock_digest": lock_digest,
        "lock_id": "lock/" + lock_digest.removeprefix("sha256:"),
    }


def _validate_content_lock(
    lock: Mapping[str, Any],
    files: Mapping[str, str],
    receipt: Mapping[str, Any],
) -> bool:
    core = {key: value for key, value in lock.items() if key not in {"lock_digest", "lock_id"}}
    digest = _digest(core)
    return bool(
        lock.get("lock_digest") == digest
        and lock.get("lock_id") == "lock/" + digest.removeprefix("sha256:")
        and lock.get("artifact_digest") == _artifact_digest(files)
        and lock.get("artifact_files") == _file_manifest(files)
        and lock.get("receipt_id") == receipt.get("receipt_id")
        and lock.get("receipt_digest") == receipt.get("receipt_digest")
        and receipt.get("artifact_digest") == _artifact_digest(files)
        and receipt.get("oracle_pass") is True
        and receipt.get("revoked_at") is None
    )


def _run_existing_oracle(
    material: Mapping[str, Any],
    files: Mapping[str, str],
    *,
    lane: str,
) -> dict[str, Any]:
    """Safe readback followed by the registered buildout's existing hidden oracle."""
    with _isolated_materialization(files) as (_workspace, readback):
        runner = material["runner"]
        result = runner(material["spec"]["genome"], readback, lane=lane)
    return result


def _first_mounted_path(material: Mapping[str, Any]) -> str:
    mounted = sorted(name for name in material["exact_files"] if name != material["entry"])
    if not mounted:
        raise ReplayIntegrityError(f"{material['step']}: recipe has no mounted non-entry primitive")
    return mounted[0]


def _missing_files(material: Mapping[str, Any]) -> tuple[dict[str, str], str]:
    """Exact receipt-backed artifact with one load-bearing mounted primitive removed."""
    affected = _first_mounted_path(material)
    files = dict(material["exact_files"])
    del files[affected]
    return files, affected


def _mutated_files(material: Mapping[str, Any]) -> tuple[dict[str, str], str]:
    """Exact receipt-backed artifact with one mounted primitive replaced post-lock."""
    mutated = dict(material["exact_files"])
    affected = _first_mounted_path(material)
    mutated[affected] = (
        "# deterministic post-lock mutation control; never an authorized primitive\n"
        "raise RuntimeError('mutated mounted primitive')\n"
    )
    return mutated, affected


PROTOCOL_DIGEST = ""


def _run_key(
    *,
    primitive_id: str,
    receipt_digest: str,
    lane: str,
    repeat: int,
) -> str:
    return _digest(
        {
            "protocol_digest": PROTOCOL_DIGEST,
            "primitive_id": primitive_id,
            "receipt_digest": receipt_digest,
            "lane": lane,
            "repeat": repeat,
        }
    )


def _execute_lane(
    material: Mapping[str, Any],
    lane: str,
    repeat: int,
    *,
    searcher: _search.PrimitiveSearchFederation,
    receipt_db: Path,
) -> dict[str, Any]:
    primitive_id = str(material["card"]["primitive_id"])
    current_receipt = _receipt_for_lock(primitive_id, db_path=receipt_db)
    search_count = 0
    selected_id: str | None = None
    assembly: dict[str, Any] | None = None
    content_lock: dict[str, Any] | None = None
    receipt_validated = False
    artifact_matches_lock: bool | None = None
    expected_pass = lane in {LANE_BASELINE, LANE_LINKER}
    control_blocker: str | None = None
    control_action: str | None = None
    control_affected_path: str | None = None
    control_original_file_digest: str | None = None

    if lane == LANE_BASELINE:
        files = dict(material["genome"]["good"])
    elif lane == LANE_MISSING:
        # One opaque token avoids accidentally matching ordinary words such as
        # "missing", "primitive", or "capability" in a real recipe card.
        missing_query = "zzqv" + hashlib.sha256(primitive_id.encode("utf-8")).hexdigest()[:24]
        linked = _search_and_link(material, searcher=searcher, query=missing_query)
        search_count = int(linked["search"].get("count") or 0)
        assembly = linked["assembly"]
        if search_count != 0 or assembly.get("n_residual") != 1 or assembly.get("assembly_valid"):
            raise ReplayIntegrityError(f"missing control unexpectedly resolved for {primitive_id}")
        control_blocker = "missing_capability_residual"
        files, control_affected_path = _missing_files(material)
        control_action = "removed_mounted_non_entry_primitive"
        control_original_file_digest = _digest(
            material["exact_files"][control_affected_path].encode("utf-8")
        )
        artifact_matches_lock = _artifact_digest(files) == current_receipt["artifact_digest"]
        if artifact_matches_lock:
            raise ReplayIntegrityError(f"removed mounted primitive did not change {primitive_id} artifact")
    else:
        linked = _search_and_link(material, searcher=searcher)
        search_count = int(linked["search"].get("count") or 0)
        assembly = linked["assembly"]
        selected = [
            row for row in linked["search"].get("results") or []
            if row.get("primitive_id") == primitive_id
        ]
        if not selected:
            raise ReplayIntegrityError(f"trusted search did not return expected recipe {primitive_id}")
        selected_id = primitive_id
        locked_ids = set((assembly.get("lock") or {}).values())
        if locked_ids != {primitive_id}:
            raise ReplayIntegrityError(f"linker selected {sorted(locked_ids)}, expected {primitive_id}")
        current_receipt = _receipt_for_lock(primitive_id, db_path=receipt_db)
        receipt_validated = True
        content_lock = _make_content_lock(material, assembly, current_receipt)
        if lane == LANE_LINKER:
            files = dict(material["exact_files"])
            artifact_matches_lock = _validate_content_lock(content_lock, files, current_receipt)
            if not artifact_matches_lock:
                raise ReplayIntegrityError(f"exact linker artifact failed content lock for {primitive_id}")
            # Revalidate immediately before materialization; stale/revoked evidence fails closed.
            revalidated = _receipt_for_lock(primitive_id, db_path=receipt_db)
            if revalidated["receipt_digest"] != current_receipt["receipt_digest"]:
                raise ReplayIntegrityError(f"receipt changed before materialization for {primitive_id}")
        elif lane == LANE_MUTATED:
            files, control_affected_path = _mutated_files(material)
            artifact_matches_lock = _validate_content_lock(content_lock, files, current_receipt)
            if artifact_matches_lock:
                raise ReplayIntegrityError(f"post-lock mutation was not detected for {primitive_id}")
            control_blocker = "post_lock_artifact_digest_mismatch"
            control_action = "replaced_mounted_non_entry_primitive"
            control_original_file_digest = _digest(
                material["exact_files"][control_affected_path].encode("utf-8")
            )
        else:
            raise ValueError(f"unknown replay lane: {lane}")

    oracle = _run_existing_oracle(material, files, lane=lane)
    oracle_pass = bool(oracle.get("oracle_pass"))
    checks = dict(oracle.get("oracle_checks") or {})
    if expected_pass and not oracle_pass:
        raise ReplayIntegrityError(f"{lane} unexpectedly failed {primitive_id}: {oracle}")
    if not expected_pass and oracle_pass:
        raise ReplayIntegrityError(f"{lane} unexpectedly passed {primitive_id}: {oracle}")
    outcome_as_expected = oracle_pass is expected_pass
    row: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_linker_executable_replay_run",
        "benchmark_kind": BENCHMARK_KIND,
        "protocol_digest": PROTOCOL_DIGEST,
        "run_key": _run_key(
            primitive_id=primitive_id,
            receipt_digest=str(current_receipt["receipt_digest"]),
            lane=lane,
            repeat=repeat,
        ),
        "primitive_id": primitive_id,
        "step": material["step"],
        "genome": material["spec"]["genome"],
        "lane": lane,
        "repeat": repeat,
        "search_count": search_count,
        "search_selected_primitive_id": selected_id,
        "linker_lock": dict(assembly.get("lock") or {}) if assembly else {},
        "linker_n_residual": int(assembly.get("n_residual") or 0) if assembly else None,
        "linker_n_adapters": int(assembly.get("n_adapters") or 0) if assembly else None,
        "linker_deterministic_composition": (
            bool(assembly.get("deterministic_composition")) if assembly else None
        ),
        "assembly_artifact_digest": _digest(str(assembly.get("artifact") or "")) if assembly else None,
        "receipt_validated": receipt_validated,
        "receipt_id": current_receipt["receipt_id"] if receipt_validated else None,
        "receipt_digest": current_receipt["receipt_digest"] if receipt_validated else None,
        "content_lock_id": content_lock.get("lock_id") if content_lock else None,
        "content_lock_digest": content_lock.get("lock_digest") if content_lock else None,
        "artifact_digest": _artifact_digest(files),
        "artifact_matches_lock": artifact_matches_lock,
        "materialized_files": sorted(files),
        "materialization": "validated_non_symlink_temp_then_registered_hidden_oracle",
        "control_blocker": control_blocker,
        "control_action": control_action,
        "control_affected_path": control_affected_path,
        "control_original_file_digest": control_original_file_digest,
        "reference_receipt_artifact_digest": current_receipt["artifact_digest"],
        "oracle_pass": oracle_pass,
        "oracle_checks": checks,
        "oracle_checks_passed": sum(value is True for value in checks.values()),
        "oracle_checks_total": len(checks),
        "oracle_behavior_digest": _digest(checks),
        "expected_pass": expected_pass,
        "outcome_as_expected": outcome_as_expected,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "token_accounting": TOKEN_ACCOUNTING,
        "model_calls": 0,
        "simulation": False,
        "executed_hidden_oracle": True,
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "reportable": False,
        "headline_eligible": False,
        "evidence_note": (
            "Real trusted search/link/receipt/lock/materialization/hidden-oracle replay; no model calls, so token "
            "usage and token savings are unavailable. Repeats are deterministic non-independent executions."
        ),
        **BOUNDARY,
    }
    row["row_digest"] = _digest({key: value for key, value in row.items() if key != "row_digest"})
    return row


def _validate_row(row: Mapping[str, Any]) -> None:
    if row.get("schema_version") != SCHEMA_VERSION:
        raise ReplayIntegrityError("ledger row schema mismatch")
    expected = _digest({key: value for key, value in row.items() if key != "row_digest"})
    if row.get("row_digest") != expected:
        raise ReplayIntegrityError(f"ledger row digest mismatch for {row.get('run_key')}")
    if row.get("candidate") is not True or row.get("serves_truth") is not False:
        raise ReplayIntegrityError("ledger row boundary mismatch")
    if row.get("input_tokens") is not None or row.get("output_tokens") is not None or row.get("total_tokens") is not None:
        raise ReplayIntegrityError("offline replay must not fabricate model token counts")


def _load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    keys: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReplayIntegrityError(f"invalid ledger JSON at line {line_number}") from exc
            if not isinstance(row, dict):
                raise ReplayIntegrityError(f"non-object ledger row at line {line_number}")
            _validate_row(row)
            run_key = str(row.get("run_key") or "")
            if not run_key or run_key in keys:
                raise ReplayIntegrityError(f"missing or duplicate run key at line {line_number}")
            keys.add(run_key)
            rows.append(row)
    return rows


@contextlib.contextmanager
def _ledger_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _append_row(path: Path, row: Mapping[str, Any]) -> bool:
    _validate_row(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _ledger_lock(path):
        existing = {item["run_key"]: item for item in _load_ledger(path)}
        prior = existing.get(row["run_key"])
        if prior is not None:
            if prior != dict(row):
                raise ReplayIntegrityError(f"immutable run key collision: {row['run_key']}")
            return False
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(dict(row)) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return True


def run_replay(
    *,
    ledger: Path | str = DEFAULT_LEDGER,
    receipt_db: Path | str = DEFAULT_RECEIPT_DB,
    recipe_cards: Path | str = DEFAULT_RECIPE_CARDS,
    repeats: int = REPORTING_MIN_N,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    ledger_path, db_path, cards_path = Path(ledger), Path(receipt_db), Path(recipe_cards)
    materials = _receipts._current_materials()
    if len(materials) != 5:
        raise ReplayIntegrityError(f"expected five current deterministic recipes, found {len(materials)}")
    searcher = _search.PrimitiveSearchFederation(
        recipe_receipt_db=db_path,
        recipe_cards_path=cards_path,
    )
    existing = _load_ledger(ledger_path)
    existing_keys = {row["run_key"] for row in existing}
    appended = skipped = 0
    for primitive_id, material in sorted(materials.items()):
        receipt = _receipt_for_lock(primitive_id, db_path=db_path)
        for repeat in range(repeats):
            for lane in LANES:
                key = _run_key(
                    primitive_id=primitive_id,
                    receipt_digest=str(receipt["receipt_digest"]),
                    lane=lane,
                    repeat=repeat,
                )
                if key in existing_keys:
                    skipped += 1
                    continue
                row = _execute_lane(
                    material,
                    lane,
                    repeat,
                    searcher=searcher,
                    receipt_db=db_path,
                )
                if _append_row(ledger_path, row):
                    appended += 1
                    existing_keys.add(key)
                else:
                    skipped += 1
    return {
        "record_type": "semantic_linker_executable_replay_progress",
        "protocol_digest": PROTOCOL_DIGEST,
        "recipes": len(materials),
        "lanes": len(LANES),
        "repeats": repeats,
        "expected_current_rows": len(materials) * len(LANES) * repeats,
        "appended": appended,
        "skipped": skipped,
        **BOUNDARY,
    }


def _lane_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    return {
        "n": n,
        "n_oracle_pass": sum(row.get("oracle_pass") is True for row in rows),
        "n_oracle_fail": sum(row.get("oracle_pass") is False for row in rows),
        "n_outcome_as_expected": sum(row.get("outcome_as_expected") is True for row in rows),
        "pass_rate": round(sum(row.get("oracle_pass") is True for row in rows) / n, 4) if n else None,
        "tokens_available": False,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
    }


def build_report(
    rows: Sequence[Mapping[str, Any]],
    *,
    ledger: str = "",
    repeats: int = REPORTING_MIN_N,
) -> dict[str, Any]:
    current = [row for row in rows if row.get("protocol_digest") == PROTOCOL_DIGEST]
    materials = _receipts._current_materials()
    required_cells = [
        (primitive_id, lane)
        for primitive_id in sorted(materials)
        for lane in LANES
    ]
    counts = Counter((str(row["primitive_id"]), str(row["lane"])) for row in current)
    exact_cells = {
        f"{primitive_id}|{lane}": _lane_summary(
            [row for row in current if row["primitive_id"] == primitive_id and row["lane"] == lane]
        )
        for primitive_id, lane in required_cells
    }
    mechanical_min_n_gate = bool(required_cells) and all(
        counts[cell] >= REPORTING_MIN_N for cell in required_cells
    )

    by_lane = {
        lane: _lane_summary([row for row in current if row["lane"] == lane])
        for lane in LANES
    }
    keyed: dict[tuple[str, int, str], Mapping[str, Any]] = {
        (str(row["primitive_id"]), int(row["repeat"]), str(row["lane"])): row
        for row in current
    }
    paired: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for primitive_id in sorted(materials):
        for repeat in range(repeats):
            baseline = keyed.get((primitive_id, repeat, LANE_BASELINE))
            linker = keyed.get((primitive_id, repeat, LANE_LINKER))
            if baseline is not None and linker is not None:
                paired.append((baseline, linker))
    both_pass = [pair for pair in paired if pair[0]["oracle_pass"] is True and pair[1]["oracle_pass"] is True]
    pair_counts = Counter(str(baseline["primitive_id"]) for baseline, _linker in both_pass)
    paired_min_n_gate = bool(materials) and all(
        pair_counts[primitive_id] >= REPORTING_MIN_N for primitive_id in materials
    )
    behavior_matches = sum(
        baseline.get("oracle_behavior_digest") == linker.get("oracle_behavior_digest")
        for baseline, linker in both_pass
    )
    missing_ok = all(
        row.get("oracle_pass") is False
        and row.get("control_blocker") == "missing_capability_residual"
        and row.get("linker_n_residual") == 1
        and row.get("artifact_matches_lock") is False
        and row.get("control_action") == "removed_mounted_non_entry_primitive"
        and bool(row.get("control_affected_path"))
        for row in current if row.get("lane") == LANE_MISSING
    ) and any(row.get("lane") == LANE_MISSING for row in current)
    mutated_ok = all(
        row.get("oracle_pass") is False
        and row.get("control_blocker") == "post_lock_artifact_digest_mismatch"
        and row.get("artifact_matches_lock") is False
        and row.get("control_action") == "replaced_mounted_non_entry_primitive"
        and bool(row.get("control_affected_path"))
        for row in current if row.get("lane") == LANE_MUTATED
    ) and any(row.get("lane") == LANE_MUTATED for row in current)
    return {
        "record_type": "semantic_linker_executable_replay_report",
        "benchmark_kind": BENCHMARK_KIND,
        "protocol_digest": PROTOCOL_DIGEST,
        "ledger": ledger,
        "n_rows": len(current),
        "n_recipes": len(materials),
        "n_lanes": len(LANES),
        "requested_repeats": repeats,
        "reporting_min_n": REPORTING_MIN_N,
        "mechanical_min_n_gate_met": mechanical_min_n_gate,
        "underfilled_exact_cells": [
            f"{primitive_id}|{lane}"
            for primitive_id, lane in required_cells
            if counts[(primitive_id, lane)] < REPORTING_MIN_N
        ],
        "exact_recipe_lane_cells": exact_cells,
        "by_lane": by_lane,
        "paired_baseline_linker": {
            "n_pairs": len(paired),
            "n_both_pass": len(both_pass),
            "n_both_pass_behavior_match": behavior_matches,
            "both_pass_by_recipe": dict(sorted(pair_counts.items())),
            "mechanical_both_pass_min_n_gate_met": paired_min_n_gate,
            "tokens_available": False,
            "token_savings": None,
            "comparison_rule": "matched primitive_id + repeat; both-pass only",
        },
        "negative_controls": {
            "missing_control_passes_gate": missing_ok,
            "mutated_control_passes_gate": mutated_ok,
        },
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "tokens_available": False,
        "token_accounting": TOKEN_ACCOUNTING,
        "reportable": False,
        "headline_eligible": False,
        "reportability_reason": (
            "real hidden-oracle replay with deterministic non-independent repeats and no model/provider token "
            "usage; MIN_N gates are mechanical integrity checks only"
        ),
        **BOUNDARY,
    }


def report_from_ledger(path: Path | str = DEFAULT_LEDGER, *, repeats: int = REPORTING_MIN_N) -> dict[str, Any]:
    ledger = Path(path)
    return build_report(_load_ledger(ledger), ledger=str(ledger), repeats=repeats)


def _protocol_payload() -> dict[str, Any]:
    materials = _receipts._current_materials()
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark_kind": BENCHMARK_KIND,
        "lanes": LANES,
        "reporting_min_n": REPORTING_MIN_N,
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "token_accounting": TOKEN_ACCOUNTING,
        "recipe_inputs": {
            primitive_id: {
                "identity_digest": material["identity_digest"],
                "declaration_digest": material["declaration_digest"],
                "contract_digest": material["contract_digest"],
                "artifact_digest": material["artifact_digest"],
                "oracle_digest": material["oracle_digest"],
                "protocol_digest": material["protocol_digest"],
            }
            for primitive_id, material in sorted(materials.items())
        },
        "implementation_digests": {
            function.__name__: _source_digest(function)
            for function in (
                _isolated_materialization,
                _search_and_link,
                _make_content_lock,
                _validate_content_lock,
                _run_existing_oracle,
                _execute_lane,
                _validate_row,
            )
        },
    }


PROTOCOL_DIGEST = _digest(_protocol_payload())


def self_test() -> bool:
    with tempfile.TemporaryDirectory(prefix="semantic-linker-executable-replay-test-") as temp:
        root = Path(temp)
        receipt_db = root / "receipts.sqlite3"
        cards = root / "recipe_cards.jsonl"
        ledger = root / "runs.jsonl"

        receipt_run = _receipts.run_and_store(db_path=receipt_db, cards_path=cards)
        assert receipt_run["oracle_pass_receipts"] == 5, receipt_run
        # One real execution per recipe/lane keeps the hermetic gate bounded:
        # missing/replaced modules intentionally make each HTTP oracle exhaust
        # its boot probe.  The production default remains MIN_N=8, and this
        # underfilled self-test verifies that the report refuses reportability.
        self_test_repeats = 1
        progress = run_replay(
            ledger=ledger,
            receipt_db=receipt_db,
            recipe_cards=cards,
            repeats=self_test_repeats,
        )
        expected = 5 * len(LANES) * self_test_repeats
        assert progress["appended"] == expected, progress
        rows = _load_ledger(ledger)
        assert len(rows) == expected
        for row in rows:
            assert row["input_tokens"] is row["output_tokens"] is row["total_tokens"] is None
            if row["lane"] in {LANE_BASELINE, LANE_LINKER}:
                assert row["oracle_pass"] is True and row["outcome_as_expected"] is True, row
            else:
                assert row["oracle_pass"] is False and row["outcome_as_expected"] is True, row
        report = build_report(rows, ledger=str(ledger), repeats=self_test_repeats)
        assert REPORTING_MIN_N == 8
        assert report["mechanical_min_n_gate_met"] is False, report
        assert len(report["underfilled_exact_cells"]) == 5 * len(LANES), report
        assert report["paired_baseline_linker"]["mechanical_both_pass_min_n_gate_met"] is False, report
        assert report["paired_baseline_linker"]["n_both_pass"] == 5, report
        assert report["negative_controls"]["missing_control_passes_gate"] is True, report
        assert report["negative_controls"]["mutated_control_passes_gate"] is True, report
        assert report["tokens_available"] is False
        assert report["reportable"] is False and report["headline_eligible"] is False
        assert report["statistical_independence_claimed"] is False

        before = ledger.read_bytes()
        resumed = run_replay(
            ledger=ledger,
            receipt_db=receipt_db,
            recipe_cards=cards,
            repeats=self_test_repeats,
        )
        assert resumed["appended"] == 0 and resumed["skipped"] == expected, resumed
        assert ledger.read_bytes() == before

        # Materialization path traversal and ledger tampering both fail closed.
        try:
            with _isolated_materialization({"../escape.py": "pass\n"}):
                pass
        except ReplayIntegrityError:
            pass
        else:
            raise AssertionError("path traversal unexpectedly materialized")
        tampered = root / "tampered.jsonl"
        first = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
        first["oracle_pass"] = not first["oracle_pass"]
        tampered.write_text(_canonical(first) + "\n", encoding="utf-8")
        try:
            _load_ledger(tampered)
        except ReplayIntegrityError:
            pass
        else:
            raise AssertionError("tampered immutable ledger row unexpectedly validated")

        print(
            "OK semantic_linker_executable_replay self-test: 5 receipt-backed recipes x 4 lanes x "
            f"{self_test_repeats} bounded real execution = {expected} immutable rows; trusted search -> linker -> "
            "current receipt -> content lock -> isolated exact files -> real hidden oracle passed for baseline/linker; "
            "removing/replacing a mounted non-entry primitive failed all controls; resume idempotent; no token "
            "numbers fabricated; underfilled MIN_N correctly refuses reporting; production default remains 8; "
            "non-independent, reportable=false, headline=false, serves_truth=false"
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Executable receipt-locked semantic-linker replay.")
    parser.add_argument("--run", action="store_true", help="execute missing replay cells, then print the report")
    parser.add_argument("--report", action="store_true", help="validate the ledger and print a report without running")
    parser.add_argument("--self-test", action="store_true", help="run hermetic temp-store/temp-ledger proof gates")
    parser.add_argument("--repeats", type=int, default=REPORTING_MIN_N)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--receipt-db", type=Path, default=DEFAULT_RECEIPT_DB)
    parser.add_argument("--recipe-cards", type=Path, default=DEFAULT_RECIPE_CARDS)
    args = parser.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.run:
        progress = run_replay(
            ledger=args.ledger,
            receipt_db=args.receipt_db,
            recipe_cards=args.recipe_cards,
            repeats=args.repeats,
        )
        report = report_from_ledger(args.ledger, repeats=args.repeats)
        print(json.dumps({"progress": progress, "report": report}, indent=2, sort_keys=True))
        return
    if args.report:
        print(json.dumps(report_from_ledger(args.ledger, repeats=args.repeats), indent=2, sort_keys=True))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
