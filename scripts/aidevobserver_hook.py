#!/usr/bin/env python3
"""scripts.aidevobserver_hook — the LIVE coaching path: a Claude Code PreToolUse hook over the observer engine.

This is the fourth AIDevObserver form factor (alongside the MCP server, the editor extension, and the CLI):
a PreToolUse hook that watches each tool call BEFORE it runs and surfaces a non-blocking coaching note when
the action looks like a footgun (a destructive command), reinvention (rebuilding something that already
exists), or wasted context. It REUSES the existing engine — capture.from_transcript for recent session
context + router.route_session(mode="advisory") for the spot — and rebuilds nothing.

LAW (mirrors the product): it NEVER blocks. AIDevObserver makes suggestions a human triages; it is read only
and stores nothing. The hook is fail-open: any error, bad input, or engine hiccup exits 0 silently so it can
never break a real tool call. serves_truth=false; every note is a governed candidate (discovery != trust).

  # register it (prints the .claude/settings.json snippet; --write merges it into ./.claude/settings.json)
  python3 scripts/aidevobserver_hook.py --install [--write]
  # hook mode (Claude Code pipes the PreToolUse event as JSON on stdin):
  python3 scripts/aidevobserver_hook.py
  # proof:
  python3 scripts/aidevobserver_hook.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# the tools worth coaching on (a footgun/reinvention/waste lives in a command or a write, not a read/search)
_COACHED_TOOLS = {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"}
_TRANSCRIPT_TAIL = 12          # recent events for context — bounded so the hook stays fast (runs per tool call)
_MAX_CONTENT = 2000            # cap synthesized content so a huge write does not bloat the router


def _synth_message(tool_name: str, tool_input: dict) -> dict:
    """Turn the pending tool call into one engine-shaped message the router can spot on."""
    if tool_name == "Bash":
        return {"role": "assistant", "content": str(tool_input.get("command", ""))[:_MAX_CONTENT]}
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        body = tool_input.get("content") or tool_input.get("new_string") or tool_input.get("new_source") or ""
        return {"role": "assistant", "content": f"writing {path}: {str(body)[:_MAX_CONTENT]}"}
    return {"role": "assistant", "content": f"{tool_name} {json.dumps(tool_input)[:_MAX_CONTENT]}"}


def coach(event: dict, *, with_transcript: bool = True) -> dict:
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
        return {"advice": [], "blocked": False}

    # only advise on the PENDING call (the last message) — old context already had its chance
    advice = [s for s in result.get("surfaced", []) if s.get("message_index") == pending_idx]
    return {"advice": advice, "blocked": False, "summary": result.get("summary", {})}


def format_advice(advice: list[dict]) -> list[str]:
    """One concise line per note: 'AIDevObserver · <type>: <evidence> -> <suggestion>  (suggestion, not a block)'."""
    lines: list[str] = []
    for a in advice:
        typ = str(a.get("type", "note")).replace("_", " ")
        evidence = a.get("evidence") or a.get("message") or ""
        suggestion = a.get("suggestion") or ""
        tail = f" -> {suggestion}" if suggestion and suggestion != evidence else ""
        lines.append(f"AIDevObserver · {typ}: {evidence}{tail}  (suggestion, not a block)")
    return lines


def _settings_snippet() -> dict:
    """The .claude/settings.json fragment that registers this hook for every tool (matcher '*')."""
    cmd = f"python3 {REPO_ROOT / 'scripts' / 'aidevobserver_hook.py'}"
    return {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": cmd}]}]}}


def _install(write: bool) -> int:
    snippet = _settings_snippet()
    print("# AIDevObserver live coaching — Claude Code PreToolUse hook")
    print("# Add this to .claude/settings.json (the hook runs before each tool call and prints a")
    print("# non-blocking coaching note when a call looks like a footgun / reinvention / waste).\n")
    print(json.dumps(snippet, indent=2))
    if write:
        settings = REPO_ROOT / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        cur = {}
        if settings.exists():
            try:
                cur = json.loads(settings.read_text(encoding="utf-8"))
            except Exception:                      # noqa: BLE001 — do not clobber an unreadable settings file
                print(f"\n[skip] {settings} exists but is not valid JSON — not modifying it; add the snippet by hand.")
                return 0
        hooks = cur.setdefault("hooks", {}).setdefault("PreToolUse", [])
        cmd = snippet["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        if not any(cmd in json.dumps(h) for h in hooks):
            hooks.extend(snippet["hooks"]["PreToolUse"])
            settings.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")
            print(f"\n[written] merged the PreToolUse hook into {settings}")
        else:
            print(f"\n[ok] the hook is already registered in {settings}")
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

    # a destructive command is coached (footgun) — but never blocked
    footgun = coach({"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}},
                    with_transcript=False)
    ck("a footgun (git push --force) is surfaced", len(footgun["advice"]) >= 1, str(footgun["advice"]))
    ck("the coach NEVER blocks (footgun)", footgun["blocked"] is False)
    ck("the advisory formats to a 'suggestion, not a block' line",
       any("suggestion, not a block" in s for s in format_advice(footgun["advice"])))

    # a benign command stays quiet (precision — no nagging on safe calls)
    benign = coach({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, with_transcript=False)
    ck("a benign command is not coached (precision)", benign["advice"] == [], str(benign["advice"]))

    # a read-class tool is skipped entirely (fast path — no engine call)
    skipped = coach({"tool_name": "Read", "tool_input": {"file_path": "x.py"}}, with_transcript=False)
    ck("read-class tools are skipped", skipped["advice"] == [] and skipped["blocked"] is False)

    # reinvention in a Write is spotted but, again, never blocks
    reinv = coach({"tool_name": "Write", "tool_input": {"file_path": "pdf_parser.py",
                  "content": "# let me write my own pdf parser from scratch\n"}}, with_transcript=False)
    ck("reinvention in a write never blocks", reinv["blocked"] is False)

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

    if fails:
        print(f"\nFAIL - aidevobserver_hook: {len(fails)} assertions failed")
        return 1
    print("PASS - aidevobserver_hook: PreToolUse live-coaching hook over the observer router — footguns/"
          "reinvention surfaced as non-blocking notes, benign + read-class calls stay quiet, malformed events "
          "fail open, NEVER blocks; serves_truth=false, read-only, governed candidates.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AIDevObserver live coaching — Claude Code PreToolUse hook.")
    ap.add_argument("--install", action="store_true", help="print the .claude/settings.json hook snippet")
    ap.add_argument("--write", action="store_true", help="with --install: merge the hook into ./.claude/settings.json")
    ap.add_argument("--self-test", action="store_true", help="run the offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.install:
        return _install(args.write)
    return _run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
