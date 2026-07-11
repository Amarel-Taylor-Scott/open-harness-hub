#!/usr/bin/env python3
"""scripts.quickstart_aidevobserver — the ONE-COMMAND onboarding path: a fresh checkout to a working
AIDevObserver in one invocation, with a measured wall-clock receipt.

SaaS north-star requirement: adoption must take minutes, not an afternoon of wiring. This command makes a
checkout fully operational for a developer using Claude Code (or any MCP client):

  1. MCP        — merge the unified AIDevObserver server (session review + capability retrieval) into the
                  target project's .mcp.json (idempotent; never clobbers other entries)
  2. HOOK       — install the PreToolUse reuse hook via its own registrar (aidevobserver_hook --install
                  --write; fail-open by design)
  3. SERVICE    — start observer_runtime (:9431) via its registry start command when not already up
  4. VERIFY     — MCP handshake (tools/list on both servers), service /sessions probe, hook present in
                  settings — every step PASS/FAIL in the receipt, nothing assumed

Default is a DRY RUN that prints the plan; ``--write`` applies it. Deterministic + conservative: existing
config always wins over ours; re-running is a no-op. The receipt is a governed candidate
(serves_truth=false) — onboarding never promotes anything.

    python3 scripts/quickstart_aidevobserver.py            # dry-run plan for this checkout
    python3 scripts/quickstart_aidevobserver.py --write    # apply to this checkout (measured)
    python3 scripts/quickstart_aidevobserver.py --target /path/to/project --write
    python3 scripts/quickstart_aidevobserver.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, repo_root  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import fcntl  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402  wall-clock is MEASURED for the receipt only — never used in ids/keys
import urllib.request  # noqa: E402
from contextlib import contextmanager  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

OBSERVER_PORT = 9431                     # single-sourced in architecture/local_service_registry.json (observer_runtime)
_SERVICE_PROBE_TIMEOUT_S = 5.0           # a health probe answers fast or the service is not up
_SERVICE_START_WAIT_S = 6.0              # grace period for the service to bind after a cold start
_MCP_HANDSHAKE_TIMEOUT_S = 60.0          # server import + index open can take seconds on first run
_MAX_CONFIG_BYTES = 4 * 1024 * 1024      # project MCP/settings config is control-plane data, never a corpus

#: the ONE agent-facing MCP server an adopter needs (path is substrate-relative; rendered per checkout). The
#: legacy capability-retrieval server remains runnable for old configs, but its tools are now included here.
_MCP_SERVERS: dict[str, str] = {
    "aidevobserver": "scripts/aidevobserver_mcp_server.py",
}


def _project_root(target_root: Optional[Path] = None) -> Path:
    """Return the onboarding target; omitted means the historical monorepo default."""
    if target_root is None:
        return Path(repo_root())
    return Path(target_root).expanduser().resolve()


def _mcp_config_path(target_root: Optional[Path] = None) -> Path:
    return _project_root(target_root) / ".mcp.json"


def plan_mcp_entries() -> dict[str, dict[str, Any]]:
    """The .mcp.json entries this checkout needs (absolute script paths so any-cwd clients resolve)."""
    return {
        name: {"command": "python3", "args": [str(_sbc_boot / rel)]}
        for name, rel in sorted(_MCP_SERVERS.items())
    }


class _ConfigRefused(Exception):
    """A config cannot be read or replaced safely; public receipts expose only its bounded reason."""


def _safe_text(value: object, *, maximum: int = 512) -> str:
    """Strip terminal controls/newlines from subprocess and path-derived receipt text."""

    printable = "".join(ch if ch.isprintable() else " " for ch in str(value))
    return " ".join(printable.split())[:maximum]


def _nofollow_flag() -> int:
    return getattr(os, "O_NOFOLLOW", 0)


def _read_config(path: Path) -> dict[str, Any]:
    """Read one bounded regular JSON file without following a final-component symlink."""

    try:
        if path.is_symlink():
            raise _ConfigRefused("config path is a symbolic link")
        fd = os.open(path, os.O_RDONLY | _nofollow_flag())
    except FileNotFoundError:
        return {}
    except _ConfigRefused:
        raise
    except OSError as exc:
        raise _ConfigRefused("config could not be opened safely") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise _ConfigRefused("config is not a regular file")
        if info.st_size > _MAX_CONFIG_BYTES:
            raise _ConfigRefused("config exceeds the size limit")
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = json.load(handle)
    except _ConfigRefused:
        raise
    except (json.JSONDecodeError, UnicodeError, OSError) as exc:
        raise _ConfigRefused("config is not valid UTF-8 JSON") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    if not isinstance(value, dict):
        raise _ConfigRefused("config root is not an object")
    return value


@contextmanager
def _config_lock(path: Path):
    """Cooperative per-config lock opened with O_NOFOLLOW and owner-only permissions."""

    lock_path = path.with_name(f"{path.name}.lock")
    if lock_path.is_symlink():
        raise _ConfigRefused("config lock path is a symbolic link")
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | _nofollow_flag(), 0o600)
    except OSError as exc:
        raise _ConfigRefused("config lock could not be opened safely") from exc
    with os.fdopen(fd, "a+", encoding="utf-8") as lock:
        lock_info = os.fstat(lock.fileno())
        if (not stat.S_ISREG(lock_info.st_mode) or lock_info.st_uid != os.geteuid()
                or lock_info.st_nlink != 1):
            raise _ConfigRefused("config lock is not a regular file")
        os.fchmod(lock.fileno(), 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _atomic_write_config(path: Path, value: dict[str, Any]) -> None:
    """fsync a private sibling temp and atomically replace a non-symlink config."""

    if path.is_symlink():
        raise _ConfigRefused("config path is a symbolic link")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise _ConfigRefused("config path became a symbolic link")
        os.replace(temporary, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _entry_matches(entry: object, planned: dict[str, Any]) -> bool:
    """Only the exact executable and argv we own count as installed; never execute an arbitrary preserved entry."""

    return (
        isinstance(entry, dict)
        and entry.get("command") == planned["command"]
        and entry.get("args") == planned["args"]
    )


def apply_mcp(write: bool, target_root: Optional[Path] = None) -> dict[str, Any]:
    """Merge the unified server safely; a conflicting preserved command is a visible failure, never a false green."""
    root = _project_root(target_root)
    if not root.is_dir():
        return {"step": "mcp", "ok": False,
                "detail": _safe_text(f"target is not an existing directory: {root}"), **BOUNDARY}
    path = _mcp_config_path(root)
    planned = plan_mcp_entries()

    def merge_once() -> dict[str, Any]:
        existing = _read_config(path)
        servers = existing.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise _ConfigRefused("mcpServers is not an object")
        conflicts = sorted(name for name, entry in planned.items()
                           if name in servers and not _entry_matches(servers[name], entry))
        if conflicts:
            return {"step": "mcp", "ok": False, "added": [], "already_present": [],
                    "conflicts": conflicts,
                    "detail": "existing AIDevObserver MCP entry has a different command; preserved and refused",
                    **BOUNDARY}
        added = sorted(name for name in planned if name not in servers)
        for name in added:
            servers[name] = planned[name]
        if write and added:
            _atomic_write_config(path, existing)
        installed = sorted(name for name, entry in planned.items()
                           if _entry_matches(servers.get(name), entry))
        # Dry-run additions are plans, not installed commands.  Write mode succeeds only after an exact read-back.
        if write:
            persisted = _read_config(path).get("mcpServers", {})
            installed = sorted(name for name, entry in planned.items()
                               if isinstance(persisted, dict) and _entry_matches(persisted.get(name), entry))
        ok = len(installed) == len(planned) if write else True
        return {"step": "mcp", "ok": ok, "added": added,
                "already_present": sorted(name for name in planned if name not in added),
                "installed_verified": installed if write else [],
                "detail": "exact command read back" if write and ok else "planned; no files changed",
                **BOUNDARY}

    try:
        if write:
            with _config_lock(path):
                return merge_once()
        return merge_once()
    except _ConfigRefused as exc:
        return {"step": "mcp", "ok": False, "added": [], "already_present": [],
                "detail": _safe_text(exc), **BOUNDARY}
    except OSError:
        return {"step": "mcp", "ok": False, "added": [], "already_present": [],
                "detail": "config could not be updated safely", **BOUNDARY}


def apply_hook(write: bool, target_root: Optional[Path] = None) -> dict[str, Any]:
    """Install the PreToolUse reuse hook through its OWN registrar (single source of the hook snippet)."""
    root = _project_root(target_root)
    cmd = ["python3", str(_sbc_boot / "scripts" / "aidevobserver_hook.py"), "--install",
           "--target", str(root)]
    if write:
        cmd.append("--write")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=root)
    except (OSError, subprocess.TimeoutExpired):
        return {"step": "hook", "ok": False, "wrote": False, "supported": True,
                "detail": "hook registrar could not be completed", **BOUNDARY}
    ok = proc.returncode == 0
    output = proc.stdout or proc.stderr or ""
    last_line = output.strip().splitlines()[-1] if output else ""
    return {"step": "hook", "ok": ok, "wrote": write and ok and last_line.startswith("[written]"),
            "already_present": write and ok and last_line.startswith("[ok]"), "supported": True,
            "detail": _safe_text(last_line), **BOUNDARY}


def _service_up() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{OBSERVER_PORT}/sessions",
                                    timeout=_SERVICE_PROBE_TIMEOUT_S) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001 — any failure = not up (the probe is the definition of up)
        return False


def apply_service(write: bool) -> dict[str, Any]:
    """Start observer_runtime when it is not already answering; never spawn a duplicate."""
    if _service_up():
        return {"step": "service", "ok": True, "detail": f"already up on :{OBSERVER_PORT}", **BOUNDARY}
    if not write:
        return {"step": "service", "ok": True, "detail": "would start observer_local_service --serve", **BOUNDARY}
    try:
        subprocess.Popen(  # detached on purpose: the service outlives the quickstart
            ["python3", str(_sbc_boot / "scripts" / "observer_local_service.py"), "--serve"],
            cwd=_sbc_boot, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return {"step": "service", "ok": False, "detail": "service process could not be started", **BOUNDARY}
    deadline = time.monotonic() + _SERVICE_START_WAIT_S
    while time.monotonic() < deadline:
        if _service_up():
            return {"step": "service", "ok": True, "detail": f"started on :{OBSERVER_PORT}", **BOUNDARY}
        time.sleep(0.25)
    return {"step": "service", "ok": False, "detail": "service did not answer within the grace period",
            **BOUNDARY}


def _mcp_handshake(script_path: Path, target_root: Optional[Path] = None) -> tuple[bool, list[str]]:
    """One real initialize + tools/list over stdio — the adopter's first experience, verified."""
    payload = (b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}\n'
               b'{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n')
    try:
        proc = subprocess.run(["python3", str(script_path)], input=payload, capture_output=True,
                              timeout=_MCP_HANDSHAKE_TIMEOUT_S, cwd=_project_root(target_root))
    except (OSError, subprocess.TimeoutExpired):
        return False, []
    tools: list[str] = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        try:
            result = json.loads(line).get("result") or {}
        except json.JSONDecodeError:
            continue
        for tool in result.get("tools", []) or []:
            tools.append(_safe_text(tool.get("name", ""), maximum=128))
    return proc.returncode == 0 and bool(tools), tools


def _hook_entry_present(settings: dict[str, Any]) -> bool:
    expected = f"python3 {_sbc_boot / 'scripts' / 'aidevobserver_hook.py'}"
    hooks = settings.get("hooks", {}).get("PreToolUse", []) if isinstance(settings.get("hooks"), dict) else []
    if not isinstance(hooks, list):
        return False
    for group in hooks:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            continue
        for hook in group["hooks"]:
            if isinstance(hook, dict) and hook.get("type") == "command" and hook.get("command") == expected:
                return True
    return False


def verify(target_root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Every onboarding claim re-checked from the OUTSIDE — nothing reported that was not observed."""
    root = _project_root(target_root)
    receipts: list[dict[str, Any]] = []
    planned = plan_mcp_entries()
    try:
        config = _read_config(_mcp_config_path(root))
        servers = config.get("mcpServers", {})
    except _ConfigRefused:
        servers = {}
    for name, expected in sorted(planned.items()):
        configured = isinstance(servers, dict) and _entry_matches(servers.get(name), expected)
        # Never execute a preserved arbitrary command.  Only after exact command+argv matching do we invoke our
        # known server path and verify the handshake an adopter will receive.
        ok, tools = _mcp_handshake(Path(expected["args"][0]), root) if configured else (False, [])
        receipts.append({"step": f"verify_mcp:{name}", "ok": configured and ok, "tools": tools,
                         "configured_command_matches": configured,
                         "detail": "installed command matched and answered" if configured and ok
                         else "installed command missing, conflicting, or did not answer", **BOUNDARY})
    receipts.append({"step": "verify_service", "ok": _service_up(),
                     "detail": f"GET :{OBSERVER_PORT}/sessions", **BOUNDARY})
    settings = root / ".claude" / "settings.json"
    try:
        hook_present = _hook_entry_present(_read_config(settings))
    except _ConfigRefused:
        hook_present = False
    receipts.append({"step": "verify_hook", "ok": hook_present, "supported": True,
                     "detail": _safe_text(settings), **BOUNDARY})
    return receipts


def run(write: bool, target_root: Optional[Path] = None) -> dict[str, Any]:
    started = time.monotonic()
    root = _project_root(target_root)
    if not root.is_dir():
        steps = [{"step": "target", "ok": False,
                  "detail": _safe_text(f"target is not an existing directory: {root}"), **BOUNDARY}]
        return {"record_type": "aidevobserver_quickstart_receipt",
                "mode": "write" if write else "dry_run", "target": str(root), "ok": False,
                "elapsed_seconds": round(time.monotonic() - started, 1), "steps": steps, **BOUNDARY}
    steps = [apply_mcp(write, root), apply_hook(write, root), apply_service(write)]
    if write:
        steps.extend(verify(root))
    elapsed = round(time.monotonic() - started, 1)
    ok = all(s["ok"] for s in steps)
    return {"record_type": "aidevobserver_quickstart_receipt", "mode": "write" if write else "dry_run",
            "target": str(root), "ok": ok, "elapsed_seconds": elapsed, "steps": steps, **BOUNDARY}


def _self_test() -> int:
    import tempfile
    from unittest.mock import patch

    checks: list[tuple[str, bool]] = []

    def snapshot(root: Path) -> dict[str, bytes]:
        return {str(path.relative_to(root)): path.read_bytes()
                for path in sorted(root.rglob("*")) if path.is_file()}

    # (a) the plan is deterministic and points at real scripts on this checkout
    plan = plan_mcp_entries()
    checks.append(("plan installs one unified AIDevObserver server", set(plan) == {"aidevobserver"}))
    checks.append(("every planned server script exists", all(Path(e["args"][0]).is_file() for e in plan.values())))
    checks.append(("plan is deterministic", json.dumps(plan_mcp_entries(), sort_keys=True)
                   == json.dumps(plan_mcp_entries(), sort_keys=True)))
    checks.append(("omitting --target preserves the monorepo default", _project_root() == Path(repo_root())))

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        target = temp / "coding-project"
        target.mkdir()

        # (b) the full dry-run plan is hermetic and mutates no target file.
        before = snapshot(target)
        with patch.object(sys.modules[__name__], "_service_up", return_value=False):
            receipt = run(write=False, target_root=target)
        after = snapshot(target)
        checks.append(("target dry run mutates nothing", before == after == {}))
        checks.append(("target dry run emits all three plan steps",
                       receipt["mode"] == "dry_run" and len(receipt["steps"]) == 3))
        hook_step = next(step for step in receipt["steps"] if step["step"] == "hook")
        checks.append(("target hook is supported in the dry-run plan",
                       hook_step.get("supported") is True and hook_step.get("wrote") is False))

        # (c) write creates valid MCP config; a second write is byte-identical.
        first = apply_mcp(write=True, target_root=target)
        mcp_path = target / ".mcp.json"
        created = json.loads(mcp_path.read_text(encoding="utf-8"))
        first_bytes = mcp_path.read_bytes()
        second = apply_mcp(write=True, target_root=target)
        checks.append(("write creates valid target MCP config",
                       first["ok"] and set(created["mcpServers"]) == set(_MCP_SERVERS)))
        checks.append(("target MCP rerun is idempotent",
                       second["added"] == [] and mcp_path.read_bytes() == first_bytes))
        checks.append(("written MCP config is owner-only",
                       stat.S_IMODE(mcp_path.stat().st_mode) == 0o600))

        # (d) unrelated existing servers and top-level fields survive the merge.
        existing_target = temp / "existing-project"
        existing_target.mkdir()
        existing_path = existing_target / ".mcp.json"
        existing_path.write_text(json.dumps({"mcpServers": {"custom-server": {"command": "custom"}},
                                             "projectField": {"keep": True}}), encoding="utf-8")
        merge = apply_mcp(write=True, target_root=existing_target)
        merged = json.loads(existing_path.read_text(encoding="utf-8"))
        checks.append(("existing MCP entries and top-level fields survive",
                       merge["ok"] and merged["mcpServers"]["custom-server"] == {"command": "custom"}
                       and merged["projectField"] == {"keep": True}))

        # (e) malformed JSON is refused byte-for-byte.
        bad_target = temp / "bad-json-project"
        bad_target.mkdir()
        bad_path = bad_target / ".mcp.json"
        bad_path.write_text("{ definitely-not-json", encoding="utf-8")
        bad_before = bad_path.read_bytes()
        refused = apply_mcp(write=True, target_root=bad_target)
        checks.append(("bad target MCP JSON is refused without mutation",
                       refused["ok"] is False and bad_path.read_bytes() == bad_before))

        # A pre-existing command under our public name is preserved but cannot produce a success receipt.
        conflict_target = temp / "conflicting-command-project"
        conflict_target.mkdir()
        conflict_path = conflict_target / ".mcp.json"
        conflicting = {"mcpServers": {"aidevobserver": {
            "command": "python3", "args": ["/untrusted/not-our-server.py"],
        }}}
        conflict_path.write_text(json.dumps(conflicting), encoding="utf-8")
        conflict_before = conflict_path.read_bytes()
        conflict = apply_mcp(write=True, target_root=conflict_target)
        checks.append(("conflicting preserved MCP command is not reported as installed",
                       conflict["ok"] is False and conflict.get("conflicts") == ["aidevobserver"]
                       and conflict_path.read_bytes() == conflict_before))

        # Neither the target config nor its lock may be redirected through a symlink.
        symlink_target = temp / "symlink-project"
        symlink_target.mkdir()
        victim = temp / "victim.json"
        victim.write_text('{"preserve":true}', encoding="utf-8")
        (symlink_target / ".mcp.json").symlink_to(victim)
        symlink_refused = apply_mcp(write=True, target_root=symlink_target)
        checks.append(("symlink MCP config is refused without touching its target",
                       symlink_refused["ok"] is False and victim.read_text(encoding="utf-8") == '{"preserve":true}'))

        lock_target = temp / "symlink-lock-project"
        lock_target.mkdir()
        (lock_target / ".mcp.json.lock").symlink_to(victim)
        lock_refused = apply_mcp(write=True, target_root=lock_target)
        checks.append(("symlink MCP lock is refused", lock_refused["ok"] is False))

        # The target-aware registrar writes only the selected external project.
        default_settings = _project_root() / ".claude" / "settings.json"
        default_before = default_settings.read_bytes() if default_settings.exists() else None
        installed_hook = apply_hook(write=True, target_root=target)
        target_settings = target / ".claude" / "settings.json"
        first_hook_bytes = target_settings.read_bytes()
        repeated_hook = apply_hook(write=True, target_root=target)
        default_after = default_settings.read_bytes() if default_settings.exists() else None
        checks.append(("external target hook installs only into the selected project",
                       installed_hook.get("wrote") is True and target_settings.exists()
                       and "aidevobserver_hook" in target_settings.read_text(encoding="utf-8")
                       and default_before == default_after))
        checks.append(("external target hook rerun is byte-idempotent",
                       repeated_hook["ok"] and target_settings.read_bytes() == first_hook_bytes))

        # Verification inspects the actual installed entry before invoking our known script; it never runs an
        # arbitrary preserved command.  The correctly installed target gets a green MCP receipt.
        with patch.object(sys.modules[__name__], "_mcp_handshake", return_value=(True, ["primitive_search"])), \
             patch.object(sys.modules[__name__], "_service_up", return_value=True):
            verified = verify(target)
            conflicted_verify = verify(conflict_target)
        verified_mcp = next(step for step in verified if step["step"] == "verify_mcp:aidevobserver")
        conflict_mcp = next(step for step in conflicted_verify if step["step"] == "verify_mcp:aidevobserver")
        checks.append(("verification handshakes the exact installed command",
                       verified_mcp["ok"] is True and verified_mcp["configured_command_matches"] is True))
        checks.append(("verification refuses a different preserved command without executing it",
                       conflict_mcp["ok"] is False and conflict_mcp["configured_command_matches"] is False))
        checks.append(("public detail sanitizer removes terminal controls and newlines",
                       "\x1b" not in _safe_text("bad\x1b[31m\nline") and "\n" not in _safe_text("bad\nline")))

        # (f) governance
        checks.append(("receipt + steps are candidate/serves_truth=false",
                       receipt["serves_truth"] is False
                       and all(s["serves_truth"] is False for s in receipt["steps"])))
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - quickstart_aidevobserver: ONE command can target this checkout or an arbitrary existing coding "
          "project — MCP and hook merges are idempotent and preserve existing entries; malformed JSON is refused; "
          "external targets receive their own hook without modifying the monorepo; the observer service still "
          "launches from the substrate. Hermetic target dry-run "
          "proven mutation-free. serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--write", action="store_true", help="apply the plan (default: dry-run print)")
    ap.add_argument("--target", type=Path,
                    help="existing coding-project directory to onboard (default: this monorepo)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    receipt = run(write=args.write, target_root=args.target)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
