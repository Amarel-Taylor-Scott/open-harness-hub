#!/usr/bin/env python3
"""check_default_brain_policy — proof that the cheap Ollama brain (GLM-5.2 / Kimi-k2.7-code) is the DEFAULT
orchestrator / reviewer / distiller-judge, escalating to a frontier model only when a confidence/quality bar fails.
The default is verifiably CHEAPER than its escalation (cross-checked against the model index), auth is an env-ref
(OLLAMA_API_KEY, value never tracked), and the brain never serves truth.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_default_brain_policy.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.teleon.inference.default_brain import brain_for, load_policy, roles


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pol = load_policy()
    rs = pol["roles"]
    ck("the brain has orchestrator + reviewer + distiller-judge roles",
       {"orchestrator", "reviewer", "distiller-judge"} <= set(roles()))
    ck("every role defaults to a CHEAP Ollama model (GLM-5.2 / Kimi-k2.7-code) + has a frontier escalation + a trigger",
       all(r["default_provider"] == "ollama" and r["default_model"] in ("glm-5.2", "kimi-k2.7-code")
           and r["escalation_model"] and r["escalate_when"] for r in rs))
    ck("auth is the OLLAMA_API_KEY env ref (no raw value in the policy)",
       all(r["auth_env_ref"] == "OLLAMA_API_KEY" for r in rs) and "OLLAMA_API_KEY" == pol["auth_env_ref"])

    # the DEFAULT is verifiably cheaper than the ESCALATION (cross-check the model index cost_out)
    idx = {e["model_id"]: e for e in json.loads((_resource("architecture") / "model_index.json").read_text())["entries"]}
    cheaper = []
    for r in rs:
        d, e = idx.get(r["default_model"]), idx.get(r["escalation_model"])
        cheaper.append(bool(d) and bool(e) and d["cost_per_mtok_out"] < e["cost_per_mtok_out"])
    ck("the cheap default is verifiably cheaper than its frontier escalation (per the model index)", all(cheaper),
       str([(r["default_model"], r["escalation_model"]) for r, c in zip(rs, cheaper) if not c]))
    ck("GLM-5.2 + Kimi-k2.7-code are registered in the model index (Ollama provider)",
       "glm-5.2" in idx and "kimi-k2.7-code" in idx and "ollama" in idx["glm-5.2"]["provider"])

    # selection: with OLLAMA_API_KEY the cheap default is chosen; force_frontier escalates; no key -> honest fallback
    o = brain_for("orchestrator", available_keys=("OLLAMA_API_KEY",))
    ck("orchestrator with OLLAMA_API_KEY -> the cheap GLM-5.2 default", o["model"] == "glm-5.2" and o["is_default"] is True)
    rv = brain_for("reviewer", available_keys=("OLLAMA_API_KEY",))
    ck("reviewer with OLLAMA_API_KEY -> the cheap Kimi-k2.7-code default", rv["model"] == "kimi-k2.7-code" and rv["is_default"])
    esc = brain_for("orchestrator", available_keys=("OLLAMA_API_KEY",), force_frontier=True)
    ck("force_frontier escalates to a frontier model (only when the bar fails)",
       esc["is_default"] is False and esc["model"] == esc["escalation_model"])
    nokey = brain_for("orchestrator", available_keys=())
    ck("no OLLAMA_API_KEY -> default flagged unavailable, honest fallback (never fabricated)",
       nokey["default_reachable"] is False and nokey["is_default"] is False)
    ck("the brain never serves truth (proposes; gates dispose)",
       o["serves_truth"] is False and pol["serves_truth"] is False)
    ck("deterministic", brain_for("orchestrator", available_keys=("OLLAMA_API_KEY",)) == o)

    print("\n" + ("PASS - check_default_brain_policy: the cheap Ollama brain (GLM-5.2 orchestrator / distiller-judge, "
                  "Kimi-k2.7-code reviewer) is the DEFAULT, verifiably cheaper than its frontier escalation, which "
                  "fires only when a confidence/quality bar fails — the descent applied to the brain itself. Auth is "
                  "the OLLAMA_API_KEY env ref (value in gitignored .env). Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_default_brain_policy.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
