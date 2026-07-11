"""src.teleon.tuning.tuner — the self-tuning TUNER that learns from the action ledger CONTRASTIVELY.

The runtime makes selections (model / route / component); the action ledger (src.teleon.tuning.action_ledger)
records each as evidence with its outcome (passed/failed, cost, latency, tokens). This tuner READS that ledger
and, by CONTRAST, proposes selection-policy adjustments:

    group actions into SIMILAR contexts  →  within a context, contrast the SUCCESSFUL vs FAILED choices
    →  when one choice dominates another (more reliable, or equally reliable but cheaper) by a margin with
       enough support  →  propose a policy delta: "in context X, prefer model A over B"

Contrastive, not absolute: a choice is judged only AGAINST its siblings in the SAME context, so the proposal is
"prefer A over B here", carrying the success/failure evidence that justifies it.

GOVERNED (CLAUDE.md):
  * It PROPOSES, never auto-applies a destructive change. ``apply_delta`` REFUSES without explicit human approval,
    and even when approved it is LOSSLESS — it returns a NEW versioned policy layer and never mutates the input.
  * Deterministic + offline; every threshold is a named constant with a rationale (No Magic Values).
  * serves_truth=false — a proposed delta is a candidate adjustment, never a truth claim. Teleon-layer; no Baltor.

Run:  PYTHONPATH=. python3 _repos/teleon/backend/src/teleon/tuning/tuner.py --self-test
"""
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Run-as-script support: repo root on sys.path so ``import src.teleon.*`` resolves when executed directly.
_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.experiments.ids import ID_HASH_SUFFIX_LEN, sha256_hex  # noqa: E402  single-source hash helpers
from src.teleon.tuning.action_ledger import ActionLedger, ActionRecord  # noqa: E402

# -- tuning thresholds (named constants; a contrastive proposal must clear ALL the relevant ones) --------------
DEFAULT_DIMENSION = "model"          #: which key of ``choice`` the proposal contrasts on (→ "prefer model A over B")
DEFAULT_MIN_SUPPORT = 2              #: min observations of EACH side before its pass-rate is trustworthy (1 sample lies)
DEFAULT_MIN_PASSRATE_GAP = 0.20      #: A must beat B's pass-rate by ≥ this (20 pts) to win on RELIABILITY
DEFAULT_PASSRATE_EPSILON = 0.05      #: pass-rates within this (5 pts) count as "equally reliable" → decide on COST
DEFAULT_MIN_COST_GAIN = 1e-9         #: when equally reliable, A must be STRICTLY cheaper than B to win on cost
_CONFIDENCE_SMOOTHING = 2.0          #: Laplace-style prior so tiny samples don't read as high confidence
SERVES_TRUTH = False                 #: a proposed delta is a candidate adjustment, never a truth claim
POLICY_DELTA_KIND = "prefer_over"    #: the only delta shape emitted today: prefer one choice over another in a context
WIN_RELIABILITY = "reliability"      #: A passed more often than B
WIN_COST = "cost"                    #: A was as reliable as B but cheaper


class TunerRefused(PermissionError):
    """Raised when a destructive/un-approved apply is attempted — the tuner proposes, it never auto-applies."""


@dataclass(frozen=True)
class PolicyDelta:
    """A proposed, governed selection-policy adjustment: in ``context`` (for ``task``), prefer ``prefer`` over
    ``over`` along ``dimension`` (e.g. model). ``evidence`` carries the contrasted success/failure stats and
    ``confidence`` ∈ [0,1] folds the margin with the support. A candidate, never auto-applied; serves_truth=false."""

    task: str
    dimension: str
    context: dict[str, Any]
    prefer: Any                          # the dominant choice value (e.g. model "A")
    over: Any                            # the dominated choice value (e.g. model "B")
    win_reason: str                      # WIN_RELIABILITY | WIN_COST
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)
    kind: str = POLICY_DELTA_KIND
    serves_truth: bool = SERVES_TRUTH

    def rationale(self) -> str:
        e = self.evidence
        return (f"in {self.task} context {json.dumps(self.context, sort_keys=True)}: prefer {self.dimension}="
                f"{self.prefer!r} over {self.over!r} — {self.win_reason} "
                f"(pass {e.get('pass_rate_prefer')} vs {e.get('pass_rate_over')}, "
                f"cost {e.get('mean_cost_prefer')} vs {e.get('mean_cost_over')}, "
                f"n {e.get('n_prefer')} vs {e.get('n_over')})")

    def delta_id(self) -> str:
        body = {"task": self.task, "dimension": self.dimension, "context": self.context,
                "prefer": self.prefer, "over": self.over, "kind": self.kind}
        return f"delta_{sha256_hex(body)[:ID_HASH_SUFFIX_LEN]}"

    def to_record(self) -> dict[str, Any]:
        rec = asdict(self)
        rec["delta_id"] = self.delta_id()
        rec["rationale"] = self.rationale()
        return rec


def _context_key(task: str, context: dict, keys) -> str:
    """The SIMILARITY bucket key: the task plus the selected context features (canonical, order-independent).
    ``keys=None`` uses every context feature (exact context); passing a subset COARSENS similarity (generalize)."""
    items = context.items() if keys is None else [(k, context[k]) for k in keys if k in context]
    return json.dumps({"task": task, "ctx": dict(sorted(items))}, sort_keys=True, separators=(",", ":"))


def _choice_value(choice: dict, dimension: str):
    """The value being contrasted: ``choice[dimension]`` when present, else the whole canonical choice (so records
    that don't carry the named dimension still bucket coherently instead of being silently dropped)."""
    if dimension in choice:
        return choice[dimension]
    return json.dumps(choice, sort_keys=True, separators=(",", ":"))


def _stats(observations: list[dict]) -> dict:
    """Contrast stats for one choice within one context: n, passes/fails, pass-rate, mean cost/latency/tokens.
    COMPUTED from the records — this is the successful-vs-failed split the tuner contrasts on."""
    n = len(observations)
    passes = sum(1 for o in observations if o["outcome"].get("passed"))
    cost = sum(float(o["outcome"].get("cost", 0.0)) for o in observations)
    lat = sum(float(o["outcome"].get("latency_ms", 0.0)) for o in observations)
    tok = sum(int(o["outcome"].get("tokens", 0)) for o in observations)
    return {"n": n, "passes": passes, "fails": n - passes,
            "pass_rate": round(passes / n, 4) if n else 0.0,
            "mean_cost": round(cost / n, 6) if n else 0.0,
            "mean_latency_ms": round(lat / n, 4) if n else 0.0,
            "mean_tokens": round(tok / n, 4) if n else 0.0}


class ContrastiveTuner:
    """Reads an action ledger and PROPOSES selection-policy deltas by contrasting successful vs failed choices in
    similar contexts. Proposes only — never auto-applies. Deterministic, offline, serves_truth=false."""

    def __init__(self, ledger: ActionLedger, *, dimension: str = DEFAULT_DIMENSION,
                 context_keys=None, min_support: int = DEFAULT_MIN_SUPPORT,
                 min_passrate_gap: float = DEFAULT_MIN_PASSRATE_GAP,
                 passrate_epsilon: float = DEFAULT_PASSRATE_EPSILON,
                 min_cost_gain: float = DEFAULT_MIN_COST_GAIN) -> None:
        self.ledger = ledger
        self.dimension = dimension
        self.context_keys = context_keys      # None = exact context; a subset coarsens "similar"
        self.min_support = min_support
        self.min_passrate_gap = min_passrate_gap
        self.passrate_epsilon = passrate_epsilon
        self.min_cost_gain = min_cost_gain

    def _buckets(self) -> dict[str, dict]:
        """Group ledger actions into {context_key: {"task","context", "choices": {value: [records]}}}."""
        buckets: dict[str, dict] = {}
        for r in self.ledger.all():
            task = r.get("task", "")
            context = r.get("context", {}) or {}
            ckey = _context_key(task, context, self.context_keys)
            b = buckets.setdefault(ckey, {"task": task, "context": dict(context), "choices": {}})
            cval = _choice_value(r.get("choice", {}) or {}, self.dimension)
            b["choices"].setdefault(json.dumps(cval, sort_keys=True), {"value": cval, "obs": []})["obs"].append(r)
        return buckets

    def _confidence(self, strength: float, support: int) -> float:
        """Fold the win MARGIN (strength ∈ [0,1]) with the SUPPORT via Laplace smoothing — small samples are
        discounted so a 2-vs-2 win never reads as certain. Deterministic."""
        return round(max(0.0, min(1.0, strength)) * support / (support + _CONFIDENCE_SMOOTHING), 4)

    def _compare(self, task, context, a, b) -> PolicyDelta | None:
        """Contrast choice A against choice B in one context. Returns a delta only if A DOMINATES B by the
        thresholds: strictly more reliable, OR equally reliable but strictly cheaper. Otherwise None."""
        sa, sb = a["stats"], b["stats"]
        if sa["n"] < self.min_support or sb["n"] < self.min_support:
            return None                                       # not enough evidence on one side — stay honest
        gap = sa["pass_rate"] - sb["pass_rate"]
        win_reason = strength = None
        if gap >= self.min_passrate_gap:                      # A is more RELIABLE
            win_reason, strength = WIN_RELIABILITY, gap
        elif abs(gap) <= self.passrate_epsilon and sb["mean_cost"] - sa["mean_cost"] >= self.min_cost_gain:
            win_reason = WIN_COST                             # equally reliable, A is CHEAPER
            denom = sb["mean_cost"] if sb["mean_cost"] > 0 else 1.0
            strength = (sb["mean_cost"] - sa["mean_cost"]) / denom
        if win_reason is None:
            return None
        evidence = {"n_prefer": sa["n"], "n_over": sb["n"],
                    "pass_rate_prefer": sa["pass_rate"], "pass_rate_over": sb["pass_rate"],
                    "mean_cost_prefer": sa["mean_cost"], "mean_cost_over": sb["mean_cost"],
                    "mean_latency_ms_prefer": sa["mean_latency_ms"], "mean_latency_ms_over": sb["mean_latency_ms"],
                    "passrate_gap": round(gap, 4)}
        conf = self._confidence(strength, min(sa["n"], sb["n"]))
        return PolicyDelta(task=task, dimension=self.dimension, context=context,
                           prefer=a["value"], over=b["value"], win_reason=win_reason,
                           confidence=conf, evidence=evidence)

    def proposals(self) -> list[PolicyDelta]:
        """The contrastive policy deltas across all contexts — proposals ONLY (never applied). Within each context,
        rank choices (most reliable, then cheapest) and propose the leader over each choice it dominates. Sorted
        deterministically by (confidence desc, delta_id)."""
        out: list[PolicyDelta] = []
        for bucket in self._buckets().values():
            choices = []
            for c in bucket["choices"].values():
                choices.append({"value": c["value"], "stats": _stats(c["obs"])})
            # rank: most reliable first, then cheapest, then by canonical value (stable + deterministic)
            choices.sort(key=lambda c: (-c["stats"]["pass_rate"], c["stats"]["mean_cost"],
                                        json.dumps(c["value"], sort_keys=True)))
            for i, leader in enumerate(choices):
                for other in choices[i + 1:]:
                    delta = self._compare(bucket["task"], bucket["context"], leader, other)
                    if delta is not None:
                        out.append(delta)
        out.sort(key=lambda d: (-d.confidence, d.delta_id()))
        return out

    def best_choice_for(self, task: str, context: dict):
        """The empirically best choice value for a context (the recommendation): the most-reliable / then-cheapest
        choice with enough support. Returns None HONESTLY when the evidence is too thin. This is exactly what an
        applied policy would predict — until applied it is a recommendation, not a rule."""
        ckey = _context_key(task, context, self.context_keys)
        bucket = self._buckets().get(ckey)
        if not bucket:
            return None
        ranked = sorted(
            ({"value": c["value"], "stats": _stats(c["obs"])} for c in bucket["choices"].values()),
            key=lambda c: (-c["stats"]["pass_rate"], c["stats"]["mean_cost"], json.dumps(c["value"], sort_keys=True)))
        for c in ranked:
            if c["stats"]["n"] >= self.min_support:
                return c["value"]
        return None

    def summary(self) -> dict:
        """A computed readout: #contexts examined, #proposals, and the proposals as records."""
        props = self.proposals()
        return {"contexts": len(self._buckets()), "n_proposals": len(props),
                "dimension": self.dimension, "serves_truth": SERVES_TRUTH,
                "proposals": [p.to_record() for p in props]}

    # -- governed application boundary ---------------------------------------------------------------------
    def apply_delta(self, delta: PolicyDelta, base_policy: dict | None = None, *, approved: bool = False) -> dict:
        """GOVERNED apply. The tuner PROPOSES; applying a policy change is a human decision. This REFUSES unless
        ``approved=True`` (no silent auto-apply), and even when approved it is LOSSLESS: it returns a NEW versioned
        policy layer with the preference appended and the prior policy preserved under ``supersedes`` — it never
        mutates ``base_policy`` in place and never deletes a prior preference. serves_truth=false."""
        if not approved:
            raise TunerRefused(
                "the tuner proposes, it does not auto-apply: re-call with approved=True after human review "
                f"({delta.rationale()})")
        base = dict(base_policy or {"version": 0, "preferences": []})
        new = {"version": int(base.get("version", 0)) + 1,
               "preferences": list(base.get("preferences", [])) + [delta.to_record()],
               "supersedes": base,                       # lossless: the prior policy is preserved, not overwritten
               "serves_truth": SERVES_TRUTH}
        return new


def self_test() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tuner_"))
    ledger = ActionLedger(tmp / "actions.jsonl")

    # Empty ledger → honest empty proposals (not an error).
    assert ContrastiveTuner(ledger).proposals() == [], "an empty ledger must yield no proposals, honestly"

    ctx = {"doc": "scanned_pdf", "lang": "en"}
    # Build a contrastive dataset: in context `ctx`, model A passes 3/3, model B passes 0/3 (cheaper but unreliable).
    seq = 0
    def emit(model, passed, cost):
        nonlocal seq
        ledger.append(ActionRecord("doc_extraction", ctx, {"model": model, "route": "cheap"},
                                   passed=passed, cost=cost, latency_ms=100.0, tokens=700, occurred_at=f"t{seq}"))
        seq += 1
    for _ in range(3):
        emit("A", True, 0.003)     # reliable, a touch pricier
        emit("B", False, 0.001)    # cheap but fails

    tuner = ContrastiveTuner(ledger)
    props = tuner.proposals()
    assert props, "the tuner must propose at least one delta from contrasting A (passes) vs B (fails)"
    top = props[0]
    assert top.prefer == "A" and top.over == "B" and top.dimension == "model", \
        f"must propose prefer model A over B, got prefer={top.prefer!r} over={top.over!r}"
    assert top.win_reason == WIN_RELIABILITY, "A wins on RELIABILITY here (it passes, B fails)"
    assert top.serves_truth is False, "a proposed delta serves_truth=False"
    assert 0.0 < top.confidence <= 1.0, "confidence must be a bounded, positive signal"
    assert top.evidence["pass_rate_prefer"] == 1.0 and top.evidence["pass_rate_over"] == 0.0, "evidence is computed"

    # The empirical recommendation matches the proposal.
    assert tuner.best_choice_for("doc_extraction", ctx) == "A", "best choice for the context must be model A"
    assert tuner.best_choice_for("doc_extraction", {"doc": "novel"}) is None, "unseen context → honest None"

    # Determinism: identical ledger → identical proposal ids.
    assert [p.delta_id() for p in tuner.proposals()] == [p.delta_id() for p in ContrastiveTuner(ledger).proposals()], \
        "the tuner must be deterministic (stable delta ids)"

    # Support guard: with min_support too high to satisfy, no proposal is emitted (stays honest about thin evidence).
    assert ContrastiveTuner(ledger, min_support=99).proposals() == [], "thin-evidence guard must suppress proposals"

    # Cost-tie branch: equal reliability (both pass), A strictly cheaper than B → a COST win.
    tmp2 = Path(tempfile.mkdtemp(prefix="tuner_cost_"))
    led2 = ActionLedger(tmp2 / "a.jsonl")
    for i in range(2):
        led2.append(ActionRecord("t", {"k": "v"}, {"model": "cheap"}, passed=True, cost=0.001, occurred_at=f"c{i}"))
        led2.append(ActionRecord("t", {"k": "v"}, {"model": "dear"}, passed=True, cost=0.010, occurred_at=f"d{i}"))
    cost_props = ContrastiveTuner(led2).proposals()
    assert cost_props and cost_props[0].prefer == "cheap" and cost_props[0].win_reason == WIN_COST, \
        "equally-reliable choices must contrast on cost (prefer the cheaper)"

    # GOVERNED apply: refuses without approval, and is lossless (non-destructive) when approved.
    refused = False
    try:
        tuner.apply_delta(top)
    except TunerRefused:
        refused = True
    assert refused, "apply_delta MUST refuse without explicit human approval (proposes, never auto-applies)"
    base = {"version": 5, "preferences": [{"delta_id": "prior"}]}
    new_policy = tuner.apply_delta(top, base, approved=True)
    assert new_policy["version"] == 6, "an approved apply bumps the version"
    assert new_policy["supersedes"] == base and base["preferences"] == [{"delta_id": "prior"}], \
        "apply must be LOSSLESS: the prior policy is preserved and never mutated"
    assert any(p.get("delta_id") == top.delta_id() for p in new_policy["preferences"]), "the delta is layered in"

    print(f"tuner self-test: OK ({len(props)} contrastive proposal(s) · prefer={top.prefer} over={top.over} "
          f"conf={top.confidence} · governed apply refused-without-approval · lossless · serves_truth=False)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: tuner --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
