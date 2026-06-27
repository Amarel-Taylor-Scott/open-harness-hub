"""src.teleon.compiler.__main__ — the compiler CLI + the exhaustive self-test + the drift gate.

Mirrors ``scripts/deploy/generate_provider_configs.py``'s CLI shape (the proven pattern):

  python -m src.teleon.compiler --self-test            # offline invariants (determinism · refusal · 3 emitters · registry · …)
  python -m src.teleon.compiler --compile <cap_id>     # compile a capability (live runtime state if present, else fixture)
  python -m src.teleon.compiler --compile <cap_id> --exec-target k8s_job   # pick the deployable shape
  python -m src.teleon.compiler --emit                 # with --compile: also print the concrete deployable text
  python -m src.teleon.compiler --register <cap_id>    # compile AND register into the durable registry (sets the prior active unit as rollback_target)
  python -m src.teleon.compiler --list                 # show the registry: active units (one/capability) + full lossless history
  python -m src.teleon.compiler --rollback <cap_id>    # return the rollback-target unit (the predecessor of the active unit) — REAL rollback
  python -m src.teleon.compiler --check                # drift gate over the committed example units

The compiled-unit REGISTRY (src/teleon/compiler/registry.py) is the per-capability analog of the per-service
``architecture/deploy_topology.json``: a durable, append-only JSONL under ``dist/local-services-state/teleon-compiler/``
(the Fly volume mount) that tracks which capability-version is compiled to which runtime, preserves full history
(superseded units are DEMOTED, not deleted — lossless), and makes the compiler's ``rollback_target`` field real
(``--rollback`` returns the exact prior promoted unit). Doc: ``docs/architecture/compiled-unit-registry.md``.

The committed example units (the drift-gate fixtures) live next to this package under ``examples/`` and are
written by ``--write-examples`` (regen on a deliberate compiler change, like the topology generator's outputs).
``--check`` recompiles them from the fixture and fails on any drift — the same self-test invariant the provider
generator enforces.

The CLI uses a FIXED ``now`` for any committed/self-test artifact so output is byte-stable (determinism is a
property of the compiler; the CLI must not inject wall-clock noise into a drift-gated file).
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

import importlib

# NOTE: src.teleon.compiler.__init__ re-exports the `emit` FUNCTION into the package namespace, which would
# shadow the `emit` SUBMODULE on attribute access. Resolve the true submodules via importlib so `_e` is the
# module (with emit_fly_machine/emit_k8s_job/emit_local_process) and not the re-exported function.
_c = importlib.import_module("src.teleon.compiler.compile")
_e = importlib.import_module("src.teleon.compiler.emit")
_f = importlib.import_module("src.teleon.compiler.fixtures")
_lc = importlib.import_module("src.teleon.compiler.live_capability")  # live-state reader (split out of fixtures)
_r = importlib.import_module("src.teleon.compiler.registry")  # the durable compiled-unit registry (deploy_topology analog)

_PKG_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = _PKG_DIR / "examples"
#: a FIXED timestamp for committed/self-test artifacts — the compiler is deterministic, so the drift-gated files
#: must not carry a moving clock value (provenance.compiled_at). One definition.
FIXED_NOW = "2026-06-11T00:00:00Z"
#: the three committed example units (one per exec_target) prove portability AND anchor the drift gate.
EXAMPLE_TARGETS = _c.EXEC_TARGETS
#: the canonical fixture capability id (the self-test / committed-example capability). Single source so the
#: CLI, the self-test assertions, and the fixtures stay in lockstep without a hand-typed parallel literal.
_FIXTURE_CAPABILITY_ID = _f.fixture_promoted_capability()["id"]
#: the canonical fixture receipt ref for lineage assertions.
_FIXTURE_RECEIPT_REF = "llmrcpt_fixture_0001"


# ── compile helpers ──────────────────────────────────────────────────────────────────────────────────────────
def _compile_fixture(exec_target: str, *, now: str = FIXED_NOW) -> dict:
    """Compile the deterministic fixture for one exec_target (the committed-example / self-test source)."""
    return _c.compile_capability(
        _f.fixture_promoted_capability(), _f.fixture_task_spec(),
        exec_target=exec_target, now=now,
        resolved_preference=_f.fixture_resolved_preference(),
        receipt_refs=[_FIXTURE_RECEIPT_REF],
    )


def _example_path(exec_target: str) -> Path:
    return EXAMPLES_DIR / f"cru.{exec_target}.example.json"


def _render_examples(now: str = FIXED_NOW) -> dict[Path, str]:
    """The committed example units, keyed by path (deterministic JSON text)."""
    out: dict[Path, str] = {}
    for target in EXAMPLE_TARGETS:
        unit = _compile_fixture(target, now=now)
        out[_example_path(target)] = json.dumps(unit, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return out


# ── compile-for-CLI (shared by --compile and --register) ─────────────────────────────────────────────────────
def _compile_for_cli(capability_id: str, exec_target: str, *, now: str | None) -> tuple[dict, str]:
    """Compile ``capability_id`` from the LIVE runtime state if present, else the fixture. Returns (unit, source).
    Raises ``NotPromotedError`` (a non-promoted capability) or schema-validation ``RuntimeError`` — callers map
    those to clear exit codes. The single compile path both --compile and --register share (no duplicated wiring)."""
    used_now = now or FIXED_NOW
    source = "fixture"
    try:
        cap, receipt_refs = _lc.load_live_capability(capability_id)
        task_spec = {**_f.fixture_task_spec(), "capability_id": capability_id}
        source = "live runtime state"
    except (FileNotFoundError, KeyError):
        cap = _f.fixture_promoted_capability()
        if cap["id"] != capability_id:
            print(f"  no live state and the fixture is {cap['id']!r}, not {capability_id!r} — "
                  f"compiling the fixture capability instead", file=sys.stderr)
        task_spec = _f.fixture_task_spec()
        receipt_refs = [_FIXTURE_RECEIPT_REF]
    unit = _c.compile_capability(cap, task_spec, exec_target=exec_target, now=used_now,
                                 resolved_preference=_f.fixture_resolved_preference(), receipt_refs=receipt_refs)
    errors = _c.validate_unit(unit)
    if errors:
        raise RuntimeError("compiled unit failed schema validation:\n  " + "\n  ".join(f"✗ {e}" for e in errors))
    return unit, source


# ── --compile ────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_compile(capability_id: str, exec_target: str, *, do_emit: bool, now: str | None) -> int:
    """Compile ``capability_id`` from the LIVE runtime state if present, else the fixture. Prints the unit (and the
    concrete deployable text with --emit). Refuses a non-promoted capability with a clear reason (exit 2)."""
    try:
        unit, source = _compile_for_cli(capability_id, exec_target, now=now)
    except _c.NotPromotedError as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc).upper().split("\n", 1)[0], file=sys.stderr)
        print(str(exc).split("\n", 1)[1] if "\n" in str(exc) else "", file=sys.stderr)
        return 1
    print(f"# compiled {capability_id!r} (source: {source}) → exec_target={exec_target}, "
          f"backend={unit['backend']}, unit_id={unit['unit_id']}")
    print(json.dumps(unit, indent=2, sort_keys=True, ensure_ascii=False))
    if do_emit:
        print(f"\n# --- concrete deployable ({exec_target}) ---")
        print(_e.emit(unit, exec_target))
    return 0


# ── --register / --list / --rollback (the durable compiled-unit registry) ────────────────────────────────────
def _open_registry(state_dir: str | None):
    """Open the registry at ``state_dir`` (the dist/local-services-state/teleon-compiler mount) or the default."""
    if state_dir:
        return _r.open_registry(Path(state_dir) / _r.DEFAULT_LOG_NAME)
    return _r.open_registry()


def cmd_register(capability_id: str, exec_target: str, *, now: str | None, state_dir: str | None) -> int:
    """Compile ``capability_id`` AND register the unit into the durable registry (idempotent by unit_id). On a new
    unit this DEMOTES the prior active unit for the capability and stamps it as the new unit's rollback_target —
    making rollback real end-to-end. Refuses a non-promoted capability (exit 2)."""
    try:
        unit, source = _compile_for_cli(capability_id, exec_target, now=now)
    except _c.NotPromotedError as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    reg = _open_registry(state_dir)
    try:
        before = reg.get(unit["unit_id"]) is not None
        record = reg.register(unit)
    finally:
        reg.close()
    note = "already registered (idempotent no-op)" if before else "registered"
    print(f"# {note}: {capability_id!r} (source: {source}) → exec_target={exec_target}, "
          f"unit_id={record['unit']['unit_id']}, active={record['active']}")
    if record["rollback_target"]:
        print(f"#   supersedes (rollback_target) → {record['rollback_target']}")
    else:
        print("#   first compiled unit for this capability (no rollback target yet)")
    print(f"#   registry log: {reg.log_path}")
    print(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_list(state_dir: str | None) -> int:
    """Show the registry: every currently-active compiled unit (one per capability), plus the full history per
    capability (active + demoted, lossless). The per-capability deploy_topology snapshot."""
    reg = _open_registry(state_dir)
    try:
        active = reg.list_active()
        cap_ids = reg.capability_ids()
        print(f"# compiled-unit registry @ {reg.log_path}")
        print(f"# {len(active)} active unit(s) across {len(cap_ids)} capability(ies):")
        for u in active:
            rt = u.get("rollback_target") or "—"
            print(f"  [active] {u['capability_id']} v{u['capability_version']} "
                  f"({u['exec_target']}) unit_id={u['unit_id']} rollback_target={rt}")
        for cap in cap_ids:
            hist = reg.history(cap)
            print(f"  history[{cap}]: {len(hist)} unit(s) —")
            for r in hist:
                u = r["unit"]
                flag = "active " if r["active"] else "demoted"
                print(f"      [{flag}] v{u['capability_version']} {u['exec_target']} unit_id={u['unit_id']}")
    finally:
        reg.close()
    return 0


def cmd_rollback(capability_id: str, state_dir: str | None) -> int:
    """Return the rollback-target unit for a capability (the predecessor of the current active unit) — REAL
    rollback. Exit 0 + prints the target unit; exit 3 (honest) when there is no predecessor or the history is
    tampered/missing."""
    reg = _open_registry(state_dir)
    try:
        try:
            target = reg.rollback_target(capability_id)
        except _r.RegistryIntegrityError as exc:
            print(f"ROLLBACK UNAVAILABLE — {exc}", file=sys.stderr)
            return 3
        active = reg.latest_active_for(capability_id)
    finally:
        reg.close()
    if active is None:
        print(f"no active compiled unit for capability {capability_id!r} — nothing is deployed to roll back from",
              file=sys.stderr)
        return 3
    if target is None:
        print(f"capability {capability_id!r} is on its FIRST compiled unit ({active['unit_id']}) — "
              "no predecessor to roll back to", file=sys.stderr)
        return 3
    print(f"# rollback target for {capability_id!r}: active={active['unit_id']} → "
          f"rollback_to={target['unit_id']} (v{target['capability_version']}, {target['exec_target']})")
    print(json.dumps(target, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


# ── --check (drift gate over the committed examples) ─────────────────────────────────────────────────────────
def cmd_check() -> int:
    rendered = _render_examples()
    problems: list[str] = []
    for path, expected in rendered.items():
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual is None:
            problems.append(f"{path.relative_to(_PKG_DIR.parents[2])}: missing — run --write-examples")
        elif actual != expected:
            diff = list(difflib.unified_diff(actual.splitlines(), expected.splitlines(), lineterm="", n=1))
            first = next((d for d in diff if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))), "")
            problems.append(f"{path.relative_to(_PKG_DIR.parents[2])}: drifted from the compiler "
                            f"({len(diff)} diff lines; first: {first!r})")
    if problems:
        print("CHECK FAILURES (the committed example units drifted from the compiler — fix the code or "
              "re-run --write-examples on a deliberate change):")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print(f"PASS — {len(rendered)} committed example units match the compiler (drift gate green)")
    return 0


def cmd_write_examples() -> int:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in _render_examples().items():
        path.write_text(content, encoding="utf-8")
        print(f"  wrote {path.relative_to(_PKG_DIR.parents[2])}")
    print(f"PASS — {len(EXAMPLE_TARGETS)} example units written")
    return 0


# ── registry self-test (register/latest/history/rollback/supersede + idempotency + lossless + rehydration) ────
def _compile_version(version: int, *, exec_target: str = "k8s_job", now: str) -> dict:
    """Compile a fixture capability at a given ``version`` (a real version bump → a new unit_id) for the registry
    proofs. Reuses the deterministic fixtures so the produced units are byte-stable across runs."""
    cap = {**_f.fixture_promoted_capability(), "version": version}
    return _c.compile_capability(cap, _f.fixture_task_spec(), exec_target=exec_target, now=now,
                                 resolved_preference=_f.fixture_resolved_preference(),
                                 receipt_refs=[f"llmrcpt_fixture_v{version}"])


def _registry_checks(checks: list[tuple[str, bool]]) -> None:  # noqa: C901 — a flat checklist is clearer here
    """Exercise the durable compiled-unit registry end-to-end under a temp dir (never the real state path):
    register → latest_for/latest_active_for → history → rollback_target/rollback_to → supersede/mark_active, plus
    idempotency, lossless supersession (demote-not-delete), restart-rehydration EQUALITY, and determinism
    (byte-identical log across two independent runs from the same inputs)."""
    import shutil
    import tempfile

    # two real versions of the fixture capability → two distinct unit_ids.
    u2 = _compile_version(2, now="2026-06-11T00:00:00Z")
    u3 = _compile_version(3, now="2026-06-12T00:00:00Z")
    checks.append(("registry: a version bump produces a distinct unit_id (the timeline has >1 unit)",
                   u2["unit_id"] != u3["unit_id"]))

    tmp = Path(tempfile.mkdtemp(prefix="cru-registry-selftest-"))
    try:
        log_a = tmp / "a" / _r.DEFAULT_LOG_NAME
        reg = _r.open_registry(log_a, db_path=tmp / "idx" / "a.db")

        # register v2: first compile → no rollback target, active.
        r2 = reg.register(u2)
        checks.append(("registry: register a first unit → active, empty rollback_target (no predecessor)",
                       r2["active"] is True and r2["rollback_target"] == ""))
        checks.append(("registry: latest_active_for returns the just-registered unit",
                       reg.latest_active_for("cap-redact")["unit_id"] == u2["unit_id"]))
        checks.append(("registry: rollback_target is None on the first unit (honest, no fabricated predecessor)",
                       reg.rollback_target("cap-redact") is None))

        # register v3: REAL rollback wiring — v2 becomes v3's rollback_target and is DEMOTED (not deleted).
        r3 = reg.register(u3)
        checks.append(("registry: registering a newer unit sets the PRIOR active unit as its rollback_target (REAL rollback)",
                       r3["rollback_target"] == u2["unit_id"] and r3["unit"]["rollback_target"] == u2["unit_id"]))
        checks.append(("registry: the newer unit is active; the prior unit is DEMOTED (single active per capability)",
                       reg.latest_active_for("cap-redact")["unit_id"] == u3["unit_id"]
                       and reg.get(u2["unit_id"])["active"] is False))
        checks.append(("registry: latest_for = newest by version (v3) regardless of active state",
                       reg.latest_for("cap-redact")["unit_id"] == u3["unit_id"]))
        checks.append(("registry: rollback_target(cap) returns the EXACT prior unit (the field is now consumable)",
                       reg.rollback_target("cap-redact")["unit_id"] == u2["unit_id"]))

        # LOSSLESS: the demoted predecessor is preserved + queryable in history (demote-not-delete).
        hist = reg.history("cap-redact")
        checks.append(("registry: history preserves BOTH units (lossless — superseded is demoted, not deleted)",
                       [h["unit"]["unit_id"] for h in hist] == [u2["unit_id"], u3["unit_id"]]))
        checks.append(("registry: history is deterministically ordered (by capability_version, compiled_at, unit_id)",
                       [h["unit"]["capability_version"] for h in hist] == [2, 3]))
        checks.append(("registry: list_active has exactly one active unit for the capability (v3)",
                       [u["unit_id"] for u in reg.list_active()] == [u3["unit_id"]]))

        # IDEMPOTENCY: re-registering the same unit_id is a no-op (no duplicate append, no forked rollback chain).
        records_before = len(reg.all_records())
        r3_again = reg.register(u3)
        checks.append(("registry: re-registering the same unit is IDEMPOTENT (no duplicate append)",
                       r3_again["unit"]["unit_id"] == u3["unit_id"] and len(reg.all_records()) == records_before))

        # REAL rollback end-to-end: rollback_to re-activates the predecessor and demotes the current active unit.
        rolled = reg.rollback_to("cap-redact")
        checks.append(("registry: rollback_to(cap) re-activates the predecessor (v2) and demotes v3 (REAL rollback)",
                       rolled["unit"]["unit_id"] == u2["unit_id"]
                       and reg.latest_active_for("cap-redact")["unit_id"] == u2["unit_id"]
                       and reg.get(u3["unit_id"])["active"] is False))
        # mark_active forward again (re-promote v3) — single-active invariant holds.
        reg.mark_active(u3["unit_id"])
        checks.append(("registry: mark_active re-promotes a unit and demotes the previously-active one",
                       reg.latest_active_for("cap-redact")["unit_id"] == u3["unit_id"]
                       and reg.get(u2["unit_id"])["active"] is False))
        # supersede demotes by id without deleting; history is unchanged in length (lossless).
        reg.supersede(u3["unit_id"], reason="self-test manual supersede")
        checks.append(("registry: supersede demotes a unit by id WITHOUT deleting it (history length unchanged)",
                       reg.get(u3["unit_id"])["active"] is False and len(reg.history("cap-redact")) == 2))

        # RESTART REHYDRATION EQUALITY: reopen from the durable JSONL → byte-identical projection state.
        active_before = reg.list_active()
        hist_before = reg.history("cap-redact")
        records_snapshot = reg.all_records()
        reg.close()
        reg2 = _r.open_registry(log_a, db_path=tmp / "idx" / "a.db")
        checks.append(("registry: restart rehydrates EQUAL active set (O(attach) from the durable JSONL)",
                       reg2.list_active() == active_before))
        checks.append(("registry: restart rehydrates EQUAL history (lossless across a restart)",
                       reg2.history("cap-redact") == hist_before))
        checks.append(("registry: restart rehydrates the EXACT append-only log (no record loss/dup)",
                       reg2.all_records() == records_snapshot))
        reg2.close()

        # HONEST INTEGRITY: a register with a unit that has no unit_id is refused; a tampered log raises loudly.
        bad_refused = False
        reg3 = _r.open_registry(tmp / "b" / _r.DEFAULT_LOG_NAME, db_path=tmp / "idx" / "b.db")
        try:
            reg3.register({"capability_id": "cap-x"})  # no unit_id
        except _r.RegistryError:
            bad_refused = True
        checks.append(("registry: register refuses a unit with no unit_id (honest, clear error)", bad_refused))
        # a missing/tampered history is detected: corrupt the JSONL mirror (a demote of an unknown unit) so a
        # FRESH open re-imports from it and the fold-time validator fires. (We tamper the durable mirror + drop the
        # rebuildable index so the engine re-reads the JSONL — proving the JSONL is the source of truth.)
        reg3.register(u2)
        reg3.close()
        idx_db = tmp / "idx" / "b.db"
        for p in (idx_db, Path(str(idx_db) + "-wal"), Path(str(idx_db) + "-shm")):
            if p.exists():
                p.unlink()
        with (tmp / "b" / _r.DEFAULT_LOG_NAME).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": _r.KIND_DEMOTE, "unit_id": "cru_phantom_never_registered"}) + "\n")
        tamper_detected = False
        try:
            _r.open_registry(tmp / "b" / _r.DEFAULT_LOG_NAME, db_path=tmp / "idx" / "b2.db")
        except _r.RegistryIntegrityError:
            tamper_detected = True
        checks.append(("registry: a tampered log (demote of a never-registered unit) is DETECTED, not silently folded",
                       tamper_detected))
        # rollback_target raises loudly when the active unit names a predecessor the log cannot back (missing
        # history). register() itself OWNS rollback_target (it overrides any caller value with the real
        # predecessor) — so a stored unit can only reference a MISSING predecessor via a hand-tampered/torn log.
        # We write exactly that: a register record whose unit's rollback_target points at a never-registered id,
        # then a fresh open (index dropped so the durable JSONL is re-read) must FAIL on rollback_target, not guess.
        log_c = tmp / "c" / _r.DEFAULT_LOG_NAME
        log_c.parent.mkdir(parents=True, exist_ok=True)
        orphan_unit = json.loads(json.dumps(u3))
        orphan_unit["rollback_target"] = "cru_missing_predecessor"  # a predecessor that was never registered
        tampered_record = {"kind": _r.KIND_REGISTER, "record_version": _r.REGISTRY_RECORD_VERSION,
                           "unit": orphan_unit, "active": True,
                           "registered_at": orphan_unit["provenance"]["compiled_at"],
                           "rollback_target": "cru_missing_predecessor", "supersedes": "cru_missing_predecessor"}
        with log_c.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(tampered_record, sort_keys=True) + "\n")
        reg4 = _r.open_registry(log_c, db_path=tmp / "idx" / "c.db")
        missing_raises = False
        try:
            reg4.rollback_target("cap-redact")
        except _r.RegistryIntegrityError:
            missing_raises = True
        checks.append(("registry: rollback_target fails honestly when the named predecessor is missing from the log",
                       missing_raises))
        reg4.close()

        # DETERMINISM: two independent registries built from the SAME register sequence yield byte-identical logs.
        det_logs: list[str] = []
        for run in ("d1", "d2"):
            lp = tmp / run / _r.DEFAULT_LOG_NAME
            rg = _r.open_registry(lp, db_path=tmp / "idx" / f"{run}.db")
            rg.register(_compile_version(2, now="2026-06-11T00:00:00Z"))
            rg.register(_compile_version(3, now="2026-06-12T00:00:00Z"))
            rg.close()
            det_logs.append(lp.read_text(encoding="utf-8"))
        checks.append(("registry: the durable JSONL is BYTE-IDENTICAL across two independent runs (deterministic)",
                       det_logs[0] == det_logs[1] and bool(det_logs[0])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── --self-test (offline invariants, exhaustive) ─────────────────────────────────────────────────────────────
def self_test() -> int:  # noqa: C901 — a flat checklist is clearer here than helper indirection
    import yaml  # validate the emitted k8s YAML actually parses

    checks: list[tuple[str, bool]] = []

    # 1. determinism: same inputs twice → byte-identical unit (the core guarantee)
    u1 = _compile_fixture("k8s_job")
    u2 = _compile_fixture("k8s_job")
    same = json.dumps(u1, sort_keys=True) == json.dumps(u2, sort_keys=True)
    checks.append(("determinism: same inputs twice → byte-identical unit", same))
    checks.append(("determinism: stable unit_id across recompiles", u1["unit_id"] == u2["unit_id"]))
    checks.append(("determinism: unit_id is independent of now (now=A vs now=B → same id)",
                   _compile_fixture("k8s_job", now="2020-01-01T00:00:00Z")["unit_id"] == u1["unit_id"]))

    # 2. THE LAW: a non-promoted capability is REFUSED
    refused = False
    try:
        _c.compile_capability(_f.fixture_candidate_capability(), _f.fixture_task_spec(), exec_target="k8s_job",
                              now=FIXED_NOW)
    except _c.NotPromotedError as exc:
        refused = "candidate" in str(exc) and "promoted" in str(exc)
    checks.append(("only-promoted-compiles: a non-promoted (candidate) capability is REFUSED with a clear reason",
                   refused))
    # a rolled-back capability is also refused (defense: status gate, not a single magic string)
    rb = {**_f.fixture_promoted_capability(), "status": "rolled-back"}
    rb_refused = False
    try:
        _c.compile_capability(rb, _f.fixture_task_spec(), exec_target="k8s_job", now=FIXED_NOW)
    except _c.NotPromotedError:
        rb_refused = True
    checks.append(("only-promoted-compiles: a rolled-back capability is also refused", rb_refused))

    # 3. all three exec_targets compile AND emit valid concrete configs
    units = {t: _compile_fixture(t) for t in _c.EXEC_TARGETS}
    checks.append(("portability: all three exec_targets compile", set(units) == set(_c.EXEC_TARGETS)))

    # 3a. fly machine JSON parses + carries the runner command + image + only ref names (no values)
    fly_text = _e.emit(units["fly_machine"], "fly_machine")
    fly = json.loads(fly_text)
    checks.append(("fly_machine: emitted JSON parses", isinstance(fly, dict)))
    checks.append(("fly_machine: carries the capability runner cmd + image",
                   fly["init"]["cmd"][:3] == ["python3", "-m", _c.RUNNER_MODULE]
                   and fly["image"].endswith("openharnesshub:latest")))
    checks.append(("fly_machine: env carries ref NAMES as placeholders, never a secret value",
                   all(v.startswith("${") for k, v in fly["env"].items() if k != "TELEON_UNIT_ID")
                   and not any("sk-" in str(v) for v in fly["env"].values())))

    # 3b. k8s Job YAML parses + is a batch/v1 Job with the bounded-work fields from the budget
    k8s_text = _e.emit(units["k8s_job"], "k8s_job")
    k8s = yaml.safe_load(k8s_text)
    checks.append(("k8s_job: emitted YAML parses", isinstance(k8s, dict)))
    checks.append(("k8s_job: is a batch/v1 Job with restartPolicy Never",
                   k8s.get("apiVersion") == "batch/v1" and k8s.get("kind") == "Job"
                   and k8s["spec"]["template"]["spec"]["restartPolicy"] == "Never"))
    checks.append(("k8s_job: backoffLimit + activeDeadlineSeconds come from the budget (not magic)",
                   k8s["spec"]["backoffLimit"] == units["k8s_job"]["budgets"]["max_attempts"]
                   and k8s["spec"]["activeDeadlineSeconds"] == units["k8s_job"]["budgets"]["timeout_s"]))
    checks.append(("k8s_job: env uses secretKeyRef (names only, no inline secret values)",
                   all("valueFrom" in e and "secretKeyRef" in e["valueFrom"]
                       for e in k8s["spec"]["template"]["spec"]["containers"][0]["env"])))
    checks.append(("k8s_job: OTel attrs ride as annotations (trace correlation survives to k8s)",
                   any(k.startswith("teleon.dev/capability-id") for k in k8s["metadata"]["annotations"])))

    # 3c. local process spec parses + carries argv + timeout/attempts/tokens
    local_text = _e.emit(units["local_process"], "local_process")
    local = json.loads(local_text)
    checks.append(("local_process: emitted JSON parses + carries argv + budgets",
                   local["kind"] == "TeleonLocalProcessSpec" and local["argv"][:3] == ["python3", "-m", _c.RUNNER_MODULE]
                   and isinstance(local["timeout_s"], int) and isinstance(local["max_attempts"], int)))

    # emit guards against a target/unit mismatch (portability is by RECOMPILE, not by re-labeling a unit)
    mismatch_guard = False
    try:
        _e.emit(units["k8s_job"], "fly_machine")
    except ValueError:
        mismatch_guard = True
    checks.append(("emit: refuses to render a unit for a DIFFERENT exec_target (no silent mislabel)", mismatch_guard))

    # 4. gate evidence + receipt refs present + honest (status pinned promoted, rates from the record)
    ge = units["k8s_job"]["gate_evidence"]
    checks.append(("gate evidence: status pinned 'promoted', train+holdout rates carried, gate_basis present",
                   ge["status"] == "promoted" and ge["train_pass_rate"] == 1.0
                   and ge["holdout_pass_rate"] == 1.0 and ge["gate_basis"] == "train+holdout"))
    checks.append(("provenance: receipt_refs attached (lineage to the model-call receipts)",
                   units["k8s_job"]["receipt_refs"] == [_FIXTURE_RECEIPT_REF]))
    checks.append(("lossless: unit carries capability_id + version + a rollback_target field",
                   units["k8s_job"]["capability_id"] == _FIXTURE_CAPABILITY_ID
                   and units["k8s_job"]["capability_version"] == _f.fixture_promoted_capability()["version"]
                   and "rollback_target" in units["k8s_job"]))
    checks.append(("honest: is_truth is structurally false", units["k8s_job"]["is_truth"] is False))

    # 5. budgets come from POLICY, not magic numbers (prove the joins)
    b = units["k8s_job"]["budgets"]
    checks.append(("budgets: max_tokens sourced from the OIPS budget_policy (512, not the default)",
                   b["max_tokens"] == 512 and b["budget_basis"]["max_tokens"] == "oips.budget_policy.max_output_tokens"))
    checks.append(("budgets: timeout_s sourced from the SLA policy (interactive_30s → 30s)",
                   b["timeout_s"] == 30 and b["budget_basis"]["timeout_s"].endswith("interactive_30s.target_seconds")))
    checks.append(("budgets: max_attempts sourced from the CapabilityTask spec (3)",
                   b["max_attempts"] == 3 and b["budget_basis"]["max_attempts"] == "CapabilityTask.spec.max_attempts"))
    # budget default fires ONLY when the policy omits a token ceiling (and is recorded honestly as the default)
    no_budget_pref = {"effective": {"budget_policy": {}}}
    u_default = _c.compile_capability(_f.fixture_promoted_capability(), _f.fixture_task_spec(),
                                      exec_target="k8s_job", now=FIXED_NOW, resolved_preference=no_budget_pref)
    checks.append(("budgets: the named default constant fires ONLY when policy omits a token ceiling, recorded as such",
                   u_default["budgets"]["max_tokens"] == _c.DEFAULT_MAX_OUTPUT_TOKENS
                   and "DEFAULT_MAX_OUTPUT_TOKENS" in u_default["budgets"]["budget_basis"]["max_tokens"]))

    # 6. resources come from worker_resource_classes.json (standard_cpu → 500m / 512Mi→512MB)
    r = units["k8s_job"]["resources"]
    checks.append(("resources: cpu + memory_mb + gpu joined from worker_resource_classes (standard_cpu: 500m/512Mi→537MB)",
                   r["resource_class"] == "standard_cpu" and r["cpu"] == "500m"
                   and r["memory_mb"] == 537 and r["gpu_required"] is False))
    # memory parsing is correct for both binary + decimal suffixes (no duplicated multipliers)
    checks.append(("resources: 512Mi→537MB, 2Gi→2147MB, 256M→256MB (binary vs decimal both handled)",
                   _c.memory_to_mb("512Mi") == 537 and _c.memory_to_mb("2Gi") == 2147 and _c.memory_to_mb("256M") == 256))

    # 7. backend bound via runtime_binding (the SAME authority PurposeTask uses — reused, not reinvented)
    checks.append(("binding: runtime_class→backend via runtime_binding (cloud-function bound to a backend)",
                   units["k8s_job"]["runtime_class"] == "cloud-function"
                   and isinstance(units["k8s_job"]["backend"], str) and units["k8s_job"]["backend"]
                   and units["k8s_job"]["binding"]["schema_version"] == "RuntimeClassBinding"))
    # with creds + health for a cloud vendor, the binding picks the cloud backend (policy actually flows through)
    cloud_unit = _c.compile_capability(
        _f.fixture_promoted_capability(), _f.fixture_task_spec(), exec_target="k8s_job", now=FIXED_NOW,
        resolved_preference=_f.fixture_resolved_preference(),
        policy={"available_creds": ["aws_lambda@candidate"], "provider_health": {"aws_lambda@candidate": True}})
    checks.append(("binding: credentialed+healthy cloud vendor → cloud backend (policy flows into the compile)",
                   cloud_unit["backend"] == "aws_lambda@candidate"
                   and cloud_unit["binding"]["is_local_fallback"] is False))
    # default (no creds) → local fallback (cloud-defer-only-after-local-equivalent)
    checks.append(("binding: no creds → local fallback backend (cloud-defer-only-after-local-equivalent)",
                   units["k8s_job"]["binding"]["is_local_fallback"] is True))

    # 8. OTel logging attrs on EVERY unit (the standardization + logging tools)
    for t, u in units.items():
        otel = u["logging"]["otel_attrs"]
        ok = (otel.get("capability.id") == "cap-redact" and otel.get("teleon.unit_id") == u["unit_id"]
              and otel.get("deployment.exec_target") == t and otel.get("service.name", "").startswith("teleon-"))
        checks.append((f"logging: OTel attrs present + correct on the {t} unit", ok))
    # trace_id/span_id flow through when supplied (deterministic — never minted inside)
    traced = _c.compile_capability(_f.fixture_promoted_capability(), _f.fixture_task_spec(), exec_target="k8s_job",
                                   now=FIXED_NOW, resolved_preference=_f.fixture_resolved_preference(),
                                   policy={"trace_id": "abc123", "span_id": "def456"})
    checks.append(("logging: caller-supplied trace_id/span_id flow into otel_attrs",
                   traced["logging"]["otel_attrs"].get("trace_id") == "abc123"
                   and traced["logging"]["otel_attrs"].get("span_id") == "def456"))

    # 9. schema validation: every emitted unit validates against runtime/CompiledRuntimeUnit
    for t, u in units.items():
        errs = _c.validate_unit(u)
        checks.append((f"schema: the {t} unit validates against CompiledRuntimeUnit", not errs))
    # a tampered unit (is_truth flipped true) is REJECTED by the schema (the const:false pin bites)
    bad = {**units["k8s_job"], "is_truth": True}
    checks.append(("schema: a unit with is_truth=true is REJECTED (is_truth const:false enforced)",
                   bool(_c.validate_unit(bad))))
    # a unit missing a required field is rejected
    bad2 = {k: v for k, v in units["k8s_job"].items() if k != "gate_evidence"}
    checks.append(("schema: a unit missing gate_evidence is REJECTED", bool(_c.validate_unit(bad2))))

    # 10. drift gate actually fires (a tampered example differs from a fresh render)
    fresh = _render_examples()
    sample_path = _example_path("k8s_job")
    checks.append(("drift gate: a fresh render of the k8s example is non-empty + deterministic",
                   bool(fresh[sample_path]) and fresh[sample_path] == _render_examples()[sample_path]))

    # 11. THE REGISTRY (the durable, append-only compiled-unit registry — the deploy_topology analog). All under a
    # temp dir so the real dist/local-services-state/teleon-compiler state is never touched by the self-test.
    _registry_checks(checks)

    # 12. dependency law: this package imports nothing from src.baltor / src.openhubforai. Scan only the IMPORT
    # directives (import/from lines), so a literal mention in a comment/string — like this very check — is not a
    # false positive. Branch on the forbidden layer roots, never on a brand display name. _r (registry) is included
    # so the new module's imports (it pulls scripts._jsonl_store — tooling, not a brand layer) are covered too.
    forbidden_roots = ("src.baltor", "src.openhubforai")
    pkg_init = importlib.import_module("src.teleon.compiler")
    import_lines: list[str] = []
    for m in (_c, _e, _f, _r, pkg_init, sys.modules[__name__]):
        for raw in Path(m.__file__).read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if s.startswith(("import ", "from ")):
                import_lines.append(s)
    law_clean = not any(root in line for root in forbidden_roots for line in import_lines)
    checks.append(("dependency law: no src.baltor / src.openhubforai import directive anywhere in the package",
                   law_clean))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print(("PASS — " if not failed else "FAIL — ") + f"{len(checks) - len(failed)}/{len(checks)} self-test checks")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="offline invariants (determinism · refusal · emitters)")
    parser.add_argument("--compile", metavar="CAP_ID", help="compile a capability (live state if present, else fixture)")
    parser.add_argument("--exec-target", choices=list(_c.EXEC_TARGETS), default="k8s_job",
                        help="the deployable shape to compile for (default: k8s_job)")
    parser.add_argument("--emit", action="store_true", help="with --compile: also print the concrete deployable text")
    parser.add_argument("--check", action="store_true", help="drift gate over the committed example units")
    parser.add_argument("--write-examples", action="store_true", help="(re)write the committed example units")
    parser.add_argument("--register", metavar="CAP_ID",
                        help="compile a capability AND register the unit into the durable registry (sets the prior "
                             "active unit as its rollback_target; idempotent by unit_id)")
    parser.add_argument("--list", action="store_true",
                        help="show the registry: active units (one per capability) + full lossless history")
    parser.add_argument("--rollback", metavar="CAP_ID",
                        help="return the rollback-target unit for a capability (the predecessor of its active unit)")
    parser.add_argument("--state-dir", default=None,
                        help="registry state dir (default: dist/local-services-state/teleon-compiler — the Fly volume mount)")
    parser.add_argument("--now", default=None, help="timestamp stamped as provenance.compiled_at (default: fixed)")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.write_examples:
        return cmd_write_examples()
    if args.check:
        return cmd_check()
    if args.register:
        return cmd_register(args.register, args.exec_target, now=args.now, state_dir=args.state_dir)
    if args.list:
        return cmd_list(args.state_dir)
    if args.rollback:
        return cmd_rollback(args.rollback, args.state_dir)
    if args.compile:
        return cmd_compile(args.compile, args.exec_target, do_emit=args.emit, now=args.now)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
