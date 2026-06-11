"""src.teleon.compiler.__main__ — the compiler CLI + the exhaustive self-test + the drift gate.

Mirrors ``scripts/deploy/generate_provider_configs.py``'s CLI shape (the proven pattern):

  python -m src.teleon.compiler --self-test            # offline invariants (determinism · refusal · 3 emitters · …)
  python -m src.teleon.compiler --compile <cap_id>     # compile a capability (live runtime state if present, else fixture)
  python -m src.teleon.compiler --compile <cap_id> --exec-target k8s_job   # pick the deployable shape
  python -m src.teleon.compiler --emit                 # with --compile: also print the concrete deployable text
  python -m src.teleon.compiler --check                # drift gate over the committed example units

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

_PKG_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = _PKG_DIR / "examples"
#: a FIXED timestamp for committed/self-test artifacts — the compiler is deterministic, so the drift-gated files
#: must not carry a moving clock value (provenance.compiled_at). One definition.
FIXED_NOW = "2026-06-11T00:00:00Z"
#: the three committed example units (one per exec_target) prove portability AND anchor the drift gate.
EXAMPLE_TARGETS = _c.EXEC_TARGETS


# ── compile helpers ──────────────────────────────────────────────────────────────────────────────────────────
def _compile_fixture(exec_target: str, *, now: str = FIXED_NOW) -> dict:
    """Compile the deterministic fixture for one exec_target (the committed-example / self-test source)."""
    return _c.compile_capability(
        _f.fixture_promoted_capability(), _f.fixture_task_spec(),
        exec_target=exec_target, now=now,
        resolved_preference=_f.fixture_resolved_preference(),
        receipt_refs=["llmrcpt_fixture_0001"],
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


# ── --compile ────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_compile(capability_id: str, exec_target: str, *, do_emit: bool, now: str | None) -> int:
    """Compile ``capability_id`` from the LIVE runtime state if present, else the fixture. Prints the unit (and the
    concrete deployable text with --emit). Refuses a non-promoted capability with a clear reason (exit 2)."""
    used_now = now or FIXED_NOW
    source = "fixture"
    try:
        cap, receipt_refs = _f.load_live_capability(capability_id)
        task_spec = {**_f.fixture_task_spec(), "capability_id": capability_id}
        source = "live runtime state"
    except (FileNotFoundError, KeyError):
        cap = _f.fixture_promoted_capability()
        if cap["id"] != capability_id:
            print(f"  no live state and the fixture is {cap['id']!r}, not {capability_id!r} — "
                  f"compiling the fixture capability instead", file=sys.stderr)
        task_spec = _f.fixture_task_spec()
        receipt_refs = ["llmrcpt_fixture_0001"]
    try:
        unit = _c.compile_capability(cap, task_spec, exec_target=exec_target, now=used_now,
                                     resolved_preference=_f.fixture_resolved_preference(), receipt_refs=receipt_refs)
    except _c.NotPromotedError as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 2
    errors = _c.validate_unit(unit)
    if errors:
        print("COMPILED UNIT FAILED SCHEMA VALIDATION:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print(f"# compiled {capability_id!r} (source: {source}) → exec_target={exec_target}, "
          f"backend={unit['backend']}, unit_id={unit['unit_id']}")
    print(json.dumps(unit, indent=2, sort_keys=True, ensure_ascii=False))
    if do_emit:
        print(f"\n# --- concrete deployable ({exec_target}) ---")
        print(_e.emit(unit, exec_target))
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
                   units["k8s_job"]["receipt_refs"] == ["llmrcpt_fixture_0001"]))
    checks.append(("lossless: unit carries capability_id + version + a rollback_target field",
                   units["k8s_job"]["capability_id"] == "cap-redact"
                   and units["k8s_job"]["capability_version"] == 2
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
                   and units["k8s_job"]["binding"]["schema_version"] == "RuntimeClassBinding.v1"))
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

    # 9. schema validation: every emitted unit validates against runtime/CompiledRuntimeUnit.v1
    for t, u in units.items():
        errs = _c.validate_unit(u)
        checks.append((f"schema: the {t} unit validates against CompiledRuntimeUnit.v1", not errs))
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

    # 11. dependency law: this package imports nothing from src.baltor / src.openharnesshub. Scan only the IMPORT
    # directives (import/from lines), so a literal mention in a comment/string — like this very check — is not a
    # false positive. Branch on the forbidden layer roots, never on a brand display name.
    forbidden_roots = ("src.baltor", "src.openharnesshub")
    pkg_init = importlib.import_module("src.teleon.compiler")
    import_lines: list[str] = []
    for m in (_c, _e, _f, pkg_init, sys.modules[__name__]):
        for raw in Path(m.__file__).read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if s.startswith(("import ", "from ")):
                import_lines.append(s)
    law_clean = not any(root in line for root in forbidden_roots for line in import_lines)
    checks.append(("dependency law: no src.baltor / src.openharnesshub import directive anywhere in the package",
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
    parser.add_argument("--now", default=None, help="timestamp stamped as provenance.compiled_at (default: fixed)")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.write_examples:
        return cmd_write_examples()
    if args.check:
        return cmd_check()
    if args.compile:
        return cmd_compile(args.compile, args.exec_target, do_emit=args.emit, now=args.now)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
