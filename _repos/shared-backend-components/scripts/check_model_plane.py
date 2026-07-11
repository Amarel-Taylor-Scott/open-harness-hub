#!/usr/bin/env python3
"""scripts.check_model_plane — drift gate for the LIVE model plane.

The model-dependent paths degrade HONESTLY (hash embeddings flag promotable:false; builds label
themselves deterministic) — which is exactly why a regression is easy to miss. This gate fails
LOUDLY when the plane isn't real:

  A. EMBEDDINGS — resolve_backend() must be promotable (never the hash fallback), its dimension
     must match the model registry (scripts._config single source), and a live embed round-trips.
  B. CHAT ROUTE — resolve_route() must be reachable; --live additionally runs ONE tiny completion
     and checks a non-empty answer (skipped by default to keep CI cheap/offline-safe).
  C. GATEWAY SWITCH — OH_INFERENCE_ALLOW_NETWORK=1 so the OIPS gateway executes real models.
  D. APP SERVER PROJECTION — when :8000 answers, /api/health must report the same truth
     (promotable embeddings + llm_reachable), so the investor-facing surface can't drift.

Run with the .env loaded (set -a; . ./.env; set +a). Exit 0/1. --self-test = A+C+D (no model
call); --live adds B's completion.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])))
from scripts._config import EMBEDDING_MODELS  # noqa: E402
from scripts.embeddings import resolve_backend  # noqa: E402
from scripts.model_routes import resolve_route  # noqa: E402

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _app_health() -> dict | None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def main(live: bool) -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    backend = resolve_backend()
    ck("A: embedding backend is PROMOTABLE (no hash fallback)", backend.promotable,
       f"backend={backend.name}/{backend.model_id}")
    expected_dim = EMBEDDING_MODELS.get(backend.model_id)
    ck("A: dimension matches the model registry", expected_dim is None or backend.dim == expected_dim,
       f"dim={backend.dim} expected={expected_dim}")
    try:
        vec = backend.embed_one("model plane drift gate probe")
        ck("A: live embed round-trips at the declared dimension", len(vec) == backend.dim)
    except Exception as exc:
        ck("A: live embed round-trips at the declared dimension", False, f"{type(exc).__name__}")

    route = resolve_route()
    ck("B: chat route reachable", route.health(), f"{route.model_id} @ {route.base_url}")
    if live:
        answer = route.complete("Reply with exactly: OK", "ping", max_tokens=8, temperature=0.0)
        ck("B(live): one real completion answers", bool(answer and answer.strip()),
           repr(answer)[:60])

    ck("C: OIPS live execution switch on (OH_INFERENCE_ALLOW_NETWORK=1)",
       os.environ.get("OH_INFERENCE_ALLOW_NETWORK", "") == "1")

    health = _app_health()
    if health is None:
        print("  [ok] D: app server not running — projection check skipped honestly")
    else:
        ck("D: /api/health reports promotable embeddings",
           bool(health.get("embedding", {}).get("promotable")), json.dumps(health.get("embedding", {}))[:90])
        ck("D: /api/health reports the LLM reachable", bool(health.get("llm_reachable")),
           json.dumps(health.get("llm", {}))[:90])

    print("\n" + ("PASS — check_model_plane: real promotable embeddings, a reachable chat route, "
                  "the OIPS live switch on, and the app-server projection agreeing."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main(live="--live" in sys.argv))
