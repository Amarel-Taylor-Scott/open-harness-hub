#!/usr/bin/env python3
"""scripts.hy3_overnight_flywheel — a FREE, MULTI-PROVIDER, MULTI-KEY, STOP-gated overnight flywheel
(2026-07-08). Rotates across DIVERSE free/keyed provider lanes so we don't all fight one rate pool:
OpenRouter free models (Hy3/nemotron/qwen/gpt-oss/gemma-4 — with multi-KEY rotation), Ollama Cloud (glm-5.2/
kimi), NVIDIA Build (glm-5.2), and LOCAL Ollama (gemma4, unlimited). It mints SUBSTANTIAL deterministic
primitives (multi-function, edge-case-handling, ~20-60 lines — not one-liners) + drafts executors for our
candidate SPECS, each scanned by the security gate and stored candidate-only (serves_truth=false).

Fixes baked in: (1) upstream 429 / rate-limit is RETRYABLE — the lane goes on exponential-backoff cooldown and
we rotate to the next available lane (throttled lanes recover instead of being wasted). (2) OpenRouter keys
rotate across `.agent/openrouter_keys.txt` (add more keys = more free rate). (3) prompts demand LONGER, robust,
multi-function primitives (our hand-written packs median ~17 lines; this targets that, not 2-line stubs).

Safety: dedicated kill switch `.agent/STOP_HY3_FLYWHEEL`, capped (--iterations/--minutes), resumable
(append-only), non-destructive, candidate-only, keys only from .agent/.env (gitignored, never committed).

    python3 scripts/hy3_overnight_flywheel.py --self-test          # offline (stub LLM), no network
    python3 scripts/hy3_overnight_flywheel.py --run --iterations 8 # a short REAL multi-provider run
    # overnight:  nohup python3 scripts/hy3_overnight_flywheel.py --run --iterations 100000 --minutes 600 &
    #   stop:  touch .agent/STOP_HY3_FLYWHEEL      add keys:  append to .agent/openrouter_keys.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"hy3_overnight_flywheel requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
FLYWHEEL_VERSION = "hy3-overnight-flywheel-v2-multiprovider"
#: DIVERSE lanes = (provider, model). Different providers => separate rate pools (Ollama/NVIDIA don't share
#: OpenRouter's free limit; local Ollama has NO limit). Add/remove a lane = one row.
LANES: tuple[tuple[str, str], ...] = (
    # CLOUD lanes only (local Ollama removed — owner's 8GB GPU can't run these; it stalled the loop). Every
    # lane here can produce long output. Diverse providers => separate rate pools.
    ("openrouter", "tencent/hy3:free"),
    ("nvidia", "z-ai/glm-5.2"),
    ("ollama", "glm-5.2"),
    ("ollama", "kimi-k2.7-code"),
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
    ("openrouter", "qwen/qwen3-coder:free"),
    ("openrouter", "qwen/qwen3-next-80b-a3b-instruct:free"),
    ("openrouter", "openai/gpt-oss-120b:free"),
    ("openrouter", "google/gemma-4-31b-it:free"),
    # WIDENED free-model pool (2026-07-08, discovered live from OpenRouter /models — all pricing $0): more distinct
    # free models = more per-model rate headroom under 429 + more output variety (the multi-path law applied to lanes).
    ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
    ("openrouter", "nousresearch/hermes-3-llama-3.1-405b:free"),
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("openrouter", "nvidia/nemotron-nano-9b-v2:free"),
    ("openrouter", "openai/gpt-oss-20b:free"),
    ("openrouter", "cohere/north-mini-code:free"),
    ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    ("openrouter", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"),
    ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),
)
TASKS: tuple[str, ...] = ("composite_primitive", "spec_executor", "doc_digest")
_DOC_EXTS = (".md", ".txt", ".rst", ".py", ".json", ".yaml", ".yml")
_DOC_STATE: dict[str, Any] = {"dir": None, "chunks": None}
#: an upstream 429 / rate-limit / provider-pause is RETRYABLE (not a miss) — cool the lane and rotate.
_THROTTLE_RE = re.compile(r"429|rate.?limit|temporarily rate|Provider returned error|Too Many Requests|"
                          r"paused|usage.?pause|session_down|deadline|timed? ?out", re.I)
BACKOFF_BASE_S = 20.0    # first cooldown after a lane throttles (doubles per consecutive throttle)
BACKOFF_CAP_S = 300.0    # max per-lane cooldown
_LONG_CHARS = 500        # a "substantial" primitive body (our hand-written median ~926 chars)
#: richer capabilities that WARRANT longer, multi-function code (not one-liners)
SEED_CAPABILITIES: tuple[str, ...] = (
    "parse a full US mailing address string into components (recipient, street number, street, unit/apt, "
    "city, state, ZIP+4) with robust edge-case handling",
    "parse a money string handling currency symbols/codes, accounting negatives (parentheses), and "
    "abbreviations like 1.2M into a Decimal amount + minor units",
    "compute a Fellegi-Sunter style match score between two person records (name, dob, address) using m/u "
    "log-weights with a review band",
    "reconstruct change events between two dict snapshots (retroactive CDC): added/removed/changed fields "
    "with observed-between windows and flip-flop detection",
    "classify a party name as person/company/trust/estate and safely split compound names like 'John & Jane "
    "Doe' without inventing missing given names",
    "normalize and validate an international phone number by country, returning E.164 plus edge-case flags",
    "detect and classify the typo between two strings (insertion/deletion/transposition/keyboard-neighbor/"
    "OCR-confusion) with a likelihood score",
    "standardize a company name: strip legal suffixes, normalize punctuation and ampersands, and build both "
    "a strict and a relaxed match key",
    "a checksum dispatcher that validates a US NPI (Luhn+prefix), an IBAN (mod-97), and an ABA routing number",
    "parse an ISO 8601 datetime/interval/duration into normalized UTC components with timezone offset "
    "handling and ambiguity flags")
_SYS = ("You mint EXHAUSTIVE, production-grade DETERMINISTIC data primitives. Output ONLY one JSON object — no "
        "prose, no markdown fences. The python_body MUST be a COMPLETE, THOROUGH module — the main primitive "
        "PLUS every helper function, validator, format-handler, and closely-related sub-primitive it needs. "
        "Favor completeness over brevity: handle every edge case, invalid input, and input-format variation "
        "you can think of; typically 80-250+ lines. Do NOT truncate, summarize, or leave TODOs — write the "
        "full implementation. Pure Python stdlib only (re, decimal, datetime, unicodedata, json, math, "
        "collections). NO network, eval/exec, subprocess, or file writes. JSON keys exactly: name, "
        "input_schema, output_schema, determinism_level (D0_pure|D1_seeded), failure_modes (list), "
        "edge_cases (list), python_body (the full module as one string).")
_RAW_SNIPPET = (
    "def messy(s):\n  # legacy cleanup grab-bag seen across many notebooks\n  s=s.strip().lower()\n"
    "  s=s.replace('  ',' ')\n  for ch in ['!','?','\"']: s=s.replace(ch,'')\n  return s")


def _build_prompt(task: str, payload: str) -> str:
    if task == "spec_executor":
        return (f"Write a COMPLETE, robust deterministic executor for this primitive SPEC — keep the contract, "
                f"add a substantial multi-function body with edge cases.\nSPEC: {payload}\nReturn the JSON "
                f"object described in the system message.")
    if task == "doc_digest":
        return (f"From this SOURCE (a document or code excerpt), extract ONE reusable, well-structured "
                f"deterministic primitive that it implies or describes — a COMPLETE module with helpers and "
                f"comprehensive edge cases.\nSOURCE:\n{payload}\nReturn the JSON object described in the system "
                f"message.")
    return (f"Build an EXHAUSTIVE primitive module for this capability — the main function plus every helper, "
            f"validator, format-handler, and related sub-primitive; comprehensive edge cases; as long as is "
            f"genuinely useful (80-250+ lines).\nCAPABILITY: {payload}\nReturn the JSON object described in the "
            f"system message.")


# ── robust JSON extraction (balanced braces, fence/prose tolerant) ───────────────────────────────────────────
def _extract_json_objects(text: str) -> list[str]:
    objs: list[str] = []
    depth = 0
    start = -1
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                objs.append(text[start:i + 1])
                start = -1
    return objs


def _parse_primitive(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.replace("```json", " ").replace("```python", " ").replace("```", " ")
    for span in sorted(_extract_json_objects(cleaned), key=len, reverse=True):
        try:
            obj = json.loads(span)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and obj.get("name") and obj.get("python_body"):
            return obj
    return None


def _lane_id(lane: tuple[str, str]) -> str:
    return f"{lane[0]}/{lane[1]}"


def _spec_payloads(limit: int = 400) -> list[str]:
    out: list[str] = []
    for mod in ("standards_factory_minter", "process_stage_factory", "enrichment_primitive_catalog"):
        try:
            m = __import__(f"scripts.{mod}", fromlist=["all_cards"])
            for c in m.all_cards():
                if c.get("needs_executor") and c.get("title"):
                    out.append(f"{c['title']} | in={c.get('input_edge')} out={c.get('output_edge')}")
        except Exception:  # pragma: no cover
            continue
    return out[:limit]


def _doc_chunks() -> list[str]:
    """Document/source chunks to DIGEST into primitives (the 'process & digest so many documents' lane). Reads
    text under the configured --docs dir (default: this repo's docs/ + catalog/), chunked ~6k chars. Cached."""
    if _DOC_STATE["chunks"] is not None:
        return _DOC_STATE["chunks"]
    roots = [Path(_DOC_STATE["dir"])] if _DOC_STATE["dir"] else [_sbc_boot / "docs", _sbc_boot / "catalog"]
    chunks: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in _DOC_EXTS:
                continue
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            for j in range(0, len(text), 6000):
                chunks.append(f"[{p.name}]\n{text[j:j + 6000]}")
                if len(chunks) >= 3000:
                    break
            if len(chunks) >= 3000:
                break
        if len(chunks) >= 3000:
            break
    _DOC_STATE["chunks"] = chunks or [_RAW_SNIPPET]
    return _DOC_STATE["chunks"]


# ── TASK REGISTRY: one worker pool, MANY job types (add a task = one row). Each: produces primitive|metadata,
#    a system prompt, a source key, and a prompt builder. Concurrent workers round-robin across ALL of them. ──
_LABEL_SYS = ("You LABEL a deterministic primitive across axes for a searchable registry. Output ONLY one JSON "
              "object, no prose: {name, persona:[...], industry:[...], geography:[...], standard:[...], "
              "datatype:[...], process_stage:[...], operations:[...], quality_score:int(0-100), tags:[...], "
              "notes}. Short lowercase terms.")
_QUESTION_SYS = ("You generate DECONSTRUCTION QUESTIONS about a source. Output ONLY one JSON object: "
                 "{source, questions:[...]} with 8-15 deep, specific questions that reveal how to rebuild the "
                 "source's capabilities from deterministic primitives. No prose.")
_INTERROGATE_SYS = ("You INTERROGATE a source and extract structured facts. Output ONLY one JSON object: "
                    "{source, facts:[{q, a}]} — ask 6-12 probing questions and answer each STRICTLY from the "
                    "source. No prose, no speculation.")


def _pack_primitives(limit: int = 300) -> list[str]:
    """Existing primitives (as text) to label/vary/critique."""
    try:
        from scripts.executable_pack_pool_sync import collect_pack_cards  # noqa: PLC0415
        out: list[str] = []
        for c in collect_pack_cards():
            b = c.get("executable_body")
            if b and c.get("language") == "python":
                out.append(f"{c.get('impl_name')}: {str(c.get('title', ''))[:120]} :: {b[:1400]}")
            if len(out) >= limit:
                break
        return out
    except Exception:  # pragma: no cover
        return []


def _parse_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.replace("```json", " ").replace("```python", " ").replace("```", " ")
    for span in sorted(_extract_json_objects(cleaned), key=len, reverse=True):
        try:
            obj = json.loads(span)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _p_variation(pl: str) -> str:
    return (f"Produce a complete VARIANT of this primitive with different settings, input formats, and edge "
            f"cases (a full module, not a tweak).\nPRIMITIVE: {pl}\nReturn the JSON object described in the "
            f"system message.")


def _p_critique(pl: str) -> str:
    return (f"Critique this primitive for correctness/edge-cases/robustness, then output an IMPROVED, more "
            f"complete version.\nPRIMITIVE: {pl}\nReturn the JSON object described in the system message.")


#: task -> {produces, system, source, prompt}. Add a job type by adding a row.
TASK_SPECS: dict[str, dict[str, Any]] = {
    "composite_primitive": {"produces": "primitive", "system": _SYS, "source": "seeds",
                            "prompt": lambda pl: _build_prompt("composite_primitive", pl)},
    "spec_executor": {"produces": "primitive", "system": _SYS, "source": "specs",
                      "prompt": lambda pl: _build_prompt("spec_executor", pl)},
    "doc_digest": {"produces": "primitive", "system": _SYS, "source": "docs",
                   "prompt": lambda pl: _build_prompt("doc_digest", pl)},
    "variation": {"produces": "primitive", "system": _SYS, "source": "primitives", "prompt": _p_variation},
    "critique_improve": {"produces": "primitive", "system": _SYS, "source": "primitives", "prompt": _p_critique},
    "primitive_labeling": {"produces": "metadata", "system": _LABEL_SYS, "source": "primitives",
                           "prompt": lambda pl: f"Label this primitive across all axes.\nPRIMITIVE: {pl}"},
    "question_generation": {"produces": "metadata", "system": _QUESTION_SYS, "source": "docs",
                            "prompt": lambda pl: f"Generate deconstruction questions.\nSOURCE:\n{pl}"},
    "interrogate": {"produces": "metadata", "system": _INTERROGATE_SYS, "source": "docs",
                    "prompt": lambda pl: f"Interrogate this source; extract structured facts.\nSOURCE:\n{pl}"},
}
TASK_NAMES: tuple[str, ...] = tuple(TASK_SPECS)


def build_sources(specs: list[str] | None = None) -> dict[str, list[str]]:
    """The material each task draws from — built once, shared by all workers."""
    seeds = list(SEED_CAPABILITIES)
    return {"seeds": seeds, "specs": (specs if specs is not None else _spec_payloads()) or seeds,
            "docs": _doc_chunks() or seeds, "primitives": _pack_primitives() or seeds}


def run_iteration(i: int, lane: tuple[str, str], task: str,
                  chat_fn: Callable[[str, str, str, str], dict[str, Any]],
                  sources: dict[str, list[str]], now_ts: float) -> dict[str, Any]:
    """One worker step: run `task` (from TASK_SPECS) on a (provider, model) lane. Primitive-producing tasks are
    security-gated + formalized; metadata tasks (label/question/interrogate) are recorded as-is (no code)."""
    from scripts.primitive_security_gate import gate_body  # noqa: PLC0415
    from scripts.primitive_package_contract import formalize_card  # noqa: PLC0415
    provider_name, model = lane
    lane_id = _lane_id(lane)
    spec = TASK_SPECS[task]
    src = sources.get(spec["source"]) or sources.get("seeds") or [_RAW_SNIPPET]
    payload = src[i % len(src)]
    prompt = spec["prompt"](payload)
    base = {"iteration": i, "lane": lane_id, "task": task, "ts": now_ts, **BOUNDARY}
    try:
        res = chat_fn(provider_name, model, spec["system"], prompt)
    except Exception as exc:
        return {"record_type": "flywheel_iteration_error", "error": str(exc)[:200], **base}
    text = res.get("text") if isinstance(res, dict) else str(res)
    err = res.get("error") if isinstance(res, dict) else None
    if err and _THROTTLE_RE.search(str(err)):
        return {"record_type": "flywheel_iteration_throttled", "error": str(err)[:200], **base}
    parsed = _parse_json(text or "")
    if err or not parsed:
        return {"record_type": "flywheel_iteration_miss",
                "error": (str(err)[:120] if err else "unparseable_output"), **base}
    common = {"flywheel_task": task, "model_lane": lane_id, "provider": provider_name, "model": model,
              "usage": res.get("usage") if isinstance(res, dict) else None,
              "prompt_hash": canonical_id("p", prompt), "response_hash": canonical_id("r", text or ""),
              "flywheel_version": FLYWHEEL_VERSION, "ts": now_ts}
    if spec["produces"] == "metadata":
        return {"record_type": "flywheel_metadata", "produces": "metadata",
                "payload_ref": str(payload)[:140], "content": parsed,
                "body_chars": len(json.dumps(parsed)), **common, **BOUNDARY}
    name, body = parsed.get("name"), str(parsed.get("python_body") or "")
    if not (name and body):
        return {"record_type": "flywheel_iteration_miss", "error": "primitive_missing_name_or_body", **base}
    verdict = gate_body(body, name=str(name))
    card = formalize_card({
        "primitive_id": canonical_id("prim-fly", str(name), body), "impl_name": str(name),
        "record_type": "flywheel_primitive_candidate", "kind": "primitive", "title": str(name)[:160],
        "language": "python", "executable_body": body, "input_edge": "RawObservedValue",
        "output_edge": "TypedCanonicalValue",
        "blackbox": f"Flywheel-minted ({task}) via {lane_id}: {str(name)}. {len(body)} chars. "
                    f"Security {verdict['status']}.",
        "input_schema": parsed.get("input_schema"), "output_schema": parsed.get("output_schema"),
        "declared_failure_modes": parsed.get("failure_modes"), "declared_edge_cases": parsed.get("edge_cases"),
        "pack_module": "hy3_overnight_flywheel"})
    card.update({"produces": "primitive", "body_chars": len(body), "security_status": verdict["status"],
                 "security_findings": [f["rule"] for f in verdict["findings"]],
                 "runnable_eligible": verdict["status"] == "pass", **common})
    return card


def flywheel(*, iterations: int, minutes: float,
             chat_fn: Callable[[str, str, str, str], dict[str, Any]],
             out_path: Path, stop_path: Path, status_path: Path, clock: Callable[[], float],
             specs: list[str] | None = None, sleep_fn: Callable[[float], None] = time.sleep,
             workers: int = 8) -> dict[str, Any]:
    """CONCURRENT flywheel: `workers` threads each pick an available lane (per-lane exponential-backoff
    cooldown, round-robin) and make an LLM call IN PARALLEL — so many keys/providers run at once (how you make
    the most of the free window). STOP-gated + time/iteration-capped + append-only + thread-safe: the slow LLM
    call runs OUTSIDE the lock so calls overlap; only state + the pool append are serialized."""
    sources = build_sources(specs)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start = clock()
    lock = threading.Lock()
    stop_event = threading.Event()
    st: dict[str, Any] = {"i": 0, "minted": 0, "passed": 0, "quarantined": 0, "misses": 0, "throttled": 0,
                          "errors": 0, "long_minted": 0, "total_chars": 0, "records": 0, "by_lane": {},
                          "by_task": {}, "cooldown_until": {}, "streak": {}, "ptr": 0}
    pool = out_path.open("a")

    def _status() -> dict[str, Any]:  # call under lock
        m = st["minted"]
        s = {"record_type": "hy3_flywheel_status", "iterations_done": st["i"], "minted": m,
             "metadata_records": st["records"], "security_pass": st["passed"], "quarantined": st["quarantined"],
             "misses": st["misses"], "throttled": st["throttled"], "errors": st["errors"],
             "long_minted": st["long_minted"], "avg_body_chars": round(st["total_chars"] / m) if m else 0,
             "workers": workers, "by_lane": dict(st["by_lane"]), "by_task": dict(st["by_task"]),
             "cooldown_lanes": sorted(l for l, t in st["cooldown_until"].items() if t > clock()),
             "elapsed_min": round((clock() - start) / 60.0, 2), "flywheel_version": FLYWHEEL_VERSION, **BOUNDARY}
        status_path.write_text(json.dumps(s, indent=2, sort_keys=True))
        return s

    def _worker() -> None:
        while not stop_event.is_set():
            now = clock()
            with lock:
                if stop_path.exists():
                    stop_event.set()
                    return
                if (iterations and st["i"] >= iterations) or (minutes and (now - start) / 60.0 >= minutes):
                    return
                lane = None
                for k in range(len(LANES)):
                    cand = LANES[(st["ptr"] + k) % len(LANES)]
                    if st["cooldown_until"].get(_lane_id(cand), 0.0) <= now:
                        lane, st["ptr"] = cand, (st["ptr"] + k + 1) % len(LANES)
                        break
                if lane is None:
                    cds = [t for t in st["cooldown_until"].values() if t > now]
                    wait = min(10.0, max(0.5, (min(cds) - now) if cds else 1.0))
                else:
                    idx, task, lid = st["i"], TASK_NAMES[st["i"] % len(TASK_NAMES)], _lane_id(lane)
                    st["i"] += 1
            if lane is None:
                sleep_fn(wait)
                continue
            row = run_iteration(idx, lane, task, chat_fn, sources, now)  # SLOW — no lock, runs in parallel
            with lock:
                st["by_lane"][lid] = st["by_lane"].get(lid, 0) + 1
                rt = row.get("record_type")
                if rt == "flywheel_primitive_candidate":
                    pool.write(json.dumps(row, sort_keys=True) + "\n")
                    pool.flush()
                    st["minted"] += 1
                    st["passed"] += 1 if row.get("security_status") == "pass" else 0
                    st["quarantined"] += 1 if row.get("security_status") == "quarantine" else 0
                    st["total_chars"] += int(row.get("body_chars") or 0)
                    st["long_minted"] += 1 if int(row.get("body_chars") or 0) >= _LONG_CHARS else 0
                    st["by_task"][task] = st["by_task"].get(task, 0) + 1
                    st["streak"][lid] = 0
                elif rt == "flywheel_metadata":
                    pool.write(json.dumps(row, sort_keys=True) + "\n")
                    pool.flush()
                    st["records"] += 1
                    st["by_task"][task] = st["by_task"].get(task, 0) + 1
                    st["streak"][lid] = 0
                elif rt == "flywheel_iteration_throttled":
                    st["throttled"] += 1
                    st["streak"][lid] = st["streak"].get(lid, 0) + 1
                    st["cooldown_until"][lid] = now + min(BACKOFF_BASE_S * (2 ** (st["streak"][lid] - 1)),
                                                          BACKOFF_CAP_S)
                elif rt == "flywheel_iteration_error":
                    st["errors"] += 1
                else:
                    st["misses"] += 1
                    st["streak"][lid] = 0
                _status()

    threads = [threading.Thread(target=_worker, daemon=True) for _ in range(max(1, workers))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    pool.close()
    with lock:
        summ = _status()
    return {**summ, "record_type": "hy3_flywheel_summary", "pool_path": str(out_path)}


def _load_openrouter_keys() -> list[str]:
    """All OpenRouter keys to rotate (more keys = more free rate) — from .agent/openrouter_keys.txt, else .env."""
    kf = _sbc_boot.parent.parent / ".agent" / "openrouter_keys.txt"
    if kf.exists():
        ks = [ln.strip() for ln in kf.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
        if ks:
            return ks
    from scripts import _llm_client as L  # noqa: PLC0415
    k = L.resolve_provider("openrouter").get("key")
    return [k] if k else []


#: non-OpenRouter model max output (OpenRouter maxes are fetched live from its /models metadata)
_NONOR_MAX_OUT: dict[str, int] = {"z-ai/glm-5.2": 65536, "glm-5.2": 65536, "kimi-k2.7-code": 65536}
_MAXOUT_REJECT_RE = re.compile(r"max_tokens|maximum context|context length|too large|too many tokens|"
                               r"invalid.*max|length", re.I)


def _openrouter_max_out() -> dict[str, int]:
    """model_id -> max_completion_tokens (the model's real OUTPUT ceiling) from OpenRouter metadata."""
    import urllib.request  # noqa: PLC0415
    fallback = {"tencent/hy3:free": 262144, "nvidia/nemotron-3-super-120b-a12b:free": 262144,
                "qwen/qwen3-coder:free": 262000, "openai/gpt-oss-120b:free": 131072,
                "google/gemma-4-31b-it:free": 32768, "qwen/qwen3-next-80b-a3b-instruct:free": 32768}
    try:
        d = json.loads(urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=20).read())
        out = {m.get("id"): int((m.get("top_provider") or {}).get("max_completion_tokens"))
               for m in d.get("data", []) if (m.get("top_provider") or {}).get("max_completion_tokens")}
        return out or fallback
    except Exception:  # pragma: no cover
        return fallback


def _real_chat():
    """Real multi-provider caller: START AT THE MODEL'S MAX OUTPUT (a small fixed cap TRUNCATES primitives),
    thread-safely rotate OpenRouter keys across concurrent workers, and halve max_tokens only if the provider
    rejects the size. The 175s socket timeout bounds each call (local Ollama — the only trickle-hang risk —
    is gone)."""
    from scripts import _llm_client as L  # noqa: PLC0415
    keys = _load_openrouter_keys()
    ormap = _openrouter_max_out()
    cache: dict[str, dict] = {}
    kstate = {"ki": 0}
    klock = threading.Lock()

    def _prov(name: str) -> dict:
        if name not in cache:
            cache[name] = L.resolve_provider(name)
        return cache[name]

    def _max_out(provider_name: str, model: str) -> int:
        return ormap.get(model, 32768) if provider_name == "openrouter" else _NONOR_MAX_OUT.get(model, 32768)

    def _c(provider_name: str, model: str, system: str, user: str) -> dict[str, Any]:
        p = dict(_prov(provider_name))  # copy so per-call key rotation doesn't mutate the cache
        if provider_name == "openrouter" and keys:
            with klock:  # thread-safe rotation across concurrent workers (each call uses the next key)
                p["key"] = keys[kstate["ki"] % len(keys)]
                kstate["ki"] += 1
        mt = _max_out(provider_name, model)  # START AT MAX OUTPUT (e.g. Hy3 = 262144), not a small cap
        out: dict[str, Any] = {"text": "", "error": "no_attempt"}
        for _ in range(4):
            out = L.chat(model, system, user, p, max_tokens=mt, timeout=175)
            out = out if isinstance(out, dict) else {"text": out}
            err = out.get("error")
            if err and _MAXOUT_REJECT_RE.search(str(err)) and mt > 2048:
                mt //= 2  # provider rejected the size -> REDUCE and retry (never start small)
                continue
            break
        return out
    return _c


def _paths() -> tuple[Path, Path, Path]:
    base = _sbc_boot / "data" / "dev-intel" / "hy3_overnight_flywheel"
    return (base / "flywheel_primitive_candidates.jsonl",
            _sbc_boot.parent.parent / ".agent" / "STOP_HY3_FLYWHEEL", base / "latest_status.json")


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    long_body = (
        "def parse_addr(s):\n    import re\n    if not isinstance(s, str) or not s.strip():\n"
        "        raise ValueError('empty')\n    parts = [p.strip() for p in s.split(',') if p.strip()]\n"
        "    if len(parts) < 2:\n        raise ValueError('too few parts')\n"
        "    out = {'raw': s, 'street': parts[0], 'city': None, 'state': None, 'zip5': None, 'zip4': None}\n"
        "    m = re.search(r'\\\\b(\\\\d{5})(?:-(\\\\d{4}))?\\\\s*$', s)\n    if m:\n"
        "        out['zip5'], out['zip4'] = m.group(1), m.group(2)\n"
        "    sm = re.search(r'\\\\b([A-Z]{2})\\\\b', s)\n    if sm:\n        out['state'] = sm.group(1)\n"
        "    if len(parts) >= 2:\n        out['city'] = parts[1]\n"
        "    um = re.search(r'\\\\b(apt|unit|ste|#)\\\\s*([\\\\w-]+)', parts[0], re.I)\n    if um:\n"
        "        out['unit'] = um.group(2)\n    return out")
    canned = json.dumps({"name": "parse_addr", "input_schema": {"s": "string"}, "output_schema": "object",
                         "determinism_level": "D0_pure", "failure_modes": ["too_few_parts"],
                         "edge_cases": ["no zip"], "python_body": long_body})
    dangerous = json.dumps({"name": "danger", "python_body": "def danger(s):\n    return eval(s)",
                            "input_schema": {}, "output_schema": "any", "determinism_level": "D0_pure",
                            "failure_modes": []})
    seq = [{"text": canned, "usage": {"cost": 0}}, {"text": dangerous, "usage": {"cost": 0}},
           {"text": "no json", "usage": {}}, {"text": "", "error": "HTTP Error 429: rate-limited upstream"},
           {"text": canned, "usage": {"cost": 0}}]
    n = {"i": 0}

    def stub(provider, model, system, user):
        r = seq[n["i"] % len(seq)]
        n["i"] += 1
        return r
    clk = {"t": 0.0}
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "pool.jsonl"
        summ = flywheel(iterations=5, minutes=0, chat_fn=stub, out_path=out, stop_path=Path(td) / "STOP",
                        status_path=Path(td) / "s.json",
                        clock=lambda: clk.__setitem__("t", clk["t"] + 1) or clk["t"], specs=["spec"],
                        sleep_fn=lambda s: None, workers=1)  # serial -> deterministic stub sequence
        rows = [json.loads(x) for x in out.read_text().splitlines()] if out.exists() else []
        checks.append(("mints from parseable output; garbage=miss; 429=THROTTLED (not miss/error)",
                       summ["minted"] == 3 and summ["misses"] == 1 and summ["throttled"] == 1
                       and summ["errors"] == 0))
        checks.append(("minted rows carry (provider, model) lane id + body_chars; substantial body tracked",
                       all("/" in r["model_lane"] and r["provider"] and r["body_chars"] > 0 for r in rows)
                       and summ["long_minted"] >= 1 and summ["avg_body_chars"] > 200))
        checks.append(("security gate: eval->quarantine + not runnable; clean->pass + runnable",
                       any(r["security_status"] == "quarantine" and not r["runnable_eligible"] for r in rows)
                       and any(r["security_status"] == "pass" and r["runnable_eligible"] for r in rows)))
    # CONCURRENCY smoke: 3 workers, all-canned stub -> mints all 6, thread-safe, no crash
    clk2 = {"t": 0.0}
    lk2 = threading.Lock()

    def _clock2():
        with lk2:
            clk2["t"] += 1
            return clk2["t"]
    with tempfile.TemporaryDirectory() as td2:
        s3 = flywheel(iterations=5, minutes=0, chat_fn=lambda p, m, s, u: {"text": canned, "usage": {}},
                      out_path=Path(td2) / "p.jsonl", stop_path=Path(td2) / "STOP",
                      status_path=Path(td2) / "s.json", clock=_clock2, specs=["x"], sleep_fn=lambda s: None,
                      workers=3)
    checks.append(("CONCURRENT run (3 workers) mints all 5 (primitive tasks), thread-safe, 0 errors",
                   s3["minted"] == 5 and s3["errors"] == 0 and s3["iterations_done"] == 5))
    checks.append(("run_iteration flags a rate-limit as throttled (retryable), not a miss",
                   run_iteration(0, ("openrouter", "x:free"), "composite_primitive",
                                 lambda p, m, s, u: {"text": "", "error": "429 Too Many Requests"},
                                 {"seeds": ["cap"]}, 0.0)["record_type"] == "flywheel_iteration_throttled"))
    # TASK REGISTRY: many job types, incl. metadata tasks routed differently (no code gate)
    md = run_iteration(0, ("ollama", "glm-5.2"), "primitive_labeling",
                       lambda p, m, s, u: {"text": json.dumps({"name": "x", "industry": ["healthcare"],
                                                               "quality_score": 80})},
                       {"primitives": ["x: t :: body"]}, 0.0)
    checks.append(("task registry: >=8 job types (gen/spec/digest/variation/critique/label/question/"
                   "interrogate); labeling -> flywheel_metadata record, not a code primitive",
                   len(TASK_NAMES) >= 8 and TASK_SPECS["question_generation"]["produces"] == "metadata"
                   and md["record_type"] == "flywheel_metadata" and md["flywheel_task"] == "primitive_labeling"
                   and md["content"].get("industry") == ["healthcare"]))
    checks.append(("lanes span cloud providers (openrouter/nvidia/ollama); NO local ollama; Hy3 leads",
                   {l[0] for l in LANES} == {"openrouter", "nvidia", "ollama"}
                   and LANES[0] == ("openrouter", "tencent/hy3:free")))
    fenced = ('```json\n{"name":"x","input_schema":{"a":{"n":1}},"python_body":"def x(s):\\n    return s",'
              '"output_schema":"s","determinism_level":"D0_pure","failure_modes":[]}\n```')
    checks.append(("parser survives fences + nested JSON", (_parse_primitive(fenced) or {}).get("name") == "x"))
    failed = [nm for nm, ok in checks if not ok]
    for nm, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {nm}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - hy3_overnight_flywheel v2: {len(LANES)} lanes across "
          f"{len({l[0] for l in LANES})} providers, multi-key rotation, per-lane backoff cooldown, "
          f"LONGER-primitive prompts, security-gated + candidate-only. Offline self-test. serves_truth=false.")
    return 0


def _add_keys(new_keys: list[str]) -> int:
    """Append+dedup OpenRouter keys to the gitignored keys file. Returns the total count."""
    kf = _sbc_boot.parent.parent / ".agent" / "openrouter_keys.txt"
    kf.parent.mkdir(parents=True, exist_ok=True)
    existing = [ln.strip() for ln in kf.read_text().splitlines() if ln.strip()] if kf.exists() else []
    for k in new_keys:
        k = k.strip()
        if k.startswith("sk-or-") and k not in existing:
            existing.append(k)
    kf.write_text("\n".join(existing) + "\n")
    return len(existing)


def main(argv: list[str] | None = None) -> int:
    import datetime  # noqa: PLC0415
    import sys as _sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--iterations", type=int, default=8)
    ap.add_argument("--minutes", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=8, help="concurrent lanes in flight (many keys => raise this)")
    ap.add_argument("--docs", default=None, help="dir of documents to DIGEST into primitives (doc_digest lane)")
    ap.add_argument("--add-keys", action="store_true",
                    help="read OpenRouter keys (one per line) from stdin, append+dedup to the keys file")
    args = ap.parse_args(argv)
    if args.add_keys:
        print(f"OpenRouter keys now: {_add_keys(_sys.stdin.read().splitlines())}")
        return 0
    if args.self_test:
        return _self_test()
    if args.run:
        if args.docs:
            _DOC_STATE["dir"] = args.docs
        pool, stop, status = _paths()
        keys = _load_openrouter_keys()
        print(f"flywheel v3 CONCURRENT: {len(LANES)} lanes x {args.workers} workers | keys={len(keys)} | "
              f"{len(TASK_NAMES)} job types {list(TASK_NAMES)} | iterations<={args.iterations} "
              f"minutes<={args.minutes or '∞'} | docs={args.docs or 'repo docs/'} | STOP: touch {stop}")
        summ = flywheel(iterations=args.iterations, minutes=args.minutes, chat_fn=_real_chat(), out_path=pool,
                        stop_path=stop, status_path=status, workers=args.workers,
                        clock=lambda: datetime.datetime.now(datetime.timezone.utc).timestamp())
        print(json.dumps({k: summ[k] for k in ("iterations_done", "minted", "metadata_records", "long_minted",
              "avg_body_chars", "security_pass", "quarantined", "misses", "throttled", "errors", "by_task",
              "by_lane", "elapsed_min")}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
