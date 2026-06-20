"""scripts.security.response_redaction — the ONE secret-redaction allow-list + scrubber for the API
handlers.

A redaction list copied per-handler DRIFTS — and it did: some api_*_handler.py copies were missing
``Bearer `` (would pass a raw bearer token through) while others were missing ``.claude/`` (would pass
an agent-config path). Seven copies of a secret allow-list that disagree on what a secret IS reads as
unaudited to security diligence — and is the exact "a value typed twice is a value that drifts" failure
the repo's NO-MAGIC-VALUES law exists to prevent. Single source: import SECRET_MARKERS / scrub / LEAK_RE
here; never re-declare them in a handler (enforced by scripts/check_response_redaction_single_source.py).

This is the SUPERSET of what the handlers had drifted to (the most secure union), so centralizing can
only redact more, never less.
"""
from __future__ import annotations

import json
import re
from typing import Any

#: substring markers — a dict KEY containing one is dropped; a string VALUE containing one is redacted.
SECRET_MARKERS: tuple[str, ...] = (
    "OH_SHOWCASE_TOKEN",   # the showcase access token
    "sk-",                 # OpenAI-style provider keys
    "api_key",             # any *_api_key field name
    "Authorization",       # auth header name
    "Bearer ",             # a bearer token value
    "MEMORY.md",           # the agent memory index path
    ".agent/",             # agent state dir
    ".claude/",            # agent config dir
)

#: value-level leak regex (provider key shapes + bearer + secret:// refs) for whole-payload scans —
#: complements the substring markers above for handlers that scan a serialized blob.
LEAK_RE = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12}|ghp_[A-Za-z0-9]{20,}"
    r"|secret://[^\"\s]*?:[^\"\s]+|Bearer\s+[A-Za-z0-9._-]{12,})")

REDACTED = "<redacted>"


def scrub(obj: Any, *, skip_keys: frozenset[str] = frozenset()) -> Any:
    """Recursively drop secret-ish dict keys and redact secret-ish string values. ``skip_keys`` are
    dropped outright (e.g. a ``raw_bytes`` blob a handler never echoes back)."""
    if isinstance(obj, dict):
        return {k: scrub(v, skip_keys=skip_keys) for k, v in obj.items()
                if k not in skip_keys and not any(m in str(k) for m in SECRET_MARKERS)}
    if isinstance(obj, list):
        return [scrub(v, skip_keys=skip_keys) for v in obj]
    if isinstance(obj, str) and any(m in obj for m in SECRET_MARKERS):
        return REDACTED
    return obj


def has_leak(payload: Any) -> bool:
    """True if a JSON-serialized payload contains a value-level secret leak (LEAK_RE)."""
    return bool(LEAK_RE.search(json.dumps(payload, default=str)))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    # the superset carries every marker any handler had — so centralizing never weakens redaction
    for m in ("OH_SHOWCASE_TOKEN", "sk-", "api_key", "Authorization", "Bearer ", "MEMORY.md", ".agent/", ".claude/"):
        ck(f"marker present: {m!r}", m in SECRET_MARKERS)
    # scrub drops secret keys, redacts secret values, recurses, honors skip_keys.
    # secret-shaped fixtures are ASSEMBLED at runtime so no raw-key / inline-api_key literal appears in
    # tracked source (the repo's secret-hygiene convention; see scripts/email_port.py).
    _kname = "api" + "_key"
    _skkey = "sk-" + "ABCDEF1234567890"   # synthetic provider-key SHAPE for the leak regex, not a real key
    out = scrub({"ok": "fine", _kname: "x", "note": "Bearer abc123", "deep": [{"Authorization": "y", "keep": 1}],
                 "raw_bytes": "blob"}, skip_keys=frozenset({"raw_bytes"}))
    ck("secret key dropped", _kname not in out)
    ck("skip_keys dropped", "raw_bytes" not in out)
    ck("secret value redacted", out["note"] == REDACTED)
    ck("non-secret kept", out["ok"] == "fine")
    ck("recurses into lists/dicts", out["deep"][0] == {"keep": 1})
    # leak regex catches value-level secrets, ignores clean payloads
    ck("LEAK_RE catches provider key", has_leak({"v": _skkey}))
    ck("LEAK_RE catches bearer", has_leak({"h": "Bearer abcdef123456ghijkl"}))
    ck("LEAK_RE clean on safe payload", not has_leak({"answer": "10 business days"}))
    print(("PASS — " if not fails else "FAIL — ")
          + f"response_redaction: {len(SECRET_MARKERS)} canonical markers + recursive scrub + leak regex, "
            "single-sourced for every API handler (no per-handler drift).")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
