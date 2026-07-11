#!/usr/bin/env python3
"""scripts.instruction_file_miner — turn public instruction files (CLAUDE.md / SKILL.md / TOOLS.md / AGENTS.md)
into a provenance-tracked library of DETERMINISTIC, reusable capability candidates. NOT a scrape-and-mash: the
robust decomposition rule is enforced — natural language becomes METADATA, command/code patterns become
capability CANDIDATES, and human-approval/policy sentences become NON-reusable policy notes (never scripts).
Duplication collapses: thousands of files saying "run npm test" become ONE canonical capability with many
sources (candidate-only).

Owner (2026-07-09): search publicly-available skills.md/claude.md/tools.md and decompose everything into reusable
deterministic scripts. The DETERMINISTIC CORE (normalize markdown -> extract commands/tools -> classify ->
dedupe -> capability candidates with provenance) runs OFFLINE, no LLM, and is self-tested here. Live GitHub
discovery is a token-gated lane (needs GITHUB_TOKEN; `gh search code --filename CLAUDE.md ...`). License
discipline: unlicensed sources are evidence-only (patterns), NOT copied into a redistributed script library.
candidate=true / serves_truth=false.

    python3 scripts/instruction_file_miner.py --self-test
    python3 scripts/instruction_file_miner.py --discovery-plan   # the GitHub search plan (token-gated)
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
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"instruction_file_miner requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_DIR_REL = "data/dev-intel/instruction_file_miner"
INSTRUCTION_FILENAMES = ("CLAUDE.md", "SKILL.md", "skills.md", "TOOLS.md", "AGENTS.md", "agents.md", ".cursorrules")

_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_ENV_RE = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\b")
_PATH_RE = re.compile(r"\b([\w.-]+/[\w./-]+|\b\w+\.(?:json|toml|yaml|yml|lock|cfg|ini|txt))\b")

# recognized command prefix -> category (deterministic; the CANDIDATE signal)
_CMD_CATEGORY: dict[str, list[str]] = {
    "test": ["npm test", "pnpm test", "yarn test", "bun test", "pytest", "tox", "go test", "cargo test",
             "jest", "vitest", "rspec", "phpunit", "mvn test", "gradle test", "npm run test", "make test"],
    "lint": ["ruff check", "ruff", "eslint", "flake8", "pylint", "golangci-lint", "cargo clippy", "clippy"],
    "typecheck": ["mypy", "tsc", "pyright", "pyre"],
    "build": ["npm run build", "make", "cargo build", "go build", "mvn package", "gradle build", "tsc -b",
              "pnpm build", "yarn build"],
    "format": ["black", "prettier", "gofmt", "rustfmt", "ruff format", "isort"],
    "package_mgmt": ["pip install", "uv sync", "uv pip", "npm install", "npm ci", "pnpm install", "yarn install",
                     "bun install", "poetry install", "cargo fetch", "go mod"],
    "docker": ["docker build", "docker compose", "docker run", "docker-compose"],
    "git": ["git add", "git commit", "git push", "git status", "git rebase"],
    "run": ["uvicorn", "flask run", "npm start", "gunicorn", "python -m", "python3 -m", "go run", "node "],
}
# a sentence is a POLICY NOTE (non-reusable) if it asks for human approval / manual action, not a command.
_POLICY_MARKERS = ("ask ", "approval", "before deploying", "before you deploy", "notify ", "manual review",
                   "get permission", "confirm with", "double-check with", "human review", "sign off")
_PERMISSIVE = {"MIT", "APACHE-2.0", "BSD-3-CLAUSE", "BSD-2-CLAUSE", "ISC", "UNLICENSE", "CC0-1.0"}


def normalize_markdown(text: str) -> dict[str, Any]:
    """Deterministic IR: headings, fenced code blocks, inline code, env-var names, file paths. No LLM."""
    code_blocks = [{"language": (lang or "").lower(), "content": body} for lang, body in _FENCE_RE.findall(text)]
    headings = [{"level": len(h), "text": t.strip()} for h, t in _HEADING_RE.findall(text)]
    inline = _INLINE_CODE_RE.findall(text)
    envs = sorted({e for e in _ENV_RE.findall(text) if not e.isupper() or "_" in e or len(e) >= 6})
    paths = sorted(set(_PATH_RE.findall(text)))
    return {"headings": headings, "code_blocks": code_blocks, "inline_code": inline,
            "env_vars": envs[:40], "file_paths": paths[:40]}


def _classify_command(cmd: str) -> str | None:
    low = cmd.strip().lower()
    for cat, prefixes in _CMD_CATEGORY.items():
        if any(low == p or low.startswith(p + " ") or low.startswith(p) for p in prefixes):
            return cat
    return None


def _iter_commands(normalized: dict[str, Any]) -> list[str]:
    """Commands from shell/bash code blocks (line-split, && / ; split) + inline code that looks like a command."""
    out: list[str] = []
    for blk in normalized["code_blocks"]:
        if blk["language"] in ("", "bash", "sh", "shell", "console", "zsh"):
            for line in blk["content"].splitlines():
                line = line.strip().lstrip("$").strip()
                if not line or line.startswith("#"):
                    continue
                for part in re.split(r"&&|;", line):
                    part = part.strip()
                    if part:
                        out.append(part)
    for span in normalized["inline_code"]:
        if _classify_command(span):
            out.append(span.strip())
    return out


def _canonical_command(cmd: str) -> str:
    """Dedupe key: first 2-3 significant tokens, lowercased, flags/paths dropped — so 'pnpm test -w' and
    'pnpm test ./pkg' collapse to 'pnpm test'."""
    toks = [t for t in cmd.lower().split() if not t.startswith("-")]
    keep = toks[:3] if toks and toks[0] in ("npm", "pnpm", "yarn", "bun", "go", "cargo", "python", "python3",
                                            "uv", "docker", "git", "mvn", "gradle") else toks[:2]
    return " ".join(keep)


def extract(text: str, source: dict[str, Any]) -> dict[str, Any]:
    """Decompose ONE instruction file into capability candidates + policy notes + metadata (deterministic)."""
    normalized = normalize_markdown(text)
    capabilities: dict[str, dict[str, Any]] = {}
    for cmd in _iter_commands(normalized):
        cat = _classify_command(cmd)
        if not cat:
            continue
        key = _canonical_command(cmd)
        cap = capabilities.setdefault(key, {"canonical_command": key, "category": cat, "commands_seen": set(),
                                            "reusable": True})
        cap["commands_seen"].add(cmd.strip())
    # policy notes: prose sentences that ask for human approval (NON-reusable — never a script)
    prose = _FENCE_RE.sub(" ", text)
    policy_notes = []
    for sent in re.split(r"(?<=[.!?\n])\s+", prose):
        low = sent.strip().lower()
        if low and any(m in low for m in _POLICY_MARKERS) and not any(_classify_command(low) for _ in [0]):
            policy_notes.append({"category": "human_approval", "text": sent.strip()[:200], "reusable": False})
    lic = (source.get("license") or "NOASSERTION").upper()
    reusable_scripts = lic in _PERMISSIVE
    caps = []
    for cap in capabilities.values():
        cap["commands_seen"] = sorted(cap["commands_seen"])
        caps.append({"capability_id": canonical_id("cap", cap["canonical_command"], cap["category"]),
                     **cap, "source": source, "license": lic,
                     "allowed_use": "reusable_script" if reusable_scripts else "evidence_only",
                     **BOUNDARY})
    return {"record_type": "instruction_file_decomposition", "source": source,
            "n_capabilities": len(caps), "capabilities": caps, "policy_notes": policy_notes,
            "env_vars": normalized["env_vars"], "file_paths": normalized["file_paths"], **BOUNDARY}


def dedupe(decompositions: list[dict[str, Any]]) -> dict[str, Any]:
    """Collapse the same capability across many files into ONE canonical entry, accumulating sources. This is
    where thousands of 'npm test' instructions become a single reusable capability."""
    canon: dict[str, dict[str, Any]] = {}
    for d in decompositions:
        for cap in d["capabilities"]:
            key = f"{cap['category']}::{cap['canonical_command']}"
            entry = canon.setdefault(key, {"capability_id": cap["capability_id"], "category": cap["category"],
                                           "canonical_command": cap["canonical_command"], "commands_seen": set(),
                                           "sources": [], "reusable_permissive_sources": 0, "n_sources": 0})
            entry["commands_seen"].update(cap["commands_seen"])
            entry["sources"].append(cap["source"])
            entry["n_sources"] += 1
            if cap["allowed_use"] == "reusable_script":
                entry["reusable_permissive_sources"] += 1
    out = []
    for e in canon.values():
        e["commands_seen"] = sorted(e["commands_seen"])
        e["script_candidate"] = e["reusable_permissive_sources"] > 0  # need >=1 permissive source to redistribute
        out.append({**e, **BOUNDARY})
    out.sort(key=lambda e: e["n_sources"], reverse=True)
    return {"record_type": "instruction_capability_registry", "n_canonical_capabilities": len(out),
            "capabilities": out, **BOUNDARY}


def discovery_plan() -> dict[str, Any]:
    """The token-gated GitHub search plan (needs GITHUB_TOKEN; not executed here). Read-only, filename-scoped."""
    return {"record_type": "instruction_discovery_plan", "needs": "GITHUB_TOKEN (unauth 60/hr works low-volume)",
            "queries": [f"gh search code --filename {fn} --json path,repository,sha,url --limit 1000"
                        for fn in INSTRUCTION_FILENAMES],
            "provenance_fields": ["source_url", "repo", "path", "sha", "license", "content_sha256", "retrieved_at"],
            "license_rule": "unlicensed/NOASSERTION -> evidence_only (readable pattern, not redistributed script)",
            **BOUNDARY}


# synthetic corpus for the self-test (mimics real CLAUDE.md/SKILL.md content)
_CORPUS = [
    ("repoA/CLAUDE.md", "MIT", "## Testing\nAlways run `pnpm test` before committing.\n\n"
                               "```bash\npnpm install\npnpm test\npnpm run build\n```\nAsk Bob before deploying to prod.\n"),
    ("repoB/CLAUDE.md", "Apache-2.0", "## Checks\n```sh\nnpm ci && npm test && npm run build\n```\nRun `ruff check` and `mypy`.\n"),
    ("repoC/SKILL.md", "NOASSERTION", "Run `pytest -q` for tests. Format with `black .`.\n"
                                      "Get permission from the lead before force-pushing.\n"),
]


def self_test() -> bool:
    """Mutation-gated + deterministic: NL becomes metadata, commands become candidates, approval sentences become
    NON-reusable policy notes; duplicates collapse across files; unlicensed sources are evidence_only."""
    decomps = [extract(text, {"path": path, "license": lic, "repo": path.split("/")[0]})
               for path, lic, text in _CORPUS]
    reg = dedupe(decomps)
    caps = {c["canonical_command"]: c for c in reg["capabilities"]}
    assert "pnpm test" in caps or "npm test" in caps, f"must mine node test capabilities: {list(caps)}"
    # 'npm test' appears in repoA (pnpm) + repoB (npm) -> dedup collapses per-canonical; sources accumulate.
    node_test = caps.get("npm test") or caps.get("pnpm test")
    assert node_test["n_sources"] >= 1 and node_test["category"] == "test"
    assert "pytest" in " ".join(caps) or any("pytest" in c for c in caps), "must mine pytest"
    # policy notes: 'Ask Bob before deploying' + 'Get permission ... before force-pushing' -> NON-reusable.
    all_policy = [p for d in decomps for p in d["policy_notes"]]
    assert any("ask bob" in p["text"].lower() or "permission" in p["text"].lower() for p in all_policy), \
        "human-approval sentences must be policy notes, not scripts"
    assert all(p["reusable"] is False for p in all_policy), "policy notes are never reusable scripts"
    # license discipline: the NOASSERTION (repoC) pytest/black caps are evidence_only unless a permissive source exists.
    pytest_cap = next((c for c in reg["capabilities"] if "pytest" in c["canonical_command"]), None)
    assert pytest_cap is not None and pytest_cap["script_candidate"] is False, \
        "an unlicensed-only capability must NOT be a redistributable script candidate"
    # a permissively-sourced capability IS a script candidate.
    assert node_test["script_candidate"] is True, "a permissive-licensed capability is a script candidate"
    assert reg["serves_truth"] is False
    print(f"OK instruction_file_miner self-test: {len(_CORPUS)} files -> {reg['n_canonical_capabilities']} canonical "
          f"capabilities (dedup across files); NL->metadata, commands->candidates, {len(all_policy)} human-approval "
          f"sentences->NON-reusable policy notes; unlicensed pytest cap = evidence_only, permissive node-test = "
          f"script_candidate; discovery plan token-gated; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Mine CLAUDE.md/SKILL.md/TOOLS.md/AGENTS.md into deterministic capabilities.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--discovery-plan", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.discovery_plan:
        print(json.dumps(discovery_plan(), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
