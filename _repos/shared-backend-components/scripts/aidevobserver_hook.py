#!/usr/bin/env python3
"""scripts.aidevobserver_hook — the LIVE coaching path: a Claude Code PreToolUse hook over the observer engine.

This is the fourth AIDevObserver form factor (alongside the MCP server, the editor extension, and the CLI):
a PreToolUse hook that watches each tool call BEFORE it runs and surfaces a non-blocking coaching note when
the action looks like a footgun (a destructive command), reinvention (rebuilding something that already
exists), or wasted context. It REUSES the existing engine — capture.from_transcript for recent session
context + router.route_session(mode="advisory") for the spot — and rebuilds nothing.

LAW (mirrors the product): it NEVER blocks. AIDevObserver makes suggestions a human triages; primitive sources
remain read-only. It stores only a short-lived hash+primitive-id dedupe cache so it does not repeat the same
advice; no source or prompt body enters that cache. The hook is fail-open: any error, bad input, or engine hiccup exits 0 silently so it can
never break a real tool call. serves_truth=false; every note is a governed candidate (discovery != trust).

  # register it (prints the .claude/settings.json snippet; --write merges it into ./.claude/settings.json)
  python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --install [--write] [--target PROJECT]
  # hook mode (Claude Code pipes the PreToolUse event as JSON on stdin):
  python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py
  # proof:
  python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --self-test
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*`/
# `from src.*` on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch (this is an auto-firing
# PreToolUse hook launched from the repo root). install() prepends every code root so both import families resolve.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
import time

# REPO_ROOT stays the MONOREPO root — it is the workspace root this hook installs .claude/settings.json into.
REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])

from src.teleon.observer.settings import HOOK_SETTINGS  # noqa: E402

# the tools worth coaching on (a footgun/reinvention/waste lives in a command or a write, not a read/search)
_COACHED_TOOLS = {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"}
_TRANSCRIPT_TAIL = HOOK_SETTINGS.transcript_tail_events
_MAX_CONTENT = HOOK_SETTINGS.max_synthesized_content_chars
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
_MAX_REUSE_QUERY_TOKENS = 32
_DEDUPE_TTL_SECONDS = 24 * 60 * 60
_MAX_DEDUPE_BYTES = 1 * 1024 * 1024
_MAX_DEDUPE_ENTRIES = 4_096
_MAX_SETTINGS_BYTES = 4 * 1024 * 1024
_MAX_TERMINAL_FIELD_CHARS = 1_000


def _default_dedupe_path() -> Path:
    """A private per-user cache, never a predictable shared-/tmp file."""

    configured = os.environ.get("XDG_CACHE_HOME", "")
    base = Path(configured).expanduser() if configured and Path(configured).is_absolute() else Path.home() / ".cache"
    return base / "aidevobserver" / "hook-dedupe.json"


_DEDUPE_PATH = _default_dedupe_path()
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _terminal_text(value: object, *, maximum: int = _MAX_TERMINAL_FIELD_CHARS) -> str:
    """Collapse one untrusted field to printable one-line terminal text."""

    without_ansi = _ANSI_ESCAPE_RE.sub("", str(value))
    printable = "".join(ch if ch.isprintable() else " " for ch in without_ansi)
    return " ".join(printable.split())[:maximum]


def _nofollow_flag() -> int:
    return getattr(os, "O_NOFOLLOW", 0)


def _ensure_private_cache_dir(path: Path) -> None:
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.is_symlink():
        raise OSError("cache directory is a symlink")
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise OSError("cache directory is not user-owned")
    os.chmod(path, 0o700)


def _read_small_json_nofollow(path: Path, *, maximum_bytes: int) -> dict:
    if path.is_symlink():
        raise OSError("refusing symlink")
    try:
        fd = os.open(path, os.O_RDONLY | _nofollow_flag())
    except FileNotFoundError:
        return {}
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_size > maximum_bytes:
            raise OSError("unsafe cache/config file")
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = json.load(handle)
    finally:
        if fd >= 0:
            os.close(fd)
    return value if isinstance(value, dict) else {}


def _atomic_json_replace(path: Path, value: dict) -> None:
    """Write owner-only JSON beside its target and replace atomically without following a target symlink."""

    if path.is_symlink():
        raise OSError("refusing symlink")
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise OSError("refusing symlink")
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


def _synth_message(tool_name: str, tool_input: dict) -> dict:
    """Turn the pending tool call into one engine-shaped message the router can spot on."""
    if tool_name == "Bash":
        return {"role": "assistant", "content": str(tool_input.get("command", ""))[:_MAX_CONTENT]}
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        body = tool_input.get("content") or tool_input.get("new_string") or tool_input.get("new_source") or ""
        return {"role": "assistant", "content": f"writing {path}: {str(body)[:_MAX_CONTENT]}"}
    return {"role": "assistant", "content": f"{tool_name} {json.dumps(tool_input)[:_MAX_CONTENT]}"}


def _reuse_query(tool_input: dict, messages: list[dict]) -> str:
    """Build a compact local-search query from intent, path, and changed symbols—not whole source bodies."""

    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    body = str(
        tool_input.get("content")
        or tool_input.get("new_string")
        or tool_input.get("new_source")
        or ""
    )
    latest_user = next(
        (str(message.get("content") or "") for message in reversed(messages) if message.get("role") == "user"),
        "",
    )
    symbols = re.findall(
        r"\b(?:def|class|function|async\s+def)\s+([A-Za-z_][A-Za-z0-9_]*)|"
        r"\b([A-Za-z_][A-Za-z0-9_]{3,})\b",
        body[:_MAX_CONTENT],
    )
    flattened = [left or right for left, right in symbols]
    seed = " ".join((Path(path).stem.replace("_", " "), latest_user[-1_000:], " ".join(flattened)))
    tokens = re.findall(r"[A-Za-z0-9_]+", seed)
    stop = {"this", "that", "with", "from", "return", "self", "none", "true", "false", "import",
            "write", "writing", "file", "into", "have", "will", "should", "then", "when"}
    selected = [token for token in dict.fromkeys(tokens) if token.lower() not in stop]
    return " ".join(selected[:_MAX_REUSE_QUERY_TOKENS])


def _strong_reuse_advice(query: str, federation=None) -> list[dict]:
    if not query.strip():
        return []
    try:
        if federation is None:
            from scripts.primitive_search_federation import PrimitiveSearchFederation

            federation = PrimitiveSearchFederation()
        if hasattr(federation, "search_trusted_recipes"):
            response = federation.search_trusted_recipes(query, limit=3)
        else:
            response = federation.search(query, limit=3, sync=False)
    except Exception:  # noqa: BLE001 - full-corpus search is advisory and must fail open
        return []
    strong: list[dict] = []
    for row in response.get("results") or []:
        scope = str(row.get("verification_scope") or "")
        if scope not in {
            "descriptor_specific_execution",
            "recipe_specific_hidden_oracle_execution",
        }:
            continue
        primitive_id = str(row.get("primitive_id") or "")
        if not primitive_id:
            continue
        strong.append(
            {
                "type": "primitive_reuse_match",
                "primitive_id": primitive_id,
                "evidence": f"{primitive_id} · {row.get('title') or 'matching primitive'}",
                "suggestion": (
                    f"Inspect with primitive_get; {row.get('input_edge') or '?'} -> "
                    f"{row.get('output_edge') or '?'}; proof={row.get('proof_status') or 'unverified'}"
                ),
                "verification_scope": scope,
                "receipt_id": (row.get("trusted_receipt") or {}).get("receipt_id"),
                "candidate": True,
                "serves_truth": False,
            }
        )
    return strong


def _dedupe_reuse(advice: list[dict], event: dict, *, path: Path = _DEDUPE_PATH) -> list[dict]:
    """Suppress repeat primitive suggestions using only a hashed session key and primitive id."""

    reuse = [row for row in advice if row.get("type") == "primitive_reuse_match"]
    if not reuse:
        return advice
    session = str(event.get("session_id") or event.get("transcript_path") or event.get("cwd") or "anonymous")
    session_digest = hashlib.sha256(session.encode("utf-8")).hexdigest()[:24]
    now = time.time()
    lock_path = path.with_name(f".{path.name}.lock")
    try:
        _ensure_private_cache_dir(path.parent)
        if lock_path.is_symlink():
            raise OSError("refusing symlink lock")
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | _nofollow_flag(), 0o600)
        with os.fdopen(lock_fd, "a+", encoding="utf-8") as lock:
            info = os.fstat(lock.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or info.st_nlink != 1):
                raise OSError("unsafe lock")
            os.fchmod(lock.fileno(), 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = _read_small_json_nofollow(path, maximum_bytes=_MAX_DEDUPE_BYTES)
            except (json.JSONDecodeError, UnicodeError):
                state = {}
            if not isinstance(state, dict):
                state = {}
            state = {key: float(value) for key, value in state.items()
                     if isinstance(value, (int, float)) and now - float(value) < _DEDUPE_TTL_SECONDS}
            kept: list[dict] = []
            for row in advice:
                if row.get("type") != "primitive_reuse_match":
                    kept.append(row)
                    continue
                primitive_id = str(row.get("primitive_id") or "")[:512]
                key = f"{session_digest}:{primitive_id}"
                if key not in state:
                    kept.append(row)
                    state[key] = now
            if len(state) > _MAX_DEDUPE_ENTRIES:
                state = dict(sorted(state.items(), key=lambda item: item[1], reverse=True)[:_MAX_DEDUPE_ENTRIES])
            _atomic_json_replace(path, state)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            return kept
    except (OSError, ValueError):
        return advice


def coach(
    event: dict, *, with_transcript: bool = True, federation=None, dedupe_reuse: bool = True
) -> dict:
    """Pure core (no stdin/stdout): a PreToolUse event -> advisory notes about the PENDING call.

    Returns {advice:[finding...], blocked:False}. ALWAYS blocked=False — the coach never gates. Fail-open:
    any engine error yields no advice rather than raising (the hook must never break a real tool call)."""
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input") or {}
    if tool_name not in _COACHED_TOOLS or not isinstance(tool_input, dict):
        return {"advice": [], "blocked": False}

    messages: list[dict] = []
    transcript = event.get("transcript_path")
    if with_transcript and transcript:
        try:
            from src.teleon.observer.capture import from_transcript
            messages.extend(from_transcript(str(transcript))[-_TRANSCRIPT_TAIL:])
        except Exception:                          # noqa: BLE001 — context is a bonus, never required
            messages = []
    messages.append(_synth_message(tool_name, tool_input))
    pending_idx = len(messages) - 1

    try:
        from src.teleon.observer.router import route_session
        result = route_session(messages, mode="advisory")
    except Exception:                              # noqa: BLE001 — fail-open: no coaching beats a broken tool call
        result = {"surfaced": [], "summary": {"router_error": "fail_open"}}

    # only advise on the PENDING call (the last message) — old context already had its chance
    advice = [s for s in result.get("surfaced", []) if s.get("message_index") == pending_idx]
    if tool_name in _WRITE_TOOLS:
        reuse_advice = _strong_reuse_advice(_reuse_query(tool_input, messages[:-1]), federation=federation)
        for row in reuse_advice:
            row["message_index"] = pending_idx
        advice.extend(reuse_advice)
    if dedupe_reuse:
        advice = _dedupe_reuse(advice, event)
    return {"advice": advice, "blocked": False, "summary": result.get("summary", {})}


def format_advice(advice: list[dict]) -> list[str]:
    """One concise line per note: 'AIDevObserver · <type>: <evidence> -> <suggestion>  (suggestion, not a block)'."""
    lines: list[str] = []
    for a in advice:
        typ = _terminal_text(str(a.get("type", "note")).replace("_", " "), maximum=80)
        evidence = _terminal_text(a.get("evidence") or a.get("message") or "")
        suggestion = _terminal_text(a.get("suggestion") or "")
        tail = f" -> {suggestion}" if suggestion and suggestion != evidence else ""
        lines.append(f"AIDevObserver · {typ}: {evidence}{tail}  (suggestion, not a block)")
    return lines


def _settings_snippet() -> dict:
    """The .claude/settings.json fragment that registers this hook for every tool (matcher '*')."""
    cmd = f"python3 {_resource('scripts/aidevobserver_hook.py')}"
    return {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": cmd}]}]}}


def _hook_registered(hooks: list, command: str) -> bool:
    for group in hooks:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            continue
        if any(isinstance(hook, dict) and hook.get("type") == "command" and hook.get("command") == command
               for hook in group["hooks"]):
            return True
    return False


def _install(write: bool, target_root: Path | None = None) -> int:
    snippet = _settings_snippet()
    root = Path(target_root).expanduser().resolve() if target_root is not None else REPO_ROOT
    if not root.is_dir():
        print(f"[error] target is not an existing directory: {_terminal_text(root)}")
        return 1
    print("# AIDevObserver live coaching — Claude Code PreToolUse hook")
    print("# Add this to .claude/settings.json (the hook runs before each tool call and prints a")
    print("# non-blocking coaching note when a call looks like a footgun / reinvention / waste).\n")
    print(json.dumps(snippet, indent=2))
    if write:
        settings = root / ".claude" / "settings.json"
        settings_dir = settings.parent
        lock_path = settings.with_name(f".{settings.name}.lock")
        try:
            if settings_dir.is_symlink():
                raise OSError("settings directory is a symlink")
            settings_dir.mkdir(parents=True, exist_ok=True)
            info = settings_dir.stat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
                raise OSError("settings directory is not user-owned")
            if lock_path.is_symlink():
                raise OSError("settings lock is a symlink")
            lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | _nofollow_flag(), 0o600)
            with os.fdopen(lock_fd, "a+", encoding="utf-8") as lock:
                lock_info = os.fstat(lock.fileno())
                if (not stat.S_ISREG(lock_info.st_mode) or lock_info.st_uid != os.geteuid()
                        or lock_info.st_nlink != 1):
                    raise OSError("settings lock is unsafe")
                os.fchmod(lock.fileno(), 0o600)
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                cur = _read_small_json_nofollow(settings, maximum_bytes=_MAX_SETTINGS_BYTES)
                if not isinstance(cur.get("hooks", {}), dict):
                    raise ValueError("settings hooks is not an object")
                hooks = cur.setdefault("hooks", {}).setdefault("PreToolUse", [])
                if not isinstance(hooks, list):
                    raise ValueError("settings hooks.PreToolUse is not a list")
                cmd = snippet["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
                if not _hook_registered(hooks, cmd):
                    hooks.extend(snippet["hooks"]["PreToolUse"])
                    _atomic_json_replace(settings, cur)
                    print(f"\n[written] merged the PreToolUse hook into {_terminal_text(settings)}")
                else:
                    print(f"\n[ok] the hook is already registered in {_terminal_text(settings)}")
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except (OSError, ValueError, json.JSONDecodeError, UnicodeError):
            print(f"\n[skip] {_terminal_text(settings)} is unsafe, unreadable, or incompatible — not modifying it.")
            return 1
    else:
        print("\n# (re-run with --write to merge it into ./.claude/settings.json automatically)")
    return 0


def _run_hook() -> int:
    """Hook mode: read the PreToolUse event from stdin, print any advisory to stderr, ALWAYS exit 0."""
    try:
        event = json.load(sys.stdin)
    except Exception:                              # noqa: BLE001 — fail-open on any malformed input
        return 0
    try:
        for line in format_advice(coach(event).get("advice", [])):
            print(line, file=sys.stderr)
    except Exception:                              # noqa: BLE001 — a coaching note must never break the tool call
        pass
    return 0


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    class _FixtureFederation:
        def search(self, query, *, limit, sync):
            if "jwt" not in query.lower() and "pdf" not in query.lower():
                return {"results": []}
            return {
                "results": [
                    {
                        "primitive_id": "prim:test:verified-parser",
                        "title": "Validate JWT or parse PDF",
                        "input_edge": "UntrustedDocument",
                        "output_edge": "ValidatedPayload",
                        "verification_scope": "recipe_specific_hidden_oracle_execution",
                        "proof_status": "passed",
                        "trusted_receipt": {"receipt_id": "receipt/fixture"},
                    }
                ]
            }

    # a destructive command is coached (footgun) — but never blocked
    footgun = coach({"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}},
                    with_transcript=False)
    ck("a footgun (git push --force) is surfaced", len(footgun["advice"]) >= 1, str(footgun["advice"]))
    ck("the coach NEVER blocks (footgun)", footgun["blocked"] is False)
    ck("the advisory formats to a 'suggestion, not a block' line",
       any("suggestion, not a block" in s for s in format_advice(footgun["advice"])))
    hostile_line = format_advice([{
        "type": "note\x1b[31m", "evidence": "first\nsecond\x1b[2J", "suggestion": "safe\rnext",
    }])[0]
    ck("terminal advice strips ANSI and control characters into one line",
       "\x1b" not in hostile_line and "\n" not in hostile_line and "\r" not in hostile_line
       and "[31m" not in hostile_line and "[2J" not in hostile_line, hostile_line)

    # a benign command stays quiet (precision — no nagging on safe calls)
    benign = coach({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, with_transcript=False)
    ck("a benign command is not coached (precision)", benign["advice"] == [], str(benign["advice"]))

    # a read-class tool is skipped entirely (fast path — no engine call)
    skipped = coach({"tool_name": "Read", "tool_input": {"file_path": "x.py"}}, with_transcript=False)
    ck("read-class tools are skipped", skipped["advice"] == [] and skipped["blocked"] is False)

    # reinvention in a Write is spotted but, again, never blocks
    reinv = coach({"tool_name": "Write", "tool_input": {"file_path": "pdf_parser.py",
                  "content": "# let me write my own pdf parser from scratch\n"}}, with_transcript=False,
                  federation=_FixtureFederation(), dedupe_reuse=False)
    ck("reinvention in a write never blocks", reinv["blocked"] is False)
    ck("ordinary writes search verified primitives without requiring a magic intent phrase",
       any(row.get("type") == "primitive_reuse_match" for row in reinv["advice"]), str(reinv["advice"]))
    ck("automatic reuse advice returns compact identity/edges and never a primitive body",
       all("body" not in row and "payload" not in row and "code" not in row for row in reinv["advice"]))

    novel = coach({"tool_name": "Write", "tool_input": {"file_path": "novel_consensus.py",
                  "content": "def original_consensus_lattice(): pass\n"}}, with_transcript=False,
                  federation=_FixtureFederation(), dedupe_reuse=False)
    ck("a novel write remains quiet on the direct primitive-search lane",
       not any(row.get("type") == "primitive_reuse_match" for row in novel["advice"]), str(novel["advice"]))

    # fail-open: malformed / empty events never raise and never block
    for bad in ({}, {"tool_name": "Bash"}, {"tool_name": "Bash", "tool_input": None}, {"tool_input": {"command": "x"}}):
        r = coach(bad, with_transcript=False)
        ck(f"malformed event is fail-open: {bad}", r["advice"] == [] and r["blocked"] is False)

    # the install snippet is a valid, registerable PreToolUse hook
    snip = _settings_snippet()
    hook = snip["hooks"]["PreToolUse"][0]
    ck("install snippet is a '*' PreToolUse command hook",
       hook["matcher"] == "*" and hook["hooks"][0]["type"] == "command"
       and "aidevobserver_hook.py" in hook["hooks"][0]["command"])
    ck("default dedupe cache is per-user rather than shared tmp",
       _DEDUPE_PATH.parent == _default_dedupe_path().parent
       and _DEDUPE_PATH != Path(tempfile.gettempdir()) / "aidevobserver-hook-dedupe.json")

    with tempfile.TemporaryDirectory(prefix="aidevobserver_hook_install_") as temp_dir:
        target = Path(temp_dir)
        cache_path = target / "private-cache" / "dedupe.json"
        reuse_row = {"type": "primitive_reuse_match", "primitive_id": "prim:test:one"}
        dedupe_event = {"session_id": "private-session-text"}
        first_advice = _dedupe_reuse([reuse_row], dedupe_event, path=cache_path)
        second_advice = _dedupe_reuse([reuse_row], dedupe_event, path=cache_path)
        cache_text = cache_path.read_text(encoding="utf-8")
        ck("dedupe cache suppresses repeats and stores no raw session text",
           first_advice == [reuse_row] and second_advice == []
           and "private-session-text" not in cache_text and "prim:test:one" in cache_text)
        ck("dedupe cache and lock are owner-only regular files",
           stat.S_ISREG(cache_path.stat().st_mode) and stat.S_IMODE(cache_path.stat().st_mode) == 0o600
           and stat.S_IMODE(cache_path.with_name(f".{cache_path.name}.lock").stat().st_mode) == 0o600)

        victim_cache = target / "cache-victim.json"
        victim_cache.write_text('{"preserve":true}', encoding="utf-8")
        symlink_cache = target / "symlink-cache" / "dedupe.json"
        symlink_cache.parent.mkdir()
        symlink_cache.symlink_to(victim_cache)
        fail_open_advice = _dedupe_reuse([reuse_row], dedupe_event, path=symlink_cache)
        ck("dedupe cache refuses symlink targets and fails open",
           fail_open_advice == [reuse_row]
           and victim_cache.read_text(encoding="utf-8") == '{"preserve":true}')

        settings = target / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
                                        "unrelated": {"preserve": True}}), encoding="utf-8")
        first = _install(True, target)
        first_bytes = settings.read_bytes()
        second = _install(True, target)
        installed = json.loads(settings.read_text(encoding="utf-8"))
        ck("installer targets an arbitrary project and preserves unrelated settings",
           first == 0 and installed["unrelated"] == {"preserve": True}
           and len(installed["hooks"]["PreToolUse"]) == 2)
        ck("external hook installation is byte-idempotent", second == 0 and settings.read_bytes() == first_bytes)

        malformed = target / "malformed"
        malformed.mkdir()
        malformed_settings = malformed / ".claude" / "settings.json"
        malformed_settings.parent.mkdir()
        malformed_settings.write_text("{not-json", encoding="utf-8")
        before = malformed_settings.read_bytes()
        ck("malformed external settings are refused byte-for-byte",
           _install(True, malformed) != 0 and malformed_settings.read_bytes() == before)

        symlink_install = target / "symlink-install"
        symlink_install.mkdir()
        symlink_settings_dir = symlink_install / ".claude"
        real_settings_dir = target / "real-settings"
        real_settings_dir.mkdir()
        symlink_settings_dir.symlink_to(real_settings_dir, target_is_directory=True)
        ck("installer refuses a symlink settings directory",
           _install(True, symlink_install) != 0 and not (real_settings_dir / "settings.json").exists())

    if fails:
        print(f"\nFAIL - aidevobserver_hook: {len(fails)} assertions failed")
        return 1
    print("PASS - aidevobserver_hook: PreToolUse live-coaching hook over the observer router — footguns/"
          "reinvention surfaced as non-blocking notes, benign + read-class calls stay quiet, malformed events "
          "fail open, NEVER blocks; source corpus read-only, metadata-only dedupe; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AIDevObserver live coaching — Claude Code PreToolUse hook.")
    ap.add_argument("--install", action="store_true", help="print the .claude/settings.json hook snippet")
    ap.add_argument("--write", action="store_true", help="with --install: merge the hook into ./.claude/settings.json")
    ap.add_argument("--target", type=Path, help="existing coding-project root to receive .claude/settings.json")
    ap.add_argument("--self-test", action="store_true", help="run the offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.install:
        return _install(args.write, args.target)
    return _run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
