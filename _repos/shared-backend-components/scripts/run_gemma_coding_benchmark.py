#!/usr/bin/env python3
"""Run small coding-generation prompts against Open WebUI Gemma.

Outputs are benchmark artifacts only: candidate=true, serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import concurrent.futures
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    OPENWEBUI_DEFAULT_BASE_URL,
    OPENWEBUI_DEFAULT_MODEL,
    REPO_ROOT,
)
from scripts._llm_client import chat, resolve_provider  # noqa: E402
from scripts.openwebui_cdp_client import cdp_chat  # noqa: E402

DEFAULT_OUT = _resource("generated") / "gemma_leetcode_coding_benchmark.json"
SYSTEM = (
    "You are a coding model. Return exactly one fenced python code block. "
    "No prose outside the code block. Use Python 3 standard library only."
)
PROMPTS = [
    "Implement function two_sum(nums, target) returning indices of two numbers that add to target. Include 3 asserts.",
    "Implement function valid_parentheses(s) returning True when brackets are balanced. Include 4 asserts.",
    "Implement class LRUCache with get and put in O(1). Include a short assert-based smoke test.",
    "Implement function merge_intervals(intervals) returning merged inclusive intervals. Include 3 asserts.",
    "Implement function top_k_frequent(nums, k) returning the k most frequent numbers. Include 3 asserts.",
    "Implement function binary_search(nums, target) returning the index or -1. Include 4 asserts.",
    "Implement function longest_substring_without_repeating(s) returning the maximum length. Include 4 asserts.",
    "Implement function product_except_self(nums) without division. Include 3 asserts.",
    "Implement function coin_change(coins, amount) returning the fewest coins or -1. Include 3 asserts.",
    "Implement function num_islands(grid) returning the number of islands in a 2D grid. Include 2 asserts.",
]


def _call(index: int, prompt: str, *, mode: str, model: str, cdp_url: str, max_tokens: int, timeout: int) -> dict[str, Any]:
    started = time.time()
    if mode == "cdp":
        try:
            result = cdp_chat(
                prompt,
                system=SYSTEM,
                model=model,
                cdp_url=cdp_url or None,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            text = result.get("assistant_content") or ""
            usage = result.get("usage") or {}
            finish_reason = result.get("finish_reason")
            error = None
        except Exception as exc:  # noqa: BLE001
            text = ""
            usage = {}
            finish_reason = None
            error = f"{type(exc).__name__}: {exc}"
    else:
        provider = resolve_provider("openwebui")
        result = chat(model, SYSTEM, prompt, provider, max_tokens=max_tokens, timeout=timeout)
        text = result.get("text") or ""
        usage = result.get("usage") or {}
        finish_reason = result.get("finish_reason")
        error = result.get("error")
    elapsed = round(time.time() - started, 3)
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    total_tokens = int((usage or {}).get("total_tokens") or 0)
    return {
        "task_index": index,
        "prompt": prompt,
        "assistant_content": text,
        "usage": usage,
        "finish_reason": finish_reason,
        "error": error,
        "duration_seconds": elapsed,
        "completion_tps": round(completion_tokens / elapsed, 3) if elapsed and completion_tokens else 0,
        "total_tps": round(total_tokens / elapsed, 3) if elapsed and total_tokens else 0,
        "candidate": True,
        "serves_truth": False,
    }


def run_benchmark(
    *,
    mode: str,
    model: str,
    cdp_url: str,
    limit: int,
    max_tokens: int,
    timeout: int,
    workers: int,
    out: Path,
) -> dict[str, Any]:
    prompts = PROMPTS[:limit] if limit > 0 else PROMPTS
    started = time.time()
    if workers <= 1:
        rows = [
            _call(index, prompt, mode=mode, model=model, cdp_url=cdp_url, max_tokens=max_tokens, timeout=timeout)
            for index, prompt in enumerate(prompts)
        ]
    else:
        rows_by_index: list[dict[str, Any] | None] = [None] * len(prompts)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _call,
                    index,
                    prompt,
                    mode=mode,
                    model=model,
                    cdp_url=cdp_url,
                    max_tokens=max_tokens,
                    timeout=timeout,
                ): index
                for index, prompt in enumerate(prompts)
            }
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                try:
                    rows_by_index[index] = future.result()
                except Exception as exc:  # noqa: BLE001
                    rows_by_index[index] = {
                        "task_index": index,
                        "prompt": prompts[index],
                        "assistant_content": "",
                        "usage": {},
                        "finish_reason": None,
                        "error": f"{type(exc).__name__}: {exc}",
                        "duration_seconds": 0,
                        "completion_tps": 0,
                        "total_tps": 0,
                        "candidate": True,
                        "serves_truth": False,
                    }
        rows = [row for row in rows_by_index if row is not None]
    total_usage = {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in rows),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in rows),
    }
    elapsed = round(time.time() - started, 3)
    manifest = {
        "record_type": "gemma_coding_benchmark",
        "provider": "open_webui",
        "mode": mode,
        "base_url": OPENWEBUI_DEFAULT_BASE_URL,
        "model": model,
        "workers": workers,
        "task_count": len(rows),
        "success_count": sum(1 for row in rows if not row.get("error") and "```python" in row.get("assistant_content", "")),
        "error_count": sum(1 for row in rows if row.get("error")),
        "usage": total_usage,
        "duration_seconds": elapsed,
        "aggregate_completion_tps": (
            round(total_usage["completion_tokens"] / elapsed, 3)
            if elapsed and total_usage["completion_tokens"]
            else 0
        ),
        "aggregate_total_tps": (
            round(total_usage["total_tokens"] / elapsed, 3)
            if elapsed and total_usage["total_tokens"]
            else 0
        ),
        "results": rows,
        "candidate": True,
        "serves_truth": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    manifest = {
        "record_type": "gemma_coding_benchmark",
        "candidate": True,
        "serves_truth": False,
        "task_count": len(PROMPTS),
    }
    ok = manifest["candidate"] is True and manifest["serves_truth"] is False and manifest["task_count"] >= 5
    print("PASS - Gemma coding benchmark prompts are candidate-only and configured." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["direct", "cdp"], default="cdp")
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    manifest = run_benchmark(
        mode=args.mode,
        model=args.model,
        cdp_url=args.cdp_url,
        limit=args.limit,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        workers=max(1, args.workers),
        out=Path(args.out),
    )
    print(json.dumps({key: value for key, value in manifest.items() if key != "results"}, indent=2, sort_keys=True))
    return 0 if manifest["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
