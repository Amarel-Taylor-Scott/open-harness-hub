"""src.teleon.seeds.profession_calculators -- DETERMINISTIC profession calculators: the actual clean-room
If-Statement implementations that CLOSE the determinism_ceiling=1.0 capability candidates the
profession_capability_seeder only DECLARES.

A seeder candidate names a durable gap (a base model cannot reliably compute a commercial driver federal
hours-of-service status); a calculator here is the deterministic ANSWER to it. Each calculator is a pure,
deterministic function over PROVIDED inputs (never model-guessed) that encodes the PUBLICLY-STATED rule
structure of a federal/public regulation -- the limits are facts stated in the CFR, not copyrightable
expression, so this is clean-room with no third-party code vendored.

Every calculator is registered as a governed CapabilitySeed, so it runs through the normal screen -> eval ->
promotion pipeline and NEVER serves truth: a calculation is a CANDIDATE that still needs verification against
the live authoritative source (rule currency is the freshness wedge) before it can be promoted to active.

Implemented (this module is extended one calculator per cycle):
  - commercial-driver-hours-of-service         -> closes candidate commercial-driver-hours-of-service-rule
  - pharmacist-controlled-substance-schedule   -> closes candidate pharmacist-controlled-substance-schedule
  - seafarer-port-state-control                -> closes candidate seafarer-port-state-control

Teleon-layer; never imports src.baltor.
"""
from __future__ import annotations

import re

from src.teleon.seeds.capability_seed import CapabilitySeed, SeedResult, register

#: implementation slot -> the profession_capability_seeder candidate slot it closes (lineage; lossless -- an
#: implementation always points back at the declared gap it answers).
IMPLEMENTS = dict([
    ("commercial-driver-hours-of-service", "commercial-driver-hours-of-service-rule"),
    ("pharmacist-controlled-substance-schedule", "pharmacist-controlled-substance-schedule"),
    ("seafarer-port-state-control", "seafarer-port-state-control"),
])

# -- FMCSA Hours-of-Service (property-carrying CMV, 49 CFR 395.3) -- public federal regulation -------------
# The numeric limits below are facts stated in the CFR (not copyrightable). v1 models the four core limits;
# the split-sleeper-berth and adverse-driving exceptions are a documented follow-on (like the court-deadline
# seed holiday calendar).
_DRIVE_LIMIT_MIN = 11 * 60          # 395.3(a)(3)(i): 11-hour driving limit
_WINDOW_LIMIT_MIN = 14 * 60         # 395.3(a)(2): 14-consecutive-hour window (off-duty does NOT extend it)
_DRIVE_BEFORE_BREAK_MIN = 8 * 60    # 395.3(a)(3)(ii): 30-min break required after 8 cumulative driving hours
_MIN_BREAK_MIN = 30                 # the qualifying break length
_CYCLE_LIMIT_MIN = dict([(7, 60 * 60), (8, 70 * 60)])   # 395.3(b): 60h/7d or 70h/8d on-duty limit
_DEFAULT_CYCLE_DAYS = 8

_DRIVING = "driving"
_ON_DUTY = "on_duty_not_driving"
_OFF = ("off_duty", "sleeper_berth")   # off-duty statuses; either can satisfy the 30-min break

#: deterministic tie-break order when two limits bind with equal remaining time -- surface the MORE
#: restrictive action first (a 34h restart / 10h reset before a 30-min break).
_RULE_ORDER = ("cycle_limit", "drive_limit_11h", "window_limit_14h", "break_30min")
_RULE_ACTION = dict(
    break_30min="take a 30-minute break (off-duty/sleeper/on-duty-not-driving) before driving again",
    drive_limit_11h="a 10-consecutive-hour off-duty reset is required before driving again",
    window_limit_14h="a 10-consecutive-hour off-duty reset is required before driving again",
    cycle_limit="a 34-consecutive-hour off-duty restart is required to reset the 7/8-day cycle",
)


def hours_of_service(payload):
    """Deterministic FMCSA HOS status for a property-carrying CMV driver over a PROVIDED duty timeline.

    payload (all optional -- safe defaults so the seed runs on any input):
      segments: list of (status, minutes) dicts, where status is one of driving, on_duty_not_driving,
                off_duty, sleeper_berth; chronological, for the CURRENT duty period after the last
                qualifying 10h+ off-duty reset.
      cycle_days: 7 or 8 (default 8 -> 70h).
      prior_cycle_onduty_minutes: on-duty minutes already in the rolling cycle BEFORE this shift (default 0).
      restart_taken: a 34h+ off-duty restart cleared the cycle (default False -> prior counts).

    Returns a deterministic status dict. A result is a CANDIDATE (never truth) -- verify against the live rule.
    """
    p = payload or {}
    segments = p.get("segments") or []
    cycle_days = p.get("cycle_days", _DEFAULT_CYCLE_DAYS)
    if cycle_days not in _CYCLE_LIMIT_MIN:
        cycle_days = _DEFAULT_CYCLE_DAYS
    cycle_limit = _CYCLE_LIMIT_MIN[cycle_days]
    prior = 0 if p.get("restart_taken") else max(0, int(p.get("prior_cycle_onduty_minutes", 0) or 0))

    driving_used = window_used = onduty_shift = since_break = 0
    for seg in segments:
        status = seg.get("status")
        mins = max(0, int(seg.get("minutes", 0) or 0))   # clamp negative/garbage durations to 0
        window_used += mins                              # 14h clock runs over EVERY segment (off-duty consumes it)
        if status == _DRIVING:
            driving_used += mins
            onduty_shift += mins
            since_break += mins
        elif status == _ON_DUTY:
            onduty_shift += mins
            if mins >= _MIN_BREAK_MIN:                   # on-duty-not-driving of 30+ min also satisfies the break
                since_break = 0
        elif status in _OFF:
            if mins >= _MIN_BREAK_MIN:                   # only a 30+ min pause resets the 8h-drive break clock
                since_break = 0
        # unknown status counts toward the window only (conservative) -- no driving/on-duty credit
    cycle_used = prior + onduty_shift

    remaining = dict(
        drive_limit_11h=max(0, _DRIVE_LIMIT_MIN - driving_used),
        window_limit_14h=max(0, _WINDOW_LIMIT_MIN - window_used),
        break_30min=max(0, _DRIVE_BEFORE_BREAK_MIN - since_break),
        cycle_limit=max(0, cycle_limit - cycle_used),
    )
    limiting_rule = min(_RULE_ORDER, key=lambda r: (remaining[r], _RULE_ORDER.index(r)))
    remaining_drive_min = remaining[limiting_rule]

    violations = []
    if driving_used > _DRIVE_LIMIT_MIN:
        violations.append("drive_limit_11h")
    if window_used > _WINDOW_LIMIT_MIN:
        violations.append("window_limit_14h")
    if since_break > _DRIVE_BEFORE_BREAK_MIN:
        violations.append("break_30min")
    if cycle_used > cycle_limit:
        violations.append("cycle_limit")

    can_drive_now = not violations and remaining_drive_min > 0
    return dict(
        can_drive_now=can_drive_now,
        violations=sorted(violations),
        remaining_drive_min=remaining_drive_min,
        limiting_rule=limiting_rule,
        required_action=(_RULE_ACTION[limiting_rule] if (violations or remaining_drive_min == 0)
                         else "none -- within all limits"),
        driving_used_min=driving_used,
        window_used_min=window_used,
        driving_since_break_min=since_break,
        onduty_cycle_used_min=cycle_used,
        cycle_days=cycle_days,
        cycle_limit_min=cycle_limit,
        implements_candidate=IMPLEMENTS["commercial-driver-hours-of-service"],
        note=("v1 models the 11h drive / 14h window / 30-min break / 60-70h cycle limits; the "
              "split-sleeper-berth and adverse-driving exceptions are a documented follow-on. A calculation "
              "is a CANDIDATE -- verify against the live FMCSA rule (currency is the freshness wedge) before "
              "promotion."),
    )


def _hos_runner(payload):
    return SeedResult(
        output=hours_of_service(payload),
        provenance=("deterministic If-Statement over FMCSA 49 CFR 395.3 limits (11h drive / 14h window / "
                    "30-min break / 60-70h cycle); never model-guessed; clean-room (public federal "
                    "regulation, no third-party code vendored)"))


register(CapabilitySeed(
    slot="commercial-driver-hours-of-service",
    intent="Compute a commercial driver federal Hours-of-Service status deterministically (11h/14h/30-min/60-70h).",
    learned_from="profession_capability_seeder candidate commercial-driver-hours-of-service-rule (FMCSA 49 CFR 395.3, public regulation)",
    source_license="US public domain (federal regulation)",
    category="identity-compliance",
    determinism_ceiling=1.0, adoptable=True, drop_in=True,
    lesson=("an Hours-of-Service check MUST be a deterministic If-Statement over the CFR limits, never a model "
            "guess -- the profession seeder declares the durable gap (determinism_ceiling=1.0) and this module "
            "is the clean-room implementation that closes it; a calculation stays a candidate until verified "
            "against the live rule (currency)."),
    runner=_hos_runner))


# -- DEA controlled-substance schedule (Controlled Substances Act, 21 USC 812 / 21 CFR 1308) -----------------
# A substance's federal SCHEDULE (I-V) is a published fact (21 CFR 1308.11-1308.15); the prescribing/refilling
# CONSEQUENCES of a schedule are published facts too (21 CFR 1306). Both are clean-room -- no third-party code
# or proprietary drug database is vendored, only the publicly-stated rule structure. The part a base model
# botches is the CONSEQUENCE logic: it routinely conflates Schedule V's "as authorized" refills with the III/IV
# 5-refills/6-months cap, or grants Schedule II refills. So this is a deterministic If-Statement, never a guess.
_SCHEDULES = ("I", "II", "III", "IV", "V")

#: substance (normalized generic) -> federal CSA schedule. A curated, well-established subset of the public
#: 21 CFR 1308 lists; NOT exhaustive -- an unmatched substance returns schedule_known=False (verify upstream).
_SCHEDULE_OF = dict([
    # Schedule I (no accepted medical use -> not prescribable): 1308.11
    ("heroin", "I"), ("lsd", "I"), ("mdma", "I"), ("psilocybin", "I"), ("marijuana", "I"),
    ("peyote", "I"), ("mescaline", "I"), ("methaqualone", "I"),
    # Schedule II (high abuse, accepted use; no refills): 1308.12
    ("oxycodone", "II"), ("fentanyl", "II"), ("morphine", "II"), ("hydrocodone", "II"),
    ("hydromorphone", "II"), ("methadone", "II"), ("methamphetamine", "II"), ("cocaine", "II"),
    ("amphetamine", "II"), ("methylphenidate", "II"), ("oxymorphone", "II"), ("pentobarbital", "II"),
    ("secobarbital", "II"),
    # Schedule III: 1308.13
    ("buprenorphine", "III"), ("ketamine", "III"), ("testosterone", "III"), ("nandrolone", "III"),
    ("benzphetamine", "III"),
    # Schedule IV: 1308.14
    ("alprazolam", "IV"), ("clonazepam", "IV"), ("diazepam", "IV"), ("lorazepam", "IV"),
    ("temazepam", "IV"), ("tramadol", "IV"), ("zolpidem", "IV"), ("carisoprodol", "IV"),
    ("modafinil", "IV"), ("phenobarbital", "IV"),
    # Schedule V: 1308.15
    ("pregabalin", "V"), ("lacosamide", "V"), ("brivaracetam", "V"), ("diphenoxylate atropine", "V"),
])

#: common brand / colloquial name (normalized) -> generic key in _SCHEDULE_OF (clean-room: public names only).
_ALIASES = dict([
    ("oxycontin", "oxycodone"), ("percocet", "oxycodone"), ("norco", "hydrocodone"),
    ("vicodin", "hydrocodone"), ("dilaudid", "hydromorphone"), ("adderall", "amphetamine"),
    ("ritalin", "methylphenidate"), ("concerta", "methylphenidate"), ("suboxone", "buprenorphine"),
    ("subutex", "buprenorphine"), ("xanax", "alprazolam"), ("klonopin", "clonazepam"),
    ("valium", "diazepam"), ("ativan", "lorazepam"), ("restoril", "temazepam"), ("ultram", "tramadol"),
    ("ambien", "zolpidem"), ("soma", "carisoprodol"), ("provigil", "modafinil"), ("lyrica", "pregabalin"),
    ("vimpat", "lacosamide"), ("briviact", "brivaracetam"), ("lomotil", "diphenoxylate atropine"),
    ("ecstasy", "mdma"), ("molly", "mdma"), ("cannabis", "marijuana"), ("weed", "marijuana"),
    ("acid", "lsd"),
])

_CSA_REFILL_MAX = 5         # 21 CFR 1306.22: Schedule III/IV -- no more than 5 refills
_CSA_REFILL_WINDOW_MO = 6   # 21 CFR 1306.22: ...within 6 months of the date of issue


def _normalize(name):
    return re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()


def _norm_schedule(value):
    """Accept I-V / 1-5 / 'schedule iii' / 'C-II' and return a canonical roman 'I'..'V', or None."""
    if value is None:
        return None
    t = re.sub(r"[^a-z0-9]+", "", str(value).lower())
    for pre in ("schedule", "sched", "cs"):
        if t.startswith(pre):
            t = t[len(pre):]
    if t.startswith("c") and len(t) > 1:   # 'c-ii' / 'cii'
        t = t[1:]
    roman = dict([("1", "I"), ("2", "II"), ("3", "III"), ("4", "IV"), ("5", "V")])
    if t in roman:
        return roman[t]
    up = t.upper()
    return up if up in _SCHEDULES else None


def _csa_rules(schedule):
    """Deterministic prescribing/refill consequences of a CSA schedule (21 CFR 1306). Unknown -> all None."""
    if schedule == "I":
        return dict(prescribable=False, refills_allowed=False, max_refills=0, refill_window_months=None,
                    oral_prescription_allowed=False, written_or_epcs_required=None, otc_possible=False,
                    basis="21 USC 812(b)(1): Schedule I has no accepted medical use -> not prescribable")
    if schedule == "II":
        return dict(prescribable=True, refills_allowed=False, max_refills=0, refill_window_months=None,
                    oral_prescription_allowed=False, written_or_epcs_required=True, otc_possible=False,
                    basis="21 CFR 1306.11/1306.12: written or EPCS prescription, NO refills (oral only in emergency)")
    if schedule in ("III", "IV"):
        return dict(prescribable=True, refills_allowed=True, max_refills=_CSA_REFILL_MAX,
                    refill_window_months=_CSA_REFILL_WINDOW_MO, oral_prescription_allowed=True,
                    written_or_epcs_required=False, otc_possible=False,
                    basis="21 CFR 1306.22: up to 5 refills within 6 months of the date of issue")
    if schedule == "V":
        return dict(prescribable=True, refills_allowed=True, max_refills=None, refill_window_months=None,
                    oral_prescription_allowed=True, written_or_epcs_required=False, otc_possible=True,
                    basis="Schedule V: refills as authorized by the prescriber (1306.22's 5/6 cap names only III & "
                          "IV); some Schedule V products are OTC-dispensable where state law permits")
    return dict(prescribable=None, refills_allowed=None, max_refills=None, refill_window_months=None,
                oral_prescription_allowed=None, written_or_epcs_required=None, otc_possible=None,
                basis="schedule unknown -- provide a substance in the clean-room 21 CFR 1308 subset or an explicit schedule")


def controlled_substance(payload):
    """Deterministic DEA Controlled Substances Act status for a PROVIDED substance or schedule.

    payload (all optional -- safe defaults so the seed runs on any input):
      substance:          a drug name (generic or common brand) to look up in the clean-room 21 CFR 1308 subset.
      schedule:           an explicit CSA schedule (I-V / 1-5 / 'C-II'); used directly when given (wins over lookup).
      requested_refills:  an integer refill count to test against the schedule's refill rule.
      months_since_issue: months elapsed since the prescription's date of issue (tests the 6-month window).

    Returns a deterministic status dict. A result is a CANDIDATE (never truth) -- a substance can be
    rescheduled (currency is the freshness wedge); verify against the live DEA scheduling before promotion.
    """
    p = payload or {}
    substance_raw = p.get("substance")
    matched = None
    schedule = _norm_schedule(p.get("schedule"))
    if substance_raw and schedule is None:
        key = _normalize(substance_raw)
        key = _ALIASES.get(key, key)
        sch = _SCHEDULE_OF.get(key)
        if sch is not None:
            schedule = sch
            matched = key
    rules = _csa_rules(schedule)

    req = p.get("requested_refills")
    refill_request_permitted = None
    if req is not None:
        try:
            req = max(0, int(req))
        except (TypeError, ValueError):
            req = 0
        if rules["refills_allowed"] is False:
            refill_request_permitted = (req == 0)              # only an initial fill (0 refills) is allowed
        elif rules["refills_allowed"] is True:
            refill_request_permitted = (rules["max_refills"] is None) or (req <= rules["max_refills"])
        # unknown schedule -> stays None (never guessed)

    months = p.get("months_since_issue")
    within_refill_window = None
    if months is not None and rules["refill_window_months"] is not None:
        try:
            within_refill_window = float(months) <= rules["refill_window_months"]
        except (TypeError, ValueError):
            within_refill_window = None

    dispense_permitted = rules["prescribable"]
    if dispense_permitted and refill_request_permitted is False:
        dispense_permitted = False
    if dispense_permitted and within_refill_window is False:
        dispense_permitted = False
    if rules["prescribable"] is None:
        dispense_permitted = None                               # unknown schedule -> never assert dispensability

    out = dict(
        substance=substance_raw,
        matched_substance=matched,
        schedule=schedule,
        schedule_known=schedule is not None,
        requested_refills=req,
        refill_request_permitted=refill_request_permitted,
        months_since_issue=months,
        within_refill_window=within_refill_window,
        dispense_permitted=dispense_permitted,
        implements_candidate=IMPLEMENTS["pharmacist-controlled-substance-schedule"],
        note=("schedule placement and its prescribing/refill consequences are public facts (21 CFR 1308 / "
              "1306); a substance can be rescheduled, so a result is a CANDIDATE -- verify against the live DEA "
              "scheduling (currency is the freshness wedge) before promotion."),
    )
    out.update(rules)
    return out


def _csa_runner(payload):
    return SeedResult(
        output=controlled_substance(payload),
        provenance=("deterministic If-Statement over the DEA Controlled Substances Act schedules (21 CFR 1308) "
                    "and their prescribing/refill consequences (21 CFR 1306); never model-guessed; clean-room "
                    "(public federal regulation, no third-party drug database or code vendored)"))


register(CapabilitySeed(
    slot="pharmacist-controlled-substance-schedule",
    intent="Resolve a substance's federal DEA schedule (I-V) and its prescribing/refill rules deterministically.",
    learned_from="profession_capability_seeder candidate pharmacist-controlled-substance-schedule (DEA CSA, 21 CFR 1308/1306, public regulation)",
    source_license="US public domain (federal regulation)",
    category="identity-compliance",
    determinism_ceiling=1.0, adoptable=True, drop_in=True,
    lesson=("a controlled-substance schedule lookup AND its refill consequences MUST be a deterministic "
            "If-Statement over the published CSA lists, never a model guess -- base models conflate Schedule V's "
            "as-authorized refills with the III/IV 5-refills/6-months cap and sometimes grant Schedule II "
            "refills; the profession seeder declares the durable gap (determinism_ceiling=1.0) and this is the "
            "clean-room implementation that closes it; a result stays a candidate until verified against the "
            "live DEA scheduling (currency)."),
    runner=_csa_runner))


# -- Paris/Tokyo MoU Port State Control: Ship Risk Profile -> inspection priority/interval -------------------
# The Paris MoU New Inspection Regime (NIR, in force 1 Jan 2011) and the parallel Tokyo MoU regime assign every
# ship a Ship Risk Profile (High / Standard / Low) from a PUBLISHED weighting-points scheme over generic
# parameters (ship type, age, flag-list, recognised-organisation performance, company performance) and historic
# parameters (deficiencies, detentions), then derive the inspection interval and Priority (I = must be inspected,
# II = may be inspected). Those points, thresholds and intervals are facts published in the Paris/Tokyo MoU PSC
# procedures, not copyrightable expression -> clean-room, no third-party code or data vendored. The part a base
# model botches is the same shape as the CSA Schedule-V conflation: it guesses a uniform annual interval, forgets
# the age threshold is 12 years (not 15/20), treats a high-risk SHIP TYPE as automatically High Risk, and -- the
# headline error -- assumes "no weighting points" == Low Risk, when Low Risk additionally requires a WHITE-list
# flag, HIGH RO & company performance and ZERO detentions (a single detention blocks Low Risk yet only TWO score
# an HRS point). So this is a deterministic If-Statement over the published matrix, never a guess.
_PSC_HIGH_RISK_SHIP_TYPES = frozenset(
    ["chemical tanker", "gas carrier", "oil tanker", "bulk carrier", "passenger ship"])
_PSC_AGE_THRESHOLD_YEARS = 12          # generic param: a ship older than 12 years scores the age point
_PSC_DEFICIENCY_THRESHOLD = 5          # an inspection with MORE THAN 5 deficiencies scores / blocks Low Risk
_PSC_DETENTION_HRS_THRESHOLD = 2       # 2+ detentions in the previous 36 months score the historic HRS point...
_PSC_HRS_POINTS = 5                    # ...and a total weighting of 5+ points => High Risk Ship

#: published weighting points (Paris MoU NIR) added per parameter when it is in its high-risk condition.
_PSC_PT_SHIP_TYPE = 2
_PSC_PT_AGE = 1
_PSC_PT_FLAG = 1
_PSC_PT_RO = 1
_PSC_PT_COMPANY = 1
_PSC_PT_DEFICIENCIES = 1
_PSC_PT_DETENTIONS = 1

#: profile -> (lower, upper) periodic inspection interval in MONTHS. The window opens at the lower bound
#: (Priority II = may be inspected); past the upper bound the periodic inspection is overdue (Priority I = must).
_PSC_INTERVAL_MONTHS = dict([("high", (5, 6)), ("standard", (10, 12)), ("low", (24, 36))])
_PSC_PROFILE_LABEL = dict([("high", "High Risk Ship"), ("standard", "Standard Risk Ship"),
                           ("low", "Low Risk Ship")])

#: common ship-type spellings (normalized) -> the canonical high-risk type key (clean-room: public names only).
_PSC_SHIP_TYPE_ALIASES = dict([
    ("bulker", "bulk carrier"), ("bulk", "bulk carrier"), ("bulk carriers", "bulk carrier"),
    ("crude tanker", "oil tanker"), ("crude oil tanker", "oil tanker"), ("product tanker", "oil tanker"),
    ("oil chemical tanker", "oil tanker"), ("tanker", "oil tanker"),
    ("lng carrier", "gas carrier"), ("lpg carrier", "gas carrier"), ("lng", "gas carrier"),
    ("lpg", "gas carrier"), ("gas tanker", "gas carrier"),
    ("passenger", "passenger ship"), ("cruise ship", "passenger ship"), ("cruise", "passenger ship"),
    ("ropax", "passenger ship"), ("chemical", "chemical tanker"), ("chemical carrier", "chemical tanker"),
])


def _psc_num(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _psc_flag(value):
    """Normalize a Paris MoU flag-performance list to 'white' | 'grey' | 'black', else None."""
    t = _normalize(value).replace("gray", "grey")
    for f in ("white", "grey", "black"):
        if f in t:
            return f
    return None


def _psc_perf(value):
    """Normalize an RO / company performance level to 'high' | 'medium' | 'low' | 'very low', else None."""
    t = _normalize(value)
    if not t:
        return None
    if "very low" in t or t in ("vlow", "vlr", "vl"):
        return "very low"
    for level in ("high", "medium", "low"):
        if level in t:
            return level
    return None


def _psc_ship_type(value):
    t = _normalize(value)
    if not t:
        return None
    return _PSC_SHIP_TYPE_ALIASES.get(t, t)


def ship_risk_profile(payload):
    """Deterministic Paris/Tokyo MoU Port State Control Ship Risk Profile + inspection priority/interval.

    payload (all optional -- safe defaults so the seed runs on any input):
      ship_type:                    a ship type (e.g. 'oil tanker', 'general cargo', 'container').
      age_years:                    ship age in years.
      flag_list:                    Paris MoU flag-performance list -- 'white' | 'grey' | 'black'.
      ro_performance:               recognised-organisation performance -- 'high' | 'medium' | 'low' | 'very low'.
      company_performance:          ISM company performance -- 'high' | 'medium' | 'low' | 'very low'.
      inspection_deficiencies:      list of per-inspection deficiency counts over the previous 36 months.
      detentions_36mo:              number of detentions in the previous 36 months.
      months_since_last_inspection: months since the last periodic inspection (drives Priority).
      overriding_factor:            an overriding factor is present (collision/grounding/class suspension/...) -> Priority I.
      inspected_last_36mo:          whether the ship was inspected at least once in the period (default True; Low Risk needs it).

    Returns a deterministic profile dict. A result is a CANDIDATE (never truth) -- the flag/RO/company lists and the
    rule itself change (currency is the freshness wedge); verify against the live Paris/Tokyo MoU regime before promotion.
    """
    p = payload or {}
    ship_type = _psc_ship_type(p.get("ship_type"))
    age = _psc_num(p.get("age_years"))
    flag = _psc_flag(p.get("flag_list"))
    ro = _psc_perf(p.get("ro_performance"))
    company = _psc_perf(p.get("company_performance"))
    defs = []
    for d in (p.get("inspection_deficiencies") or []):
        n = _psc_num(d)
        if n is not None:
            defs.append(max(0, int(n)))
    detentions = max(0, int(_psc_num(p.get("detentions_36mo")) or 0))
    worst_deficiencies = max(defs) if defs else 0
    has_high_def_inspection = any(d > _PSC_DEFICIENCY_THRESHOLD for d in defs)

    points = dict(
        ship_type=_PSC_PT_SHIP_TYPE if ship_type in _PSC_HIGH_RISK_SHIP_TYPES else 0,
        age=_PSC_PT_AGE if (age is not None and age > _PSC_AGE_THRESHOLD_YEARS) else 0,
        flag=_PSC_PT_FLAG if flag == "black" else 0,
        recognised_organisation=_PSC_PT_RO if ro in ("low", "very low") else 0,
        company=_PSC_PT_COMPANY if company in ("low", "very low") else 0,
        deficiencies=_PSC_PT_DEFICIENCIES if has_high_def_inspection else 0,
        detentions=_PSC_PT_DETENTIONS if detentions >= _PSC_DETENTION_HRS_THRESHOLD else 0,
    )
    total_points = sum(points.values())

    ever_inspected = bool(p.get("inspected_last_36mo", True)) or bool(defs) or detentions > 0
    # Low Risk requires ALL low-risk conditions -- and is STRICTER than "zero weighting points": a WHITE-list flag
    # (not merely non-black), HIGH RO & company (not merely non-low) and ZERO detentions. Ship type & age add HRS
    # points but are NOT in the Low-Risk gate, so a high-risk-type ship with a clean record can still be Low Risk.
    low_risk = (
        total_points < _PSC_HRS_POINTS
        and flag == "white"
        and ro == "high"
        and company == "high"
        and detentions == 0
        and not has_high_def_inspection
        and ever_inspected
    )

    if total_points >= _PSC_HRS_POINTS:
        profile = "high"
    elif low_risk:
        profile = "low"
    else:
        profile = "standard"

    lower, upper = _PSC_INTERVAL_MONTHS[profile]
    msi = _psc_num(p.get("months_since_last_inspection"))
    overriding = bool(p.get("overriding_factor"))
    if overriding:
        priority, inspection_due, priority_reason = "I", True, "overriding factor present -> mandatory inspection"
    elif msi is None:
        priority, inspection_due, priority_reason = None, None, "months since last inspection not provided"
    elif msi > upper:
        priority, inspection_due, priority_reason = "I", True, (
            "periodic window (" + str(upper) + " months) exceeded -> must be inspected")
    elif msi >= lower:
        priority, inspection_due, priority_reason = "II", True, (
            "within the open inspection window (" + str(lower) + "-" + str(upper) + " months) -> may be inspected")
    else:
        priority, inspection_due, priority_reason = None, False, (
            "before the window opens (< " + str(lower) + " months) -> not yet due")

    return dict(
        risk_profile=profile,
        risk_profile_label=_PSC_PROFILE_LABEL[profile],
        weighting_points=points,
        total_weighting_points=total_points,
        hrs_threshold=_PSC_HRS_POINTS,
        low_risk_eligible=low_risk,
        inspection_interval_months=dict(lower=lower, upper=upper),
        priority=priority,
        inspection_due=inspection_due,
        priority_reason=priority_reason,
        normalized=dict(ship_type=ship_type, flag_list=flag, ro_performance=ro, company_performance=company,
                        age_years=age, detentions_36mo=detentions, worst_inspection_deficiencies=worst_deficiencies),
        implements_candidate=IMPLEMENTS["seafarer-port-state-control"],
        note=("v1 models the Paris/Tokyo MoU New Inspection Regime weighting matrix (ship type 2 / age>12y 1 / "
              "black-flag 1 / low RO 1 / low company 1 / >5-deficiency inspection 1 / 2+ detentions 1; High Risk "
              "at 5+ points), the Low-Risk gate (white flag + high RO & company + zero detentions -- STRICTER than "
              "zero points), and the per-profile interval/Priority (HRS 5-6mo, SRS 10-12mo, LRS 24-36mo; Priority "
              "I=must inspect, II=may inspect). Ship type & age add HRS points but do NOT block Low Risk. A "
              "calculation is a CANDIDATE -- verify against the live Paris/Tokyo MoU rule (currency is the "
              "freshness wedge) before promotion."),
    )


def _srp_runner(payload):
    return SeedResult(
        output=ship_risk_profile(payload),
        provenance=("deterministic If-Statement over the Paris/Tokyo MoU Port State Control New Inspection Regime "
                    "Ship Risk Profile (weighting points -> High/Standard/Low) and its inspection interval/Priority; "
                    "never model-guessed; clean-room (published intergovernmental PSC procedures, no third-party "
                    "code or data vendored)"))


register(CapabilitySeed(
    slot="seafarer-port-state-control",
    intent="Compute a Paris/Tokyo MoU Ship Risk Profile and inspection priority/interval deterministically.",
    learned_from="profession_capability_seeder candidate seafarer-port-state-control (Paris/Tokyo MoU New Inspection Regime, public PSC procedures)",
    source_license="public (intergovernmental MoU / IMO procedures)",
    category="identity-compliance",
    determinism_ceiling=1.0, adoptable=True, drop_in=True,
    lesson=("a Port State Control Ship Risk Profile MUST be a deterministic If-Statement over the published Paris/"
            "Tokyo MoU weighting matrix, never a model guess -- base models guess a uniform annual interval, miss "
            "the 12-year age threshold, treat a high-risk ship TYPE as automatically High Risk, and assume zero "
            "weighting points == Low Risk when Low Risk also demands a white flag, high RO & company and zero "
            "detentions (one detention blocks Low Risk yet two are needed to score an HRS point); the profession "
            "seeder declares the durable gap (determinism_ceiling=1.0) and this is the clean-room implementation "
            "that closes it; a result stays a candidate until verified against the live rule (currency)."),
    runner=_srp_runner))
