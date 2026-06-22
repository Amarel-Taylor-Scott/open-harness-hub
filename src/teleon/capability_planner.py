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
    needed_capability: str        # research capability (list / text / deep_detail) | "document_extraction"
    research_descent: dict        # the descent over the research catalog (selected + escalation order)
    steps: tuple = field(default_factory=tuple)
    stop: dict = field(default_factory=dict)
    capability_type: str = "hub_population"   # hub_population | document_extraction
    route: dict = field(default_factory=dict)  # engine route (e.g. the document cascade) for non-hub capabilities
    serves_truth: bool = False

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["steps"] = [s.__dict__ for s in self.steps]
        return d


#: a capability that EXTRACTS a schema from documents (PDF/email/scan) routes to the document cascade, not the hubs.
_DOCEXTRACT_HINTS = ("extract", "pull out", "pull the", "ocr", "schema from", "fields from", "invoice", "lease",
                     "contract", "from these pdf", "from the pdf", "from a pdf", "from the email", "from emails",
                     "from scans", "from documents", "email attachment", "attachments and extract")


# Capability TYPES beyond extraction — routed to the tunable-task method grids (rules → small model → LLM, cheapest
# that meets the bar). Ordered most-specific-first; matched by keyword (the catalog has no triggers, so they live here).
_TASK_KEYWORDS: list = [
    ("jira-task-sync", ["jira task", "jira issue", "jira ticket", "create a jira", "update a jira", "create an issue", "create a ticket in"]),
    ("wiki-page-draft", ["confluence", "jira page", "wiki page", "draft a page", "update the page", "documentation page", "knowledge base page"]),
    ("transcription-asr", ["transcrib", "audio to text", "speech to text", "speech-to-text", " asr", "voice to text"]),
    ("image-tagging", ["classify an image", "classify images", "tag an image", "tag images", "image classif", "label an image", "image label", "tag photos"]),
    ("pii-redaction", ["redact", "pii", "scrub personal", "mask personal", "de-identif", "remove personal information", "mask pii"]),
    ("fragile-fact-detection", ["fragile fact", "stale fact", "facts that will change", "facts likely to", "volatile fact", "unsourced claim", "facts that go stale", "find fragile"]),
    ("inconsistency-detection", ["inconsisten", "contradict", "conflicting fact", "conflicting claim", "find conflicts", "discrepanc", "reconcile conflicts", "mismatched facts"]),
    ("email-reply", ["reply to", "draft a reply", "draft an email", "email reply", "respond to the email", "write a reply", "answer the email", "respond to this message"]),
    ("agent-routing", ["to another agent", "to an agent", "to a specialist", "to the right agent", "to an expert", "another agent", "hand off to", "handoff", "delegate to", "which agent", "assign to an agent", "route to an agent"]),
    ("escalation-decision", ["escalate to a human", "escalate to a person", "should we escalate", "escalation decision", "needs a human", "route to a human", "hand to a human"]),
    ("tool-selection", ["which tool", "select a tool", "pick a tool", "choose a tool", "tool to call", "function to call", "tool selection", "pick the function"]),
    ("intent-detection", ["detect intent", "user intent", "intent detection", "what does the user want", "classify intent", "identify intent"]),
    ("sql-generation", ["nl to sql", "nl2sql", "text to sql", "text-to-sql", "generate sql", "sql query", " sql ", "to sql", "query the database", "query the db", "natural language to sql"]),
    ("code-review", ["code review", "review a code", "review the code", "review this pr", "review a pr", "pull request review", "diff review"]),
    ("content-moderation", ["moderat", "unsafe content", "flag unsafe", "toxic", "abusive content", "content safety", "safety filter"]),
    ("dedup-near-duplicate", ["near-duplicate", "near duplicate", "deduplicat", "dedupe", "detect duplicate", "find duplicate"]),
    ("entity-resolution", ["entity resolution", "canonical entit", "record linkage", "resolve records", "match records", "link records", "resolve duplicates to"]),
    ("translation", ["translate", "translation"]),
    ("summarization", ["summari", "tl;dr", "tldr", "abstract of", "condense"]),
    ("grounded-answer", ["answer a question", "answer questions", "with citation", "cite sources", "q&a", "question answering", "grounded answer", "answer with", "look up the answer", "search and answer", "rag"]),
    ("slot-filling", ["fill the slots", "slot filling", "fill in the fields", "fill the fields", "fill the required", "fill out the", "gather the required", "collect the required fields", "fill the form fields", "fill required fields"]),
    ("text-classification", ["classif", "categor", "label text", "label these", "tag text", "taxonomy", "label the"]),
    ("email-triage", ["triage", "route the inbox", "route inbox", "inbox", "sort emails", "assign tickets", "route emails"]),
    ("document-schema-extraction", ["extract", "pull out", "fields from", "schema from", "ocr", "invoice", "lease", "contract", "form fields"]),
]


def _match_task(t: str) -> str | None:
    """First catalog task whose keyword appears (most-specific-first). Returns a task_id or None."""
    for task_id, kws in _TASK_KEYWORDS:
        if any(k in t for k in kws):
            return task_id
    return None


def classify_capability_type(intent: str) -> str:
    """Route an open-ended capability to a TYPE: hub_population (populate a hub), document_extraction (the richer
    extraction cascade), or task:<id> for any of the other tunable-task capability types (classify / answer / summarize
    / translate / dedupe / route / transcribe / sql / moderate / entity-resolution / image-tag)."""
    t = (intent or "").lower()
    if re.search(r"\b(scrape|crawl)\b.*\b(internet|web|github|sources?)\b", t) or "hub" in t:
        return "hub_population"          # populating a hub, even if it says 'extract'
    task = _match_task(t)
    if task == "document-schema-extraction":
        return "document_extraction"     # the richer dedicated cascade (acquire→prune→patterns→cheap→supervise)
    if task:
        return "task:" + task            # the tunable-task method grid (cheapest tier that meets the bar)
    return "hub_population"


def resolve_schema(intent: str) -> str | None:
    """Map free text to a known extraction schema template (land lease / oil & gas / invoice / …), or None."""
    t = (intent or "").lower()
    if "lease" in t and ("oil" in t or "gas" in t):
        return "oil_gas_lease"
    if "lease" in t or ("land" in t and "agreement" in t):
        return "land_lease"
    try:
        from src.teleon.extraction.schema_templates import template_names
        for name in template_names():
            if name in t or name.replace("_", " ") in t:
                return name
    except Exception:  # noqa: BLE001
        pass
    return None


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


def _plan_document_extraction(intent: str) -> CapabilityPlan:
    """A capability like 'intake a PDF/email and extract this schema' → routed to the document cascade (the efficient
    way), NOT the hub pipeline. The owner's point: write the capability; the system makes it most efficient."""
    schema = resolve_schema(intent)
    steps = (
        PlanStep("acquire", "extraction.document_extraction_cascade._pick_acquire",
                 "OCR / text extraction — cheapest acquire the document supports"),
        PlanStep("prune_compress", "extraction.document_extraction_cascade (prune_compress)",
                 "cut gibberish + redundant text → fewer tokens before any LLM"),
        PlanStep("patterns", "extraction.document_extraction_cascade (regex/heuristic_patterns)",
                 "deterministic pattern extraction — answers BEFORE any LLM call"),
        PlanStep("cheap_llm", "extraction.document_extraction_cascade (cheap_llm)",
                 "cheapest-capable LLM on ONLY the unfilled fields, chunked"),
        PlanStep("supervise", "extraction.document_extraction_cascade.supervise_extraction",
                 "LLM as CONTROL SUPERVISOR — audits the cheap methods, escalates only the flagged fields"),
    )
    return CapabilityPlan(intent=intent, hub="", iterative=False, scheduled=False, cadence="per_document",
                          schedule_every=None, needed_capability="document_extraction", research_descent={},
                          steps=steps, stop={"mode": "cascade"}, capability_type="document_extraction",
                          route={"engine": "document_extraction_cascade", "schema_template": schema})


def _plan_tunable_task(intent: str, task_id: str, *, available_keys: tuple = ("LLM_API_KEY",)) -> CapabilityPlan:
    """A capability like 'classify these tickets' / 'answer with citations' / 'summarize' → routed to the tunable-task
    method grid (rules/cheap → small model → LLM), cheapest tier that meets the bar. The same efficiency motion as
    extraction, generalized across the 13 capability types."""
    from src.teleon.evolution import auto_tuning
    task = auto_tuning.get_task(task_id) or {}
    setup = auto_tuning.auto_tune_setup(task_id, available_keys=available_keys)
    steps = tuple(PlanStep(t["tier"], f"teleon.evolution.auto_tuning ({task_id})",
                           f"{t.get('methods', '')}" + (" · deterministic" if t.get("deterministic") else ""))
                  for t in task.get("tiers", []))
    return CapabilityPlan(intent=intent, hub="", iterative=False, scheduled=False, cadence="per_request",
                          schedule_every=None, needed_capability=task_id, research_descent={}, steps=steps,
                          stop={"objective": task.get("objective"), "metric": task.get("requirement_metric")},
                          capability_type="task:" + task_id,
                          route={"engine": "tunable_task_harness", "task_id": task_id, "name": task.get("name"),
                                 "cheapest_tier": setup.get("cheapest_tier"), "escalation_order": setup.get("escalation_order"),
                                 "deterministic_possible": task.get("deterministic_possible")})


def plan(intent: str, *, hubs: list[str], kinds: dict | None = None, available: set | None = None,
         max_rounds: int = 5, no_new_rounds: int = 2) -> CapabilityPlan:
    """Decompose an open-ended capability into a typed, executable plan. document_extraction → the cascade; a tunable
    task (classify/answer/summarize/...) → its method grid; hub_population → the classify + hub + research-descent plan."""
    ctype = classify_capability_type(intent)
    if ctype == "document_extraction":
        return _plan_document_extraction(intent)
    if ctype.startswith("task:"):
        return _plan_tunable_task(intent, ctype.split(":", 1)[1])
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
    # document-extraction capabilities route to the cascade (efficient by construction), not the hub loop
    if p.capability_type == "document_extraction":
        from src.teleon.extraction.document_extraction_cascade import compare_strategies
        from src.teleon.extraction.schema_templates import get_template
        schema = get_template(p.route.get("schema_template")) if p.route.get("schema_template") else None
        required = schema or {"party_a": "structured", "party_b": "structured", "effective_date": "structured",
                              "terms": "semi", "special_provisions": "unstructured"}
        cmp = compare_strategies(required, {"has_text_layer": True, "scanned": False})
        return {"capability_type": "document_extraction", "schema_template": p.route.get("schema_template"),
                "fields": cmp["fields"], "frontier_only_cost": cmp["frontier_only"]["cost"],
                "cascade_cost": cmp["cascade"]["cost"], "supervised_cost": cmp["supervised"]["cost"],
                "pct_saved": cmp["supervised"]["pct_saved"], "llm_role": cmp["supervised"]["llm_role"],
                "made_efficient": True, "serves_truth": False}
    # any other tunable-task capability → the method-grid descent (cheapest tier that meets the bar)
    if p.capability_type.startswith("task:"):
        r = p.route
        return {"capability_type": p.capability_type, "task_id": r.get("task_id"), "name": r.get("name"),
                "cheapest_tier": r.get("cheapest_tier"), "escalation_order": r.get("escalation_order"),
                "deterministic_possible": r.get("deterministic_possible"),
                "objective": p.stop.get("objective"), "metric": p.stop.get("metric"),
                "made_efficient": True, "serves_truth": False}

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


__all__ = ["PlanStep", "CapabilityPlan", "classify", "classify_capability_type", "resolve_hub", "resolve_schema",
           "infer_capability", "plan", "execute"]
