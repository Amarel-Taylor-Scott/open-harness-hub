#!/usr/bin/env python3
"""Run live model workers over primitive factory shard prompts.

This script turns planned primitive-factory shards into model output receipts.
It does not parse outputs into trusted primitives and never promotes truth.
Use it when a configured coding model such as Open WebUI Gemma should draft
candidate primitive/group JSONL for many shards in parallel.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    OPENWEBUI_DEFAULT_MODEL,
    OPENWEBUI_TOKEN_ENV,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE,
    REPO_ROOT,
)
from scripts._llm_client import (  # noqa: E402
    GEMMA_RATE_LIMITED_ERROR_LABEL,
    GEMMA_SESSION_DOWN_ERROR_LABEL,
    OLLAMA_USAGE_LIMIT_MARKER_SESSION,
    OLLAMA_USAGE_PAUSE_ERROR_LABEL,
    chat,
    resolve_provider,
)
from scripts.openwebui_cdp_client import cdp_chat  # noqa: E402

DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "primitive_factory" / "model_outputs"
WORKER_SYSTEM_PROMPT = (
    "You draft candidate primitive and primitive-group JSONL only. "
    "Return JSON objects separated by newlines. Start immediately with the first JSON object. "
    "Do not include prose, markdown, headings, explanations, analysis, or code fences. "
    "Every emitted object must keep candidate=true and serves_truth=false. "
    "Do not copy source code. Include source_refs, visible input/output edges, "
    "hidden_member_edges for groups, mutators, proof_requirements, promotion_blockers, "
    "dedupe_key, effects, runtime_targets, and confidence signals."
)
RETRYABLE_ERROR_MARKERS = (
    "HTTP Error 429",
    "too many concurrent requests",
    "Too Many Requests",
    "rate limit",
    "temporarily unavailable",
)
#: checked BEFORE the retryable markers: a usage-cap 429 (account quota exhausted) or an active Ollama usage
#: pause means retrying only burns quota timeouts for nothing — fail fast with the honest label instead.
#: Gemma lane: a session-down origin (Cloudflare 5xx breaker) or the severe fleet-wide rate limiter must also
#: never be retried in-place — retrying hammers the dead origin / the shared GPU; the failed-shard retry loop
#: requeues the shard after the pause/slot window instead.
NON_RETRYABLE_ERROR_MARKERS = (
    OLLAMA_USAGE_PAUSE_ERROR_LABEL,
    OLLAMA_USAGE_LIMIT_MARKER_SESSION,
    GEMMA_SESSION_DOWN_ERROR_LABEL,
    GEMMA_RATE_LIMITED_ERROR_LABEL,
)
DEFAULT_RETRY_ATTEMPTS = 4
DEFAULT_RETRY_BASE_SECONDS = 8.0
TARGET_SENTENCE_RE = re.compile(
    r"Emit at least \d+ useful rows for this shard; do not emit more than \d+ rows\.",
    re.IGNORECASE,
)


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _sha(value: Any, *, n: int = 20) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(row)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _append_jsonl(path: Path, row: dict[str, Any], *, lock: threading.Lock | None = None) -> None:
    line = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if lock is None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
        return
    with lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def _default_shards_path(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_DAILY_SHARDS_DIR) / run_date / "shards.jsonl"


def _select_shards(rows: list[dict[str, Any]], *, offset: int, limit: int) -> list[dict[str, Any]]:
    selected = rows[max(0, offset):]
    return selected[:limit] if limit > 0 else selected


def _retarget_prompt(prompt: str, *, raw_candidate_target: int, useful_candidate_target: int) -> str:
    if raw_candidate_target <= 0 and useful_candidate_target <= 0:
        return prompt
    raw = raw_candidate_target if raw_candidate_target > 0 else max(1, useful_candidate_target)
    useful = useful_candidate_target if useful_candidate_target > 0 else raw
    useful = max(1, min(useful, raw))
    sentence = f"Emit exactly {useful} useful rows for this shard; do not emit more than {raw} rows."
    if TARGET_SENTENCE_RE.search(prompt):
        prompt = TARGET_SENTENCE_RE.sub(sentence, prompt, count=1)
    else:
        prompt = sentence + "\n" + prompt
    return (
        "Open WebUI microbatch override: keep the response short, valid JSONL, and stop immediately after "
        f"{useful} complete JSON objects. Do not continue with fragments or repair notes.\n"
        + prompt
    )


def _retarget_shards(
    rows: list[dict[str, Any]],
    *,
    prompt_field: str,
    raw_candidate_target: int,
    useful_candidate_target: int,
) -> list[dict[str, Any]]:
    if raw_candidate_target <= 0 and useful_candidate_target <= 0:
        return rows
    retargeted: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        raw = raw_candidate_target if raw_candidate_target > 0 else int(copy.get("raw_candidate_target") or 0)
        useful = useful_candidate_target if useful_candidate_target > 0 else int(copy.get("useful_candidate_target") or 0)
        copy["raw_candidate_target"] = raw
        copy["useful_candidate_target"] = useful
        copy[prompt_field] = _retarget_prompt(
            str(copy.get(prompt_field) or ""),
            raw_candidate_target=raw,
            useful_candidate_target=useful,
        )
        copy["prompt_target_override"] = {
            "raw_candidate_target": raw,
            "useful_candidate_target": useful,
            "candidate": True,
            "serves_truth": False,
        }
        retargeted.append(copy)
    return retargeted


def _receipt_for_shard(
    shard: dict[str, Any],
    *,
    provider_name: str,
    model: str,
    prompt_field: str,
    text: str,
    usage: dict[str, Any],
    finish_reason: str | None,
    error: str | None,
    started_at: float,
) -> dict[str, Any]:
    prompt = str(shard.get(prompt_field) or "")
    elapsed = round(time.time() - started_at, 3)
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    total_tokens = int((usage or {}).get("total_tokens") or 0)
    return {
        "record_type": "primitive_factory_model_output",
        "output_id": f"pfmo:{_sha({'shard': shard.get('shard_id'), 'model': model, 'text': text, 'error': error})}",
        "shard_id": shard.get("shard_id"),
        "run_date": shard.get("run_date"),
        "lane_id": shard.get("lane_id"),
        "provider": provider_name,
        "model": model,
        "prompt_field": prompt_field,
        "prompt_sha256": _sha(prompt, n=64),
        "raw_candidate_target": shard.get("raw_candidate_target"),
        "useful_candidate_target": shard.get("useful_candidate_target"),
        "assistant_content": text,
        "usage": usage or {},
        "finish_reason": finish_reason,
        "error": error,
        "status": "error" if error else "candidate_model_output",
        "duration_seconds": elapsed,
        "completion_tps": round(completion_tokens / elapsed, 3) if elapsed and completion_tokens else 0,
        "total_tps": round(total_tokens / elapsed, 3) if elapsed and total_tokens else 0,
        "candidate": True,
        "serves_truth": False,
    }


def _dry_run_receipt(shard: dict[str, Any], *, provider_name: str, model: str, prompt_field: str) -> dict[str, Any]:
    return _receipt_for_shard(
        shard,
        provider_name=provider_name,
        model=model,
        prompt_field=prompt_field,
        text="",
        usage={},
        finish_reason=None,
        error=None,
        started_at=time.time(),
    ) | {"status": "planned", "dry_run": True}


def _retryable_error(error: Any) -> bool:
    text = str(error or "").lower()
    if any(marker.lower() in text for marker in NON_RETRYABLE_ERROR_MARKERS):
        return False
    return any(marker.lower() in text for marker in RETRYABLE_ERROR_MARKERS)


def _parse_utc_time(value: Any) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _gemma_pause_status(*, provider_name: str, model: str) -> dict[str, Any]:
    if provider_name != "openwebui" or model != OPENWEBUI_DEFAULT_MODEL:
        return {"active": False}
    pause_path = _resource(PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE)
    payload = _read_json(pause_path)
    if not payload or payload.get("enabled") is False:
        return {"active": False, "pause_file": str(pause_path)}
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return {"active": False, "expired": True, "expires_at_utc": expires_at.isoformat(), "pause_file": str(pause_path)}
    return {
        "active": True,
        "pause_file": str(pause_path),
        "expires_at_utc": expires_at.isoformat() if expires_at else "",
        "reason": str(payload.get("reason") or "gemma_calls_paused"),
    }


def run_worker(
    *,
    shards_path: Path,
    out_dir: Path,
    provider_name: str,
    model: str,
    prompt_field: str,
    workers: int,
    limit: int,
    offset: int,
    max_tokens: int,
    timeout: int,
    dry_run: bool,
    mode: str,
    cdp_url: str,
    prompt_raw_candidate_target: int = 0,
    prompt_useful_candidate_target: int = 0,
) -> dict[str, Any]:
    all_shards = _read_jsonl(shards_path)
    selected = _select_shards(all_shards, offset=offset, limit=limit)
    selected = _retarget_shards(
        selected,
        prompt_field=prompt_field,
        raw_candidate_target=prompt_raw_candidate_target,
        useful_candidate_target=prompt_useful_candidate_target,
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = resolve_provider(provider_name)
    if not provider.get("base_url"):
        raise AssertionError(f"{provider_name} provider has no base URL")
    if not dry_run and mode == "direct" and not provider.get("key"):
        raise AssertionError(f"{provider_name} provider needs {provider.get('key_var') or OPENWEBUI_TOKEN_ENV}")

    started = time.time()
    call_events_path = out_dir / "call_events.jsonl"
    call_event_lock = threading.Lock()
    pause_status = _gemma_pause_status(provider_name=provider_name, model=model)

    def _emit_call_event(
        event_type: str,
        shard: dict[str, Any],
        *,
        call_started: float | None = None,
        receipt: dict[str, Any] | None = None,
        error: str | None = None,
        attempt: int | None = None,
        sleep_seconds: float | None = None,
    ) -> None:
        elapsed = round(time.time() - call_started, 3) if call_started else 0
        usage = (receipt or {}).get("usage") or {}
        row = {
            "record_type": "primitive_factory_model_call_event",
            "event_id": f"pfmce:{_sha({'event': event_type, 'shard': shard.get('shard_id'), 'model': model, 'time': _now_utc()})}",
            "event_type": event_type,
            "created_at": _now_utc(),
            "run_date": shard.get("run_date"),
            "shard_id": shard.get("shard_id"),
            "lane_id": shard.get("lane_id"),
            "provider": provider_name,
            "model": model,
            "mode": mode,
            "prompt_field": prompt_field,
            "raw_candidate_target": shard.get("raw_candidate_target"),
            "useful_candidate_target": shard.get("useful_candidate_target"),
            "status": (receipt or {}).get("status") or ("started" if event_type == "call_started" else "unknown"),
            "duration_seconds": elapsed,
            "usage": usage,
            "finish_reason": (receipt or {}).get("finish_reason"),
            "error": error if error is not None else (receipt or {}).get("error"),
            "attempt": attempt,
            "sleep_seconds": sleep_seconds,
            "candidate": True,
            "serves_truth": False,
        }
        _append_jsonl(call_events_path, row, lock=call_event_lock)

    receipts: list[dict[str, Any]] = []
    if dry_run:
        receipts = [
            _dry_run_receipt(shard, provider_name=provider_name, model=model, prompt_field=prompt_field)
            for shard in selected
        ]
    elif pause_status.get("active"):
        receipts = []
        for shard in selected:
            started_paused = time.time()
            reason = str(pause_status.get("reason") or "gemma_calls_paused")
            receipt = _receipt_for_shard(
                shard,
                provider_name=provider_name,
                model=model,
                prompt_field=prompt_field,
                text="",
                usage={},
                finish_reason="paused",
                error=None,
                started_at=started_paused,
            ) | {
                "status": "paused",
                "pause_reason": reason,
                "pause_file": str(pause_status.get("pause_file") or ""),
                "pause_expires_at_utc": str(pause_status.get("expires_at_utc") or ""),
            }
            _emit_call_event("call_paused", shard, call_started=started_paused, receipt=receipt)
            receipts.append(receipt)
    else:
        def _one(shard: dict[str, Any]) -> dict[str, Any]:
            call_started = time.time()
            _emit_call_event("call_started", shard, call_started=call_started)
            prompt = str(shard.get(prompt_field) or "")
            if not prompt:
                receipt = _receipt_for_shard(
                    shard,
                    provider_name=provider_name,
                    model=model,
                    prompt_field=prompt_field,
                    text="",
                    usage={},
                    finish_reason=None,
                    error=f"missing prompt field: {prompt_field}",
                    started_at=call_started,
                )
                _emit_call_event("call_finished", shard, call_started=call_started, receipt=receipt)
                return receipt
            if mode == "cdp" and provider_name == "openwebui":
                result = {"text": "", "usage": {}, "finish_reason": None, "error": "cdp_call_not_attempted"}
                for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
                    try:
                        normalized = cdp_chat(
                            prompt,
                            system=WORKER_SYSTEM_PROMPT,
                            model=model,
                            base_url=str(provider.get("base_url") or ""),
                            cdp_url=cdp_url or None,
                            max_tokens=max_tokens,
                            timeout=timeout,
                        )
                        result = {
                            "text": normalized.get("assistant_content") or "",
                            "usage": normalized.get("usage") or {},
                            "finish_reason": normalized.get("finish_reason"),
                            "error": None,
                        }
                    except Exception as exc:  # noqa: BLE001
                        result = {
                            "text": "",
                            "usage": {},
                            "finish_reason": None,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    if not result.get("error") or not _retryable_error(result.get("error")) or attempt >= DEFAULT_RETRY_ATTEMPTS:
                        break
                    sleep_seconds = round(DEFAULT_RETRY_BASE_SECONDS * attempt, 3)
                    _emit_call_event(
                        "call_retry",
                        shard,
                        call_started=call_started,
                        error=str(result.get("error") or ""),
                        attempt=attempt,
                        sleep_seconds=sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
            else:
                result = {"text": "", "usage": {}, "finish_reason": None, "error": "direct_call_not_attempted"}
                for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
                    result = chat(model, WORKER_SYSTEM_PROMPT, prompt, provider, max_tokens=max_tokens, timeout=timeout)
                    if not result.get("error") or not _retryable_error(result.get("error")) or attempt >= DEFAULT_RETRY_ATTEMPTS:
                        break
                    sleep_seconds = round(DEFAULT_RETRY_BASE_SECONDS * attempt, 3)
                    _emit_call_event(
                        "call_retry",
                        shard,
                        call_started=call_started,
                        error=str(result.get("error") or ""),
                        attempt=attempt,
                        sleep_seconds=sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
            receipt = _receipt_for_shard(
                shard,
                provider_name=provider_name,
                model=model,
                prompt_field=prompt_field,
                text=str(result.get("text") or ""),
                usage=result.get("usage") or {},
                finish_reason=result.get("finish_reason"),
                error=result.get("error"),
                started_at=call_started,
            )
            _emit_call_event("call_finished", shard, call_started=call_started, receipt=receipt)
            return receipt

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = [pool.submit(_one, shard) for shard in selected]
            for future in as_completed(futures):
                receipts.append(future.result())

    receipts.sort(key=lambda row: str(row.get("shard_id") or ""))
    outputs_path = out_dir / "model_outputs.jsonl"
    manifest_path = out_dir / "manifest.json"
    _write_jsonl(outputs_path, receipts)

    total_usage = {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in receipts),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in receipts),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in receipts),
    }
    manifest_duration = round(time.time() - started, 3)
    manifest = {
        "record_type": "primitive_factory_model_worker_manifest",
        "provider": provider_name,
        "model": model,
        "shards_path": str(shards_path.relative_to(REPO_ROOT) if shards_path.is_relative_to(REPO_ROOT) else shards_path),
        "out_dir": str(out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir),
        "outputs_path": str(outputs_path.relative_to(REPO_ROOT) if outputs_path.is_relative_to(REPO_ROOT) else outputs_path),
        "call_events_path": str(call_events_path.relative_to(REPO_ROOT) if call_events_path.is_relative_to(REPO_ROOT) else call_events_path),
        "selected_shards": len(selected),
        "available_shards": len(all_shards),
        "workers": max(1, workers),
        "mode": mode,
        "cdp_url": cdp_url if mode == "cdp" else "",
        "dry_run": dry_run,
        "prompt_raw_candidate_target": prompt_raw_candidate_target,
        "prompt_useful_candidate_target": prompt_useful_candidate_target,
        "paused": bool(pause_status.get("active")),
        "pause_reason": str(pause_status.get("reason") or "") if pause_status.get("active") else "",
        "pause_file": str(pause_status.get("pause_file") or "") if pause_status.get("active") else "",
        "pause_expires_at_utc": str(pause_status.get("expires_at_utc") or "") if pause_status.get("active") else "",
        "error_count": sum(1 for row in receipts if row.get("error")),
        "usage": total_usage,
        "duration_seconds": manifest_duration,
        "aggregate_completion_tps": (
            round(total_usage["completion_tokens"] / manifest_duration, 3)
            if manifest_duration and total_usage["completion_tokens"]
            else 0
        ),
        "aggregate_total_tps": (
            round(total_usage["total_tokens"] / manifest_duration, 3)
            if manifest_duration and total_usage["total_tokens"]
            else 0
        ),
        "candidate": True,
        "serves_truth": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shards_path = root / "shards.jsonl"
        shard = {
            "record_type": "primitive_factory_shard",
            "shard_id": "pfs:test",
            "run_date": "2026-06-30",
            "lane_id": "test-lane",
            "raw_candidate_target": 4,
            "useful_candidate_target": 1,
            "candidate_writer_prompt": "Emit one candidate primitive JSON object.",
            "candidate": True,
            "serves_truth": False,
        }
        _write_jsonl(shards_path, [shard])
        manifest = run_worker(
            shards_path=shards_path,
            out_dir=root / "out",
            provider_name="openwebui",
            model=OPENWEBUI_DEFAULT_MODEL,
            prompt_field="candidate_writer_prompt",
            workers=2,
            limit=0,
            offset=0,
            max_tokens=64,
            timeout=5,
            dry_run=True,
            mode="direct",
            cdp_url="",
            prompt_raw_candidate_target=2,
            prompt_useful_candidate_target=1,
        )
        rows = _read_jsonl(root / "out" / "model_outputs.jsonl")
        ok = (
            manifest["selected_shards"] == 1
            and manifest["dry_run"] is True
            and rows[0]["candidate"] is True
            and rows[0]["serves_truth"] is False
            and rows[0]["status"] == "planned"
            and rows[0]["raw_candidate_target"] == 2
            and rows[0]["useful_candidate_target"] == 1
            and rows[0]["prompt_sha256"]
            and not rows[0]["assistant_content"]
        )
    retry_classification_ok = (
        _retryable_error("HTTPError: HTTP Error 429: Too Many Requests upstream hiccup") is True
        and _retryable_error("too many concurrent requests") is True
        and _retryable_error(
            'HTTPError: HTTP Error 429: Too Many Requests {"error":"you have '
            f'{OLLAMA_USAGE_LIMIT_MARKER_SESSION}, add extra usage"}}'
        ) is False
        and _retryable_error(f"{OLLAMA_USAGE_PAUSE_ERROR_LABEL}: Ollama Cloud calls are paused until later") is False
        and _retryable_error(f"AssertionError: {GEMMA_SESSION_DOWN_ERROR_LABEL}: Open WebUI CDP fetch failed: "
                             "status=521") is False
        and _retryable_error(f"AssertionError: {GEMMA_RATE_LIMITED_ERROR_LABEL}: next gemma call slot opens in "
                             "40.0s") is False
        and _retryable_error("TimeoutError: The read operation timed out") is False
        and _retryable_error("") is False
    )
    ok = ok and retry_classification_ok
    print(
        "PASS - primitive factory model worker: dry-run shard receipts are candidate-only and credential-free; "
        "usage-cap 429s, active Ollama usage pauses, Gemma session-down breaker hits, and Gemma rate-limited "
        "slots are non-retryable (fail fast, honest labels; the failed-shard retry loop requeues)."
        if ok else
        "FAIL - primitive factory model worker self-test failed"
        + ("" if retry_classification_ok else " (retry classification)")
    )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--shards", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--provider", default="openwebui", choices=sorted(["ollama", "openrouter", "openwebui"]))
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--prompt-field", default="candidate_writer_prompt")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mode", choices=["direct", "cdp"], default="direct")
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--prompt-raw-candidate-target", type=int, default=0,
                        help="Override shard prompts to emit no more than this many raw rows.")
    parser.add_argument("--prompt-useful-candidate-target", type=int, default=0,
                        help="Override shard prompts to emit exactly this many useful rows.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.workers <= 0:
        print("FAIL: --workers must be positive", file=sys.stderr)
        return 1

    shards_path = Path(args.shards) if args.shards else _default_shards_path(args.date)
    if not shards_path.is_absolute():
        shards_path = _resource(shards_path)
    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUT_DIR / args.date / args.provider
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)

    try:
        manifest = run_worker(
            shards_path=shards_path,
            out_dir=out_dir,
            provider_name=args.provider,
            model=args.model,
            prompt_field=args.prompt_field,
            workers=args.workers,
            limit=args.limit,
            offset=args.offset,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            dry_run=args.dry_run,
            mode=args.mode,
            cdp_url=args.cdp_url,
            prompt_raw_candidate_target=args.prompt_raw_candidate_target,
            prompt_useful_candidate_target=args.prompt_useful_candidate_target,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
