#!/usr/bin/env python3
"""Governed recipe cards and executed receipts for deterministic composition.

This module promotes *evidence*, not truth labels.  It takes the five source
declarations in :mod:`scripts.multi_step_task_ab.COMPOSE_STEPS`, executes the
real ``deterministic_compose_run`` hidden-oracle harness, and records a trusted
receipt only for a recipe whose hidden oracle actually passed.

The two planes deliberately remain separate:

* ``source_declarations`` and ``recipe_cards.jsonl`` contain searchable names,
  descriptions, config, and source-declared target labels.  Those labels are
  discovery hints, never proof.
* ``recipe_receipts`` contains content-addressed executed evidence.  A receipt
  is returned by :func:`trusted_receipts_for` only after its own digest, current
  recipe identity, exact assembled artifact, hidden oracle, execution protocol,
  pass outcome, declaration link, and revocation state have all been checked.

Receipt evidence is immutable.  Revocation is an append-only row in a separate
table and is exposed as ``revoked_at`` through the read view/API; this preserves
the original evidence bytes while allowing a fail-closed kill switch.

Defaults (``--run`` is explicit; importing/running with no flag does no work)::

    python3 scripts/verified_recipe_receipt_store.py --run
    python3 scripts/verified_recipe_receipt_store.py --stats
    python3 scripts/verified_recipe_receipt_store.py --self-test

Everything remains ``candidate=true / serves_truth=false``.
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
import copy  # noqa: E402
import datetime as dt  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
from contextlib import contextmanager  # noqa: E402
from typing import Any, Iterable, Iterator, Mapping, Sequence  # noqa: E402


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "verified-recipe-receipt/v1"
CARD_SCHEMA_VERSION = "verified-recipe-card/v1"
PROTOCOL_VERSION = "deterministic-compose-hidden-oracle/v1"
DEFAULT_CARD_PATH = Path(resource("data/dev-intel/verified_recipe_receipts/recipe_cards.jsonl"))
DEFAULT_DB_PATH = Path(resource("dist/verified_recipe_receipts.sqlite3"))
DEFAULT_MANIFEST_PATH = Path(resource("dist/verified_recipe_receipts.manifest.json"))


class ReceiptRejected(ValueError):
    """Raised when evidence is not eligible for the trusted receipt store."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_manifest(files: Mapping[str, str]) -> list[dict[str, Any]]:
    result = []
    for name, source in sorted(files.items()):
        raw = source.encode("utf-8")
        result.append({"path": name, "bytes": len(raw), "sha256": _digest(raw)})
    return result


def _slug(value: str) -> str:
    return value.lower().replace("_", "-")


def _recipe_id(step: str) -> str:
    return f"recipe/{_slug(step)}"


def _source_digest(obj: Any) -> str:
    try:
        source = inspect.getsource(obj)
    except (OSError, TypeError):
        source = repr(obj)
    return _digest(source.encode("utf-8"))


def _current_materials() -> dict[str, dict[str, Any]]:
    """Reconstruct the exact current recipe/artifact/protocol without executing it."""
    import scripts.multi_step_task_ab as multi  # noqa: PLC0415
    import scripts.run_large_project_ab as large  # noqa: PLC0415

    registry = large._registry()
    materials: dict[str, dict[str, Any]] = {}
    for step, spec0 in multi.COMPOSE_STEPS.items():
        spec = copy.deepcopy(spec0)
        genome, runner = registry[spec["genome"]]
        entry = str(genome.get("solution_file", "app.py"))
        molecule_files = {name: source for name, source in genome["good"].items() if name != entry}
        app_source = multi.PrimitiveSessionManager().compose_entry(spec["template"], spec["config"])
        exact_files = {**molecule_files, entry: app_source}
        primitive_id = _recipe_id(step)

        # Source-declared labels are explicitly quarantined from executed proof.
        declaration = {
            "schema_version": CARD_SCHEMA_VERSION,
            "primitive_id": primitive_id,
            "source_module": "scripts.multi_step_task_ab",
            "source_key": step,
            "source_declared_labels": {
                "genome": spec["genome"],
                "template": spec["template"],
                "primitive_targets": list(genome.get("primitive_targets") or []),
                "product_family": genome.get("product_family"),
                "realism_level": genome.get("realism_level"),
            },
            "source_declared_labels_are_evidence": False,
            **BOUNDARY,
        }
        declaration_digest = _digest(declaration)

        identity = {
            "primitive_id": primitive_id,
            "source_module": "scripts.multi_step_task_ab",
            "source_key": step,
            "genome": spec["genome"],
            "template": spec["template"],
        }
        contract = {
            "primitive_id": primitive_id,
            "goal": genome.get("goal", ""),
            "template": spec["template"],
            "config": spec["config"],
            "entry_file": entry,
            "mounted_files": sorted(molecule_files),
            "output": "runnable project artifact accepted only after its hidden oracle passes",
            "effects": ["writes an ephemeral build workspace", "boots a local test process", "runs hidden probes"],
        }
        oracle_source = str(genome.get("http_oracle") or genome.get("oracle") or "")
        if not oracle_source:
            raise ReceiptRejected(f"{primitive_id}: registered genome has no hidden oracle source")
        protocol = {
            "protocol_version": PROTOCOL_VERSION,
            "compose_function": "scripts.multi_step_task_ab.deterministic_compose_run",
            "compose_function_digest": _source_digest(multi.deterministic_compose_run),
            "buildout_function": f"{runner.__module__}.{runner.__name__}",
            "buildout_function_digest": _source_digest(runner),
            "lane": "deterministic_compose",
            "model_tokens": 0,
        }
        file_manifest = _file_manifest(exact_files)
        artifact_digest = _digest(file_manifest)

        purpose = (
            f"Deterministically assemble the {step.replace('_', ' ')} recipe from the registered "
            f"{spec['template'].replace('_', ' ')} molecule and its declared configuration."
        )
        card_core = {
            "schema_version": CARD_SCHEMA_VERSION,
            "record_type": "verified_recipe_card",
            "primitive_id": primitive_id,
            "primitive_kind": "recipe",
            "title": step.replace("_", " ").title(),
            "descriptions": {
                "purpose": purpose,
                "use_when": (
                    f"Use when a workspace needs the {step.replace('_', ' ')} capability and the exact "
                    "registered runtime contract is compatible."
                ),
                "not_when": (
                    "Do not use when the target runtime, effects, or configuration differ; solve an adapter or "
                    "residual instead of treating semantic similarity as compatibility."
                ),
                "verification": (
                    "Execution eligibility requires an unrevoked content-valid hidden-oracle receipt; source "
                    "labels and this description do not authorize reuse."
                ),
            },
            "typed_edges": {
                "consumes": [
                    {"kind": "declared_config", "name": key, "value_type": type(value).__name__}
                    for key, value in sorted(spec["config"].items())
                ],
                "mounts": sorted(molecule_files),
                "produces": [{"kind": "project_entry", "path": entry}],
                "verified_by": "hidden_oracle_receipt",
            },
            "source_declaration": declaration,
            "governance": {
                "execution_evidence": "separate_receipt_store",
                "source_labels_are_proof": False,
                "revocation_checked_on_every_trusted_read": True,
            },
            "identity_digest": _digest(identity),
            "declaration_digest": declaration_digest,
            "contract_digest": _digest(contract),
            "artifact_digest": artifact_digest,
            "oracle_digest": _digest(oracle_source.encode("utf-8")),
            "protocol_digest": _digest(protocol),
            "artifact_files": file_manifest,
            "search_text": " ".join(
                [
                    step.replace("_", " "),
                    spec["template"].replace("_", " "),
                    str(genome.get("product_family") or ""),
                    str(genome.get("goal") or ""),
                    " ".join(str(x) for x in genome.get("primitive_targets") or []),
                    _canonical(spec["config"]),
                    " ".join(sorted(molecule_files)),
                ]
            ),
            **BOUNDARY,
        }
        card_digest = _digest(card_core)
        materials[primitive_id] = {
            "step": step,
            "spec": spec,
            "genome": genome,
            "runner": runner,
            "entry": entry,
            "exact_files": exact_files,
            "file_manifest": file_manifest,
            "declaration": declaration,
            "declaration_digest": declaration_digest,
            "identity_digest": card_core["identity_digest"],
            "contract_digest": card_core["contract_digest"],
            "artifact_digest": artifact_digest,
            "oracle_digest": card_core["oracle_digest"],
            "protocol_digest": card_core["protocol_digest"],
            "card": {**card_core, "card_digest": card_digest},
        }
    return materials


def _execute_current_recipes() -> list[dict[str, Any]]:
    """Execute the actual aggregate harness once and capture its raw hidden-oracle receipts."""
    import scripts.multi_step_task_ab as multi  # noqa: PLC0415
    import scripts.run_large_project_ab as large  # noqa: PLC0415

    materials = _current_materials()
    base_registry = large._registry()
    captured: dict[str, dict[str, Any]] = {}

    def instrumented_registry() -> dict[str, tuple[dict[str, Any], Any]]:
        result: dict[str, tuple[dict[str, Any], Any]] = {}
        for genome_id, (genome, runner) in base_registry.items():
            if genome_id not in {m["spec"]["genome"] for m in materials.values()}:
                result[genome_id] = (genome, runner)
                continue

            def wrapped(
                gid: str,
                files: dict[str, str],
                lane: str = "harness_alone",
                extra_files: dict[str, str] | None = None,
                *,
                _runner: Any = runner,
            ) -> dict[str, Any]:
                receipt = _runner(gid, files, lane=lane, extra_files=extra_files)
                captured[gid] = {
                    "receipt": copy.deepcopy(receipt),
                    "files": copy.deepcopy(files),
                    "extra_files": copy.deepcopy(extra_files or {}),
                }
                return receipt

            result[genome_id] = (genome, wrapped)
        return result

    original_registry = large._registry
    large._registry = instrumented_registry
    try:
        aggregate = multi.deterministic_compose_run()
    finally:
        large._registry = original_registry

    by_step = {str(row["step"]): row for row in aggregate.get("steps") or []}
    bundles: list[dict[str, Any]] = []
    for primitive_id, material in materials.items():
        step = material["step"]
        aggregate_row = by_step.get(step) or {}
        capture = captured.get(material["spec"]["genome"])
        if capture is None:
            raise ReceiptRejected(f"{primitive_id}: deterministic harness emitted no captured build receipt")
        raw_receipt = capture["receipt"]
        actual_files = {**capture["extra_files"], **capture["files"]}
        actual_manifest = _file_manifest(actual_files)
        actual_artifact_digest = _digest(actual_manifest)
        if actual_artifact_digest != material["artifact_digest"]:
            raise ReceiptRejected(f"{primitive_id}: independently reconstructed artifact does not match execution")

        # Failed executions are intentionally absent from the store and card stream.
        if aggregate_row.get("oracle_pass") is not True or raw_receipt.get("oracle_pass") is not True:
            continue
        checks = raw_receipt.get("oracle_checks") or {}
        if not checks or not all(value is True for value in checks.values()):
            raise ReceiptRejected(f"{primitive_id}: oracle_pass lacked an all-true named check set")
        if int(aggregate_row.get("model_tokens", -1)) != 0:
            raise ReceiptRejected(f"{primitive_id}: deterministic recipe unexpectedly consumed model tokens")

        outcome = {
            "oracle_pass": True,
            "oracle_checks": checks,
            "oracle_checks_passed": sum(value is True for value in checks.values()),
            "oracle_checks_total": len(checks),
            "benchmark_kind": raw_receipt.get("benchmark_kind"),
            "model_tokens": 0,
        }
        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "trusted_deterministic_recipe_receipt",
            "primitive_id": primitive_id,
            "identity_digest": material["identity_digest"],
            "declaration_digest": material["declaration_digest"],
            "contract_digest": material["contract_digest"],
            "artifact_digest": actual_artifact_digest,
            "oracle_digest": material["oracle_digest"],
            "protocol_digest": material["protocol_digest"],
            "outcome_digest": _digest(outcome),
            "artifact_files": actual_manifest,
            **outcome,
            **BOUNDARY,
        }
        receipt_digest = _digest(payload)
        receipt_id = "receipt/" + receipt_digest.removeprefix("sha256:")
        card_payload = {
            key: value for key, value in material["card"].items() if key != "card_digest"
        }
        card_payload["receipt_id"] = receipt_id
        card = {**card_payload, "card_digest": _digest(card_payload)}
        bundles.append(
            {
                "payload": payload,
                "payload_json": _canonical(payload),
                "receipt_digest": receipt_digest,
                "receipt_id": receipt_id,
                "declaration": material["declaration"],
                "declaration_json": _canonical(material["declaration"]),
                "card": card,
            }
        )
    return bundles


_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_declarations (
    declaration_digest TEXT PRIMARY KEY,
    primitive_id TEXT NOT NULL,
    declaration_json TEXT NOT NULL,
    inserted_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS recipe_receipts (
    receipt_id TEXT PRIMARY KEY,
    primitive_id TEXT NOT NULL,
    identity_digest TEXT NOT NULL,
    declaration_digest TEXT NOT NULL REFERENCES source_declarations(declaration_digest),
    contract_digest TEXT NOT NULL,
    artifact_digest TEXT NOT NULL,
    oracle_digest TEXT NOT NULL,
    protocol_digest TEXT NOT NULL,
    outcome_digest TEXT NOT NULL,
    oracle_pass INTEGER NOT NULL CHECK (oracle_pass = 1),
    oracle_checks_json TEXT NOT NULL,
    benchmark_kind TEXT NOT NULL,
    model_tokens INTEGER NOT NULL CHECK (model_tokens = 0),
    payload_json TEXT NOT NULL,
    receipt_digest TEXT NOT NULL UNIQUE,
    inserted_at TEXT NOT NULL,
    candidate INTEGER NOT NULL CHECK (candidate = 1),
    serves_truth INTEGER NOT NULL CHECK (serves_truth = 0)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_recipe_receipts_primitive ON recipe_receipts(primitive_id);

CREATE TABLE IF NOT EXISTS receipt_revocations (
    receipt_id TEXT PRIMARY KEY REFERENCES recipe_receipts(receipt_id),
    revoked_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    revocation_digest TEXT NOT NULL UNIQUE
) STRICT;

CREATE VIEW IF NOT EXISTS recipe_receipt_status AS
SELECT r.*, v.revoked_at AS revoked_at, v.reason AS revocation_reason,
       v.revocation_digest AS revocation_digest
FROM recipe_receipts AS r
LEFT JOIN receipt_revocations AS v ON v.receipt_id = r.receipt_id;

CREATE TRIGGER IF NOT EXISTS recipe_receipts_no_update
BEFORE UPDATE ON recipe_receipts BEGIN
    SELECT RAISE(ABORT, 'recipe receipt evidence is immutable');
END;
CREATE TRIGGER IF NOT EXISTS recipe_receipts_no_delete
BEFORE DELETE ON recipe_receipts BEGIN
    SELECT RAISE(ABORT, 'recipe receipt evidence is immutable');
END;
CREATE TRIGGER IF NOT EXISTS declarations_no_update
BEFORE UPDATE ON source_declarations BEGIN
    SELECT RAISE(ABORT, 'source declarations are append-only');
END;
CREATE TRIGGER IF NOT EXISTS declarations_no_delete
BEFORE DELETE ON source_declarations BEGIN
    SELECT RAISE(ABORT, 'source declarations are append-only');
END;
CREATE TRIGGER IF NOT EXISTS revocations_no_update
BEFORE UPDATE ON receipt_revocations BEGIN
    SELECT RAISE(ABORT, 'receipt revocations are append-only');
END;
CREATE TRIGGER IF NOT EXISTS revocations_no_delete
BEFORE DELETE ON receipt_revocations BEGIN
    SELECT RAISE(ABORT, 'receipt revocations are append-only');
END;
"""


def _connect(path: Path, *, create: bool = True) -> sqlite3.Connection:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    if create:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        con.executescript(_SCHEMA)
    return con


@contextmanager
def _writer_lock(db_path: Path) -> Iterator[None]:
    lock_path = db_path.with_name(db_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _validate_bundle(bundle: Mapping[str, Any]) -> None:
    payload = bundle.get("payload")
    if not isinstance(payload, dict):
        raise ReceiptRejected("receipt payload must be an object")
    checks = payload.get("oracle_checks")
    if payload.get("oracle_pass") is not True or not isinstance(checks, dict) or not checks:
        raise ReceiptRejected("only a passing hidden-oracle result can become a receipt")
    if not all(value is True for value in checks.values()):
        raise ReceiptRejected("every named hidden-oracle check must pass")
    if payload.get("model_tokens") != 0:
        raise ReceiptRejected("deterministic receipt must record zero model tokens")
    if payload.get("candidate") is not True or payload.get("serves_truth") is not False:
        raise ReceiptRejected("receipt boundary must remain candidate=true / serves_truth=false")
    expected = _digest(payload)
    if bundle.get("receipt_digest") != expected:
        raise ReceiptRejected("receipt content digest mismatch")
    if bundle.get("receipt_id") != "receipt/" + expected.removeprefix("sha256:"):
        raise ReceiptRejected("receipt identity is not content-addressed")
    if bundle.get("payload_json") != _canonical(payload):
        raise ReceiptRejected("receipt payload JSON is not canonical")


def _append_card_once_locked(cards_path: Path, card: Mapping[str, Any]) -> bool:
    cards_path.parent.mkdir(parents=True, exist_ok=True)
    digest = str(card["card_digest"])
    if _digest({key: value for key, value in card.items() if key != "card_digest"}) != digest:
        raise ReceiptRejected("recipe card content digest mismatch")
    with cards_path.open("a+", encoding="utf-8") as handle:
        handle.seek(0)
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReceiptRejected(f"malformed card stream at line {line_no}") from exc
            if existing.get("card_digest") == digest and existing.get("receipt_id") == card.get("receipt_id"):
                return False
        handle.seek(0, os.SEEK_END)
        handle.write(_canonical(dict(card)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def store_bundles(
    bundles: Sequence[Mapping[str, Any]],
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    cards_path: Path | str = DEFAULT_CARD_PATH,
) -> dict[str, int]:
    """Atomically store valid receipts, then idempotently append their searchable cards."""
    db = Path(db_path)
    cards = Path(cards_path)
    for bundle in bundles:
        _validate_bundle(bundle)
    inserted_receipts = inserted_declarations = appended_cards = 0
    with _writer_lock(db):
        with _connect(db) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                for bundle in bundles:
                    payload = bundle["payload"]
                    declaration = bundle["declaration"]
                    declaration_digest = str(payload["declaration_digest"])
                    if _digest(declaration) != declaration_digest:
                        raise ReceiptRejected("source declaration digest mismatch")
                    before = con.total_changes
                    con.execute(
                        "INSERT OR IGNORE INTO source_declarations VALUES (?,?,?,?)",
                        (
                            declaration_digest,
                            payload["primitive_id"],
                            bundle["declaration_json"],
                            _utc_now(),
                        ),
                    )
                    inserted_declarations += con.total_changes - before
                    existing = con.execute(
                        "SELECT payload_json, receipt_digest FROM recipe_receipts WHERE receipt_id=?",
                        (bundle["receipt_id"],),
                    ).fetchone()
                    if existing is not None:
                        if existing["payload_json"] != bundle["payload_json"] or existing["receipt_digest"] != bundle["receipt_digest"]:
                            raise ReceiptRejected("content-addressed receipt id collision")
                        continue
                    con.execute(
                        """INSERT INTO recipe_receipts (
                            receipt_id, primitive_id, identity_digest, declaration_digest, contract_digest,
                            artifact_digest, oracle_digest, protocol_digest, outcome_digest, oracle_pass,
                            oracle_checks_json, benchmark_kind, model_tokens, payload_json, receipt_digest,
                            inserted_at, candidate, serves_truth
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            bundle["receipt_id"],
                            payload["primitive_id"],
                            payload["identity_digest"],
                            declaration_digest,
                            payload["contract_digest"],
                            payload["artifact_digest"],
                            payload["oracle_digest"],
                            payload["protocol_digest"],
                            payload["outcome_digest"],
                            1,
                            _canonical(payload["oracle_checks"]),
                            str(payload["benchmark_kind"]),
                            0,
                            bundle["payload_json"],
                            bundle["receipt_digest"],
                            _utc_now(),
                            1,
                            0,
                        ),
                    )
                    inserted_receipts += 1
                con.commit()
                con.execute("PRAGMA wal_checkpoint(FULL)")
            except Exception:
                con.rollback()
                raise
        # A crash after the DB commit but before a card append is repaired by the
        # next idempotent run; the shared lock prevents interleaved JSONL writes.
        for bundle in bundles:
            appended_cards += int(_append_card_once_locked(cards, bundle["card"]))
    return {
        "input_bundles": len(bundles),
        "inserted_declarations": inserted_declarations,
        "inserted_receipts": inserted_receipts,
        "appended_cards": appended_cards,
    }


def run_and_store(
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    cards_path: Path | str = DEFAULT_CARD_PATH,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run all five real hidden oracles and store only their passing receipts."""
    bundles = _execute_current_recipes()
    stored = store_bundles(bundles, db_path=db_path, cards_path=cards_path)
    receipt = {
        "record_type": "verified_recipe_receipt_run",
        "declared_recipes": len(_current_materials()),
        "oracle_pass_receipts": len(bundles),
        "failed_recipes_emitted": 0,
        "store": stored,
        **BOUNDARY,
    }
    if manifest_path is not None:
        stats = store_stats(db_path=db_path, cards_path=cards_path)
        _atomic_json(Path(manifest_path), stats)
        receipt["stats"] = stats
        receipt["manifest_path"] = str(Path(manifest_path))
    return receipt


def _row_payload_matches(row: sqlite3.Row, expected: Mapping[str, Any]) -> bool:
    try:
        payload = json.loads(row["payload_json"])
        checks = json.loads(row["oracle_checks_json"])
        declaration = json.loads(row["declaration_json"])
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(payload, dict) or not isinstance(checks, dict) or not isinstance(declaration, dict):
        return False
    if _canonical(payload) != row["payload_json"] or _digest(payload) != row["receipt_digest"]:
        return False
    if row["receipt_id"] != "receipt/" + str(row["receipt_digest"]).removeprefix("sha256:"):
        return False
    mirrored = {
        "primitive_id": row["primitive_id"],
        "identity_digest": row["identity_digest"],
        "declaration_digest": row["declaration_digest"],
        "contract_digest": row["contract_digest"],
        "artifact_digest": row["artifact_digest"],
        "oracle_digest": row["oracle_digest"],
        "protocol_digest": row["protocol_digest"],
        "outcome_digest": row["outcome_digest"],
        "oracle_pass": bool(row["oracle_pass"]),
        "oracle_checks": checks,
        "benchmark_kind": row["benchmark_kind"],
        "model_tokens": row["model_tokens"],
        "candidate": bool(row["candidate"]),
        "serves_truth": bool(row["serves_truth"]),
    }
    if any(payload.get(key) != value for key, value in mirrored.items()):
        return False
    if payload.get("oracle_pass") is not True or not checks or not all(value is True for value in checks.values()):
        return False
    if payload.get("model_tokens") != 0 or payload.get("candidate") is not True or payload.get("serves_truth") is not False:
        return False
    if _digest(declaration) != row["declaration_digest"] or declaration.get("primitive_id") != row["primitive_id"]:
        return False
    for key in (
        "identity_digest",
        "declaration_digest",
        "contract_digest",
        "artifact_digest",
        "oracle_digest",
        "protocol_digest",
    ):
        if payload.get(key) != expected.get(key):
            return False
    if row["revoked_at"] is not None:
        revocation = {
            "receipt_id": row["receipt_id"],
            "revoked_at": row["revoked_at"],
            "reason": row["revocation_reason"],
        }
        # Corrupt revocation metadata also fails closed.
        if _digest(revocation) != row["revocation_digest"]:
            return False
        return False
    return True


def trusted_receipts_for(
    primitive_ids: Iterable[str],
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return only current, passing, unrevoked, content-valid executed receipts.

    This is the search integration boundary.  Call it with candidate recipe
    primitive IDs after retrieval/ranking; absence means the recipe is not
    execution-authorized by this store.  It never upgrades ``serves_truth``.
    """
    requested = sorted({str(value) for value in primitive_ids if str(value)})
    db = Path(db_path)
    if not requested or not db.exists():
        return []
    current = _current_materials()
    eligible = [value for value in requested if value in current]
    if not eligible:
        return []
    marks = ",".join("?" for _ in eligible)
    query = f"""SELECT s.*, d.declaration_json
                FROM recipe_receipt_status AS s
                JOIN source_declarations AS d ON d.declaration_digest=s.declaration_digest
                WHERE s.primitive_id IN ({marks}) ORDER BY s.primitive_id, s.receipt_id"""
    accepted: list[dict[str, Any]] = []
    with _connect(db, create=False) as con:
        for row in con.execute(query, eligible):
            expected = current.get(row["primitive_id"])
            if expected is None or not _row_payload_matches(row, expected):
                continue
            payload = json.loads(row["payload_json"])
            accepted.append(
                {
                    **payload,
                    "receipt_id": row["receipt_id"],
                    "receipt_digest": row["receipt_digest"],
                    "inserted_at": row["inserted_at"],
                    "revoked_at": None,
                }
            )
    return accepted


def revoke_receipt(
    receipt_id: str,
    reason: str,
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    revoked_at: str | None = None,
) -> dict[str, str]:
    """Append one irreversible revocation for immutable evidence."""
    if not reason.strip():
        raise ReceiptRejected("revocation reason is required")
    db = Path(db_path)
    when = revoked_at or _utc_now()
    record = {"receipt_id": receipt_id, "revoked_at": when, "reason": reason.strip()}
    record["revocation_digest"] = _digest(record)
    with _writer_lock(db):
        with _connect(db) as con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT 1 FROM recipe_receipts WHERE receipt_id=?", (receipt_id,)).fetchone() is None:
                raise ReceiptRejected("cannot revoke an unknown receipt")
            try:
                con.execute(
                    "INSERT INTO receipt_revocations VALUES (?,?,?,?)",
                    (receipt_id, when, reason.strip(), record["revocation_digest"]),
                )
                con.commit()
            except Exception:
                con.rollback()
                raise
    return record


def store_stats(
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    cards_path: Path | str = DEFAULT_CARD_PATH,
) -> dict[str, Any]:
    db, cards = Path(db_path), Path(cards_path)
    base: dict[str, Any] = {
        "declared_recipes": len(_current_materials()),
        "source_declarations": 0,
        "stored_receipts": 0,
        "trusted_receipts": 0,
        "revoked_receipts": 0,
        "invalid_or_stale_receipts": 0,
        "recipe_cards": 0,
        **BOUNDARY,
    }
    if cards.exists():
        with cards.open(encoding="utf-8") as handle:
            base["recipe_cards"] = sum(1 for line in handle if line.strip())
    if not db.exists():
        return base
    with _connect(db, create=False) as con:
        base["source_declarations"] = int(con.execute("SELECT COUNT(*) FROM source_declarations").fetchone()[0])
        base["stored_receipts"] = int(con.execute("SELECT COUNT(*) FROM recipe_receipts").fetchone()[0])
        base["revoked_receipts"] = int(con.execute("SELECT COUNT(*) FROM receipt_revocations").fetchone()[0])
    ids = list(_current_materials())
    base["trusted_receipts"] = len(trusted_receipts_for(ids, db_path=db))
    base["invalid_or_stale_receipts"] = base["stored_receipts"] - base["trusted_receipts"] - base["revoked_receipts"]
    return base


def _copy_db(source: Path, target: Path) -> None:
    with _connect(source, create=False) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def self_test() -> bool:
    """Hermetic real-oracle test plus mutation, tamper, failure, and revocation gates."""
    with tempfile.TemporaryDirectory(prefix="verified-recipe-receipts-") as temp:
        root = Path(temp)
        db = root / "receipts.sqlite3"
        cards = root / "cards.jsonl"

        # Real hidden-oracle harness: all five current recipes must independently earn receipts.
        first = run_and_store(db_path=db, cards_path=cards)
        materials = _current_materials()
        assert len(materials) == 5, materials
        assert first["oracle_pass_receipts"] == 5 and first["failed_recipes_emitted"] == 0, first
        trusted = trusted_receipts_for(materials, db_path=db)
        assert len(trusted) == 5 and all(r["oracle_pass"] is True for r in trusted), trusted
        assert all(r["candidate"] is True and r["serves_truth"] is False for r in trusted)

        # Idempotent DB + append-safe JSONL: a repeat creates no duplicate evidence/cards.
        second = run_and_store(db_path=db, cards_path=cards)
        assert second["store"]["inserted_receipts"] == 0, second
        assert second["store"]["appended_cards"] == 0, second
        assert sum(1 for line in cards.read_text(encoding="utf-8").splitlines() if line) == 5

        sample = trusted[0]
        sample_id = sample["primitive_id"]
        sample_receipt = sample["receipt_id"]

        # SQL trigger catches ordinary mutation attempts.
        with _connect(db, create=False) as con:
            try:
                con.execute("UPDATE recipe_receipts SET artifact_digest='tampered' WHERE receipt_id=?", (sample_receipt,))
            except sqlite3.DatabaseError as exc:
                assert "immutable" in str(exc)
            else:
                raise AssertionError("immutable receipt update unexpectedly succeeded")

        # At-rest payload tamper is rejected even if an attacker bypasses the trigger.
        tamper_db = root / "tamper.sqlite3"
        _copy_db(db, tamper_db)
        with sqlite3.connect(tamper_db) as con:
            con.execute("DROP TRIGGER recipe_receipts_no_update")
            con.execute("UPDATE recipe_receipts SET payload_json='{}' WHERE receipt_id=?", (sample_receipt,))
            con.commit()
        assert trusted_receipts_for([sample_id], db_path=tamper_db) == []

        # A self-consistent forged digest with the wrong current identity is still rejected.
        mismatch_db = root / "mismatch.sqlite3"
        _copy_db(db, mismatch_db)
        with sqlite3.connect(mismatch_db) as con:
            con.row_factory = sqlite3.Row
            con.execute("DROP TRIGGER recipe_receipts_no_update")
            row = con.execute("SELECT * FROM recipe_receipts WHERE receipt_id=?", (sample_receipt,)).fetchone()
            forged_payload = json.loads(row["payload_json"])
            forged_payload["identity_digest"] = _digest({"forged": True})
            forged_digest = _digest(forged_payload)
            forged_id = "receipt/" + forged_digest.removeprefix("sha256:")
            con.execute(
                """UPDATE recipe_receipts SET receipt_id=?, identity_digest=?, payload_json=?, receipt_digest=?
                   WHERE receipt_id=?""",
                (forged_id, forged_payload["identity_digest"], _canonical(forged_payload), forged_digest, sample_receipt),
            )
            con.commit()
        assert trusted_receipts_for([sample_id], db_path=mismatch_db) == []

        # Revocation is append-only and removes otherwise valid evidence from trusted reads.
        revoke_db = root / "revoke.sqlite3"
        _copy_db(db, revoke_db)
        revoke_receipt(sample_receipt, "self-test revocation", db_path=revoke_db, revoked_at="2026-07-09T00:00:00Z")
        assert trusted_receipts_for([sample_id], db_path=revoke_db) == []

        # Failed oracle evidence is rejected at the only public store boundary and emits no card.
        failed_db = root / "failed.sqlite3"
        failed_cards = root / "failed.jsonl"
        failed = copy.deepcopy(_execute_current_recipes()[0])
        failed["payload"]["oracle_pass"] = False
        failed["payload_json"] = _canonical(failed["payload"])
        failed["receipt_digest"] = _digest(failed["payload"])
        failed["receipt_id"] = "receipt/" + failed["receipt_digest"].removeprefix("sha256:")
        try:
            store_bundles([failed], db_path=failed_db, cards_path=failed_cards)
        except ReceiptRejected:
            pass
        else:
            raise AssertionError("failed oracle result unexpectedly entered the receipt store")
        assert not failed_db.exists() and not failed_cards.exists()

        stats = store_stats(db_path=db, cards_path=cards)
        assert stats["trusted_receipts"] == stats["stored_receipts"] == stats["recipe_cards"] == 5, stats
        print(
            "OK verified_recipe_receipt_store self-test: 5/5 deterministic recipes passed their real hidden "
            "oracles and earned immutable content-addressed receipts; repeat was idempotent; SQL mutation, "
            "payload tamper, identity mismatch, revocation, and failed-oracle insertion were all rejected; "
            "candidate=true serves_truth=false"
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed cards + trusted receipts for deterministic recipes.")
    parser.add_argument("--run", action="store_true", help="execute all real hidden oracles and store passing receipts")
    parser.add_argument("--stats", action="store_true", help="read and validate receipt/card counts")
    parser.add_argument("--self-test", action="store_true", help="run hermetic temp-dir mutation-gated tests")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARD_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.run:
        receipt = run_and_store(
            db_path=args.db,
            cards_path=args.cards,
            manifest_path=args.manifest,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        if receipt["oracle_pass_receipts"] != receipt["declared_recipes"]:
            raise SystemExit(1)
        return
    if args.stats:
        print(json.dumps(store_stats(db_path=args.db, cards_path=args.cards), indent=2, sort_keys=True))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
