#!/usr/bin/env python3
"""check_profession_calculators -- proof for the DETERMINISTIC profession calculators that CLOSE the
determinism_ceiling=1.0 capability candidates the profession_capability_seeder only DECLARES. Validates the
FMCSA Hours-of-Service calculator against the four core CFR limits (11h drive / 14h window / 30-min break /
60-70h cycle), its faithful handling of the nuances a base model gets wrong (off-duty CONSUMES the 14h window;
a sub-30-min pause does NOT reset the 8h break clock; on-duty-not-driving DOES satisfy the break; a 34h restart
resets the cycle; 60h/7-day vs 70h/8-day), determinism, candidate-not-truth, and lineage to the declared
candidate. Adding deterministic calculators is how a "gap candidate" advances toward promotion-readiness.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_profession_calculators.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.seeds import all_seeds
from src.teleon.seeds.profession_calculators import IMPLEMENTS, controlled_substance, hours_of_service, ship_risk_profile
from src.teleon.seeds.profession_capability_seeder import seed_professions

_H = 60  # minutes per hour
_HOS = "commercial-driver-hours-of-service"
_HOS_CAND = "commercial-driver-hours-of-service-rule"
_CSA = "pharmacist-controlled-substance-schedule"
_CSA_CAND = "pharmacist-controlled-substance-schedule"
_SRP = "seafarer-port-state-control"
_SRP_CAND = "seafarer-port-state-control"


def _seg(status, hr=0, mn=0):
    return dict(status=status, minutes=hr * _H + mn)


def _self_test():
    fails = []

    def ck(name, ok, detail=""):
        flag = "ok" if ok else "FAIL"
        tail = (": " + detail) if (detail and not ok) else ""
        print("  [" + flag + "] " + name + tail)
        if not ok:
            fails.append(name)

    # lineage: every calculator closes a DECLARED determinism=1.0 candidate (impl -> candidate; lossless)
    cands = seed_professions()
    cand_slots = set(c["capability_slot"] for c in cands)
    for impl, cand in IMPLEMENTS.items():
        ck("calculator " + impl + " closes declared candidate " + cand, cand in cand_slots, str(sorted(cand_slots))[:160])
    hos_cand = None
    for c in cands:
        if c["capability_slot"] == _HOS_CAND:
            hos_cand = c
            break
    ck("the HOS candidate is declared deterministic (ceiling 1.0)",
       bool(hos_cand) and hos_cand["determinism_ceiling"] == 1.0, str(hos_cand))

    # registered as a governed seed that never serves truth and carries lineage
    seed = None
    for s in all_seeds():
        if s.slot == _HOS:
            seed = s
            break
    ck("HOS is a registered CapabilitySeed", seed is not None)
    ck("the seed is declared deterministic (ceiling 1.0)", bool(seed) and seed.determinism_ceiling == 1.0)
    run0 = seed.run(dict(segments=[])) if seed else dict(serves_truth=None, output=dict())
    ck("running the seed never serves truth (candidate)", run0["serves_truth"] is False)
    ck("the seed result carries lineage back to the candidate it closes",
       run0["output"].get("implements_candidate") == _HOS_CAND)

    # correctness: 11h driving limit (compliant -> 30-min break binds first; over-limit -> violation)
    A = hours_of_service(dict(segments=[_seg("driving", 6)]))
    ck("compliant mid-shift can drive; 30-min break binds first at 2h remaining",
       A["can_drive_now"] and not A["violations"] and A["remaining_drive_min"] == 2 * _H
       and A["limiting_rule"] == "break_30min", str(A))
    B = hours_of_service(dict(segments=[_seg("driving", 11, 30)]))
    ck("over the 11h driving limit -> violation, cannot drive, 0 remaining",
       "drive_limit_11h" in B["violations"] and not B["can_drive_now"] and B["remaining_drive_min"] == 0, str(B))

    # 14h window: off-duty CONSUMES the window (does NOT extend it) -- 8h drive + 7h off = 15h elapsed
    C = hours_of_service(dict(segments=[_seg("driving", 8), _seg("off_duty", 7)]))
    ck("off-duty consumes the 14h window (not extends): 8h drive + 7h off -> window violation, no drive violation",
       "window_limit_14h" in C["violations"] and "drive_limit_11h" not in C["violations"]
       and not C["can_drive_now"], str(C))

    # 30-min break: required at 8h driving; on-duty-not-driving satisfies it; a sub-30 pause does NOT reset it
    D1 = hours_of_service(dict(segments=[_seg("driving", 8)]))
    ck("8 cumulative driving hours with no break -> 30-min break required (cannot drive, no violation yet)",
       not D1["can_drive_now"] and D1["limiting_rule"] == "break_30min" and not D1["violations"]
       and "break" in D1["required_action"], str(D1))
    D2 = hours_of_service(dict(segments=[_seg("driving", 8), _seg("on_duty_not_driving", 0, 30), _seg("driving", 2)]))
    ck("on-duty-not-driving 30-min satisfies the break (post-2020 rule); driving resumes, 11h limit then binds",
       D2["can_drive_now"] and "break_30min" not in D2["violations"]
       and D2["limiting_rule"] == "drive_limit_11h" and D2["remaining_drive_min"] == 1 * _H, str(D2))
    D3 = hours_of_service(dict(segments=[_seg("driving", 8), _seg("off_duty", 0, 20), _seg("driving", 0, 30)]))
    ck("a sub-30-min pause does NOT reset the 8h break clock -> break violation (redteam)",
       "break_30min" in D3["violations"], str(D3))

    # 60/70-hour cycle + 34h restart; 60h/7-day distinct from 70h/8-day
    E1 = hours_of_service(dict(segments=[_seg("driving", 1, 30)], prior_cycle_onduty_minutes=69 * _H, cycle_days=8))
    ck("70h/8-day cycle: 69h prior + 1h30 -> cycle violation, cannot drive",
       "cycle_limit" in E1["violations"] and not E1["can_drive_now"], str(E1))
    E2 = hours_of_service(dict(segments=[_seg("driving", 1, 30)], prior_cycle_onduty_minutes=69 * _H, cycle_days=8, restart_taken=True))
    ck("a 34h restart clears the cycle -> compliant again",
       "cycle_limit" not in E2["violations"] and E2["can_drive_now"], str(E2))
    E3 = hours_of_service(dict(segments=[_seg("driving", 1, 30)], prior_cycle_onduty_minutes=59 * _H, cycle_days=7))
    ck("60h/7-day cycle is distinct from 70h/8-day (59h + 1h30 -> 60h violation)",
       "cycle_limit" in E3["violations"] and E3["cycle_limit_min"] == 60 * _H, str(E3))

    # determinism + robustness (mirrors the x=1 determinism probe in check_capability_seeds)
    pay = dict(segments=[_seg("driving", 4), _seg("on_duty_not_driving", 2)])
    ck("deterministic (same input -> identical output)", hours_of_service(pay) == hours_of_service(pay))
    G = hours_of_service(dict(x=1))
    ck("robust to an unrelated payload (empty timeline -> can drive, no violations)",
       G["can_drive_now"] and not G["violations"] and G["remaining_drive_min"] == 480)
    ck("robust to a None payload", hours_of_service(None)["can_drive_now"])
    ck("negative/garbage durations are clamped to 0",
       hours_of_service(dict(segments=[_seg("driving", -5)]))["driving_used_min"] == 0)

    # -- DEA controlled-substance schedule (21 CFR 1308 lookup + 1306 prescribing/refill consequences) -------
    csa_seed = None
    for s_ in all_seeds():
        if s_.slot == _CSA:
            csa_seed = s_
            break
    ck("controlled-substance-schedule is a registered CapabilitySeed", csa_seed is not None)
    ck("the CSA seed is declared deterministic (ceiling 1.0)", bool(csa_seed) and csa_seed.determinism_ceiling == 1.0)
    csa_run0 = csa_seed.run(dict(substance="oxycodone")) if csa_seed else dict(serves_truth=None, output=dict())
    ck("running the CSA seed never serves truth (candidate)", csa_run0["serves_truth"] is False)
    ck("the CSA seed result carries lineage back to the candidate it closes",
       csa_run0["output"].get("implements_candidate") == _CSA_CAND)

    # substance lookup by generic and by brand alias; Schedule I is not prescribable
    ox = controlled_substance(dict(substance="oxycodone"))
    ck("oxycodone -> Schedule II, prescribable, NO refills (1306.12)",
       ox["schedule"] == "II" and ox["prescribable"] and ox["refills_allowed"] is False and ox["max_refills"] == 0, str(ox))
    xan = controlled_substance(dict(substance="Xanax"))
    ck("brand 'Xanax' resolves to alprazolam -> Schedule IV, 5 refills / 6 months",
       xan["matched_substance"] == "alprazolam" and xan["schedule"] == "IV"
       and xan["max_refills"] == 5 and xan["refill_window_months"] == 6, str(xan))
    her = controlled_substance(dict(substance="heroin"))
    ck("Schedule I (heroin) is NOT prescribable -> dispense not permitted",
       her["schedule"] == "I" and her["prescribable"] is False and her["dispense_permitted"] is False, str(her))

    # the consequence logic a base model botches: a Schedule II refill request is refused; an initial fill is fine
    ii_refill = controlled_substance(dict(substance="fentanyl", requested_refills=1))
    ck("Schedule II refill request (1) is REFUSED (1306.12: no refills) -> dispense not permitted",
       ii_refill["refill_request_permitted"] is False and ii_refill["dispense_permitted"] is False, str(ii_refill))
    ii_zero = controlled_substance(dict(substance="fentanyl", requested_refills=0))
    ck("Schedule II with 0 refills (initial fill) IS permitted",
       ii_zero["refill_request_permitted"] is True and ii_zero["dispense_permitted"] is True, str(ii_zero))

    # Schedule III/IV: 5 refills ok, 6 not (1306.22 cap); past the 6-month window a refill is refused
    iv_ok = controlled_substance(dict(schedule="IV", requested_refills=5))
    iv_over = controlled_substance(dict(schedule="IV", requested_refills=6))
    ck("Schedule IV permits 5 refills but not 6 (1306.22 cap)",
       iv_ok["refill_request_permitted"] is True and iv_over["refill_request_permitted"] is False, str(iv_over))
    iii_expired = controlled_substance(dict(schedule="III", requested_refills=2, months_since_issue=7))
    ck("past the 6-month window a Schedule III refill is refused even with refills remaining",
       iii_expired["within_refill_window"] is False and iii_expired["dispense_permitted"] is False, str(iii_expired))

    # Schedule V is NOT capped at the III/IV 5-refill limit (the conflation base models make) -- as authorized
    v_many = controlled_substance(dict(substance="pregabalin", requested_refills=9))
    ck("Schedule V is NOT capped at the III/IV 5-refill limit (refills as authorized) -- 9 permitted (redteam)",
       v_many["schedule"] == "V" and v_many["max_refills"] is None
       and v_many["refill_request_permitted"] is True and v_many["otc_possible"] is True, str(v_many))

    # schedule designators normalize; an unknown substance is FLAGGED, never guessed
    ck("schedule designators normalize: 'C-II' and '2' -> Schedule II",
       controlled_substance(dict(schedule="C-II"))["schedule"] == "II"
       and controlled_substance(dict(schedule="2"))["schedule"] == "II")
    unk = controlled_substance(dict(substance="acetaminophen"))
    ck("an unscheduled/unknown substance is FLAGGED (schedule_known False), never guessed",
       unk["schedule_known"] is False and unk["dispense_permitted"] is None, str(unk))

    # determinism + robustness (mirrors the determinism probe used for the HOS calculator)
    pay2 = dict(substance="lorazepam", requested_refills=3, months_since_issue=2)
    ck("CSA deterministic (same input -> identical output)", controlled_substance(pay2) == controlled_substance(pay2))
    ck("CSA robust to a None payload (unknown schedule, nothing guessed)",
       controlled_substance(None)["schedule_known"] is False)

    # -- Paris/Tokyo MoU Port State Control: Ship Risk Profile -> inspection priority/interval --------------
    srp_seed = None
    for s2 in all_seeds():
        if s2.slot == _SRP:
            srp_seed = s2
            break
    ck("port-state-control ship-risk-profile is a registered CapabilitySeed", srp_seed is not None)
    ck("the SRP seed is declared deterministic (ceiling 1.0)", bool(srp_seed) and srp_seed.determinism_ceiling == 1.0)
    srp_run0 = srp_seed.run(dict(ship_type="oil tanker")) if srp_seed else dict(serves_truth=None, output=dict())
    ck("running the SRP seed never serves truth (candidate)", srp_run0["serves_truth"] is False)
    ck("the SRP seed result carries lineage back to the candidate it closes",
       srp_run0["output"].get("implements_candidate") == _SRP_CAND)
    srp_cand = None
    for c in cands:
        if c["capability_slot"] == _SRP_CAND:
            srp_cand = c
            break
    ck("the SRP candidate is declared deterministic (ceiling 1.0)",
       bool(srp_cand) and srp_cand["determinism_ceiling"] == 1.0, str(srp_cand))

    # High Risk Ship: a 5+ weighting-point ship -> High; overdue (>upper) -> Priority I (must be inspected)
    hrs = ship_risk_profile(dict(ship_type="oil tanker", age_years=20, flag_list="black",
                                 company_performance="very low", months_since_last_inspection=7))
    ck("oil tanker(2)+age>12(1)+black(1)+low company(1)=5 -> High Risk Ship; 7mo>6 -> Priority I",
       hrs["risk_profile"] == "high" and hrs["total_weighting_points"] == 5
       and hrs["priority"] == "I" and hrs["inspection_due"] is True, str(hrs))

    # the headline nuance: a high-risk ship TYPE alone does NOT prevent Low Risk (type/age score points only
    # toward HRS; the Low-Risk gate excludes type & age)
    low_type = ship_risk_profile(dict(ship_type="oil tanker", age_years=5, flag_list="white",
                                      ro_performance="high", company_performance="high",
                                      months_since_last_inspection=30))
    ck("a high-risk ship TYPE alone (clean white-flag record) is Low Risk -- type adds HRS points but does NOT block Low Risk",
       low_type["risk_profile"] == "low" and low_type["total_weighting_points"] == 2
       and low_type["priority"] == "II", str(low_type))

    # zero weighting points != Low Risk: a grey-flag ship is Standard, not Low (Low needs a WHITE flag)
    grey = ship_risk_profile(dict(ship_type="general cargo", age_years=5, flag_list="grey",
                                  ro_performance="high", company_performance="high"))
    ck("a grey-flag ship with ZERO weighting points is Standard, not Low (Low Risk requires a white flag) (redteam)",
       grey["risk_profile"] == "standard" and grey["total_weighting_points"] == 0
       and grey["low_risk_eligible"] is False, str(grey))

    # detention asymmetry: ONE detention blocks Low Risk but scores NO HRS point; TWO score the point
    det1 = ship_risk_profile(dict(ship_type="general cargo", age_years=5, flag_list="white",
                                  ro_performance="high", company_performance="high", detentions_36mo=1))
    det2 = ship_risk_profile(dict(ship_type="general cargo", age_years=5, flag_list="white",
                                  ro_performance="high", company_performance="high", detentions_36mo=2))
    ck("one detention blocks Low Risk (->Standard) yet scores NO HRS point; two detentions score the point (redteam)",
       det1["risk_profile"] == "standard" and det1["total_weighting_points"] == 0
       and det2["total_weighting_points"] == 1, str([det1["total_weighting_points"], det2["total_weighting_points"]]))

    # the age point binds ABOVE 12 years (12 -> 0, 13 -> 1), not at 15/20
    age12 = ship_risk_profile(dict(ship_type="general cargo", age_years=12))
    age13 = ship_risk_profile(dict(ship_type="general cargo", age_years=13))
    ck("the age point binds ABOVE 12 years (12 -> 0, 13 -> 1), not at 15/20",
       age12["weighting_points"]["age"] == 0 and age13["weighting_points"]["age"] == 1, str([age12["weighting_points"], age13["weighting_points"]]))

    # inspection intervals differ by profile (models guess a uniform annual interval)
    ck("intervals differ by profile: HRS 5-6mo, SRS 10-12mo, LRS 24-36mo",
       hrs["inspection_interval_months"] == dict(lower=5, upper=6)
       and grey["inspection_interval_months"] == dict(lower=10, upper=12)
       and low_type["inspection_interval_months"] == dict(lower=24, upper=36), str(hrs["inspection_interval_months"]))

    # Priority bands within the SRS window + the not-yet-due case + overriding factor -> Priority I
    srs_open = ship_risk_profile(dict(ship_type="container", age_years=8, flag_list="grey", months_since_last_inspection=11))
    srs_over = ship_risk_profile(dict(ship_type="container", age_years=8, flag_list="grey", months_since_last_inspection=13))
    srs_early = ship_risk_profile(dict(ship_type="container", age_years=8, flag_list="grey", months_since_last_inspection=9))
    ck("SRS window: 11mo -> Priority II (may), 13mo -> Priority I (must), 9mo -> not yet due",
       srs_open["priority"] == "II" and srs_open["inspection_due"] is True and srs_over["priority"] == "I"
       and srs_early["priority"] is None and srs_early["inspection_due"] is False,
       str([srs_open["priority"], srs_over["priority"], srs_early["priority"]]))
    overr = ship_risk_profile(dict(ship_type="general cargo", age_years=3, flag_list="white",
                                   ro_performance="high", company_performance="high", overriding_factor=True))
    ck("an overriding factor forces Priority I regardless of the window",
       overr["priority"] == "I" and overr["inspection_due"] is True, str(overr))

    # determinism + robustness (mirrors the determinism probe used for the other calculators)
    pay3 = dict(ship_type="bulk carrier", age_years=14, flag_list="grey", detentions_36mo=1, months_since_last_inspection=11)
    ck("SRP deterministic (same input -> identical output)", ship_risk_profile(pay3) == ship_risk_profile(pay3))
    ck("SRP robust to a None payload (no crash; not yet due without a date)",
       ship_risk_profile(None)["risk_profile"] == "standard" and ship_risk_profile(None)["priority"] is None)
    ck("garbage deficiency entries are ignored, not crashed",
       ship_risk_profile(dict(inspection_deficiencies=["x", None, 7]))["weighting_points"]["deficiencies"] == 1)

    n_impl = len(IMPLEMENTS)
    if not fails:
        print("")
        print("PASS - check_profession_calculators: " + str(n_impl) + " deterministic profession calculator(s) "
              "implement determinism=1.0 candidates the profession seeder declares (FMCSA HOS: 11h drive / 14h "
              "window / 30-min break / 60-70h cycle, with off-duty-consumes-window + sub-30-no-reset + restart "
              "nuances; DEA CSA: schedule I-V lookup + the prescribing/refill consequences -- Schedule II no refills, "
              "III/IV 5-refills/6-months, Schedule V NOT capped at that limit -- 21 CFR 1308/1306; Paris/Tokyo MoU PSC: the Ship Risk Profile weighting matrix -> High/Standard/Low + inspection interval & Priority I/II, with the high-risk-TYPE-does-not-block-Low-Risk and one-detention-blocks-Low-yet-two-score-a-point nuances); each is a "
              "clean-room If-Statement over public regulation, lineage-linked to its candidate, and NEVER "
              "serves truth (a candidate until verified against the live rule).")
    else:
        print("")
        print(str(len(fails)) + " FAILURES: " + str(fails))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_profession_calculators.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
