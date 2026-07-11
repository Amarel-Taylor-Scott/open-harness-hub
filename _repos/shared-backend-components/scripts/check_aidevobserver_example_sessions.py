"""Validate the AIDevObserver replayable example session pack.

The examples are synthetic demo inputs for AIDevObserver/AIDevExplorer. They are downloadable/uploadable
artifacts, but they are still candidate evidence only: no example, finding, or replay serves truth.
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
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
import re
import sys
from pathlib import Path


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
sys.path.insert(0, str(REPO))

from src.teleon.observer.review import review_session

EXAMPLES_DIR = _resource("web/aidevobserver/examples")
MANIFEST_PATH = EXAMPLES_DIR / "manifest.json"
APP_JS_PATH = _resource("web/aidevobserver/aidevobserver-main.jsx")
SECRET_PATTERNS = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
REQUIRED_JS_MARKERS = (
    "SESSION_REPLAY_EXAMPLES",
    "openSessionReplay",
    "ADO_EXAMPLE_SESSION_TEXT_KEY",
    "parseSessionJson",
    "SessionReplayGrid",
)


def parse_text_transcript(text: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^(user|agent|assistant|tool|system)\s*:\s*(.*)$", line, re.I)
        if not match:
            messages.append({"role": "user", "content": line})
            continue
        role = match.group(1).lower()
        messages.append({"role": "assistant" if role == "agent" else role, "content": match.group(2)})
    return messages


def parse_jsonl_transcript(text: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"line {line_no} is not a JSON object")
        role = str(obj.get("role") or "user")
        content = obj.get("content", obj.get("text", obj.get("message", "")))
        messages.append({"role": "assistant" if role == "agent" else role, "content": str(content)})
    return messages


def has_secret_like_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def check_manifest(fails: list[str]) -> list[dict]:
    if not MANIFEST_PATH.exists():
        fails.append("manifest missing")
        return []
    manifest = json.loads(MANIFEST_PATH.read_text())
    if manifest.get("serves_truth") is not False:
        fails.append("manifest must declare serves_truth=false")
    sessions = manifest.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        fails.append("manifest must contain sessions")
        return []
    return sessions


def check_session_files(sessions: list[dict], fails: list[str]) -> tuple[int, int]:
    txt_count = 0
    jsonl_count = 0
    finding_sessions = 0
    synthetic_public_project_sessions = 0
    for session in sessions:
        sid = session.get("id", "<missing>")
        source_kind = session.get("source_kind")
        if source_kind == "synthetic_from_public_project":
            synthetic_public_project_sessions += 1
        for key, parser in (("txt", parse_text_transcript), ("jsonl", parse_jsonl_transcript)):
            rel = session.get(key)
            if not rel:
                fails.append(f"{sid}: missing {key} file reference")
                continue
            path = EXAMPLES_DIR / rel
            if not path.exists():
                fails.append(f"{sid}: {rel} missing")
                continue
            text = path.read_text()
            if has_secret_like_text(text):
                fails.append(f"{sid}: {rel} contains secret-like text")
            if source_kind == "synthetic_from_public_project" and "synthetic_from_public_project" not in text:
                fails.append(f"{sid}: {rel} must preserve synthetic_from_public_project labeling")
            try:
                messages = parser(text)
            except Exception as exc:  # noqa: BLE001 - proof script reports all failures.
                fails.append(f"{sid}: {rel} parse failed: {exc}")
                continue
            if len(messages) < 4:
                fails.append(f"{sid}: {rel} should contain at least 4 messages")
            if not any(m["role"] == "user" for m in messages):
                fails.append(f"{sid}: {rel} should contain a user message")
            if not any(m["role"] == "assistant" for m in messages):
                fails.append(f"{sid}: {rel} should contain an assistant message")
            if key == "txt":
                txt_count += 1
                report = review_session(messages)
                repeat = review_session(messages)
                if report != repeat:
                    fails.append(f"{sid}: review is not deterministic")
                if report.get("serves_truth") is not False:
                    fails.append(f"{sid}: review must be serves_truth=false")
                if not all(f.get("candidate") is True and f.get("serves_truth") is False for f in report.get("report", [])):
                    fails.append(f"{sid}: every finding must be a governed candidate")
                if report.get("report"):
                    finding_sessions += 1
            else:
                jsonl_count += 1
    if synthetic_public_project_sessions < 3:
        fails.append(f"expected at least 3 synthetic_from_public_project examples, got {synthetic_public_project_sessions}")
    return txt_count + jsonl_count, finding_sessions


def check_ui_references(sessions: list[dict], fails: list[str]) -> None:
    if not APP_JS_PATH.exists():
        fails.append("AIDevObserver app JS missing")
        return
    js = APP_JS_PATH.read_text()
    for marker in REQUIRED_JS_MARKERS:
        if marker not in js:
            fails.append(f"app missing marker {marker}")
    for session in sessions:
        sid = session.get("id", "")
        if sid and sid not in js:
            fails.append(f"app does not expose replay example {sid}")


def _self_test() -> int:
    fails: list[str] = []
    sessions = check_manifest(fails)
    checked_files, finding_sessions = check_session_files(sessions, fails)
    check_ui_references(sessions, fails)
    if checked_files < 16:
        fails.append(f"expected at least 16 transcript files, checked {checked_files}")
    if finding_sessions < 3:
        fails.append(f"expected at least 3 examples with observer findings, got {finding_sessions}")
    if fails:
        print("FAIL - aidevobserver example sessions")
        for fail in fails:
            print(f"  [XX] {fail}")
        return 1
    print(
        "PASS - aidevobserver example sessions: "
        f"{len(sessions)} replay demos, {checked_files} upload/download files, "
        f"{finding_sessions} sessions with governed findings; serves_truth=false."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
