#!/usr/bin/env python3
"""Deploy preflight — one command that says GO / NO-GO before `fly deploy`.

Aggregates the deploy-CRITICAL invariants (the subset of the repo's ~390 checks that, if red,
make a cloud deploy unsafe or broken) into a single gate. It does NOT replace the per-service
self-tests — it answers the narrower question "is the deploy ARTIFACT set internally consistent
and free of the specific footguns the 2026-06-11 deep dive found?". Read-only; no network.

Checks (each → PASS/FAIL with a one-line reason):
  1. topology ↔ generated configs in sync (generate_provider_configs --check)
  2. every public web app carries OH_SHOWCASE_TOKEN in its secret set (no open origin in cloud)
  3. every stateful service has a volume mount AND no `[http_service]` (single-machine law)
  4. each backend service's persistence path is INSIDE its declared state_mount (no off-volume
     state — the class of bug that lost baltor/worker data)
  5. .dockerignore re-includes the registry catalog bundle (else the deployed catalog is empty)
  6. model_provider_graph.json is valid JSON and every node with a base_url is well-formed
  7. no secret VALUES embedded in any fly/*.toml or the compose file (only key names)
  8. the queue key is identical across topology, foundry, and every watch file
  9. each service's command module imports (smoke `python -c import`) — catches a broken deploy
     before it ships

Exit 0 = GO. Non-zero = NO-GO (printed reasons). `--json` for machine output.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
sys.path.insert(0, str(REPO))

#: the shared-backend-components root (holds ``scripts/``) — its parent-of-scripts must be on the child
#: PYTHONPATH so a spawned interpreter can ``import scripts.*``; the per-repo ``backend`` roots resolve
#: ``import src.<x>.*`` (mirrors scripts._repo_paths.install for a subprocess, which does not inherit sys.path).
_SBC_ROOT = Path(__file__).resolve().parents[2]


def _child_env() -> dict:
    """os.environ for a preflight subprocess, with PYTHONPATH extended to resolve scripts.* and src.<x>.*
    (a spawned python does NOT inherit the parent's sys.path, only PYTHONPATH). Fixes a false NO-GO where
    the import checks reported 'No module named scripts' purely because PYTHONPATH was unset in the child."""
    roots = [str(_SBC_ROOT)] + [str(p) for p in sorted((REPO / "_repos").glob("*/backend")) if p.is_dir()]
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        roots.append(existing)
    return {**os.environ, "PYTHONPATH": os.pathsep.join(roots)}

TOPOLOGY = _resource("architecture") / "deploy_topology.json"
FLY_DIR = _resource("fly")
COMPOSE = _resource("deploy") / "docker-compose.deploy.yml"
# The LIVE .dockerignore is at the build-context root (_repos/), which compose reaches via `context: ../..`.
# Docker never reads the monorepo-root file for this build, so the catalog-bundle guard must check this one.
DOCKERIGNORE = _resource("architecture").parents[1] / ".dockerignore"   # SBC/architecture -> SBC -> _repos/
PROVIDER_GRAPH = _resource("architecture") / "model_provider_graph.json"
CATALOG_BUNDLE_MARKER = "dist/sites/aidoneright-design"
SECRET_VALUE_SIGNATURES = ("sk-or-v1-", "sk-ant-", "ghp_", "AKIA")  # never in committed configs


def _result(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "ok": ok, "detail": detail}


def check_configs_in_sync() -> dict:
    proc = subprocess.run([sys.executable, str(_resource("scripts/deploy/generate_provider_configs.py")), "--check"],
                          cwd=REPO, capture_output=True, text=True, env=_child_env())
    ok = proc.returncode == 0
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
    return _result("configs_in_sync_with_topology", ok, tail[0])


def check_public_apps_tokened(topo: dict) -> dict:
    bad = []
    for svc in topo["services"]:
        if svc.get("public"):
            keys = [k for grp in svc.get("secret_groups", [])
                    for k in topo["secret_group_contents"].get(grp, [])]
            if "OH_SHOWCASE_TOKEN" not in keys:
                bad.append(svc["name"])
    return _result("public_apps_require_showcase_token", not bad,
                   "all public apps carry OH_SHOWCASE_TOKEN" if not bad
                   else f"open origin risk: {bad}")


def check_single_machine_law(topo: dict) -> dict:
    bad = []
    for svc in topo["services"]:
        if svc.get("state_mount") and svc.get("public"):
            # a stateful service that also serves a public proxy could be auto-scaled OUT → forked state
            bad.append(f"{svc['name']} (stateful AND public)")
    return _result("single_machine_law", not bad,
                   "no stateful service is publicly auto-scalable" if not bad else str(bad))


def check_state_paths_in_volume(topo: dict) -> dict:
    """Every persistence-path env on a service must live under that service's state_mount."""
    problems = []
    for svc in topo["services"]:
        mount = svc.get("state_mount")
        if not mount:
            continue
        for key, val in (svc.get("env") or {}).items():
            if not isinstance(val, str) or not val.startswith("/"):
                continue  # only absolute-path envs are state paths
            if not val.startswith(mount.rstrip("/") + "/") and val != mount:
                problems.append(f"{svc['name']}.{key}={val} not under {mount}")
    return _result("state_paths_inside_volume", not problems,
                   "all declared state paths ride the volume" if not problems else "; ".join(problems))


def check_dockerignore_bundle() -> dict:
    # The catalog bundle ships iff the LIVE (context-root) .dockerignore does not net-exclude it: either no
    # dist exclusion matches it, or it is excluded then re-included. (Was: required a `!` re-include line,
    # which false-fails a .dockerignore that simply never excludes dist — the _repos/ one.)
    text = DOCKERIGNORE.read_text(encoding="utf-8") if DOCKERIGNORE.is_file() else ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    reincluded = f"!{CATALOG_BUNDLE_MARKER}" in text
    dist_excluded = any(
        (ln.rstrip("/*") in ("dist", "shared-backend-components/dist")
         or ln.startswith("dist/") or ln.startswith("shared-backend-components/dist"))
        for ln in lines if not ln.startswith("!"))
    ok = reincluded or not dist_excluded
    return _result("dockerignore_reincludes_catalog_bundle", ok,
                   "catalog bundle ships in the image (not excluded by the context-root .dockerignore)" if ok
                   else "FATAL: dist excluded with no re-include — deployed catalog would be EMPTY")


def check_provider_graph_valid() -> dict:
    try:
        d = json.loads(PROVIDER_GRAPH.read_text(encoding="utf-8"))
    except Exception as exc:
        return _result("provider_graph_valid", False, f"invalid JSON: {exc}")
    nodes = d.get("nodes") or d.get("providers") or []
    bad = [n.get("id", "?") for n in nodes
           if n.get("base_url") and not re.match(r"^https?://", str(n["base_url"]))]
    return _result("provider_graph_valid", not bad,
                   f"{len(nodes)} nodes, base_urls well-formed" if not bad else f"bad base_url: {bad}")


def check_no_secret_values() -> dict:
    leaks = []
    for path in list(FLY_DIR.glob("*.toml")) + ([COMPOSE] if COMPOSE.is_file() else []):
        text = path.read_text(encoding="utf-8")
        for sig in SECRET_VALUE_SIGNATURES:
            if sig in text:
                leaks.append(f"{path.name}:{sig}")
    return _result("no_secret_values_in_configs", not leaks,
                   "configs carry key NAMES only" if not leaks else f"LEAK: {leaks}")


def check_queue_key_single_source(topo: dict) -> dict:
    from scripts.foundry.queues import DEFAULT_QUEUE_KEY
    scaling = next(s for s in topo["services"] if s["name"] == "worker")["scaling"]
    watch = topo.get("k8s_cross_checks", {}).get("queue_key_watch_files", [])
    bad = []
    if scaling["queue_key"] != DEFAULT_QUEUE_KEY:
        bad.append("topology≠foundry")
    for rel in watch:
        p = _resource(rel)
        if not p.is_file() or DEFAULT_QUEUE_KEY not in p.read_text(encoding="utf-8"):
            bad.append(rel)
    return _result("queue_key_single_source", not bad,
                   f"queue key {DEFAULT_QUEUE_KEY!r} consistent everywhere" if not bad else str(bad))


def check_command_modules_import(topo: dict) -> dict:
    """Smoke-import each service's command module so a broken import is caught pre-deploy."""
    problems = []
    seen = set()
    for svc in topo["services"]:
        cmd = svc.get("command") or []
        mod = None
        for i, tok in enumerate(cmd):
            if tok == "-m" and i + 1 < len(cmd):
                mod = cmd[i + 1]
                break
            if tok.endswith(".py"):
                mod = tok.replace("/", ".")[:-3]
                break
        if not mod or mod in seen:
            continue
        seen.add(mod)
        proc = subprocess.run([sys.executable, "-c", f"import importlib; importlib.import_module('{mod}')"],
                              cwd=REPO, capture_output=True, text=True, env=_child_env())
        if proc.returncode != 0:
            last = (proc.stderr.strip().splitlines() or [""])[-1]
            problems.append(f"{mod}: {last[:80]}")
    return _result("command_modules_import", not problems,
                   f"{len(seen)} command modules import clean" if not problems else "; ".join(problems))


def run() -> tuple[bool, list[dict]]:
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    results = [
        check_configs_in_sync(),
        check_public_apps_tokened(topo),
        check_single_machine_law(topo),
        check_state_paths_in_volume(topo),
        check_dockerignore_bundle(),
        check_provider_graph_valid(),
        check_no_secret_values(),
        check_queue_key_single_source(topo),
        check_command_modules_import(topo),
    ]
    return all(r["ok"] for r in results), results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    go, results = run()
    if args.json:
        print(json.dumps({"go": go, "checks": results}, indent=2))
    else:
        for r in results:
            print(f"  [{'GO ' if r['ok'] else 'NO-GO'}] {r['check']} — {r['detail']}")
        print(f"\n{'GO — deploy artifacts are consistent' if go else 'NO-GO — fix the above before fly deploy'}")
    return 0 if go else 1


if __name__ == "__main__":
    raise SystemExit(main())
