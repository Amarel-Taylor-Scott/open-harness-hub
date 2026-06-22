"""src.teleon.capability_planner — turn an OPEN-ENDED plain-text capability into an executable, possibly-iterative,
possibly-scheduled, MULTI-COMPONENT plan.

The owner's requirement: given "scrape the internet for additional skills to include in openskillshub.io", the
capability processor must be intelligent enough to recognize that this is

  * ITERATIVE       — "additional / more / keep / continuously" ⇒ loop, don't run once;
  * MULTI-COMPONENT — string modules together: pick a research component (the descent over the research catalog) →
                      discover (OpenClaw/Hermes) → digest → dedupe → (improve) → verify → version → (contribute);
  * SCHEDULED       — "daily / nightly / keep fresh / on a schedule" ⇒ recur on a cadence (the hubs flywheel honors it).

So this planner CLASSIFIES the intent, RESOLVES the target hub, INFERS the research capability needed (which drives the
research-catalog descent — cheap feed/api first, the LLM-driven browser only for deep detail), DECOMPOSES into typed
steps, and EXECUTES it as a bounded LOOP (stop on the freshness bar / no-new-for-K-rounds / a round cap) or emits a
SCHEDULE descriptor. Each round reuses src.teleon.hub_freshness.keep_hub_fresh (the unbounded→bounded freshness motion)
and records to the descent brain. Teleon may import the open layer (dependency law); serves_truth=false throughout.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# the open layer (allowed: teleon may_depend_on openharnesshub)
from src.openharnesshub.research_catalog import descent_plan as research_descent_plan

_ITERATIVE_HINTS = ("additional", "more ", "keep ", "continuous", "continually", "ongoing", "expand", "grow",
                    "all ", "until", "populate", "as many", "every ", "regularly", "over time", "accumulate")
_SCHEDULE_HINTS = ("schedule", "scheduled", "daily", "nightly", "hourly", "weekly", "monthly", "every day",
                   "every week", "cron", "keep fresh", "keep it fresh", "keep current", "keep updated", "regularly",
                   "continuous", "continually", "ongoing", "on a cadence")
#: rough natural-cadence → flywheel CYCLES (the hubs flywheel counts cycles, not wall-clock).
_EVERY = {"hourly": 1, "nightly": 7, "daily": 7, "weekly": 14, "monthly": 30}
_DEEP_HINTS = ("deep", "detail", "details", "full ", "behind", "navigate", "interact", "click", "multi-page", "drill")
_TEXT_HINTS = ("text", "content", "article", "read ", "body", "documentation", "docs ")
_IMPROVE_HINTS = ("improve", "enhance", "refine", "think about ways to improve", "better", "upgrade")
_CONTRIBUTE_HINTS = ("share", "contribute", "publish", "promote", "make available", "open up")


@dataclass(frozen=True)
class PlanStep:
    name: str          # research_select / discover / digest / dedupe / improve / verify / version / contribute
    binds_to: str      # the module/component that executes this step (multi-component stringing)
    detail: str


@dataclass(frozen=True)
class CapabilityPlan:
    intent: str
    hub: str
    iterative: bool
    scheduled: bool
    cadence: str                  # run_once | iterate | schedule
    schedule_every: int | None    # cycles between runs (schedule cadence)
    needed_capability: str        # research capability (list / text / deep_detail)
    research_descent: dict        # the descent over the research catalog (selected + escalation order)
    steps: tuple = field(default_factory=tuple)
    stop: dict = field(default_factory=dict)
    serves_truth: bool = False

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["steps"] = [s.__dict__ for s in self.steps]
        return d


def classify(intent: str) -> dict:
    """Recognize whether an open-ended capability is iterative and/or scheduled (the core 'be intelligent' step)."""
    t = (intent or "").lower()
    iterative = any(h in t for h in _ITERATIVE_HINTS) or bool(re.search(r"\b(scrape|find|collect|gather|crawl)\b", t))
    scheduled = any(h in t for h in _SCHEDULE_HINTS)
    every = next((c for k, c in _EVERY.items() if k in t), None)
    return {"iterative": iterative, "scheduled": scheduled, "schedule_every": every}


def resolve_hub(intent: str, hubs: list[str], *, kinds: dict | None = None) -> str | None:
    """Map free text to a hub: exact name, domain (openskillshub.io), or the hub's content_kind keyword."""
    t = re.sub(r"[^a-z0-9]+", " ", (intent or "").lower())
    norm = {h: re.sub(r"[^a-z0-9]+", " ", h.lower()) for h in hubs}
    for h, n in norm.items():                                    # exact-ish name / domain match
        bare = n.replace("open", "").replace("hub", "").strip()
        if n in t or h.lower() in t.replace(" ", "") or (bare and bare in t.replace(" ", "")):
            return h
    if kinds:                                                    # content_kind keyword (e.g. "skills" -> OpenSkillsHub)
        for h, kind in kinds.items():
            k = re.sub(r"[^a-z0-9]+", " ", str(kind).lower()).strip()
            if k and (k in t or k.rstrip("s") in t.split()):
                return h
    return None


def infer_capability(intent: str) -> str:
    """Which research capability the detail needs → drives the research-catalog descent (browser only for deep detail)."""
    t = (intent or "").lower()
    if any(h in t for h in _DEEP_HINTS):
        return "deep_detail"
    if any(h in t for h in _TEXT_HINTS):
        return "text"
    return "list"


def plan(intent: str, *, hubs: list[str], kinds: dict | None = None, available: set | None = None,
         max_rounds: int = 5, no_new_rounds: int = 2) -> CapabilityPlan:
    """Decompose an open-ended capability into a typed, executable plan (classification + hub + research descent + steps)."""
    c = classify(intent)
    hub = resolve_hub(intent, hubs, kinds=kinds) or (hubs[0] if hubs else "")
    cap = infer_capability(intent)
    # the research-catalog descent: cheapest component that can get this detail (browser only when needed)
    avail = available if available is not None else {"network", "api_key", "browser_runtime", "llm"}
    rd = research_descent_plan(cap, available=avail)

    t = (intent or "").lower()
    steps = [
        PlanStep("research_select", "openharnesshub.research_catalog.select_component",
                 f"descend the research catalog → cheapest component for '{cap}' (selected: {rd.get('selected')})"),
        PlanStep("discover", "openharnesshub.discovery.OpenClaw/Hermes",
                 "run the hub's finders across the (allowed) tool repository — continuous append"),
        PlanStep("digest", "openharnesshub.hub_engine.HubEngine.digest", "normalize + enrich each candidate"),
        PlanStep("dedupe", "openharnesshub.component_store (content-hash)", "collapse duplicates (idempotent, lossless versions)"),
    ]
    if any(h in t for h in _IMPROVE_HINTS):
        steps.append(PlanStep("improve", "openharnesshub.hub_engine.HubEngine.improve",
                              "ask the model for one concrete improvement → a new lossless version"))
    steps += [
        PlanStep("verify", "openharnesshub.hub_engine.HubEngine.verify", "the hub's verify gate (discovery≠trust)"),
        PlanStep("version", "openharnesshub.component_store.put_version", "append a new governed version"),
    ]
    if any(h in t for h in _CONTRIBUTE_HINTS):
        steps.append(PlanStep("contribute", "openharnesshub.hub_engine.HubEngine.contribute",
                              "opt-in promote a verified version to global (feeds Teleon/Baltor substrate)"))

    cadence = "schedule" if c["scheduled"] else ("iterate" if c["iterative"] else "run_once")
    stop = {"max_rounds": max_rounds if cadence != "run_once" else 1,
            "stop_when_no_new_rounds": no_new_rounds, "freshness_bar": "per hub settings"}
    return CapabilityPlan(intent=intent, hub=hub, iterative=c["iterative"], scheduled=c["scheduled"],
                          cadence=cadence, schedule_every=c["schedule_every"], needed_capability=cap,
                          research_descent=rd, steps=tuple(steps), stop=stop)


def execute(p: CapabilityPlan, *, hub_engines: dict, openclaw=None, tools: list | None = None, brain=None,
            tenant: str = "_global", run_round=None) -> dict:
    """Execute the plan as a BOUNDED loop. Each round runs one freshness pass (keep_hub_fresh by default; injectable).
    Iterates until: a round adds nothing new for ``stop_when_no_new_rounds`` consecutive rounds, OR ``max_rounds`` is
    hit. For a scheduled plan it still runs the rounds NOW and ALSO returns a schedule descriptor for the flywheel/cron
    to honor (this function never sleeps). serves_truth=false."""
    if run_round is None:
        from src.teleon.hub_freshness import keep_hub_fresh
        def run_round(hub, intent):  # noqa: E306
            return keep_hub_fresh(hub, intent, hub_engines=hub_engines, openclaw=openclaw, tools=tools or [],
                                  brain=brain, tenant=tenant)

    max_rounds = int(p.stop.get("max_rounds", 1))
    no_new_cap = int(p.stop.get("stop_when_no_new_rounds", 2))
    rounds, totals, no_new_streak, stopped = [], {"discovered": 0, "ingested": 0, "verified": 0}, 0, "max_rounds"
    for i in range(max_rounds):
        r = run_round(p.hub, p.intent) or {}
        rounds.append({"round": i + 1, "discovered": r.get("discovered", 0), "ingested": r.get("ingested", 0),
                       "verified": r.get("verified", 0), "bounded_tool": r.get("bounded_tool"),
                       "pct_saved": r.get("pct_saved", 0.0)})
        for k in totals:
            totals[k] += int(r.get(k, 0) or 0)
        no_new_streak = no_new_streak + 1 if r.get("ingested", 0) == 0 else 0
        if p.cadence != "run_once" and no_new_streak >= no_new_cap:
            stopped = f"no new for {no_new_cap} rounds"
            break
        if p.cadence == "run_once":
            stopped = "run_once"
            break

    schedule = None
    if p.scheduled:
        schedule = {"recurring": True, "every_cycles": p.schedule_every or "hub settings cadence",
                    "honored_by": "the hubs flywheel (per-hub cadence) / cron"}
    return {"hub": p.hub, "intent": p.intent, "cadence": p.cadence, "rounds_run": len(rounds), "rounds": rounds,
            "totals": totals, "stopped_because": stopped, "schedule": schedule,
            "research_selected": p.research_descent.get("selected"), "serves_truth": False}


__all__ = ["PlanStep", "CapabilityPlan", "classify", "resolve_hub", "infer_capability", "plan", "execute"]
