#!/usr/bin/env python3
"""scripts.check_model_provider_lanes — every provider LANE is wired end-to-end (config + env→route).

Proves the inference lanes the owner uses are wired, not just listed:
  * each lane's ``base_url`` exists as a governed node in ``_repos/shared-backend-components/architecture/model_provider_graph.json``,
    and every external node carries ``secret_ref`` + ``local_equivalent`` (the graph law);
  * each lane's ENV VAR actually routes through ``scripts.foundry.model_route.from_env`` to a
    ``ModelRoute`` named for that lane (the env→route wiring — deterministic, no network);
  * a LIVE smoke (a tiny chat) runs ONLY when a real key is present AND ``OH_LANE_SMOKE_LIVE=1``
    (so CI never networks; with keys it actually pings). Reported honestly either way.

Lanes: Ollama Cloud · Mistral · OpenRouter · Anthropic · OpenAI/compatible · local Ollama.

CLI: python3 _repos/shared-backend-components/scripts/check_model_provider_lanes.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.foundry.model_route import from_env  # noqa: E402

_GRAPH = _resource("architecture") / "model_provider_graph.json"

#: lane → (env key that activates it, base_url that must exist in the graph, route-name prefix).
#: None base_url = a lane that resolves from env (no fixed graph host) — only the route wiring is checked.
_LANES = [
    {"name": "ollama_cloud", "env": "OLLAMA_API_KEY", "base": "https://ollama.com/v1", "prefix": "ollama:"},
    {"name": "mistral", "env": "MISTRAL_API_KEY", "base": "https://api.mistral.ai/v1", "prefix": "mistral:"},
    {"name": "openrouter", "env": "OPENROUTER_API_KEY", "base": "https://openrouter.ai/api/v1", "prefix": "openrouter:"},
    {"name": "anthropic", "env": "ANTHROPIC_API_KEY", "base": "https://api.anthropic.com/v1", "prefix": "anthropic:"},
    {"name": "openai_compatible", "env": "OPENAI_API_KEY", "base": "https://api.openai.com/v1", "prefix": "openai:"},
    {"name": "ollama_local", "env": None, "base": "http://localhost:11434/v1", "prefix": None},
]

#: every provider env key, so a lane test can isolate ONE key (clear the higher-priority ones).
_ALL_KEYS = ["OLLAMA_API_KEY", "MISTRAL_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]


def _graph_nodes() -> list[dict]:
    g = json.loads(_GRAPH.read_text(encoding="utf-8"))
    return g.get("nodes", g.get("providers", []))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    nodes = _graph_nodes()
    by_base = {str(n.get("base_url", "")): n for n in nodes}

    # 1. every lane with a fixed host has a governed node carrying the graph law.
    for lane in _LANES:
        if not lane["base"]:
            continue
        node = by_base.get(lane["base"])
        check(f"{lane['name']}: base_url is a governed graph node", node is not None, lane["base"])
        if node and node.get("external"):
            check(f"{lane['name']}: external node has secret_ref + local_equivalent",
                  bool(node.get("secret_ref")) and bool(node.get("local_equivalent")), str(node.get("node_id")))

    # 2. env→route wiring: set ONE key (clear the higher-priority ones), assert from_env routes to it.
    saved = {k: os.environ.pop(k, None) for k in _ALL_KEYS + ["OH_CHAT_MODEL", "OPENAI_BASE_URL"]}
    try:
        for lane in _LANES:
            if not lane["env"]:
                continue
            for k in _ALL_KEYS:
                os.environ.pop(k, None)
            os.environ[lane["env"]] = "test-key-not-used-offline"
            route = from_env()
            check(f"{lane['name']}: env {lane['env']} → a ModelRoute",
                  route is not None and route.name.startswith(lane["prefix"]),
                  f"got {route.name if route else None}")
            os.environ.pop(lane["env"], None)
        # no keys → None (offline defaults), never a phantom route.
        for k in _ALL_KEYS:
            os.environ.pop(k, None)
        check("no provider key → from_env() is None (offline defaults)", from_env() is None)
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

    # 3. live smoke — only when a real key is present AND opted in; honest report otherwise.
    live_done = []
    if os.environ.get("OH_LANE_SMOKE_LIVE") == "1":
        for lane in _LANES:
            if lane["env"] and os.environ.get(lane["env"]):
                try:
                    r = from_env()
                    if r is not None:
                        reply = r.complete("Reply with the single word: ok")  # pragma: no cover - network
                        live_done.append(f"{lane['name']}={'ok' if reply else 'empty'}")
                except Exception as e:  # noqa: BLE001
                    live_done.append(f"{lane['name']}=ERR:{type(e).__name__}")
    live_note = f"live-smoked: {live_done}" if live_done else "live smoke skipped (no key + OH_LANE_SMOKE_LIVE=1)"

    ok = not fails
    print("\n" + (f"PASS — check_model_provider_lanes: {len(_LANES)} lanes wired (graph nodes carry "
                  f"secret_ref+local_equivalent; env→route mapping verified offline). {live_note}."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify every model-provider lane is wired.")
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
