"""src.teleon.inference.receipts — durable, append-only JSONL sink for ModelInvocationReceipts.

WHY (model-plane unification step 1): receipts used to live only in per-process dicts (e.g. the
/api/inference handler's projection store) and were lost on restart. Every model-call plane now
appends each minted receipt here — the OIPS gateway (plane "oips") and the scripts.model_routes
shim (plane "model_routes"); the llm_gateway/foundry planes follow in later waves — so invocation
provenance survives restarts and all planes share ONE sink.

Guarantees:
  - METADATA + HASHES ONLY: a ModelInvocationReceipt already carries input/output HASHES, never raw
    prompts; this module additionally scrubs any raw-content/credential keys before writing
    (defense in depth — see _FORBIDDEN_RECEIPT_KEYS).
  - BEST-EFFORT, NEVER RAISES: provenance persistence must never break a live call path; a failed
    append returns False instead of raising.
  - NO CYCLES: stdlib-only and imports nothing from the rest of src/teleon, so oips, adapters, and
    repo tooling (scripts/) may all import it freely.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

_REPO_ROOT = Path(__file__).resolve().parents[3]
#: the ONE durable receipt sink shared by every model-call plane (append-only JSONL, one receipt per line)
RECEIPTS_JSONL_PATH = _REPO_ROOT / "dist" / "local-services-state" / "model-receipts" / "receipts.jsonl"
#: keys that must NEVER reach disk — raw content or credentials (receipts carry hashes, not text/keys)
_FORBIDDEN_RECEIPT_KEYS = frozenset({
    "api_key", "authorization", "bearer_token", "secret",
    "input_text", "output_text", "prompt", "prompt_template", "messages",
})


def base_host_of(url: str | None) -> str | None:
    """The EFFECTIVE base host of an endpoint URL as ``hostname[:port]`` — never userinfo
    credentials, never path/query (safe to record in a receipt). None when unparseable/empty."""
    try:
        split = urlsplit(str(url or ""))
        if not split.hostname:
            return None
        return split.hostname + (f":{split.port}" if split.port else "")
    except Exception:
        return None


def sanitize_receipt(receipt: dict) -> dict:
    """Drop any raw-content/credential keys (defense in depth — receipts are metadata + hashes only)."""
    return {k: v for k, v in receipt.items() if k not in _FORBIDDEN_RECEIPT_KEYS}


def persist_receipt(receipt: dict, *, plane: str, path: Path | None = None) -> bool:
    """Append one receipt (stamped with its ``plane`` of origin) as a JSONL line under
    RECEIPTS_JSONL_PATH (parents created). Best-effort: returns True on success, False on any
    failure — NEVER raises, so persistence can never break a live model call."""
    try:
        target = path or RECEIPTS_JSONL_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({**sanitize_receipt(dict(receipt)), "plane": plane}, sort_keys=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return True
    except Exception:
        return False


def load_receipts(*, limit: int | None = None, path: Path | None = None) -> list[dict]:
    """Read persisted receipts back (rehydration proof + projection feed). Newest-last; ``limit``
    keeps only the most recent N. Best-effort: unreadable file/lines are skipped, never raised."""
    target = path or RECEIPTS_JSONL_PATH
    rows: list[dict] = []
    try:
        with target.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rows.append(json.loads(raw))
                except Exception:
                    continue
    except Exception:
        return []
    return rows[-limit:] if limit else rows


__all__ = ["RECEIPTS_JSONL_PATH", "base_host_of", "sanitize_receipt", "persist_receipt", "load_receipts"]
