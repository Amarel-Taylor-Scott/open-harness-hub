"""demos.byo_key_demo — the BYO-KEY demo plane: run any surface's demo with the USER's own API key, transiently.

Owner 2026-06-25: "demo pages on all surfaces that allow users to bring their own keys." A user pastes their key;
it is placed in a TRANSIENT environment scope for ONE call (so the existing ProviderLLM / key_holder picks it up),
the demo runs, and the key is REMOVED again — never stored on disk, never kept in a global, never logged. Only a
REDACTED status (`sk-…last4`) is ever returned. Honest-unavailable when a demo needs a key and none is given, or no
LLM lane is reachable. serves_truth=false (candidate output; Baltor's demo answers only from its source).

  python3 -m src.teleon.demos.byo_key_demo --self-test
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

KEY_ENV = "OH_LLM_API_KEY"   # the single shared key env var the LLM lane reads (BYO → the user's account)


def redact(key: str | None) -> str:
    if not key:
        return "none"
    return f"{key[:3]}…{key[-4:]}" if len(key) > 8 else "set"


@contextmanager
def transient_key(byo_key: str | None, env_var: str = KEY_ENV):
    """Put the user's key in the environment for ONE call, then restore — never persisted, never logged."""
    had = env_var in os.environ
    prev = os.environ.get(env_var)
    if byo_key:
        os.environ[env_var] = byo_key
    try:
        yield
    finally:
        if had:
            os.environ[env_var] = prev  # type: ignore[assignment]
        else:
            os.environ.pop(env_var, None)


def _run_observer(inputs: dict) -> dict:
    from src.teleon.observer.review import review_session
    msgs = inputs.get("messages") or [{"role": "user", "content": "let me write a pdf parser from scratch"}]
    rep = review_session(msgs)
    return {"kind": "session_review", "summary": rep["summary"], "serves_truth": rep["serves_truth"]}


def _run_llm(inputs: dict, *, system: str, default_prompt: str) -> dict:
    from src.teleon.llm_port import ProviderLLM
    llm = ProviderLLM(provider=inputs.get("provider", "ollama"))
    if not llm.available():
        return {"available": False, "note": "would call YOUR model with YOUR key — no reachable LLM lane in this environment"}
    prompt = inputs.get("prompt") or default_prompt
    return {"available": True, "output": llm.complete(system, prompt, max_tokens=220)}


DEMOS: dict[str, dict] = {
    "aidevobserver": {"label": "Review an AI coding session", "needs_key": False, "run": _run_observer},
    "teleon": {"label": "Compile a capability (cheapest proven plan)", "needs_key": True,
               "run": lambda i: _run_llm(i, system="You are Teleon, a runtime that turns a request into the cheapest proven plan.",
                                         default_prompt="summarize server logs into a cited incident report")},
    "baltor": {"label": "Answer only from a verified source", "needs_key": True,
               "run": lambda i: _run_llm(i, system="You are Baltor. Answer ONLY from the provided source; cite it, or say MISSING.",
                                         default_prompt="What is the maximum legal interest rate? Source: (paste a statute)")},
    "open-star-hubs": {"label": "Suggest reusable components for a task", "needs_key": True,
                       "run": lambda i: _run_llm(i, system="You are the Open*Hubs store. Suggest reusable components (Knowledge Corpus, If Statement, Action) for the task.",
                                                 default_prompt="extract renewal + liability clauses from contracts")},
}


def run_byo_demo(demo_id: str, byo_key: str | None = None, inputs: dict | None = None) -> dict:
    """Run a surface's demo with the user's BYO key (transient). Never returns or logs the raw key."""
    demo = DEMOS.get(demo_id)
    if not demo:
        return {"ok": False, "status": "unknown_demo", "demos": sorted(DEMOS)}
    if demo["needs_key"] and not byo_key:
        return {"ok": False, "status": "needs_key", "key_status": "none",
                "message": f"“{demo['label']}” needs your API key — paste one to run it with your own account."}
    with transient_key(byo_key):
        result = demo["run"](inputs or {})
    return {"ok": True, "demo": demo_id, "label": demo["label"], "result": result,
            "key_status": redact(byo_key), "used_byo": bool(byo_key), "serves_truth": False}


def self_test() -> int:
    import json
    # 1) a no-key demo runs deterministically
    obs = run_byo_demo("aidevobserver", inputs={"messages": [{"role": "user", "content": "let me write my own pdf parser"}]})
    assert obs["ok"] and obs["result"]["summary"]["findings"] >= 1, "observer demo runs without a key"

    # 2) a key-needing demo is honest-unavailable without a key (no fake green)
    assert run_byo_demo("teleon")["status"] == "needs_key", "key-needing demo must ask for a key"

    # 3) BYO key is honored TRANSIENTLY, REDACTED, and NEVER leaked
    before = os.environ.get(KEY_ENV)
    out = run_byo_demo("teleon", byo_key="sk-secret-ABCD1234", inputs={"prompt": "hi"})
    assert out["ok"] and out["used_byo"] and out["key_status"] == "sk-…1234", out.get("key_status")
    assert "sk-secret-ABCD1234" not in json.dumps(out), "raw key must NEVER appear in the result"
    assert os.environ.get(KEY_ENV) == before, "BYO key must be transient — env restored after the call"

    # 4) all four surfaces are wired
    assert set(DEMOS) == {"aidevobserver", "teleon", "baltor", "open-star-hubs"}, "a demo per product surface"
    print("byo_key_demo self-test: OK (transient + redacted + never-leaked key; honest-unavailable; 4 surfaces)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: byo_key_demo --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
