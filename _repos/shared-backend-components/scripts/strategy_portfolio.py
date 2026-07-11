#!/usr/bin/env python3
"""scripts.strategy_portfolio — the generic MULTI-PATH capability for CODE (the reusable analog of a
primitive's variant portfolio).

The MULTI-PATH law: *a design choice is a PORTFOLIO of contract-substitutable paths behind one selector, not
an `if`.* The repo already does this for the FIVE bake-off processing paths (``run_path_bakeoff`` races them,
``path_selection_policy`` routes them) — but each is bespoke. There was no GENERIC mechanism any code decision
could adopt to become multi-path. This is it, and it gives our CODE the same flexibility the generated
PRIMITIVES have (which carry variant portfolios in the registry):

  * register N named, contract-substitutable implementations for one capability — adding a way to do something
    is a NEW ROW, never an edit to an `if`;
  * ``active()`` returns the ACTIVE_DEFAULT — adopting a portfolio reproduces today's behaviour EXACTLY
    (the default is the only path that runs until you choose to experiment);
  * ``race(inputs, comparator)`` runs EVERY strategy on the IDENTICAL input, ranks by measured receipts
    (higher score wins), and returns the winner PLUS the losers as LABELLED FALLBACKS — never a lock-in, so a
    re-run can re-adapt as conditions change (exactly the primitive bake-off discipline);
  * every decision is appended to an in-memory ledger.

Deterministic: no wall-clock, no RNG here (a strategy may introduce its own; the harness does not). The race
NEVER promotes a candidate to truth — it ranks receipts. serves_truth=false.

    PYTHONPATH=. python3 scripts/strategy_portfolio.py --self-test
"""
from __future__ import annotations

import sys
from typing import Any, Callable, Optional


class StrategyPortfolio:
    """A named capability with a portfolio of contract-substitutable implementations behind one selector."""

    def __init__(self, capability: str, *, default: Optional[str] = None) -> None:
        self.capability = capability
        self._strategies: dict[str, Callable[..., Any]] = {}
        self._default: Optional[str] = default
        self._ledger: list[dict] = []

    # --- registration: adding a path is a ROW, never an `if` ------------------------------------------------
    def register(self, name: str, fn: Callable[..., Any], *, is_default: bool = False) -> "StrategyPortfolio":
        """Register a contract-substitutable implementation. The FIRST registered becomes the default unless a
        later one claims ``is_default`` (or one was named at construction)."""
        if name in self._strategies:
            raise ValueError(f"strategy {name!r} already registered for capability {self.capability!r}")
        self._strategies[name] = fn
        if is_default or (self._default is None and len(self._strategies) == 1):
            self._default = name
        return self

    def strategy(self, name: str, *, is_default: bool = False) -> Callable[[Callable], Callable]:
        """Decorator form of :meth:`register` — ``@portfolio.strategy("fast")`` over a function."""
        def deco(fn: Callable) -> Callable:
            self.register(name, fn, is_default=is_default)
            return fn
        return deco

    def set_default(self, name: str) -> None:
        if name not in self._strategies:
            raise KeyError(f"unknown strategy {name!r} for capability {self.capability!r}")
        self._default = name

    def names(self) -> list[str]:
        return list(self._strategies)

    # --- selection: the ACTIVE_DEFAULT path (reproduces today's behaviour) ----------------------------------
    def active_name(self) -> str:
        if self._default is None:
            raise RuntimeError(f"capability {self.capability!r} has no strategies registered")
        return self._default

    def active(self) -> Callable[..., Any]:
        return self._strategies[self.active_name()]

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the ACTIVE strategy — the drop-in replacement for the hardcoded call it supersedes."""
        name = self.active_name()
        result = self._strategies[name](*args, **kwargs)
        self._ledger.append({"capability": self.capability, "action": "run", "strategy": name, "serves_truth": False})
        return result

    # --- the race: try EVERY way on the same input, rank by receipts, KEEP the losers ----------------------
    def race(self, inputs: Any, comparator: Callable[[Any], float], *,
             on_error: str = "skip") -> dict:
        """Race every strategy on the IDENTICAL ``inputs`` (a tuple ``(args, kwargs)`` or a single positional
        value), score each output via ``comparator(output) -> float`` (higher is better), and return the ranked
        portfolio. The winner is a routing DEFAULT, never truth; losers are retained as labelled fallbacks so a
        re-run can re-adapt. ``on_error='skip'`` records a failing strategy with score ``-inf`` (never crashes
        the race); ``on_error='raise'`` propagates."""
        args, kwargs = self._normalize_inputs(inputs)
        results: list[dict] = []
        for name, fn in self._strategies.items():
            try:
                output = fn(*args, **kwargs)
                score = float(comparator(output))
                results.append({"strategy": name, "score": score, "ok": True})
            except Exception as exc:  # noqa: BLE001 — a broken path must not kill the race
                if on_error == "raise":
                    raise
                results.append({"strategy": name, "score": float("-inf"), "ok": False,
                                "error": f"{type(exc).__name__}: {exc}"})
        results.sort(key=lambda r: r["score"], reverse=True)
        winner = results[0]["strategy"] if results and results[0]["ok"] else None
        decision = {
            "record_type": "strategy_portfolio_race",
            "capability": self.capability,
            "winner": winner,
            "ranked": results,                 # ALL paths kept (losers labelled, never discarded)
            "fallbacks": [r["strategy"] for r in results[1:]],
            "serves_truth": False,             # a race ranks receipts; it never promotes to truth
        }
        self._ledger.append(decision)
        return decision

    def ledger(self) -> list[dict]:
        return list(self._ledger)

    @staticmethod
    def _normalize_inputs(inputs: Any) -> tuple[tuple, dict]:
        """Accept ``(args_tuple, kwargs_dict)``, or a bare positional value, uniformly."""
        if isinstance(inputs, tuple) and len(inputs) == 2 and isinstance(inputs[0], tuple) and isinstance(inputs[1], dict):
            return inputs
        return (inputs,), {}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # A capability with THREE contract-substitutable ways to sum a list. The default reproduces one exactly.
    p = StrategyPortfolio("sum_list")
    p.register("builtin", lambda xs: sum(xs), is_default=True)
    p.register("loop", lambda xs: (lambda acc=0: [acc := acc + x for x in xs] and acc)())
    p.register("broken", lambda xs: 1 / 0)  # a path that throws — the race must survive it

    checks.append(("adding a strategy is a ROW (3 registered, all contract-substitutable)", p.names() == ["builtin", "loop", "broken"]))
    checks.append(("active() is the ACTIVE_DEFAULT and run() reproduces it exactly",
                   p.active_name() == "builtin" and p.run([1, 2, 3, 4]) == 10))

    # the race: every non-broken path returns 10; comparator rewards correctness (closeness to 10).
    decision = p.race([1, 2, 3, 4], comparator=lambda out: -abs((out or 0) - 10))
    ok_strats = {r["strategy"] for r in decision["ranked"] if r["ok"]}
    checks.append(("race runs EVERY path on the same input", len(decision["ranked"]) == 3))
    checks.append(("race SURVIVES a throwing path (recorded, not crashed)",
                   any(r["strategy"] == "broken" and not r["ok"] for r in decision["ranked"])))
    checks.append(("winner is a correct path; losers KEPT as labelled fallbacks (never discarded)",
                   decision["winner"] in ok_strats and len(decision["fallbacks"]) == 2 and "broken" in decision["fallbacks"]))
    checks.append(("ranked best-first by receipts (score descending)",
                   [r["score"] for r in decision["ranked"]] == sorted([r["score"] for r in decision["ranked"]], reverse=True)))

    # switching the default is a selector change, not a rewrite; behaviour stays contract-identical.
    p.set_default("loop")
    checks.append(("selector switch changes the active path, same contract", p.active_name() == "loop" and p.run([5, 5]) == 10))

    # ledger records the decisions; nothing is served as truth.
    led = p.ledger()
    checks.append(("every decision is ledgered + serves_truth=false",
                   len(led) >= 2 and all(e["serves_truth"] is False for e in led)))

    # (args, kwargs) input form works for multi-arg strategies.
    q = StrategyPortfolio("join")
    q.register("dash", lambda a, b, sep="-": f"{a}{sep}{b}", is_default=True)
    q.register("space", lambda a, b, sep=" ": f"{a}{sep}{b}")
    d2 = q.race((("x", "y"), {"sep": "|"}), comparator=lambda out: len(out))
    checks.append(("race accepts (args, kwargs) inputs uniformly", all(r["ok"] for r in d2["ranked"]) and d2["winner"] in ("dash", "space")))

    # duplicate registration is rejected (a capability can't have two paths with the same name).
    try:
        p.register("loop", lambda xs: 0)
        checks.append(("duplicate strategy name rejected", False))
    except ValueError:
        checks.append(("duplicate strategy name rejected", True))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - strategy_portfolio: the generic MULTI-PATH capability for code — register contract-"
          "substitutable paths (rows, not ifs), run the ACTIVE_DEFAULT (reproduces today), or race all on the "
          "same input and keep the losers as labelled fallbacks (never lock-in); ledgered; serves_truth=false.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
