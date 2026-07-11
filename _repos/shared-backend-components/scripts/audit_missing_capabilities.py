#!/usr/bin/env python3
"""scripts.audit_missing_capabilities — make the experiment factory SELF-AWARE about blockers. Probe the keys,
endpoints, harness tools, and runtimes actually present on this machine; for every MISSING one report what it
unlocks, the exact env-var/install, a safe test command, and the current fallback — so "blocked" becomes an
actionable accelerator request, never a dead stop (candidate-only tooling).

Owner (2026-07-09): the harness must stop hiding behind "I built the kernel" — it must continuously say what is
missing, what it would unlock, and what can run right now. This is that auditor. It NEVER prints a secret value —
only whether a key is present (env or gitignored key-file). Everything it emits is candidate=true /
serves_truth=false.

    python3 scripts/audit_missing_capabilities.py --self-test
    python3 scripts/audit_missing_capabilities.py --run     # write the missing-capabilities + accelerator report
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
AUDIT_JSON_REL = "data/dev-intel/capability_audit/missing_capabilities.json"
ACCEL_JSONL_REL = "data/dev-intel/capability_audit/accelerator_requests.jsonl"
REPORT_MD_REL = "docs/MISSING_CAPABILITIES_AND_ACCELERATORS.md"

# ── env keys: presence-only (never a value); each row says what it UNLOCKS for THIS factory ───────────────────
_ENV_KEYS: list[dict[str, str]] = [
    {"name": "ANTHROPIC_API_KEY", "unlocks": "frontier Claude lane — passes the BARE lane on LARGE buildouts "
     "(K8s worker / pipeline / DAG) where free-tier gpt-oss fails, turning capability_lift into real token-SAVINGS",
     "priority": "HIGHEST", "safe_test": "printenv ANTHROPIC_API_KEY >/dev/null && echo present",
     "fallback": "OpenRouter free-tier gpt-oss-120b (fails most LARGE bare builds -> no baseline)"},
    {"name": "OPENAI_API_KEY", "unlocks": "frontier GPT lane — same large-task baseline unlock as Claude",
     "priority": "HIGH", "safe_test": "printenv OPENAI_API_KEY >/dev/null && echo present",
     "fallback": "OpenRouter free-tier"},
    {"name": "NVIDIA_API_KEY", "unlocks": "GLM-5.2 lane via NVIDIA Build (frontier-ish, OFF the throttled free "
     "pool) — a capable bare-lane model for large tasks", "priority": "HIGH",
     "safe_test": "printenv NVIDIA_API_KEY >/dev/null && echo present", "fallback": "OpenRouter free-tier"},
    {"name": "GEMINI_API_KEY", "unlocks": "frontier Gemini lane", "priority": "MEDIUM",
     "safe_test": "printenv GEMINI_API_KEY >/dev/null && echo present", "fallback": "OpenRouter free-tier"},
    {"name": "GITHUB_TOKEN", "unlocks": "RAISES GitHub API limits (unauth 60/hr + 10 search/min -> auth 5000/hr "
     "+ 30 search/min) for SCALE ingestion of real OSS AI-built apps + issues/PRs/CI as source-backed prompts. "
     "Basic public repo search/clone works WITHOUT a token (low volume).", "priority": "MEDIUM",
     "safe_test": "printenv GITHUB_TOKEN >/dev/null && echo present",
     "fallback": "unauthenticated GitHub search/clone at 60/hr (works now, just rate-limited)"},
    {"name": "JIRA_API_TOKEN", "unlocks": "enterprise ticket mining -> source-backed project tasks",
     "priority": "MEDIUM", "safe_test": "printenv JIRA_API_TOKEN >/dev/null && echo present",
     "fallback": "synthetic prompts only"},
    {"name": "AWS_ACCESS_KEY_ID", "unlocks": "real cloud-function event tests (S3/SQS/Lambda) once LocalStack "
     "or a sandbox account is present", "priority": "LOW",
     "safe_test": "printenv AWS_ACCESS_KEY_ID >/dev/null && echo present", "fallback": "pure-local event sims"},
    {"name": "HUGGINGFACE_TOKEN", "unlocks": "gated dataset/model pulls for ML-pipeline tasks", "priority": "LOW",
     "safe_test": "printenv HUGGINGFACE_TOKEN >/dev/null && echo present", "fallback": "synthetic ML fixtures"},
]
# key-FILE presence (gitignored) counts as available too — checked without reading values.
_KEY_FILES: list[dict[str, str]] = [
    {"name": "OPENROUTER_POOL", "path": ".agent/openrouter_keys.txt",
     "unlocks": "the LLM A/B + buildout A/B + generation waves; MORE keys = less throttling on LARGE multi-turn "
     "builds (today's 120B run exhausted mid-A/B)", "priority": "HIGH"},
    {"name": "KAGGLE_TOKEN", "path_home": ".kaggle/access_token",
     "unlocks": "Kaggle notebook / Meta-Kaggle mining into pipeline+ML tasks", "priority": "LOW"},
    {"name": "RAPIDAPI_POOL", "path": ".agent/rapidapi_keys.txt",
     "unlocks": "RapidAPI Hub (thousands of API endpoints) for enrichment/search/programming tasks -> user-"
     "configurable API-wrapper primitives (credentials referenced by ENV NAME, never embedded)", "priority": "MEDIUM"},
]
# ── tools: which() presence + what each unlocks; install hint when missing ────────────────────────────────────
_TOOLS: list[dict[str, str]] = [
    {"bin": "docker", "unlocks": "container isolation for UNTRUSTED live-lane model code (buildouts currently run "
     "in a temp dir only — a real safety gap) + api_service/postgres families", "install": "https://docs.docker.com"},
    {"bin": "kind", "unlocks": "K8s worker realism O5/O6 (real cluster deploy/probe/crash-recovery) — today the "
     "worker LOGIC is tested as a subprocess only", "install": "go install sigs.k8s.io/kind@latest"},
    {"bin": "kubectl", "unlocks": "apply/inspect K8s manifests (with kind)", "install": "https://kubernetes.io/docs/tasks/tools/"},
    {"bin": "helm", "unlocks": "Helm-chart IaC families", "install": "https://helm.sh/docs/intro/install/"},
    {"bin": "terraform", "unlocks": "Terraform-module IaC families", "install": "https://developer.hashicorp.com/terraform/downloads"},
    {"bin": "localstack", "unlocks": "AWS-event cloud-function families (S3/SQS/Lambda emulation)", "install": "pipx install localstack"},
    {"bin": "uv", "unlocks": "fast dependency installs for non-stdlib (FastAPI/DuckDB/dbt) buildouts", "install": "pipx install uv"},
    {"bin": "npm", "unlocks": "Node/Express/Next.js buildout families", "install": "https://nodejs.org"},
    {"bin": "go", "unlocks": "Go HTTP-service buildout families", "install": "https://go.dev/dl/"},
    {"bin": "docker-compose", "unlocks": "multi-service (DB+queue+app) B5 integration buildouts", "install": "bundled with docker"},
    {"bin": "playwright", "unlocks": "browser_workflow_service families (real browser drives)", "install": "pip install playwright && playwright install"},
]
# ── local LLM endpoints (open-weight harness lane) ────────────────────────────────────────────────────────────
_LOCAL_ENDPOINTS: list[dict[str, str]] = [
    {"name": "ollama", "url": "http://localhost:11434/api/tags",
     "unlocks": "local open-weight generation lane (keyless, no rate limit) — but owner law: NO local models that "
     "crash the PC; use Ollama CLOUD, not local heavy models"},
    {"name": "lm_studio", "url": "http://localhost:1234/v1/models", "unlocks": "local OpenAI-compatible lane"},
    {"name": "vllm_openai", "url": "http://localhost:8000/v1/models", "unlocks": "local vLLM OpenAI-compatible lane"},
]
# receipt globs -> current experiment coverage
_COVERAGE: list[dict[str, str]] = [
    {"key": "buildout_ab_runs", "glob": "*_buildout_ab.json", "means": "executed buildout A/B receipts"},
    {"key": "buildout_replicate_distributions", "glob": "*_replicates.json", "means": "n-run savings distributions"},
    {"key": "project_ab_runs", "glob": "*live_agent_ab.json", "means": "executed project A/B receipts"},
    {"key": "savings_ledgers", "glob": "latest_savings_results.json", "means": "honest savings ledgers"},
    {"key": "token_savings_ab", "glob": "token_savings_ab_receipt.json", "means": "function-level A/B receipts"},
]


def _env_present(name: str) -> bool:
    if os.environ.get(name):
        return True
    for fn in (".env", ".env.local"):                       # presence-only scan of a gitignored dotenv (never the value)
        p = _sbc_boot.parent / fn
        try:
            if p.exists() and any(ln.strip().startswith(name + "=") and ln.split("=", 1)[1].strip()
                                  for ln in p.read_text(encoding="utf-8").splitlines()):
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _keyfile_present(spec: dict[str, str]) -> bool:
    if "path" in spec:
        for base in (_sbc_boot, _sbc_boot.parent, *_sbc_boot.parents):
            if (base / spec["path"]).exists() and (base / spec["path"]).stat().st_size > 0:
                return True
        return False
    if "path_home" in spec:
        p = Path.home() / spec["path_home"]
        return p.exists() and p.stat().st_size > 0
    return False


def audit_env_keys() -> list[dict[str, Any]]:
    out = []
    for k in _ENV_KEYS:
        out.append({**k, "present": _env_present(k["name"]), "kind": "env_key"})
    for kf in _KEY_FILES:
        out.append({"name": kf["name"], "unlocks": kf["unlocks"], "priority": kf.get("priority", "MEDIUM"),
                    "present": _keyfile_present(kf), "kind": "key_file",
                    "safe_test": f"test -s {kf.get('path', kf.get('path_home'))} && echo present",
                    "fallback": "—"})
    return out


def _version(binary: str) -> str | None:
    for flag in ("--version", "version", "-v"):
        try:
            r = subprocess.run([binary, flag], capture_output=True, text=True, timeout=5,
                               stdin=subprocess.DEVNULL)
            line = (r.stdout or r.stderr or "").splitlines()
            if line:
                return line[0][:80]
        except Exception:  # noqa: BLE001
            continue
    return None


def audit_tools() -> list[dict[str, Any]]:
    out = []
    for t in _TOOLS:
        path = shutil.which(t["bin"])
        out.append({"bin": t["bin"], "installed": path is not None, "version": _version(t["bin"]) if path else None,
                    "unlocks": t["unlocks"], "install": t["install"]})
    return out


def audit_local_endpoints() -> list[dict[str, Any]]:
    import urllib.request  # noqa: PLC0415
    out = []
    for e in _LOCAL_ENDPOINTS:
        available, detail = False, None
        try:
            with urllib.request.urlopen(e["url"], timeout=2) as r:  # noqa: S310 localhost only
                available = r.status == 200
                body = r.read(4000).decode("utf-8", "replace")
                detail = body[:200]
        except Exception as exc:  # noqa: BLE001
            detail = type(exc).__name__
        out.append({"name": e["name"], "url": e["url"], "available": available, "unlocks": e["unlocks"],
                    "detail": detail})
    return out


def audit_harness_backends() -> dict[str, Any]:
    try:
        from scripts.buildout_agent_backends import probe_backends  # noqa: PLC0415  reuse, don't duplicate
        return probe_backends()
    except Exception as exc:  # noqa: BLE001
        return {"error": type(exc).__name__, "n_available": 0}


def audit_coverage() -> dict[str, Any]:
    root = resource("data/dev-intel")
    cov = {}
    for c in _COVERAGE:
        cov[c["key"]] = {"count": len(list(root.rglob(c["glob"]))) if root.exists() else 0, "means": c["means"]}
    return cov


def audit_runtime_isolation(tools: list[dict[str, Any]]) -> dict[str, Any]:
    have = {t["bin"]: t["installed"] for t in tools}
    return {"ephemeral_tempdir": True,  # always available (buildout_forge uses it)
            "docker_container_isolation": have.get("docker", False),
            "kind_k8s_cluster": have.get("kind", False) and have.get("kubectl", False),
            "localstack_aws": have.get("localstack", False),
            "note": ("buildouts run in an ephemeral tempdir today; UNTRUSTED live-lane model code should run under "
                     "Docker isolation" + (" (available — a wiring gap to close)" if have.get("docker") else
                                           " (docker MISSING — live untrusted lane is a safety blocker)"))}


def accelerator_requests(env: list, tools: list, endpoints: list) -> list[dict[str, Any]]:
    """The actionable list: MISSING high-value items, what each unlocks. This is what the owner acts on."""
    reqs = []
    for k in env:
        if not k["present"] and k.get("priority") in ("HIGHEST", "HIGH"):
            reqs.append({"missing": k["name"], "kind": k["kind"], "priority": k["priority"],
                         "unlocks": k["unlocks"], "how": k.get("safe_test", ""), **BOUNDARY})
    for t in tools:
        if not t["installed"] and any(w in t["unlocks"] for w in ("K8s", "container", "IaC", "AWS-event")):
            reqs.append({"missing": t["bin"], "kind": "tool", "priority": "MEDIUM",
                         "unlocks": t["unlocks"], "how": t["install"], **BOUNDARY})
    reqs.sort(key=lambda r: {"HIGHEST": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(r["priority"], 4))
    return reqs


def run_audit() -> dict[str, Any]:
    env = audit_env_keys()
    tools = audit_tools()
    endpoints = audit_local_endpoints()
    backends = audit_harness_backends()
    coverage = audit_coverage()
    isolation = audit_runtime_isolation(tools)
    reqs = accelerator_requests(env, tools, endpoints)
    frontier_present = any(k["present"] for k in env if k.get("priority") in ("HIGHEST", "HIGH")
                           and "frontier" in k["unlocks"])
    questions = {
        "what_speeds_us_up_most": ("A FRONTIER model key (ANTHROPIC_API_KEY / OPENAI_API_KEY / NVIDIA_API_KEY GLM) "
                                   "— it passes the BARE lane on LARGE tasks, converting capability_lift into real "
                                   "token-SAVINGS. This is the #1 bottleneck." if not frontier_present else
                                   "A frontier key is present — scale replicates + genomes next."),
        "what_blocks_real_project_execution": ("Nothing for pure-local stdlib tasks (they run now). Docker isolation "
                                               "for UNTRUSTED live-lane code; kind for full K8s realism."),
        "what_blocks_10k_scale": "A frontier key WITH quota (throughput) + Docker for parallel per-task isolation.",
        "what_blocks_hy3_cloud_generation": "More OpenRouter keys / a dedicated generation key (free tier throttles).",
        "what_blocks_local_open_weight_harnesses": ("An Ollama/LM-Studio endpoint on localhost (none reachable now); "
                                                    "owner law: use Ollama CLOUD, not heavy local models."),
        "what_can_run_right_now": ("Pure-local buildout A/Bs (vendor / ops-API / pipeline-DAG / queue-worker) on the "
                                   "OpenRouter free pool; the decomposer; the savings ledger; codex/aider/opencode "
                                   "backend lanes."),
    }
    return {"record_type": "missing_capability_audit", "env_keys": env, "tools": tools,
            "local_endpoints": endpoints, "harness_backends": backends, "runtime_isolation": isolation,
            "experiment_coverage": coverage, "accelerator_requests": reqs,
            "n_accelerators": len(reqs), "frontier_model_present": frontier_present,
            "summary_questions": questions, **BOUNDARY}


def render_markdown(a: dict[str, Any]) -> str:
    L = ["# Missing Capabilities & Accelerators", "",
         "> Generated by `scripts/audit_missing_capabilities.py`. Presence-only — **no secret value is ever read "
         "or printed**. `serves_truth=false`.", "",
         f"**Frontier model present: {'YES' if a['frontier_model_present'] else 'NO'}** · "
         f"**{a['n_accelerators']} accelerator requests** · harness backends available: "
         f"{a['harness_backends'].get('n_available', '?')}", "",
         "## Top accelerators (provide these → unlock this)", "",
         "| Missing | Priority | Unlocks | How |", "|---|---|---|---|"]
    for r in a["accelerator_requests"]:
        L.append(f"| `{r['missing']}` | {r['priority']} | {r['unlocks'][:150]} | {r['how'][:60]} |")
    L += ["", "## Keys / endpoints (presence only)", "", "| Name | Present | Unlocks |", "|---|---|---|"]
    for k in a["env_keys"]:
        L.append(f"| {k['name']} | {'✅' if k['present'] else '❌'} | {k['unlocks'][:120]} |")
    L += ["", "## Tools", "", "| Tool | Installed | Version | Unlocks |", "|---|---|---|---|"]
    for t in a["tools"]:
        L.append(f"| {t['bin']} | {'✅' if t['installed'] else '❌'} | {t['version'] or '—'} | {t['unlocks'][:90]} |")
    L += ["", "## Runtime isolation", ""]
    for k, v in a["runtime_isolation"].items():
        L.append(f"- **{k}**: {v}")
    L += ["", "## Current experiment coverage (executed receipts)", ""]
    for k, v in a["experiment_coverage"].items():
        L.append(f"- **{k}**: {v['count']} ({v['means']})")
    L += ["", "## The six questions", ""]
    for q, ans in a["summary_questions"].items():
        L.append(f"- **{q.replace('_', ' ')}** → {ans}")
    return "\n".join(L)


def emit() -> dict[str, str]:
    a = run_audit()
    j = resource(AUDIT_JSON_REL)
    j.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps(a, indent=2, sort_keys=True), encoding="utf-8")
    aj = resource(ACCEL_JSONL_REL)
    aj.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in a["accelerator_requests"]), encoding="utf-8")
    md = resource(REPORT_MD_REL)
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render_markdown(a), encoding="utf-8")
    return {"json": str(j), "accelerators_jsonl": str(aj), "md": str(md),
            "n_accelerators": str(a["n_accelerators"]), "frontier_present": str(a["frontier_model_present"])}


def self_test() -> bool:
    """Mutation-gated: probes are real (which/env/urlopen); a bogus env key reads ABSENT; NO secret value is ever
    captured (presence is a bool); the report has the required sections + the six questions."""
    assert _env_present("NONEXISTENT_FAKE_KEY_ZZZ") is False, "a bogus key must read absent"
    a = run_audit()
    assert a["record_type"] == "missing_capability_audit" and a["serves_truth"] is False
    # presence is strictly boolean — proves we never leak a value into the record.
    for k in a["env_keys"]:
        assert isinstance(k["present"], bool), "env-key presence must be a bool (no value leakage)"
    assert set(a["summary_questions"]) >= {"what_speeds_us_up_most", "what_can_run_right_now"}
    assert isinstance(a["tools"], list) and any(t["bin"] == "docker" for t in a["tools"])
    assert isinstance(a["n_accelerators"], int)
    md = render_markdown(a)
    assert "Missing Capabilities & Accelerators" in md and "The six questions" in md
    avail = a["harness_backends"].get("n_available", 0)
    print(f"OK audit_missing_capabilities self-test: real probes (env presence-only, {len(a['tools'])} tools, "
          f"{len(a['local_endpoints'])} local endpoints, {avail} harness backends); {a['n_accelerators']} "
          f"accelerator requests; frontier_present={a['frontier_model_present']}; no secret values captured; "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit missing keys/tools/runtimes -> accelerator requests.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        paths = emit()
        print(json.dumps(paths, indent=2))
        print("\n" + render_markdown(run_audit()))
        return
    self_test()


if __name__ == "__main__":
    main()
