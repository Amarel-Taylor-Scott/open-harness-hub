"""observer.capture — the capture seam (the Spotter memo §3): normalize heterogeneous AI-tool sessions into ONE
event stream the router/reviewer consume. Capture and review become the same data used differently.

Claude Code (and Codex, near-identical) persist sessions as JSONL on disk — so review works with ZERO live install.
Each line carries message.role + content, where content is a str (user text) or typed blocks (thinking/text/
tool_use/tool_result). This flattens that into [{role, content, kind}], dropping system noise (command caveats,
stdout, empty thinking) and summarizing tool_use as 'Tool path: <head>' so reinvention/genome detection sees what was
built. serves_truth=false; reads only, never republishes session content.
"""
from __future__ import annotations

import json
from pathlib import Path

# content the reviewer should ignore (slash-command plumbing injected by the client, not real usage).
_NOISE_MARKERS = ("<local-command-stdout>", "<local-command-caveat>", "<command-name>", "<command-message>",
                  "<command-args>")
_TOOL_INPUT_KEYS = ("command", "file_path", "path", "pattern", "query", "content", "prompt", "url")
_HEAD = 240  # chars of a tool input / block we keep as the event's text (enough for intent, bounded)


def _summarize_tool(name: str, tool_input: dict) -> str:
    """A compact 'what the agent did' line: the tool + its most salient input (path/command/etc.)."""
    parts = [str(tool_input[k]) for k in _TOOL_INPUT_KEYS if k in tool_input and tool_input[k]]
    detail = " ".join(parts)[:_HEAD]
    return f"{name}: {detail}".strip()


def _flatten_content(role: str, content) -> list[dict]:
    """One message -> 0+ normalized events. str content -> one prompt/text; block list -> one event per text/tool_use."""
    out: list[dict] = []
    if isinstance(content, str):
        if content.strip() and not any(m in content for m in _NOISE_MARKERS):
            out.append({"role": role, "content": content.strip(), "kind": "prompt" if role == "user" else "text"})
        return out
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text" and b.get("text", "").strip():
                out.append({"role": role, "content": b["text"].strip(), "kind": "text"})
            elif bt == "tool_use":
                out.append({"role": role, "content": _summarize_tool(b.get("name", "tool"), b.get("input", {})),
                            "kind": "tool_use", "tool": b.get("name")})
            elif bt == "tool_result":
                c = b.get("content", "")
                txt = c if isinstance(c, str) else json.dumps(c)
                if txt.strip():
                    out.append({"role": "tool", "content": txt[: _HEAD * 8], "kind": "tool_result"})
            # thinking blocks are intentionally dropped (private reasoning, not usage signal)
    return out


def normalize_messages(records) -> list[dict]:
    """Generic: an iterable of transcript line-dicts (Claude Code / Codex shape) -> normalized events."""
    events: list[dict] = []
    for o in records:
        if not isinstance(o, dict):
            continue
        msg = o.get("message")
        if isinstance(msg, dict) and "content" in msg:
            events.extend(_flatten_content(msg.get("role", o.get("type", "user")), msg["content"]))
        elif o.get("type") in ("user", "assistant") and "content" in o:
            events.extend(_flatten_content(o["type"], o["content"]))
    return events


def from_transcript(path: str | Path) -> list[dict]:
    """Read a Claude Code / Codex JSONL transcript file -> normalized events ready for review_session."""
    lines = Path(path).read_text().splitlines()
    parsed = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            continue  # tolerate partial/corrupt lines (capture must never crash a review)
    return normalize_messages(parsed)


_SYNTHETIC = [
    {"type": "mode", "mode": "opus"},  # noise -> skipped
    {"type": "user", "message": {"role": "user", "content": "<local-command-stdout>set model</local-command-stdout>"}},
    {"type": "user", "message": {"role": "user", "content": "let me build a custom retry with exponential backoff"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": "secret reasoning"},
        {"type": "text", "text": "Sure, writing it now."},
        {"type": "tool_use", "name": "Write", "input": {"file_path": "/x/retry.py", "content": "def retry(): ..."}}]}},
    {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "wrote 12 lines"}]}},
]


def _self_test() -> int:
    from .review import review_session
    fails, checks = [], 0

    def ck(name, ok):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}")

    ev = normalize_messages(_SYNTHETIC)
    kinds = {e["kind"] for e in ev}
    ck("the user prompt is captured", any(e["kind"] == "prompt" and "retry" in e["content"] for e in ev))
    ck("assistant text is captured", any(e["kind"] == "text" for e in ev))
    ck("tool_use is summarized (tool + path)", any(
        e["kind"] == "tool_use" and "Write" in e["content"] and "retry.py" in e["content"] for e in ev))
    ck("tool_result captured for waste detection", "tool_result" in kinds)
    ck("private thinking blocks are dropped", not any("secret reasoning" in e["content"] for e in ev))
    ck("slash-command stdout noise is filtered", not any("set model" in e["content"] for e in ev))
    ck("the mode/system line is skipped", all(e["role"] in ("user", "assistant", "tool") for e in ev))

    # the captured stream feeds the reviewer end-to-end and surfaces the stack reinvention (retry -> tenacity)
    rep = review_session(ev)
    ck("captured stream -> reviewer runs", "report" in rep and rep["serves_truth"] is False)
    ck("reviewer finds the retry stack reinvention from the captured prompt", any(
        f["type"] in ("stack_reinvention", "reinvention", "adversarial") for f in rep["report"]))

    if fails:
        print(f"\nFAIL - observer.capture: {len(fails)} of {checks} failed")
        return 1
    print(f"PASS - observer.capture: normalizes Claude Code/Codex transcripts -> one event stream (drops thinking + "
          f"slash-command noise, summarizes tool_use), feeds the reviewer end-to-end; {checks} assertions; "
          f"serves_truth=false, read-only.")
    return 0
