#!/usr/bin/env python3
"""scripts.llm_quota_manager — the COMPLIANCE + BUDGET guardrail for the provider-agnostic generation router
(scripts/llm_capability_router.py). The LLM proposes; this module is one of the deterministic gates that
DISPOSES: it decides whether a lane may be called AT ALL, and it records what happened — never the content.

Owns, for the router:
  * a KILL SWITCH — `.agent/STOP_LLM_GENERATION` halts ALL generation instantly (touch the file);
  * per-provider budgets (max requests / tokens / cost) + a per-CAMPAIGN cost cap;
  * per-lane cooldowns with EXPONENTIAL BACKOFF + JITTER (a throttled lane rests, it is not wasted);
  * DRY-RUN mode (estimate + record intent, never call);
  * estimated_cost BEFORE a call and actual_cost AFTER (when the provider returns usage);
  * a REDACTING usage ledger `artifacts/llm_usage/usage_ledger.jsonl` — it stores a prompt HASH and safe
    metadata ONLY; raw prompt text and secrets can never enter it (allowlisted fields, scrubbed strings);
  * a never-drop QUEUE `artifacts/llm_usage/generation_queue.jsonl` — when every lane is exhausted the job is
    persisted, never silently dropped.

Compliance law (see docs/LLM_ENDPOINT_USAGE_POLICY.md): do NOT bypass rate limits, do NOT rotate keys to
evade limits, keys only as configured, per-campaign cost caps, kill switch, redact before any call. Every row
is candidate=true, serves_truth=false.

    python3 scripts/llm_quota_manager.py --self-test     # offline, deterministic, mutation-gated
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
import datetime as _dt  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"llm_quota_manager requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: the ONE kill switch that halts all router-driven generation (touch it to stop; delete it to resume).
KILL_SWITCH_NAME = "STOP_LLM_GENERATION"
_AGENT_DIR = _sbc_boot.parent.parent / ".agent"          # repo-root/.agent (gitignored operator surface)
_ARTIFACTS_DIR = _sbc_boot / "artifacts" / "llm_usage"    # task: artifacts under shared-backend-components
LEDGER_FILENAME = "usage_ledger.jsonl"
QUEUE_FILENAME = "generation_queue.jsonl"

DEFAULT_BACKOFF_BASE_SECONDS = 20.0   # first cooldown after a lane throttles (doubles per consecutive throttle)
DEFAULT_BACKOFF_CAP_SECONDS = 300.0   # max per-lane cooldown
_JITTER_FRACTION = 0.25               # +up-to-25% jitter so fleet workers don't re-collide on the same second

#: ONLY these keys are ever written to the ledger. Anything else a caller passes (a raw prompt, a key) is
#: DROPPED here — this allowlist is the redaction guarantee, not a convention.
LEDGER_ALLOWLIST: tuple[str, ...] = (
    "job_id", "campaign", "provider", "model", "lane", "data_class", "endpoint_type",
    "prompt_hash", "schema_hash", "input_tokens", "output_tokens", "estimated_cost", "cost",
    "latency_s", "status", "error_class", "retry", "fallback", "structured", "dry_run", "ts",
)
#: string fields still get scrubbed of anything that looks like a key/token, defence-in-depth.
_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{6,}|Bearer\s+[A-Za-z0-9._\-]{6,}|AIza[A-Za-z0-9_\-]{6,})")
_REDACTED = "[redacted]"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scrub(value: Any) -> Any:
    return _SECRET_RE.sub(_REDACTED, value) if isinstance(value, str) else value


def prompt_hash(text: str) -> str:
    """The stable hash stored in place of a raw prompt (canonical id authority; never the text itself)."""
    return canonical_id("prompt", text or "")


def schema_hash(schema: Any) -> str:
    return canonical_id("schema", json.dumps(schema, sort_keys=True, default=str) if schema else "")


def estimate_cost(capability: dict[str, Any], input_tokens: int, output_tokens: int) -> float:
    """Estimated USD before a call from the lane's cost model (0.0 for the free lanes)."""
    ci = float(capability.get("cost_input_per_million") or 0.0)
    co = float(capability.get("cost_output_per_million") or 0.0)
    return round(input_tokens / 1_000_000.0 * ci + output_tokens / 1_000_000.0 * co, 8)


def backoff_seconds(attempt: int, *, base: float = DEFAULT_BACKOFF_BASE_SECONDS,
                    cap: float = DEFAULT_BACKOFF_CAP_SECONDS, rng: Optional[random.Random] = None,
                    jitter: bool = True) -> float:
    """Exponential backoff for consecutive throttles (attempt>=1), capped, with optional +jitter. Deterministic
    when jitter=False or a seeded rng is supplied (self-test uses that)."""
    raw = min(base * (2 ** max(0, attempt - 1)), cap)
    if not jitter:
        return round(raw, 3)
    r = (rng or random).random()
    return round(raw + raw * _JITTER_FRACTION * r, 3)


class QuotaManager:
    """Per-run budget/cooldown/kill-switch state + the redacting ledger. In-memory counters (a run is a
    process); the ledger + queue are append-only on disk. Injectable clock + rng keep the self-test hermetic."""

    def __init__(self, *, budgets: Optional[dict[str, dict[str, Any]]] = None,
                 campaign: str = "adhoc", campaign_cost_cap: Optional[float] = None,
                 kill_switch_path: Optional[Path] = None, ledger_path: Optional[Path] = None,
                 queue_path: Optional[Path] = None, dry_run: bool = False,
                 clock: Callable[[], float] = time.time, rng: Optional[random.Random] = None) -> None:
        self.budgets = budgets or {}
        self.campaign = campaign
        self.campaign_cost_cap = campaign_cost_cap
        self.kill_switch_path = kill_switch_path or (_AGENT_DIR / KILL_SWITCH_NAME)
        self.ledger_path = ledger_path or (_ARTIFACTS_DIR / LEDGER_FILENAME)
        self.queue_path = queue_path or (_ARTIFACTS_DIR / QUEUE_FILENAME)
        self.dry_run = dry_run
        self.clock = clock
        self.rng = rng or random.Random(0xA1D0)
        self.spent: dict[str, dict[str, float]] = {}
        self.campaign_cost = 0.0
        self._cooldown_until: dict[str, float] = {}
        self._streak: dict[str, int] = {}

    # ── kill switch ──────────────────────────────────────────────────────────────────────────────────────
    def kill_switch_active(self) -> bool:
        return self.kill_switch_path.exists()

    # ── cooldowns (per lane id) ──────────────────────────────────────────────────────────────────────────
    def is_cooling(self, lane_id: str) -> bool:
        return self._cooldown_until.get(lane_id, 0.0) > self.clock()

    def cooldown(self, lane_id: str, *, seconds: Optional[float] = None) -> float:
        """Rest a lane. seconds=None escalates by the lane's consecutive-throttle streak (exp backoff+jitter)."""
        self._streak[lane_id] = self._streak.get(lane_id, 0) + 1
        secs = backoff_seconds(self._streak[lane_id], rng=self.rng) if seconds is None else float(seconds)
        self._cooldown_until[lane_id] = self.clock() + secs
        return secs

    def clear_streak(self, lane_id: str) -> None:
        self._streak[lane_id] = 0

    # ── budgets ──────────────────────────────────────────────────────────────────────────────────────────
    def check(self, provider_id: str, lane_id: str, *, estimated_cost: float = 0.0) -> tuple[bool, str]:
        """May this lane be called now? Ordered gates: kill switch -> cooldown -> per-provider budget ->
        per-campaign cost cap. Returns (ok, reason)."""
        if self.kill_switch_active():
            return False, "kill_switch_active"
        if self.is_cooling(lane_id):
            return False, "lane_cooling"
        b = self.budgets.get(provider_id, {})
        s = self.spent.get(provider_id, {"requests": 0.0, "tokens": 0.0, "cost": 0.0})
        if b.get("max_requests") is not None and s["requests"] >= b["max_requests"]:
            return False, "provider_request_budget_exhausted"
        if b.get("max_tokens") is not None and s["tokens"] >= b["max_tokens"]:
            return False, "provider_token_budget_exhausted"
        if b.get("max_cost") is not None and s["cost"] + estimated_cost > b["max_cost"]:
            return False, "provider_cost_budget_exceeded"
        if self.campaign_cost_cap is not None and self.campaign_cost + estimated_cost > self.campaign_cost_cap:
            return False, "campaign_cost_cap_exceeded"
        return True, "ok"

    def charge(self, provider_id: str, *, requests: int = 1, tokens: int = 0, cost: float = 0.0) -> None:
        s = self.spent.setdefault(provider_id, {"requests": 0.0, "tokens": 0.0, "cost": 0.0})
        s["requests"] += requests
        s["tokens"] += tokens
        s["cost"] += cost
        self.campaign_cost += cost

    # ── ledger + queue (append-only, redacted) ───────────────────────────────────────────────────────────
    def _append(self, path: Path, row: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    def record(self, **fields: Any) -> dict[str, Any]:
        """Append ONE redacted usage row. Only LEDGER_ALLOWLIST keys survive (raw prompt/secret kwargs are
        dropped here — that is the redaction guarantee); string values are scrubbed of key-shaped tokens."""
        row: dict[str, Any] = {k: _scrub(fields.get(k)) for k in LEDGER_ALLOWLIST}
        row["record_type"] = "llm_usage_ledger_row"
        row.setdefault("campaign", self.campaign)
        row["ts"] = fields.get("ts") or _now_iso()
        row["dry_run"] = bool(self.dry_run or fields.get("dry_run"))
        row.update(BOUNDARY)
        self._append(self.ledger_path, row)
        return row

    def enqueue(self, job: dict[str, Any]) -> dict[str, Any]:
        """Persist an unfulfillable job (all lanes exhausted / halted) so it is NEVER silently dropped."""
        row = {"record_type": "llm_generation_queue_row", "campaign": self.campaign,
               "enqueued_at": _now_iso(), "job": {k: _scrub(v) for k, v in job.items()
                                                   if k not in ("system", "user", "prompt")},
               "job_prompt_hash": prompt_hash(str(job.get("user") or job.get("prompt") or "")),
               **BOUNDARY}
        self._append(self.queue_path, row)
        return row


# ── self-test (offline, deterministic, mutation-gated) ─────────────────────────────────────────────────────
def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    clk = {"t": 1000.0}
    cap_free = {"cost_input_per_million": 0.0, "cost_output_per_million": 0.0}
    cap_paid = {"cost_input_per_million": 3.0, "cost_output_per_million": 6.0}

    checks.append(("estimate_cost is 0 for a free lane, positive + correct for a paid one",
                   estimate_cost(cap_free, 1000, 1000) == 0.0
                   and estimate_cost(cap_paid, 1_000_000, 1_000_000) == 9.0))

    # backoff grows, caps, and jitter never lowers below the raw value
    b1 = backoff_seconds(1, jitter=False)
    b2 = backoff_seconds(2, jitter=False)
    b_big = backoff_seconds(50, jitter=False)
    seeded = backoff_seconds(2, rng=random.Random(1))
    checks.append(("backoff exponential + capped; jitter only adds",
                   b2 == b1 * 2 and b_big == DEFAULT_BACKOFF_CAP_SECONDS and seeded >= b2))

    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        qm = QuotaManager(campaign="unit", kill_switch_path=tp / "STOP", ledger_path=tp / "led.jsonl",
                          queue_path=tp / "q.jsonl", clock=lambda: clk["t"], rng=random.Random(7),
                          budgets={"nvidia": {"max_requests": 2, "max_cost": 5.0}},
                          campaign_cost_cap=10.0)

        ok, reason = qm.check("nvidia", "nvidia:glm")
        checks.append(("a fresh lane passes the budget check", ok and reason == "ok"))

        # kill switch halts everything
        (tp / "STOP").write_text("halt")
        ko, kr = qm.check("nvidia", "nvidia:glm")
        checks.append(("the kill switch halts the check", (not ko) and kr == "kill_switch_active"
                       and qm.kill_switch_active()))
        (tp / "STOP").unlink()

        # per-provider request budget
        qm.charge("nvidia", requests=2)
        rok, rr = qm.check("nvidia", "nvidia:glm")
        checks.append(("provider request budget is enforced", (not rok) and rr == "provider_request_budget_exhausted"))

        # per-provider cost budget + campaign cap
        qm2 = QuotaManager(campaign="unit2", kill_switch_path=tp / "NOPE", ledger_path=tp / "l2.jsonl",
                           queue_path=tp / "q2.jsonl", clock=lambda: clk["t"],
                           budgets={"openrouter": {"max_cost": 1.0}}, campaign_cost_cap=0.5)
        cok, crs = qm2.check("openrouter", "openrouter:hy3", estimated_cost=0.75)
        checks.append(("campaign cost cap fails before the provider budget (tighter gate wins)",
                       (not cok) and crs == "campaign_cost_cap_exceeded"))

        # cooldown with streak escalation
        s1 = qm.cooldown("nvidia:glm")
        checks.append(("cooldown marks the lane as cooling and returns a positive rest",
                       s1 > 0 and qm.is_cooling("nvidia:glm")))
        clk["t"] += s1 + 1
        checks.append(("cooldown expires with the clock", not qm.is_cooling("nvidia:glm")))
        s2 = qm.cooldown("nvidia:glm")  # streak now 2
        checks.append(("consecutive throttles escalate the backoff (streak)", s2 > s1))

        # REDACTION: raw prompt + a key passed as kwargs are DROPPED; only the hash + safe fields survive
        row = qm.record(job_id="j1", provider="openrouter", model="tencent/hy3:free", lane="openrouter:hy3",
                        prompt_hash=prompt_hash("PARSE THIS SECRET ADDRESS 42 Main St"),
                        input_tokens=100, output_tokens=200, status="ok", retry=0, fallback=False,
                        system="You are a bot. api_key=sk-or-abc123deadbeef",  # must NOT reach disk
                        user="PARSE THIS SECRET ADDRESS 42 Main St",           # must NOT reach disk
                        error_class="Bearer sk-or-shouldbescrubbed")            # scrubbed even if allowlisted
        written = (tp / "led.jsonl").read_text()
        checks.append(("ledger stores the prompt HASH, never the raw prompt or a key",
                       "PARSE THIS SECRET ADDRESS" not in written and "sk-or-abc123deadbeef" not in written
                       and "system" not in row and "user" not in row and row["prompt_hash"].startswith("prompt-")))
        checks.append(("even an allowlisted string is scrubbed of key-shaped tokens",
                       _REDACTED in str(row.get("error_class")) and "sk-or-shouldbescrubbed" not in written))
        checks.append(("ledger rows are candidate/serves_truth=false", row["serves_truth"] is False
                       and row["record_type"] == "llm_usage_ledger_row"))

        # NEVER-DROP queue: an unfulfillable job is persisted without its raw prompt body
        q = qm.enqueue({"job_id": "j2", "job_type": "ideation", "user": "secret raw prompt body"})
        qtext = (tp / "q.jsonl").read_text()
        checks.append(("exhausted jobs are queued (never dropped), body hashed not stored",
                       "secret raw prompt body" not in qtext and q["job_prompt_hash"].startswith("prompt-")
                       and q["serves_truth"] is False))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - llm_quota_manager: kill switch + per-provider/per-campaign budgets + exp-backoff cooldowns "
          "+ estimated/actual cost + REDACTING ledger (prompt hash only, keys scrubbed) + never-drop queue. "
          "Offline, deterministic. serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
