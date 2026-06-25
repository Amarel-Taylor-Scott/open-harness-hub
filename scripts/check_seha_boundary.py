#!/usr/bin/env python3
"""scripts.check_seha_boundary — the deterministic monitor (Ornith reward-hacking defense, runtime form).

An autonomous/self-evolving worker (build_loop, a SEHA harness variant, the swarm) may NOT 'pass' by weakening the
verifier. This fails RED if a change touches the IMMUTABLE boundary — the proof gate, the access policy, the
monitor itself — or net-removes assertions from a check (a weakened test). Mutation lives INSIDE the boundary; the
boundary is not mutable by the mutator. Call it before any autonomous commit. See
docs/strategy/ornith-and-seha-2026-06-25.md.

  --self-test
  --check [--range A..B | --staged]   exit nonzero if the change violates the boundary
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: IMMUTABLE boundary — the verifier + governance. Only a human warrant (change-verification contract) may touch these.
PROTECTED = (
    "scripts/run_proofs.py",
    "scripts/flywheel_proof_modules.py",
    "scripts/check_seha_boundary.py",
    "architecture/access_policy.json",
    "src/teleon/runtime/access_policy.py",
)


def boundary_files(changed: list[str]) -> list[str]:
    return [f for f in changed if f in PROTECTED]


def _is_check_file(path: str) -> bool:
    return path.startswith("scripts/check_") or "self_test" in path or path.endswith("_test.py")


def weakened_checks(diff_text: str) -> list[tuple[str, int]]:
    """Net removal of `assert` lines inside a check/test file = a weakened verifier (reward-hacking signal)."""
    out: list[tuple[str, int]] = []
    cur: str | None = None
    rem = add = 0

    def flush() -> None:
        if cur and rem > add:
            out.append((cur, rem - add))

    for ln in diff_text.splitlines():
        if ln.startswith("+++ b/"):
            flush()
            path = ln[6:]
            cur = path if _is_check_file(path) else None
            rem = add = 0
        elif cur and ln.startswith("-") and not ln.startswith("---") and "assert" in ln:
            rem += 1
        elif cur and ln.startswith("+") and not ln.startswith("+++") and "assert" in ln:
            add += 1
    flush()
    return out


def _changed_and_diff(rng: str | None, staged: bool) -> tuple[list[str], str]:
    base = ["git", "diff"] + ([rng] if rng else (["--cached"] if staged else []))
    files = subprocess.run([*base[:2], "--name-only", *base[2:]], cwd=REPO, capture_output=True, text=True).stdout.split()
    diff = subprocess.run(base, cwd=REPO, capture_output=True, text=True).stdout
    return files, diff


def check(rng: str | None = None, staged: bool = False) -> int:
    files, diff = _changed_and_diff(rng, staged)
    bf = boundary_files(files)
    wk = weakened_checks(diff)
    if bf or wk:
        print("SEHA BOUNDARY VIOLATION (reward-hacking guard):")
        for f in bf:
            print(f"  immutable verifier/governance file modified: {f}")
        for f, n in wk:
            print(f"  check weakened: {f} (net -{n} assertions)")
        print("→ an autonomous worker may NOT weaken the boundary; route via human warrant (change-verification contract).")
        return 1
    print(f"SEHA boundary OK ({len(files)} files changed; none touch the immutable verifier/governance).")
    return 0


def self_test() -> int:
    assert boundary_files(["scripts/run_proofs.py", "scripts/foo.py"]) == ["scripts/run_proofs.py"]
    assert boundary_files(["scripts/foo.py"]) == []
    assert weakened_checks("+++ b/scripts/check_thing.py\n-    assert x == 1\n     pass\n"), "flag net assert removal in a check"
    assert not weakened_checks("+++ b/scripts/check_thing.py\n+    assert y == 2\n"), "adding asserts is fine"
    assert not weakened_checks("+++ b/scripts/app.py\n-    assert z\n"), "only check/test files are guarded"
    assert "scripts/run_proofs.py" in PROTECTED and "src/teleon/runtime/access_policy.py" in PROTECTED
    print("check_seha_boundary self-test: OK (protected-file + weakened-check detection)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        rng = argv[argv.index("--range") + 1] if "--range" in argv and argv.index("--range") + 1 < len(argv) else None
        return check(rng, "--staged" in argv)
    print("usage: check_seha_boundary.py --self-test | --check [--range A..B | --staged]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
