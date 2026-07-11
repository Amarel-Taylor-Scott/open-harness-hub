#!/usr/bin/env python3
"""Local Ollama model smoke receipt.

Calls the local Ollama HTTP API with a tiny bounded generation and writes an
append-only candidate receipt. This is intentionally a health/proof harness,
not a truth-serving path.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / ".aidoneright-root").exists()),
    Path(__file__).resolve().parents[2],
)
DEFAULT_OUT_DIR = REPO / "_repos" / "shared-backend-components" / "data" / "dev-intel" / "ollama_local_smoke"
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:latest")


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(payload) + "\n")


def run_smoke(*, host: str, model: str, prompt: str, out_dir: Path, timeout: int, num_predict: int) -> dict[str, Any]:
    started = _utc()
    run_id = "ollama-local-smoke-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir / "runs" / run_id
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max(1, min(num_predict, 256)),
            "temperature": 0,
        },
    }
    request = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    ok = False
    response_json: dict[str, Any] = {}
    error = ""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_json = json.loads(response.read().decode("utf-8"))
        ok = bool(str(response_json.get("response") or "").strip())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    receipt = {
        "record_type": "ollama_local_model_smoke_receipt",
        "run_id": run_id,
        "created_at": _utc(),
        "started_at": started,
        "host": host,
        "model": model,
        "ok": ok,
        "error": error,
        "response_chars": len(str(response_json.get("response") or "")),
        "usage": {
            "prompt_eval_count": response_json.get("prompt_eval_count"),
            "eval_count": response_json.get("eval_count"),
            "total_duration": response_json.get("total_duration"),
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(run_dir / "request.json", {"body": body, "candidate": True, "serves_truth": False})
    _write_json(run_dir / "response.json", {"response": response_json, "error": error, "serves_truth": False})
    _write_json(run_dir / "receipt.json", receipt)
    _write_json(out_dir / "latest_status.json", receipt)
    _append_jsonl(out_dir / "ledger.jsonl", receipt)
    return receipt


def _self_test() -> int:
    payload = {
        "model": DEFAULT_MODEL,
        "host": DEFAULT_HOST,
        "candidate": True,
        "serves_truth": False,
    }
    ok = payload["model"] and payload["host"].startswith(("http://", "https://")) and payload["serves_truth"] is False
    print("PASS - ollama_local_model_smoke writes candidate-only receipts." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", default="Print exactly: local ollama smoke ok")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--num-predict", type=int, default=24)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    receipt = run_smoke(
        host=args.host,
        model=args.model,
        prompt=args.prompt,
        out_dir=Path(args.out_dir),
        timeout=args.timeout,
        num_predict=args.num_predict,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
