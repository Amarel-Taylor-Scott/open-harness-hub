"""src.baltor.workers.worker_router — classify + policy-gate a CommandEnvelope by its command_type prefix.

This is an ADDITIVE policy/classification layer over the existing DurableStore/CommandEnvelope/
ProcessorHarness path — it does NOT replace dispatch or create a second worker framework. It answers:
  - which worker BUCKET owns this command_type? (longest queue_prefix match)
  - is the bucket ALLOWED to emit this output_type? (forbidden_outputs)
  - is the command prefix even registered?
The load-bearing safety split: open_ended/browser/model workers may emit evidence/candidates/traces;
only the gated verification/reconciliation/consumption(native_export)/human buckets may publish truth.

Deterministic, offline (reads architecture/worker_bucket_registry.json). No wall-clock, no RNG.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO / "architecture" / "worker_bucket_registry.json"

#: buckets permitted to publish served truth (always via a gate, never directly/LLM-decided).
TRUTH_BUCKETS = {"reconciliation_policy", "native_export", "distillation_determinism", "human_review_signoff"}


class WorkerPolicyError(Exception):
    """A command type maps to no bucket, or a bucket attempted a forbidden output."""


def load_buckets() -> list[dict]:
    return json.loads(_REGISTRY.read_text())["buckets"]


def route(command_type: str, *, buckets: list[dict] | None = None) -> dict:
    """Return the bucket whose queue_prefix is the longest prefix of command_type. Raise if none."""
    bs = buckets if buckets is not None else load_buckets()
    def _match_len(b):
        # match by queue_prefix OR any allowed_command_prefix (legacy exact names predate the prefix scheme);
        # return the longest matching token length, else -1.
        toks = [b["queue_prefix"], *b.get("allowed_command_prefixes", [])]
        hits = [len(tk) for tk in toks if command_type == tk or command_type.startswith(tk)]
        return max(hits) if hits else -1
    scored = [(b, _match_len(b)) for b in bs]
    scored = [(b, n) for b, n in scored if n >= 0]
    if not scored:
        raise WorkerPolicyError(f"unknown command prefix: {command_type!r}")
    return max(scored, key=lambda bn: bn[1])[0]


def validate_output(bucket: dict, output_type: str) -> bool:
    """True iff the bucket may emit output_type (i.e. it is not in forbidden_outputs)."""
    return output_type not in set(bucket.get("forbidden_outputs", []))


def can_publish_truth(bucket: dict) -> bool:
    return bool(bucket.get("can_publish_truth"))


def check_command(command_type: str, output_type: str | None = None, *, buckets: list[dict] | None = None) -> dict:
    """Route + policy-check a command. Returns an allow record, or an ErrorEnvelope-shaped dict on violation."""
    try:
        b = route(command_type, buckets=buckets)
    except WorkerPolicyError as e:
        return {"schema_version": "ErrorEnvelope", "allowed": False, "reason": "unknown_prefix",
                "error": str(e), "command_type": command_type}
    if output_type is not None and not validate_output(b, output_type):
        return {"schema_version": "ErrorEnvelope", "allowed": False, "reason": "forbidden_output",
                "error": f"bucket {b['bucket_id']!r} forbids output {output_type!r}",
                "worker_bucket": b["bucket_id"], "command_type": command_type}
    return {"allowed": True, "worker_bucket": b["bucket_id"], "command_type": command_type,
            "can_publish_truth": can_publish_truth(b)}
