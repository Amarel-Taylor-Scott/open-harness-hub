"""check_observer_router — proof for the Spotter ROUTER over the intervention taxonomy.

Asserts: the taxonomy fires the RIGHT typed modules (reinvention/footgun/adversarial/cluster/waste), each with its
own grounding; footgun evidence is REDACTED (never echoes a secret); the GLOBAL interruption budget + graduated
modes behave (review interrupts nobody; enforcing lets footguns block but never lets a non-footgun block; the budget
caps non-footgun live interruptions); patterns are single-sourced from behavioral_heuristics.json; serves_truth=false.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# install() prepends every code root so BOTH `scripts.*` and the MOVED `src.teleon.*` resolve on a bare
# `python3 scripts/<f>.py` launch — not only under run_proofs/pytest (which set the full PYTHONPATH for us).
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((p for p in _here_boot.parents if (p / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse
import json
import sys
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.observer.router import (ACTIONS, MODES, _LIVE_BUDGET, route_session)  # noqa: E402

_HEURISTICS = _resource("architecture") / "behavioral_heuristics.json"
# a fake (shape-valid, non-real) AWS-style key to prove footgun detection WITHOUT embedding a real secret.
_FAKE_SECRET_LINE = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # patterns are single-sourced in the registry (no-magic-values)
    heur = json.loads(_HEURISTICS.read_text())
    kinds = {h["kind"] for h in heur["heuristics"]}
    ck("behavioral_heuristics.json single-sources the kinds", {"footgun", "adversarial", "reinvention_cluster"} <= kinds)
    ck("registry serves_truth=false", heur["serves_truth"] is False)

    session = [
        {"role": "user", "content": "let me write a pdf parser from scratch"},        # reinvention (grounded)
        {"role": "user", "content": "I need browser automation for the login flow"},   # adversarial (API exists?)
        {"role": "user", "content": _FAKE_SECRET_LINE},                                # footgun (secret, can block)
        {"role": "user", "content": "now add jwt and a refresh token and oauth flow"}, # cluster + stack (auth infra)
        {"role": "user", "content": "let me build a custom retry with exponential backoff"},  # stack (tenacity)
        {"role": "user", "content": "try:\n    x()\nexcept:\n    pass"},                # guidance (bare except)
        {"role": "user", "content": "I'll use os.path.join(base, name) to build the path"},  # alternative (pathlib)
        {"role": "user", "content": "let me build an open source vector database and similarity search engine for embeddings with filtering"},  # product_reinvention (qdrant)
        {"role": "user", "content": "rm -rf / now"},                                   # footgun (destructive)
    ]

    rev = route_session(session, mode="review_only")
    types = {f["type"] for f in rev["report"]}
    ck("taxonomy fires >=8 distinct module types", len(types) >= 8, str(sorted(types)))
    ck("reinvention is grounded in the federation", any(
        f["type"] == "reinvention" and f["source_ref"].get("existing") for f in rev["report"]))
    ck("stack_reinvention is grounded in the dependency graph", any(
        f["type"] == "stack_reinvention" and f["source_ref"].get("covering") for f in rev["report"]))
    ck("product_reinvention is grounded in latent product space", any(
        f["type"] == "product_reinvention" and f["source_ref"].get("nearest") for f in rev["report"]))
    ck("adversarial fired (assumption challenged)", "adversarial" in types)
    ck("guidance fired (bare except)", "guidance" in types)
    ck("alternative fired (os.path -> pathlib)", "alternative" in types)
    ck("footgun fired on the secret + the destructive command", sum(
        1 for f in rev["report"] if f["type"] == "footgun") >= 2)
    ck("reinvention_cluster fired on the auth signal sequence", "reinvention_cluster" in types)

    # REAL-SCALE SHAPE: cluster detection must retain only its finite signal vocabulary. The old router appended
    # and lowercased the complete growing session for every event, so reviewing the latest 40 MB dogfood session
    # stalled for minutes. A probe module sees the shared state without coupling the assertion to wall-clock speed.
    class RouterStateShapeProbe:
        type = "state_shape_probe"

        def plausible(self, text, state):
            return True

        def ground(self, text, state):
            ck("router state does not accumulate the full transcript", "session_text" not in state)
            ck("router state keeps a bounded reinvention-cluster signal set",
               isinstance(state.get("reinvention_cluster_signals"), set)
               and len(state["reinvention_cluster_signals"]) <= sum(
                   len(h.get("match", {}).get("all_of", [])) for h in heur["heuristics"]
                   if h.get("kind") == "reinvention_cluster"))
            return []

    route_session([{"role": "user", "content": "jwt"}], modules=[RouterStateShapeProbe()])

    # A generous wall-clock ratchet catches accidental whole-session rescans without making CI timing-sensitive.
    long_session = [{"role": "user", "content": "ordinary implementation note " + ("x" * 256)} for _ in range(4000)]
    started = time.perf_counter()
    long_report = route_session(long_session, modules=[])
    elapsed = time.perf_counter() - started
    ck("4,000-event router floor stays linear/bounded", long_report["summary"]["messages"] == 4000 and elapsed < 5.0,
       f"{elapsed:.3f}s")

    # shortcut: the same tool used >= _SHORTCUT_REPEAT times in a session -> fires once
    tool_session = [{"role": "assistant", "content": f"Read file_{i}.py", "tool": "Read"} for i in range(5)]
    sc = route_session(tool_session, mode="review_only")
    shortcuts = [f for f in sc["report"] if f["type"] == "shortcut"]
    ck("shortcut fires on repeated tool use", len(shortcuts) == 1, f"{len(shortcuts)} shortcut findings")
    ck("shortcut names the repeated tool", shortcuts and "Read" in shortcuts[0]["evidence"])

    # SECURITY: footgun evidence must be REDACTED — the real secret token never appears anywhere in the result.
    blob = json.dumps(rev)
    ck("footgun evidence is redacted (no secret echoed)", "AKIAIOSFODNN7EXAMPLE" not in blob)
    ck("every footgun finding carries redacted evidence", all(
        f["evidence"] == "<redacted match>" for f in rev["report"] if f["type"] == "footgun"))

    # review_only interrupts nobody (it is a report)
    ck("review_only surfaces zero live interruptions", rev["summary"]["would_interrupt"] == 0)

    # enforcing: footguns may BLOCK; a non-footgun may NEVER block
    enf = route_session(session, mode="enforcing")
    foot_actions = [f["action"] for f in enf["surfaced"] if f["type"] == "footgun"]
    ck("enforcing lets a footgun BLOCK", "block" in foot_actions)
    ck("no non-footgun ever blocks", all(
        f["action"] != "block" for f in enf["report"] if f["type"] != "footgun"))
    ck("footguns always surface (protective, budget-exempt)", all(
        any(s["type"] == "footgun" and s["message_index"] == f["message_index"] for s in enf["surfaced"])
        for f in enf["report"] if f["type"] == "footgun"))

    # GLOBAL budget: many adversarial-triggering turns -> non-footgun live interruptions capped at _LIVE_BUDGET
    spammy = [{"role": "user", "content": t} for t in (
        "build a web scraper", "I need an ocr pipeline", "add retry logic with backoff",
        "build a vector database", "build an agent framework", "implement jwt auth")]
    adv = route_session(spammy, mode="advisory")
    non_footgun_surfaced = [s for s in adv["surfaced"] if s["type"] != "footgun"]
    ck("global interruption budget caps non-footgun live interrupts", len(non_footgun_surfaced) <= _LIVE_BUDGET,
       f"{len(non_footgun_surfaced)} > {_LIVE_BUDGET}")
    ck("advisory caps actions at notice (nothing asks/blocks live)", all(
        ACTIONS.index(s["action"]) <= ACTIONS.index("notice") for s in adv["surfaced"]))

    # graduated modes + governance
    ck("MODES are the 5-rung restraint gradient", MODES == (
        "silent_record", "review_only", "advisory", "active", "enforcing"))
    ck("every finding is a governed candidate", all(
        f["serves_truth"] is False and f["candidate"] for f in rev["report"]))
    ck("findings carry the accept/reject outcome slot (the moat signal)", all(
        "outcome" in f for f in rev["report"]))
    ck("deterministic", route_session(session, mode="review_only")["report"] == rev["report"])

    if fails:
        print(f"\nFAIL - check_observer_router: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - check_observer_router: router over the taxonomy ({len(types)} module types) — grounded "
          f"reinvention + redacted footguns (can block) + adversarial questions + session clusters + waste; global "
          f"budget + graduated modes enforced; {checks} assertions; serves_truth=false, single-sourced patterns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
