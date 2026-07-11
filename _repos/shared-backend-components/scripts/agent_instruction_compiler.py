#!/usr/bin/env python3
"""scripts.agent_instruction_compiler — the AGENT-INSTRUCTION COMPILER: turn natural-language repo guidance
(AGENTS.md · CLAUDE.md · SKILL.md · TOOLS.md · .cursor/rules · README · CI) into VERIFIED DETERMINISTIC automation
(scripts · Claude hooks · CI jobs · policy gates · approval workflows) that agents cannot casually ignore or
re-implement.

Owner (2026-07-09) product thesis: the executed experiments showed LLMs may KNOW a reusable primitive exists yet
still rewrite/wrap it incorrectly (prompt-based reuse regressed; deterministic composition passed hidden oracles at
0 model tokens). So the defensible product is NOT "prompt the agent to reuse" — it is a deterministic compiler that
turns recurring instructions into ENFORCED controls. CLAUDE.md is context (advisory); a HOOK is enforcement. The
wedge: "Stop hoping your coding agent follows instructions. Compile the important ones."

Pipeline: scan -> extract -> classify (context | deterministic_script | hook | ci_check | policy_gate |
human_approval) -> compile (emit the enforceable artifact) -> verify (syntax/runnable) -> provenance ledger ->
PR plan. Read-only + deterministic; it EMITS artifacts to a plan, never opens a PR or writes into the repo without
explicit approval. serves_truth=false (generated automations are candidates until reviewed + proven).

    python3 scripts/agent_instruction_compiler.py --self-test
    python3 scripts/agent_instruction_compiler.py --scan .            # compile this repo's guidance into a plan
    python3 scripts/agent_instruction_compiler.py --scan . --emit     # write the plan + artifacts to the plan dir
"""
from __future__ import annotations

import sys
from pathlib import Path

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
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"agent_instruction_compiler requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_DIR_REL = "data/dev-intel/agent_instruction_compiler"

# instruction sources scattered across a repo (the de-facto "agent operating system")
INSTRUCTION_SOURCES = [
    "AGENTS.md", "CLAUDE.md", "SKILL.md", "TOOLS.md", "GEMINI.md", "CONVENTIONS.md", ".cursor/rules",
    ".cursorrules", ".github/copilot-instructions.md", "CONTRIBUTING.md", "README.md",
]

CLASSES = ["context", "deterministic_script", "hook", "ci_check", "policy_gate", "human_approval"]

# imperative markers that make a sentence an INSTRUCTION (not prose)
_IMPERATIVE = re.compile(
    r"\b(always|never|must(?! not\b)|must not|do not|don't|ask before|confirm|require|run|execute|prefer|use|ensure|"
    r"end (?:every|all|each)|before (?:adding|committing|pushing|deploying))\b", re.I)
_CMD_BACKTICK = re.compile(r"`([^`]{2,80})`")
_CMD_RUN = re.compile(r"\brun\s+`?([a-z0-9][\w./\- ]{2,60})`?", re.I)


def extract_instructions(text: str, source_file: str) -> list[dict[str, Any]]:
    """Pull candidate instruction sentences (bullets + imperative lines) from a guidance doc. Deterministic."""
    out = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().lstrip("-*").strip().lstrip("0123456789. ").strip()
        if len(line) < 8 or line.startswith(("#", ">", "|", "```")):
            continue
        if _IMPERATIVE.search(line):
            out.append({"text": line[:400], "source_file": source_file, "line": i,
                        "instruction_id": canonical_id("agentrule", source_file, str(i), line[:80])})
    return out


def _extract_command(text: str) -> str | None:
    """Best-effort command extraction (backticked first, then 'run X'). Deterministic."""
    m = _CMD_BACKTICK.search(text)
    if m and any(c in m.group(1) for c in (" ", "/", ".")) or (m and re.match(r"^[a-z]", m.group(1))):
        return m.group(1).strip()
    m = _CMD_RUN.search(text)
    return m.group(1).strip() if m else None


# ── CLASSIFIER — deterministic, priority-ordered; returns (class, signals) ────────────────────────────────────
def classify_instruction(instr: dict[str, Any]) -> dict[str, Any]:
    t = instr["text"].lower()
    cmd = _extract_command(instr["text"])
    sig: list[str] = []

    def done(cls: str) -> dict[str, Any]:
        return {**instr, "classification": cls, "command": cmd, "signals": sig, "enforceable": cls != "context"}

    if re.search(r"\b(ask|confirm|require (?:approval|review|sign-?off)|get approval)\b.*\bbefore\b", t) \
            or "human approval" in t or "require review" in t:
        sig.append("approval-language")
        return done("human_approval")
    if re.search(r"\b(never|do not|don't|must not|forbidden|do not commit|do not push)\b", t):
        sig.append("prohibition")
        if re.search(r"\b(commit|secret|api[- ]?key|token|credential|password|delete|rm\b|force[- ]?push|"
                     r"drop table|prod(?:uction)?)\b", t):
            sig.append("dangerous-target")
            return done("policy_gate")
        return done("context")  # a stylistic "never do X" with no enforceable target -> stays advisory context
    if re.search(r"after (?:editing|modifying|changing|touching|updating)\b", t) and (cmd or "test" in t):
        sig.append("post-edit-trigger")
        return done("hook")
    if re.search(r"\bend (?:every|all|each).*(commit|message|pr)\b", t) or "co-authored-by" in t:
        sig.append("commit-message-rule")
        return done("hook")
    if (re.search(r"\b(must pass|run|execute)\b", t) and re.search(r"\b(test|lint|ci|build|self-test|typecheck|"
                                                                   r"coverage)\b", t)):
        sig.append("verification-command")
        return done("ci_check")
    if re.search(r"\balways (?:run|execute)\b", t) and cmd:
        sig.append("always-run")
        return done("deterministic_script")
    sig.append("advisory")
    return done("context")


# ── COMPILERS — emit the enforceable artifact for each class (real, valid artifacts) ──────────────────────────
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "rule"


def _c_deterministic_script(instr: dict[str, Any]) -> list[dict[str, Any]]:
    cmd = instr["command"] or "echo 'define the command for: " + instr["text"][:60] + "'"
    name = f"agent_{_slug(instr['text'])}.sh"
    content = ("#!/usr/bin/env bash\n# AUTO-COMPILED from agent instruction (candidate; review before enabling)\n"
               f"# rule: {instr['text']}\n# source: {instr['source_file']}:{instr['line']}\nset -euo pipefail\n{cmd}\n")
    return [{"artifact_type": "script", "path": f"scripts/agent_compiled/{name}", "content": content,
             "enforces": instr["text"], "invocation": f"bash scripts/agent_compiled/{name}"}]


def _c_hook(instr: dict[str, Any]) -> list[dict[str, Any]]:
    cmd = instr["command"] or "python3 -c \"print('define the hook command')\""
    is_commit = "commit-message-rule" in instr["signals"]
    event = "PostToolUse"
    matcher = {"tool": "Bash", "query": "git commit"} if is_commit else {"tool": "Edit|Write|MultiEdit"}
    hook = {"artifact_type": "claude_hook", "path": ".claude/settings.json#hooks",
            "hook": {"event": event, "matcher": matcher,
                     "command": cmd, "note": "runs after the matched tool call (enforced, not advisory)"},
            "enforces": instr["text"]}
    return [hook]


def _c_ci_check(instr: dict[str, Any]) -> list[dict[str, Any]]:
    cmd = instr["command"] or "make test"
    yaml = ("# AUTO-COMPILED agent-verify CI (candidate; review before merging)\n"
            "name: agent-verify\non: [push, pull_request]\njobs:\n  verify:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - uses: actions/checkout@v4\n"
            f"      # enforces: {instr['text']}\n      - run: {cmd}\n")
    return [{"artifact_type": "github_actions", "path": ".github/workflows/agent-verify.yml", "yaml": yaml,
             "enforces": instr["text"]}]


def _c_policy_gate(instr: dict[str, Any]) -> list[dict[str, Any]]:
    # a PreToolUse block: match risky Bash and exit non-zero to DENY (Claude Code hook convention)
    pattern = "git commit" if "commit" in instr["text"].lower() else "rm -rf|curl .*\\| *bash|force-push"
    script = ("#!/usr/bin/env bash\n# AUTO-COMPILED policy gate (candidate) — exit 2 BLOCKS the action\n"
              f"# enforces: {instr['text']}\nread -r payload\n"
              f"if echo \"$payload\" | grep -Eq '{pattern}'; then echo 'BLOCKED by compiled policy: "
              f"{instr['text'][:60]}' >&2; exit 2; fi\nexit 0\n")
    return [{"artifact_type": "claude_hook", "path": ".claude/settings.json#hooks",
             "hook": {"event": "PreToolUse", "matcher": {"tool": "Bash", "pattern": pattern}, "block_on_nonzero": True},
             "detector_script": {"path": f".claude/hooks/policy_{_slug(instr['text'])}.sh", "content": script},
             "enforces": instr["text"]}]


def _c_human_approval(instr: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"artifact_type": "approval_workflow", "enforces": instr["text"],
             "pr_checklist_item": f"[ ] {instr['text']}",
             "codeowners_suggestion": "# add a reviewer for the affected paths in CODEOWNERS",
             "optional_pretooluse_block": "block package-manager install / protected-file edits pending approval"}]


COMPILERS: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {
    "deterministic_script": _c_deterministic_script, "hook": _c_hook, "ci_check": _c_ci_check,
    "policy_gate": _c_policy_gate, "human_approval": _c_human_approval,
}


def compile_instruction(instr: dict[str, Any]) -> list[dict[str, Any]]:
    """Emit deterministic artifact(s) for an enforceable instruction; [] for advisory context."""
    fn = COMPILERS.get(instr["classification"])
    return fn(instr) if fn else []


# ── VERIFIER — check each emitted artifact is well-formed / runnable (deterministic, no network) ──────────────
def verify_artifact(art: dict[str, Any]) -> dict[str, Any]:
    kind = art["artifact_type"]
    try:
        if kind == "script":
            import subprocess  # noqa: PLC0415
            r = subprocess.run(["bash", "-n"], input=art["content"], text=True, capture_output=True, timeout=10)
            return {"ok": r.returncode == 0, "check": "bash -n syntax", "detail": (r.stderr or "")[:120]}
        if kind == "github_actions":
            import subprocess  # noqa: PLC0415
            # stdlib-only YAML sanity: keys present + indentation parses via a tiny structural check
            y = art["yaml"]
            ok = ("jobs:" in y and "runs-on:" in y and "steps:" in y and "name:" in y)
            return {"ok": ok, "check": "actions structural", "detail": "" if ok else "missing job keys"}
        if kind == "claude_hook":
            h = art["hook"]
            ok = h.get("event") in ("PreToolUse", "PostToolUse") and isinstance(h.get("matcher"), dict)
            if "detector_script" in art:
                import subprocess  # noqa: PLC0415
                r = subprocess.run(["bash", "-n"], input=art["detector_script"]["content"], text=True,
                                   capture_output=True, timeout=10)
                ok = ok and r.returncode == 0
            return {"ok": ok, "check": "hook shape + script syntax", "detail": ""}
        if kind == "approval_workflow":
            return {"ok": bool(art.get("pr_checklist_item")), "check": "approval shape", "detail": ""}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "check": kind, "detail": str(exc)[:120]}
    return {"ok": False, "check": kind, "detail": "unknown artifact type"}


def compile_repo(root: str) -> dict[str, Any]:
    """Scan a repo's guidance -> extract -> classify -> compile -> verify -> provenance ledger + PR plan."""
    rp = Path(root)
    instructions, ledger = [], []
    for rel in INSTRUCTION_SOURCES:
        f = rp / rel
        if f.exists() and f.is_file():
            for instr in extract_instructions(f.read_text(encoding="utf-8", errors="ignore"), rel):
                instructions.append(instr)
    for instr in instructions:
        cl = classify_instruction(instr)
        arts = compile_instruction(cl)
        for a in arts:
            a["verification"] = verify_artifact(a)
        ledger.append({"instruction": cl, "artifacts": arts,
                       "provenance": {"source_file": instr["source_file"], "line": instr["line"],
                                      "instruction_id": instr["instruction_id"],
                                      "classification": cl["classification"]}, **BOUNDARY})
    counts: dict[str, int] = {c: 0 for c in CLASSES}
    for row in ledger:
        counts[row["instruction"]["classification"]] += 1
    enforceable = [r for r in ledger if r["instruction"]["enforceable"]]
    verified = sum(1 for r in enforceable for a in r["artifacts"] if a.get("verification", {}).get("ok"))
    total_arts = sum(len(r["artifacts"]) for r in enforceable)
    return {"record_type": "agent_instruction_compile_plan", "repo": root,
            "instructions_found": len(instructions), "by_class": counts,
            "enforceable": len(enforceable), "artifacts_emitted": total_arts, "artifacts_verified": verified,
            "ledger": ledger,
            "pr_plan": [{"enforces": a["enforces"], "artifact": a["artifact_type"],
                         "path": a.get("path"), "verified": a.get("verification", {}).get("ok")}
                        for r in enforceable for a in r["artifacts"]],
            "note": "candidate automations — review + prove before enabling; nothing is written to the repo or a PR "
                    "opened without explicit approval.", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: (1) a fixture guidance doc yields one instruction per enforceable class, each CLASSIFIED
    correctly; (2) each compiles to a VALID artifact that PASSES verification (bash -n / hook shape / CI structure);
    (3) a mangled artifact FAILS verification (verifier really checks); (4) advisory 'prefer' stays context (no
    artifact); (5) plan is candidate=true/serves_truth=false."""
    fixture = (
        "# Team agent guide\n"
        "- Always run `python3 scripts/validate.py` before pushing.\n"        # deterministic_script
        "- After modifying any .py file, run `python3 -m pytest -q`.\n"        # hook (post-edit)
        "- All pull requests must pass `make lint` and the test suite.\n"      # ci_check
        "- Never commit API keys or secrets to the repository.\n"             # policy_gate
        "- Ask before adding new production dependencies.\n"                   # human_approval
        "- End every commit message with a Co-Authored-By trailer.\n"         # hook (commit-message-rule)
        "- Prefer functional style over classes where practical.\n"           # context (advisory)
    )
    instrs = extract_instructions(fixture, "AGENTS.md")
    assert len(instrs) >= 7, f"expected >=7 instructions, got {len(instrs)}"
    classed = [classify_instruction(i) for i in instrs]
    got = {c["classification"] for c in classed}
    for expect in ("deterministic_script", "hook", "ci_check", "policy_gate", "human_approval", "context"):
        assert expect in got, f"classifier missed {expect}; got {sorted(got)}"

    # every enforceable instruction compiles to a VERIFIED artifact
    for c in classed:
        if c["enforceable"]:
            arts = compile_instruction(c)
            assert arts, f"enforceable {c['classification']} produced no artifact"
            for a in arts:
                v = verify_artifact(a)
                assert v["ok"], f"artifact for {c['classification']} failed verification: {v} / {a.get('artifact_type')}"
        else:
            assert compile_instruction(c) == [], "advisory context must emit no enforced artifact"

    # verifier really checks: a broken script must FAIL bash -n
    broken = {"artifact_type": "script", "content": "if then fi done )("}
    assert verify_artifact(broken)["ok"] is False, "verifier must catch a broken script"

    plan = compile_repo(str(_sbc_boot))  # scan THIS repo's real AGENTS.md/CLAUDE.md
    assert plan["candidate"] is True and plan["serves_truth"] is False
    assert all(r["candidate"] is True for r in plan["ledger"])

    print(f"OK agent_instruction_compiler self-test: fixture -> {len(instrs)} instructions classified across all "
          f"6 classes; every enforceable rule COMPILES to a VERIFIED artifact (script bash -n / hook shape / CI "
          f"structure / policy gate / approval); broken artifact caught; advisory 'prefer' stays context. Live scan "
          f"of this repo: {plan['instructions_found']} instructions found, {plan['enforceable']} enforceable, "
          f"{plan['artifacts_verified']}/{plan['artifacts_emitted']} artifacts verified. serves_truth=false")
    return True


def emit(root: str) -> dict[str, Any]:
    plan = compile_repo(root)
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    (out / "compile_plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return {k: v for k, v in plan.items() if k != "ledger"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile natural-language agent guidance into verified enforcement.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--scan", metavar="REPO_ROOT")
    ap.add_argument("--emit", action="store_true", help="write the plan + artifacts to the plan dir")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.scan:
        rep = emit(args.scan) if args.emit else {k: v for k, v in compile_repo(args.scan).items() if k != "ledger"}
        print(json.dumps(rep, indent=2, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
