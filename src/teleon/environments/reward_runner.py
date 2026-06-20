"""src.teleon.environments.reward_runner — the deterministic local REWARD scorer (RewardProviderPort).

Scores one ``EnvironmentRunResult`` against a ``RewardSpec`` of kind ``deterministic_check`` (pure assertions
over the agent output — no code execution, no network). Each check is a small dict ``{check_id?, type, ...}``;
supported ``type`` values:

  - ``exact_answer``      — the output's answer text, normalized, EQUALS ``expected`` (whitespace/case-folded).
  - ``substring_present`` — ``needle`` appears in the output's answer text (case-insensitive).
  - ``held_out_absent``   — ``needle`` (a known-stale / contradicting value) does NOT appear — the held-out
                            contradiction must never be served. Passing means the leak is absent.
  - ``key_present``       — ``key`` exists (and is non-empty) in the output dict (e.g. a source handle / receipt).

Returns a ``RewardResult``-shaped dict ``{reward_result_id, reward_spec_id, run_id, score, max_score, passed,
breakdown, is_truth=False}``. ``passed`` is True iff every check passed AND ``score == max_score``. The
breakdown preserves per-check lineage (a winner always has lineage to the losers).

THE INVARIANT: ``is_truth`` is pinned False — a reward result is evidence, never authority. Deterministic given
the same ``run_result`` + ``reward_spec`` + ``now`` (content-addressed id; no RNG/wall-clock). Stdlib only;
never imports Baltor.
"""
from __future__ import annotations

from typing import Any

from src.teleon.experiments.ids import canonical_id
from src.teleon.ports.reward_provider import REWARD_IS_TRUTH

#: provider id of the one active, deterministic local scorer.
LOCAL_REWARD_PROVIDER_ID = "reward.local-deterministic-checker@v1"
#: the only RewardSpec.kind this scorer handles (the others — test_execution/diff_oracle — need execution).
SUPPORTED_KIND = "deterministic_check"
#: the check ``type`` values this scorer understands (single source).
CHECK_TYPES = ("exact_answer", "substring_present", "held_out_absent", "key_present")


def _norm_text(value: Any) -> str:
    """Whitespace-collapsed, case-folded text for robust deterministic comparison."""
    return " ".join(str(value).split()).casefold()


def _answer_text(run_result: dict) -> str:
    """Pull the candidate answer text out of an EnvironmentRunResult's ``output``.

    Accepts a string output, or a dict output with an ``answer`` (preferred) / ``text`` / ``output`` field;
    otherwise stringifies the whole output. Pure + deterministic — no parsing that depends on dict order."""
    out = run_result.get("output")
    if isinstance(out, str):
        return out
    if isinstance(out, dict):
        for key in ("answer", "text", "output", "value"):
            if isinstance(out.get(key), str):
                return out[key]
        return str(out)
    return "" if out is None else str(out)


def _output_dict(run_result: dict) -> dict:
    """The output as a dict for ``key_present`` checks (empty dict when the output is not a mapping)."""
    out = run_result.get("output")
    return out if isinstance(out, dict) else {}


def _eval_check(check: dict, run_result: dict) -> tuple[bool, str]:
    """Evaluate one check against the run result. Returns ``(passed, detail)``. Unknown types fail closed."""
    ctype = check.get("type")
    answer = _answer_text(run_result)
    if ctype == "exact_answer":
        expected = check.get("expected", "")
        ok = _norm_text(answer) == _norm_text(expected)
        return ok, f"answer == expected {expected!r}" if ok else f"answer {answer!r} != expected {expected!r}"
    if ctype == "substring_present":
        needle = check.get("needle", "")
        ok = _norm_text(needle) in _norm_text(answer)
        return ok, f"found {needle!r}" if ok else f"missing required substring {needle!r}"
    if ctype == "held_out_absent":
        needle = check.get("needle", "")
        leaked = _norm_text(needle) in _norm_text(answer)
        # PASS == the held-out / stale value is ABSENT (not served).
        return (not leaked), (f"held-out {needle!r} correctly absent" if not leaked
                              else f"LEAK: held-out {needle!r} present in served answer")
    if ctype == "key_present":
        key = check.get("key", "")
        out = _output_dict(run_result)
        present = key in out and out.get(key) not in (None, "", [], {})
        return present, f"key {key!r} present + non-empty" if present else f"missing/empty output key {key!r}"
    return False, f"unknown check type {ctype!r} (fails closed)"


class RewardRunner:
    """The deterministic local scorer (RewardProviderPort). ``deterministic=True``; output is never truth."""
    provider_id = LOCAL_REWARD_PROVIDER_ID
    deterministic = True

    def describe(self) -> dict:
        """RewardProviderNode-shaped card for this scorer."""
        return {
            "provider_id": self.provider_id,
            "name": "local-deterministic-checker",
            "status": "active",
            "deterministic": True,
            "serves_truth": False,
            "supported_kind": SUPPORTED_KIND,
            "check_types": list(CHECK_TYPES),
        }

    def score(self, run_result: dict, reward_spec: dict, *, now: str) -> dict:
        """Score ``run_result`` against ``reward_spec`` (kind=deterministic_check). RewardResult dict; is_truth=False."""
        spec_id = reward_spec.get("reward_spec_id", "reward.unknown")
        run_id = run_result.get("run_id", "run.unknown")
        kind = reward_spec.get("kind")
        checks = list(reward_spec.get("checks", []))
        max_score = float(reward_spec.get("max_score", float(len(checks))))

        breakdown: list[dict] = []

        if kind != SUPPORTED_KIND:
            # Fail closed for unsupported kinds (test_execution / diff_oracle need an execution-capable provider).
            reward_result_id = canonical_id("rr", spec_id, run_id, now, "unsupported-kind")
            return {
                "reward_result_id": reward_result_id,
                "reward_spec_id": spec_id,
                "run_id": run_id,
                "score": 0.0,
                "max_score": max_score,
                "passed": False,
                "breakdown": [{"check_id": "kind", "points": 0.0, "max_points": max_score, "passed": False,
                               "detail": f"unsupported RewardSpec.kind {kind!r}; this scorer handles {SUPPORTED_KIND!r}"}],
                "is_truth": REWARD_IS_TRUTH,
            }

        # Each check earns its declared weight (default: an even split of max_score across the checks).
        n = len(checks) or 1
        default_weight = max_score / n
        score = 0.0
        for idx, check in enumerate(checks):
            check_id = str(check.get("check_id", f"c{idx}"))
            max_points = float(check.get("weight", default_weight))
            passed, detail = _eval_check(check, run_result)
            points = max_points if passed else 0.0
            score += points
            breakdown.append({"check_id": check_id, "type": check.get("type"), "points": points,
                              "max_points": max_points, "passed": passed, "detail": detail})

        all_passed = all(b["passed"] for b in breakdown) if breakdown else False
        # passed iff every check passed AND the full score was earned (no partial-credit "pass").
        passed = bool(all_passed and abs(score - max_score) < 1e-9)
        reward_result_id = canonical_id("rr", spec_id, run_id, now, str(score), str(passed))
        return {
            "reward_result_id": reward_result_id,
            "reward_spec_id": spec_id,
            "run_id": run_id,
            "score": score,
            "max_score": max_score,
            "passed": passed,
            "breakdown": breakdown,
            "is_truth": REWARD_IS_TRUTH,
        }


__all__ = ["RewardRunner", "LOCAL_REWARD_PROVIDER_ID", "SUPPORTED_KIND", "CHECK_TYPES"]
