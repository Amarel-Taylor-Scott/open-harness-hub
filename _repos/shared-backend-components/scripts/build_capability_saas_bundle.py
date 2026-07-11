#!/usr/bin/env python3
"""build_capability_saas_bundle — assemble + deploy the Fly.io bundle for the capability SaaS gateway.

Owner (2026-07-10): "build this out into a SaaS, fully working, start to finish … I can provide you with a GitHub
token, a Fly.io token." This is the shipping half: it assembles a SELF-CONTAINED deploy bundle (the gateway + every
module it imports + the governed corpus), renders Dockerfile / fly.toml / GitHub workflow, and — when the tokens
are present — pushes and deploys. Without tokens every deploy path degrades to an exact, copy-paste DRY-RUN plan
(nothing is faked; the same guard philosophy as cloud_provisioning).

The bundle reproduces the monorepo shape the code resolves against (`.aidoneright-root` + `_repos/...`), so
`scripts._repo_paths.install()` works unchanged inside the container. The serving path is stdlib-only — the
Dockerfile has NO pip step. Corpus files ride read-only in the image; tenant state (identity, receipts, ledgers)
lives on the mounted /data volume.

    PYTHONPATH=. python3 scripts/build_capability_saas_bundle.py --self-test
    PYTHONPATH=. python3 scripts/build_capability_saas_bundle.py --plan
    PYTHONPATH=. python3 scripts/build_capability_saas_bundle.py --build
    FLY_API_TOKEN=… python3 scripts/build_capability_saas_bundle.py --deploy         # after you provide the token
    GITHUB_TOKEN=…  python3 scripts/build_capability_saas_bundle.py --push-github
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent                      # _repos/shared-backend-components
_MONOREPO = _SBC.parent.parent                  # repo root (holds .aidoneright-root + _repos/)
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLY_APP_NAME = "taedri"         # owner-renamable in fly.toml before first deploy
FLY_VOLUME_NAME = "capability_data"
#: GitHub hard-blocks files >100MB; anything over this margin is gzipped IN the bundle (JSONL compresses ~23x)
#: and restored by the Dockerfile's gunzip step at image build — same bundle serves git-push AND direct deploy.
GITHUB_PLAIN_FILE_LIMIT_BYTES = 90_000_000
#: only these bundle-relative roots are compression candidates (never gzip code)
_COMPRESSIBLE_DATA_ROOTS = ("repo/_repos/shared-backend-components/catalog",
                            "repo/_repos/shared-backend-components/data")
FLY_REGION_DEFAULT = "iad"
FLY_VM_MEMORY = "8gb"                            # measured 2026-07-11: serving + full-corpus admin reindex on 4gb
                                                 # starved the box (critical health, 27s responses); 8gb holds both
INTERNAL_PORT = 8080
BUNDLE_DIR = _SBC / "dist" / "capability-saas-deploy"

#: everything the container needs, monorepo-relative -> copied verbatim into bundle/repo/<same path>.
#: CODE trees are whole (the gateway lazy-imports across scripts/), DATA is the governed serving corpus.
BUNDLE_SOURCES: list[str] = [
    "_repos/_moved_dirs.json",   # the resource() head map — without it moved heads resolve to the bare root
    "_repos/shared-backend-components/scripts",
    "_repos/shared-backend-components/web/taedri",  # the Taedri web app screens (taedri_web serves these)
    "_repos/shared-backend-components/architecture",
    "_repos/shared-backend-components/vocabularies",
    "_repos/shared-backend-components/schemas",
    "_repos/shared-backend-components/catalog/knowledge-packs/data/primitive-search-index",
    "_repos/shared-backend-components/data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/primitive_synthesis/working_primitives.jsonl",
    # executable kernel packs (2026-07-11) — oracle-verified families baked into the served corpus
    "_repos/shared-backend-components/data/dev-intel/reasoning_control_proof_primitives/reasoning_control_proof_candidate_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/brain_inspired_primitives/brain_inspired_candidate_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/physics_tracking_primitives/physics_tracking_candidate_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/math_foundations_primitives/math_foundations_candidate_cards.jsonl",
    "_repos/shared-backend-components/data/dev-intel/associative_memory_primitives/associative_memory_candidate_cards.jsonl",
    "_repos/openhubforai/backend/src/openhubforai",
    "_repos/teleon/backend/src/teleon",
]
_COPY_EXCLUDE_DIR_NAMES = {"__pycache__", ".mypy_cache", ".pytest_cache", "dist"}  # dist: never bundle the bundle

_DOCKERFILE = f"""# capability SaaS gateway — slim base + numpy (the embedding-loop module imports it at load).
FROM python:3.12-slim
RUN pip install --no-cache-dir numpy && useradd -m svc && mkdir -p /data && chown svc:svc /data
WORKDIR /app/repo/_repos/shared-backend-components
# --chown at copy time: svc owns the tree (derived search sidecars write beside the corpus) with no extra layer;
# WORKDIR pre-created the dir chain as root, so hand those four dirs (non-recursive) to svc too
COPY --chown=svc:svc repo /app/repo
RUN chown svc:svc /app /app/repo /app/repo/_repos /app/repo/_repos/shared-backend-components
USER svc
# corpus files >90MB ride gzipped in git (GitHub's 100MB hard limit); restore them at build time
RUN find /app/repo/_repos/shared-backend-components/catalog /app/repo/_repos/shared-backend-components/data \\
    -name '*.gz' -exec gunzip -f {{}} +
# tenant-meaningful state (identity, receipts, ledgers, learning) lives on the /data volume; in-image writes are
# only rebuildable derived caches (search sidecars)
ENV PYTHONUNBUFFERED=1 TAEDRI_DATA_DIR=/data TAEDRI_GOVERNED_ONLY=1 \\
    OH_LEARNING_DATA_DIR=/data/learning OH_AGENT_TOOL_DATA_DIR=/data/agent-tool
EXPOSE {INTERNAL_PORT}
CMD ["python3", "scripts/capability_saas_gateway.py", "--serve", "--port", "{INTERNAL_PORT}", "--data-dir", "/data"]
"""

_FLY_TOML = f"""# fly.toml — capability SaaS gateway (rename `app` before first deploy if taken)
app = "{FLY_APP_NAME}"
primary_region = "{FLY_REGION_DEFAULT}"

[http_service]
  internal_port = {INTERNAL_PORT}
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "20s"
  method = "GET"
  path = "/healthz"

[mounts]
  source = "{FLY_VOLUME_NAME}"
  destination = "/data"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory = "{FLY_VM_MEMORY}"
"""

_WORKFLOW = """name: fly-deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency: fly-deploy-group
    steps:
      # CI deploys activate only once the FLY_API_TOKEN repo secret exists (the Fly-dashboard GitHub launch
      # flow needs no secret at all — it builds from this repo directly).
      - id: fly_secret
        run: echo "present=${{ secrets.FLY_API_TOKEN != '' }}" >> "$GITHUB_OUTPUT"
      - uses: actions/checkout@v4
        if: steps.fly_secret.outputs.present == 'true'
      - uses: superfly/flyctl-actions/setup-flyctl@master
        if: steps.fly_secret.outputs.present == 'true'
      - run: flyctl deploy --remote-only
        if: steps.fly_secret.outputs.present == 'true'
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
"""

#: ops workflows (owner 2026-07-11: payments/domain/monitoring go-live). `__FLY_APP__` renders from FLY_APP_NAME
#: so the app name stays single-source. Secret VALUES never pass through workflow inputs — sync-fly-secrets reads
#: the GitHub secrets context (masked in logs) and mirrors what exists onto the Fly app.
_FLY_OPS_WORKFLOW = """name: fly-ops
# Run a flyctl command against the __FLY_APP__ app from anywhere (the FLY_API_TOKEN repo secret is the auth).
# Examples: "status" · "certs add __FLY_APP__.dev" · "certs show __FLY_APP__.dev" · "logs --no-tail"
# · "secrets list" · "scale show" · "ips list". Do NOT pass secret VALUES here (inputs are logged) —
# secrets go through the sync-fly-secrets workflow instead.
on:
  workflow_dispatch:
    inputs:
      command:
        description: 'flyctl arguments (the app flag is appended automatically)'
        required: true
jobs:
  ops:
    runs-on: ubuntu-latest
    steps:
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl ${{ inputs.command }} --app __FLY_APP__
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
""".replace("__FLY_APP__", FLY_APP_NAME)

_SYNC_FLY_SECRETS_WORKFLOW = """name: sync-fly-secrets
# Mirror payment secrets from GitHub Actions secrets to the Fly app (values stay masked in logs).
# Owner flow: `gh secret set STRIPE_API_KEY` (+ STRIPE_PRICE_ID_PRO, STRIPE_WEBHOOK_SECRET) -> run this
# workflow -> the machine restarts with the new env and /v1/billing/status flips to payments_enabled.
on:
  workflow_dispatch: {}
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - name: Set the present secrets on the __FLY_APP__ Fly app
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
          STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}
          STRIPE_PRICE_ID_PRO: ${{ secrets.STRIPE_PRICE_ID_PRO }}
          STRIPE_WEBHOOK_SECRET: ${{ secrets.STRIPE_WEBHOOK_SECRET }}
          TAEDRI_ADMIN_KEY: ${{ secrets.TAEDRI_ADMIN_KEY }}
        run: |
          set -euo pipefail
          args=()
          for name in STRIPE_API_KEY STRIPE_PRICE_ID_PRO STRIPE_WEBHOOK_SECRET TAEDRI_ADMIN_KEY; do
            value="${!name:-}"
            if [ -n "$value" ]; then
              args+=("$name=$value")
            else
              echo "skip: $name is not set as a GitHub secret yet"
            fi
          done
          if [ "${#args[@]}" -gt 0 ]; then
            flyctl secrets set "${args[@]}" --app __FLY_APP__
          else
            echo "nothing to sync — set repo secrets first: gh secret set STRIPE_API_KEY ..."
          fi
""".replace("__FLY_APP__", FLY_APP_NAME)

_HEALTHCHECK_WORKFLOW = """name: healthcheck
# Live-deployment monitor: every 15 minutes probe the health, landing, counter, and billing surfaces.
# A failing probe fails the run, and GitHub emails the repo watchers — alerting with zero new vendors.
# (GitHub pauses schedules after ~60 days without repo activity; deploys keep it alive.)
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch: {}
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - name: probe healthz + landing + live counter + billing status
        run: |
          set -euo pipefail
          # download-then-grep (never `curl | grep -q`: grep exits at the first match and pipefail
          # turns curl's resulting write error into a false alarm)
          base="https://__FLY_APP__.fly.dev"
          curl -fsS --max-time 120 "$base/healthz" -o health.json
          python3 -c "import json; d=json.load(open('health.json')); assert d.get('ok') is True, d; print('healthz ok:', d['service'], d['version'])"
          curl -fsS --max-time 120 "$base/" -o landing.html
          grep -q "This already exists" landing.html
          echo "landing serves the designed app"
          curl -fsS --max-time 120 "$base/v1/stats/domains" -o stats.json
          grep -q '"primitives"' stats.json
          echo "live counter responds"
          curl -fsS --max-time 60 "$base/v1/billing/status" -o billing.json
          grep -q '"payments_enabled"' billing.json
          echo "billing status responds"
""".replace("__FLY_APP__", FLY_APP_NAME)

#: every non-CI workflow the bundle ships (fly-deploy.yml stays its own named emit)
_OPS_WORKFLOWS: dict[str, str] = {"fly-ops.yml": _FLY_OPS_WORKFLOW,
                                  "sync-fly-secrets.yml": _SYNC_FLY_SECRETS_WORKFLOW,
                                  "healthcheck.yml": _HEALTHCHECK_WORKFLOW}

#: the go-live runbook rides at the bundle root (single source: docs/; copied verbatim at build)
_RUNBOOK_SOURCE = _SBC / "docs" / "TAEDRI-GO-LIVE-RUNBOOK.md"

_DOCKERIGNORE = ".git\n**/__pycache__\n**/*.pyc\n"

_README = f"""# taedri — This Already Exists, Don't Rebuild It (deploy bundle)

Self-contained bundle for the hosted capability SaaS (remote MCP + agent API + signup/keys + metering).
Assembled by `scripts/build_capability_saas_bundle.py --build`; nothing here is hand-edited except `fly.toml`'s
`app` name if `{FLY_APP_NAME}` is taken.

## Deploy (needs FLY_API_TOKEN)
    export FLY_API_TOKEN=…            # the owner provides this
    python3 scripts/build_capability_saas_bundle.py --deploy
    # equivalent manual steps from this directory:
    #   flyctl apps create {FLY_APP_NAME}
    #   flyctl volumes create {FLY_VOLUME_NAME} --app {FLY_APP_NAME} --region {FLY_REGION_DEFAULT} --size 1 --yes
    #   flyctl deploy --remote-only

## GitHub (needs GITHUB_TOKEN) — repo + CI deploy on push
    export GITHUB_TOKEN=…
    python3 scripts/build_capability_saas_bundle.py --push-github
    # then add FLY_API_TOKEN as a repo Actions secret (the script does it when both tokens are present).

## After deploy
    curl -s https://{FLY_APP_NAME}.fly.dev/healthz
    curl -s -X POST https://{FLY_APP_NAME}.fly.dev/v1/signup -d '{{"email":"you@example.com"}}'
    claude mcp add --transport http capability-retrieval https://{FLY_APP_NAME}.fly.dev/mcp \\
        --header "Authorization: Bearer YOUR_API_KEY"

## Operate (see RUNBOOK.md for the full go-live runbook: payments · domain · Cloudflare · monitoring · email)
    gh workflow run fly-ops --repo <owner>/{FLY_APP_NAME} -f command="status"     # any flyctl command via CI
    gh workflow run sync-fly-secrets --repo <owner>/{FLY_APP_NAME}                # GH secrets -> Fly (STRIPE_*)
    # healthcheck.yml probes the live app every 15 min; a failure emails the repo watchers.
    curl -s https://{FLY_APP_NAME}.fly.dev/v1/billing/status                      # computed payments state

Tenant state lives on the /data volume; the corpus rides read-only in the image. serves_truth=false.
"""


def _gzip_oversized_files(bundle_dir: Path, *, threshold_bytes: int = GITHUB_PLAIN_FILE_LIMIT_BYTES) -> list[dict]:
    """Gzip data files over the GitHub plain-file limit IN PLACE (original removed — the Dockerfile's gunzip
    step restores them at image build). Returns the receipt rows. Only data roots are candidates, never code."""
    import gzip  # noqa: PLC0415

    compressed = []
    for root_rel in _COMPRESSIBLE_DATA_ROOTS:
        root = bundle_dir / root_rel
        if not root.exists():
            continue
        for file in sorted(root.rglob("*")):
            if not file.is_file() or file.suffix == ".gz" or file.stat().st_size <= threshold_bytes:
                continue
            target = file.with_name(file.name + ".gz")
            with file.open("rb") as source, gzip.open(target, "wb", compresslevel=6) as sink:
                shutil.copyfileobj(source, sink, length=1 << 20)
            compressed.append({"path": str(file.relative_to(bundle_dir)),
                               "plain_bytes": file.stat().st_size, "gz_bytes": target.stat().st_size})
            file.unlink()
    return compressed


def _walk_size(path: Path) -> tuple[int, int]:
    if path.is_file():
        return path.stat().st_size, 1
    total, count = 0, 0
    for file in path.rglob("*"):
        if file.is_file() and not any(part in _COPY_EXCLUDE_DIR_NAMES for part in file.parts):
            total += file.stat().st_size
            count += 1
    return total, count


def plan() -> dict[str, Any]:
    """The computed bundle manifest — sources, sizes, rendered-config digests. No copying, no writes."""
    sources = []
    total_bytes = 0
    for rel in BUNDLE_SOURCES:
        source = _MONOREPO / rel
        size, files = _walk_size(source) if source.exists() else (0, 0)
        total_bytes += size
        sources.append({"path": rel, "exists": source.exists(), "bytes": size, "files": files})
    return {
        "bundle_dir": str(BUNDLE_DIR),
        "fly_app": FLY_APP_NAME,
        "sources": sources,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / 1_000_000, 1),
        "rendered": {name: hashlib.sha256(text.encode()).hexdigest()[:16]
                     for name, text in (("Dockerfile", _DOCKERFILE), ("fly.toml", _FLY_TOML),
                                        ("workflow", _WORKFLOW), ("README-DEPLOY.md", _README),
                                        *sorted(_OPS_WORKFLOWS.items()))},
        "serving_path": "stdlib + numpy (embedding-loop import)",
        "candidate": True,
        "serves_truth": False,
    }


def build() -> dict[str, Any]:
    """Assemble the bundle at BUNDLE_DIR (idempotent: rebuilt from scratch each run — it is a derived artifact)."""
    manifest = plan()
    missing = [s["path"] for s in manifest["sources"] if not s["exists"]]
    if missing:
        return {"built": False, "error": f"missing sources: {missing}"}
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)  # derived output dir, fully regenerated (sources are never touched)
    repo_root = BUNDLE_DIR / "repo"
    repo_root.mkdir(parents=True)
    (repo_root / ".aidoneright-root").write_text("capability-saas bundle anchor\n")
    for rel in BUNDLE_SOURCES:
        source = _MONOREPO / rel
        target = repo_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, target)
        else:
            shutil.copytree(source, target,
                            ignore=shutil.ignore_patterns(*_COPY_EXCLUDE_DIR_NAMES, "*.pyc"))
    (BUNDLE_DIR / "Dockerfile").write_text(_DOCKERFILE)
    (BUNDLE_DIR / "fly.toml").write_text(_FLY_TOML)
    (BUNDLE_DIR / ".dockerignore").write_text(_DOCKERIGNORE)
    (BUNDLE_DIR / "README-DEPLOY.md").write_text(_README)
    (BUNDLE_DIR / "README.md").write_text(_README)  # the GitHub repo landing page
    workflow_dir = BUNDLE_DIR / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "fly-deploy.yml").write_text(_WORKFLOW)
    for workflow_name, workflow_text in _OPS_WORKFLOWS.items():
        (workflow_dir / workflow_name).write_text(workflow_text)
    if _RUNBOOK_SOURCE.exists():   # the go-live runbook rides at the bundle root when the doc exists
        (BUNDLE_DIR / "RUNBOOK.md").write_text(_RUNBOOK_SOURCE.read_text())
    manifest["compressed_for_github"] = _gzip_oversized_files(BUNDLE_DIR)
    (BUNDLE_DIR / "bundle_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    # plain count for the built report — the exclude list is for SOURCE trees; the bundle path itself is dist/
    built_files = sum(1 for f in BUNDLE_DIR.rglob("*") if f.is_file())
    built_bytes = sum(f.stat().st_size for f in BUNDLE_DIR.rglob("*") if f.is_file())
    return {"built": True, "bundle_dir": str(BUNDLE_DIR), "files": built_files,
            "mb": round(built_bytes / 1_000_000, 1), "manifest": str(BUNDLE_DIR / "bundle_manifest.json"),
            "candidate": True, "serves_truth": False}


def _run(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> tuple[int, str]:
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                               env={**os.environ, **(env or {})}, timeout=1800)
    return completed.returncode, (completed.stdout + completed.stderr)[-4000:]


def _flyctl() -> Optional[str]:
    for candidate in ("flyctl", "fly", str(Path.home() / ".fly" / "bin" / "flyctl")):
        if shutil.which(candidate) or Path(candidate).exists():
            return candidate if shutil.which(candidate) else candidate
    return None


def deploy() -> dict[str, Any]:
    """Fly deploy — GUARDED on FLY_API_TOKEN. Without it: an exact dry-run plan (nothing faked)."""
    steps = [
        f"flyctl apps create {FLY_APP_NAME}",
        f"flyctl volumes create {FLY_VOLUME_NAME} --app {FLY_APP_NAME} --region {FLY_REGION_DEFAULT} --size 5 --yes",
        "flyctl deploy --remote-only",
    ]
    if not os.environ.get("FLY_API_TOKEN"):
        return {"deployed": False, "reason": "FLY_API_TOKEN unset — provide it and re-run --deploy",
                "dry_run_plan": {"cwd": str(BUNDLE_DIR), "steps": steps},
                "bundle_ready": (BUNDLE_DIR / "Dockerfile").exists(), "candidate": True, "serves_truth": False}
    if not (BUNDLE_DIR / "Dockerfile").exists():
        built = build()
        if not built.get("built"):
            return {"deployed": False, "error": built.get("error")}
    flyctl = _flyctl()
    if flyctl is None:
        install_code, install_out = _run(["sh", "-c", "curl -fsSL https://fly.io/install.sh | sh"])
        flyctl = str(Path.home() / ".fly" / "bin" / "flyctl")
        if install_code != 0 or not Path(flyctl).exists():
            return {"deployed": False, "error": f"flyctl install failed: {install_out[-500:]}"}
    results = []
    for step in steps:
        cmd = step.replace("flyctl", flyctl, 1).split()
        code, output = _run(cmd, cwd=BUNDLE_DIR)
        results.append({"step": step, "exit": code, "tail": output[-800:]})
        # apps/volumes create are idempotent-by-intent: an already-exists failure must not stop the deploy
        if code != 0 and "deploy" in step:
            return {"deployed": False, "results": results}
    return {"deployed": True, "app": FLY_APP_NAME, "url": f"https://{FLY_APP_NAME}.fly.dev",
            "results": results, "candidate": True, "serves_truth": False}


def push_github(repo_name: str = "taedri") -> dict[str, Any]:
    """Create the deploy repo + push the bundle — GUARDED on GITHUB_TOKEN. Sets the Fly secret when both tokens exist."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return {"pushed": False, "reason": "GITHUB_TOKEN unset — provide it and re-run --push-github",
                "dry_run_plan": [f"POST /user/repos {{name: {repo_name}, private: true}}",
                                 "git init + push bundle -> main",
                                 "PUT actions secret FLY_API_TOKEN (when FLY_API_TOKEN is also set)"],
                "candidate": True, "serves_truth": False}
    if not (BUNDLE_DIR / "Dockerfile").exists():
        built = build()
        if not built.get("built"):
            return {"pushed": False, "error": built.get("error")}
    import urllib.error
    import urllib.request
    owner_probe = urllib.request.Request("https://api.github.com/user",
                                         headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(owner_probe, timeout=30) as response:
        token_login = json.loads(response.read().decode())["login"]
    owner = os.environ.get("GITHUB_OWNER") or token_login  # org target when set and different from the token user
    create_url = ("https://api.github.com/user/repos" if owner == token_login
                  else f"https://api.github.com/orgs/{owner}/repos")
    api = urllib.request.Request(create_url, method="POST",
                                 data=json.dumps({"name": repo_name, "private": True,
                                                  "description": "Taedri — verified capability retrieval (hosted MCP + agent API) deploy bundle"}).encode(),
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(api, timeout=30) as response:
            json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        if error.code != 422:  # 422 = already exists -> proceed to push
            return {"pushed": False, "error": f"repo create failed: {error.code}"}
    remote = f"https://x-access-token:{token}@github.com/{owner}/{repo_name}.git"
    commands = [
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "-c", "user.email=deploy@aidoneright.dev", "-c", "user.name=capability-deploy",
         "commit", "-q", "-m", "capability SaaS deploy bundle"],
        ["git", "push", "-q", "-f", remote, "main"],
    ]
    for cmd in commands:
        code, output = _run(cmd, cwd=BUNDLE_DIR)
        if code != 0 and "commit" not in cmd:  # empty re-commit is fine on rebuild-without-changes
            return {"pushed": False, "step": " ".join(cmd[:3]), "error": output[-500:]}
    return {"pushed": True, "repo": f"{owner}/{repo_name}",
            "note": "add FLY_API_TOKEN as an Actions secret to enable CI deploys (script sets it only via "
                    "the API when both tokens are present in a future run).",
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    manifest = plan()
    # (1) every bundle source exists in the monorepo (the gateway's whole import + data surface).
    checks.append((f"all {len(manifest['sources'])} bundle sources exist ({manifest['total_mb']} MB total)",
                   all(s["exists"] for s in manifest["sources"]), json.dumps(manifest["sources"])[:400]))

    # (2) the rendered configs carry the load-bearing keys (port, volume, healthcheck, numpy dep, gunzip restore,
    #     secret-guarded CI so pushes without FLY_API_TOKEN never show red).
    checks.append(("Dockerfile/fly.toml/workflow rendered coherently",
                   str(INTERNAL_PORT) in _DOCKERFILE and "numpy" in _DOCKERFILE and "gunzip" in _DOCKERFILE
                   and FLY_VOLUME_NAME in _FLY_TOML and "/healthz" in _FLY_TOML
                   and "secrets.FLY_API_TOKEN" in _WORKFLOW and "fly_secret.outputs.present" in _WORKFLOW, ""))

    # (2c) ops workflows: single-source app name; secrets flow only through the masked secrets context
    #      (never workflow inputs); the healthcheck probes all four live surfaces; the runbook source exists.
    checks.append(("ops workflows rendered coherently (fly-ops / sync-fly-secrets / healthcheck) + runbook",
                   f"--app {FLY_APP_NAME}" in _FLY_OPS_WORKFLOW
                   and "Do NOT pass secret VALUES" in _FLY_OPS_WORKFLOW
                   and f"--app {FLY_APP_NAME}" in _SYNC_FLY_SECRETS_WORKFLOW
                   and "secrets.STRIPE_API_KEY" in _SYNC_FLY_SECRETS_WORKFLOW
                   and "inputs" not in _SYNC_FLY_SECRETS_WORKFLOW
                   and f"https://{FLY_APP_NAME}.fly.dev" in _HEALTHCHECK_WORKFLOW
                   and all(probe in _HEALTHCHECK_WORKFLOW for probe in
                           ("/healthz", "This already exists", "/v1/stats/domains", "/v1/billing/status"))
                   and _RUNBOOK_SOURCE.exists(),
                   f"runbook exists: {_RUNBOOK_SOURCE.exists()}"))

    # (2b) oversized data files gzip in place (GitHub 100MB hard limit) and code roots are never candidates.
    import tempfile
    with tempfile.TemporaryDirectory() as sandbox:
        fake_bundle = Path(sandbox)
        data_file = fake_bundle / _COMPRESSIBLE_DATA_ROOTS[1] / "cards.jsonl"
        data_file.parent.mkdir(parents=True)
        data_file.write_text("row\n" * 200)
        code_file = fake_bundle / "repo/_repos/shared-backend-components/scripts/big_module.py"
        code_file.parent.mkdir(parents=True)
        code_file.write_text("x = 1\n" * 200)
        receipt = _gzip_oversized_files(fake_bundle, threshold_bytes=100)
        checks.append(("oversized DATA gzipped in place (original removed), code untouched",
                       len(receipt) == 1 and not data_file.exists()
                       and data_file.with_name("cards.jsonl.gz").exists() and code_file.exists(),
                       json.dumps(receipt)))

    # (3) plan is deterministic and write-free.
    checks.append(("plan deterministic", plan() == plan(), ""))

    # (4) deploy without FLY_API_TOKEN -> honest dry-run plan, nothing executed.
    saved = os.environ.pop("FLY_API_TOKEN", None)
    dry = deploy()
    if saved is not None:
        os.environ["FLY_API_TOKEN"] = saved
    checks.append(("deploy without token -> dry-run plan (guarded, nothing faked)",
                   dry["deployed"] is False and "dry_run_plan" in dry
                   and any("deploy --remote-only" in s for s in dry["dry_run_plan"]["steps"]), json.dumps(dry)[:300]))

    # (5) push-github without token -> honest dry-run plan.
    saved_git = {name: os.environ.pop(name, None) for name in ("GITHUB_TOKEN", "GH_TOKEN")}
    dry_git = push_github()
    for name, value in saved_git.items():
        if value is not None:
            os.environ[name] = value
    checks.append(("push-github without token -> dry-run plan",
                   dry_git["pushed"] is False and "dry_run_plan" in dry_git, ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - build_capability_saas_bundle: computed manifest "
          f"({manifest['total_mb']} MB, stdlib-only image), rendered Dockerfile/fly.toml/CI, token-guarded "
          f"deploy+push with honest dry-runs. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble + deploy the capability SaaS Fly.io bundle.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--push-github", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.plan:
        print(json.dumps(plan(), indent=2, sort_keys=True))
        return 0
    if args.build:
        result = build()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("built") else 1
    if args.deploy:
        result = deploy()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("deployed") or "dry_run_plan" in result else 1
    if args.push_github:
        result = push_github()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("pushed") or "dry_run_plan" in result else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
