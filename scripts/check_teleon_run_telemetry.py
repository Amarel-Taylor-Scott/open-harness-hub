#!/usr/bin/env python3
"""check_teleon_run_telemetry — proof for Teleon's OBSERVED-measurement / telemetry layer.

The objective selects on metrics; THIS proves those metrics can be the OBSERVED telemetry of real runs, not a
declared claim — and that observed evidence drives the objective + the non-det->det descent:

  * TELEMETRY — a RunLedger retains every per-run observation (cost/latency/llm/pass/output-key), in order.
  * MEASUREMENT METHODS — observed_metrics derives cost/latency/llm_usage as means, accuracy as the eval
    pass-rate, determinism as output-stability (modal-output share). Richer than one exact-match pass-rate.
  * EVIDENCE DRIVES SELECTION — candidates() feeds select() directly, so a capability is chosen on what it
    actually did; a distilled rule that OBSERVABLY matches the model's accuracy at zero cost wins minimize_cost.
  * NO COLD-START CLIFF — blend() shrinks a declared prior toward observed evidence (0 runs -> prior; many -> obs).
  * DETERMINISTIC + LOUD — same observations -> same metrics; an unrecorded impl / bad observation fails loud.

CLI: python3 scripts/check_teleon_run_telemetry.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.objectives import (
    PRESETS,
    MetricVector,
    RunLedger,
    RunObservation,
    TelemetryError,
    select,
)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    led = RunLedger()
    # The model: passes, but its free-text output VARIES run to run (3 distinct keys) -> low observed determinism.
    for i, key in enumerate(("ans-a", "ans-b", "ans-c")):
        led.record(RunObservation("model.x", cost=0.06, latency_ms=900, llm_calls=1, passed=True, output_key=key))
    # The distilled rule: passes just as often, ZERO cost, fast, no LLM, SAME output every time -> determinism 1.0.
    for _ in range(3):
        led.record(RunObservation("rule.x", cost=0.0, latency_ms=15, llm_calls=0, passed=True, output_key="ans-a"))

    # TELEMETRY: every observation retained, in order.
    ck("the ledger retains every observation in order (telemetry trace)",
       led.count("model.x") == 3 and led.count("rule.x") == 3
       and [o.output_key for o in led.observations("model.x")] == ["ans-a", "ans-b", "ans-c"])

    # MEASUREMENT METHODS: means + pass-rate + output-stability.
    m = led.observed_metrics("model.x")
    r = led.observed_metrics("rule.x")
    ck("observed cost/latency/llm are means", abs(m.cost - 0.06) < 1e-9 and m.latency == 900 and m.llm_usage == 1)
    ck("observed accuracy is the eval pass-rate", m.accuracy == 1.0 and r.accuracy == 1.0)
    ck("observed determinism is output-stability (model varies 1/3, rule stable 1.0)",
       abs(m.determinism - (1.0 / 3.0)) < 1e-9 and r.determinism == 1.0, f"model={m.determinism} rule={r.determinism}")

    # EVIDENCE DRIVES SELECTION + the descent: chosen on OBSERVED telemetry, not declared metrics.
    cands = led.candidates()
    ck("candidates() feeds select() with observed metrics", {c for c, _ in cands} == {"model.x", "rule.x"})
    ck("observed minimize_cost -> the distilled rule (it earned parity at zero cost)",
       select(cands, PRESETS["minimize_cost"])["chosen"] == "rule.x")
    ck("observed maximize_determinism -> the distilled rule (stable output)",
       select(cands, PRESETS["maximize_determinism"])["chosen"] == "rule.x")

    # NO COLD-START CLIFF: blend prior -> evidence as runs accumulate.
    prior = MetricVector(cost=1.0, latency=1000, llm_usage=1, determinism=0.5, accuracy=0.5)
    empty = RunLedger()
    ck("blend with 0 runs returns the prior unchanged", empty.blend("rule.x", prior) == prior)
    blended = led.blend("rule.x", prior, prior_weight=1.0)  # 1 pseudo-run prior + 3 observed runs
    # cost: (1.0*1 + 0.0*3)/4 = 0.25 ; accuracy: (0.5*1 + 1.0*3)/4 = 0.875
    ck("blend shrinks the prior toward observed evidence (weight = run count)",
       abs(blended.cost - 0.25) < 1e-9 and abs(blended.accuracy - 0.875) < 1e-9, str(blended.as_dict()))
    heavy = RunLedger()
    for _ in range(99):
        heavy.record(RunObservation("rule.x", cost=0.0, latency_ms=15, llm_calls=0, passed=True, output_key="ans-a"))
    ck("blend converges to observed as runs dominate the prior", heavy.blend("rule.x", prior).cost < 0.02)

    # DETERMINISTIC + LOUD
    led2 = RunLedger()
    for i, key in enumerate(("ans-a", "ans-b", "ans-c")):
        led2.record(RunObservation("model.x", cost=0.06, latency_ms=900, llm_calls=1, passed=True, output_key=key))
    ck("same observations -> same observed metrics (deterministic)",
       led2.observed_metrics("model.x").as_dict() == m.as_dict())
    raised_unknown = False
    try:
        led.observed_metrics("never.recorded")
    except TelemetryError:
        raised_unknown = True
    ck("querying an unrecorded impl fails loud", raised_unknown)
    raised_bad = False
    try:
        led.record(RunObservation("", cost=0.0, latency_ms=1, llm_calls=0, passed=True))
    except TelemetryError:
        raised_bad = True
    ck("an observation with no impl_id fails loud", raised_bad)

    print("\n" + ("PASS - check_teleon_run_telemetry: a RunLedger turns real run outcomes into an OBSERVED "
                  "MetricVector per impl (cost/latency/llm means, accuracy=pass-rate, determinism=output-stability); "
                  "those observed metrics feed select() so a capability is chosen on what it actually did — a "
                  "distilled rule that observably matches the model at zero cost wins minimize_cost; blend() removes "
                  "the cold-start cliff (prior -> evidence as runs accumulate); deterministic and fails loud."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
