#!/usr/bin/env python3
"""check_repo_emit — proof for the Teleon "emit a customer repo" output (GitOps capability delivery).

Teleon can output a compiled capability not as a worker IT runs, but as a self-contained REPOSITORY the customer runs
through THEIR OWN dev→test→prod pipeline + CI/CD (GitHub or GitLab). This compiles a real capability and proves the
emitted repo bundle is complete + governed. serves_truth=false.

  --self-test   compile a fixture capability -> emit_repo(github|gitlab) -> validate the bundle
  --emit [dir]  write a repo bundle for the fixture capability to <dir> (default ./dist/teleon-capability-repo)
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_repo_emit.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import os
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _compiled_unit(exec_target: str = "local_process") -> dict:
    from src.teleon.compiler.compile import compile_capability
    from src.teleon.compiler import fixtures
    return compile_capability(fixtures.fixture_promoted_capability(), fixtures.fixture_task_spec(),
                              exec_target=exec_target, now="2026-06-11T00:00:00Z",
                              resolved_preference=fixtures.fixture_resolved_preference(), receipt_refs=["llmrcpt_fixture_0001"])


def _self_test() -> int:
    from src.teleon.compiler.emit import emit_repo
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    unit = _compiled_unit()
    gh = emit_repo(unit, scm="github")
    gl = emit_repo(unit, scm="gitlab")
    ck("emits a multi-file repo bundle (not a single worker config)", len(gh) >= 7 and isinstance(gh, dict))
    ck("carries the capability CONTRACT (capability.json) + runner + Dockerfile + README + governance",
       all(p in gh for p in ("capability.json", "run.sh", "Dockerfile", "README.md", "GOVERNANCE.md", "tests/test_capability_contract.py")))
    ck("GitHub target ships a dev->test->prod CI workflow", ".github/workflows/ci.yml" in gh and "deploy-prod" in gh[".github/workflows/ci.yml"])
    ck("GitLab target ships a .gitlab-ci.yml with stages", ".gitlab-ci.yml" in gl and "stages:" in gl[".gitlab-ci.yml"])
    import json
    contract = json.loads(gh["capability.json"])
    ck("contract is governed (serves_truth=false) + names the capability + budgets", contract["serves_truth"] is False and contract["capability_id"] and contract["budgets"]["timeout_s"] > 0)
    ck("secrets are REFS only — no inline secret VALUES in any file", all("sk-or-" not in c and "=\nLLM_API_KEY=sk" not in c for c in gh.values()))
    ck("env refs are surfaced for the customer's CI secrets (.env.example)", ".env.example" in gh)
    ck("an unknown scm is rejected", _rejects(emit_repo, unit))
    print("\n" + ("PASS - check_repo_emit: Teleon can emit a compiled capability as a GitOps REPOSITORY (capability.json "
                  "contract + runner + Dockerfile + dev→test→prod CI for GitHub/GitLab + governance) the customer runs in "
                  "THEIR pipeline — compute external, no lock-in, brain keeps the metadata. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _rejects(fn, unit) -> bool:
    try:
        fn(unit, scm="bitbucket-nope"); return False
    except ValueError:
        return True


def _emit(dest: Path) -> int:
    from src.teleon.compiler.emit import emit_repo
    files = emit_repo(_compiled_unit(), scm="github")
    for rel, content in files.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    print(f"wrote {len(files)} files -> {dest.relative_to(REPO) if dest.is_relative_to(REPO) else dest}")
    print("  the customer: git init && git add -A && git commit && git push  -> their CI/CD runs dev→test→prod")
    return 0


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--emit" in argv:
        i = argv.index("--emit")
        dest = Path(argv[i + 1]) if i + 1 < len(argv) and not argv[i + 1].startswith("-") else _resource("dist/teleon-capability-repo")
        return _emit(dest)
    print("usage: check_repo_emit.py --self-test | --emit [dir]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
