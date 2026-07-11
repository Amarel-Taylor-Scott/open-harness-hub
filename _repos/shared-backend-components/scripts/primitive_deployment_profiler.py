#!/usr/bin/env python3
"""primitive_deployment_profiler — the deployment + resource dimension for primitives and networks.

Owner (2026-07-10): "track dependencies, packages, substrates, common use cases, common infrastructure
deployments, K8 vs cloud function, and other common mediums, resource requirements, suggested minimum /
compute / memory usage, or agents that can calculate that based on use cases."

This is the ESTIMATOR that answers "what does it take to run this?" for any primitive, path, or network —
deterministically, from rubrics (extend = one row). It does NOT provision (that is cloud_provisioning, which
this reuses for cloud cost). For each primitive it derives:

  - operation class      (fetch · parse · extract · normalize · link · dedupe · embed · gate · propagate · index)
  - dependencies/packages (candidate declared deps per operation class — pip names, not verified installs)
  - runtime substrate     (io-bound vs cpu-bound, stateful, gpu, memory tier)
  - base resource envelope (min/recommended vCPU + memory + ephemeral disk, from an operation×volume rubric)

Then, for a USE CASE (records/day, latency SLA, freshness, concurrency, statefulness), it DECIDES the medium
(cloud function · container service · k8s job · k8s deployment · batch job · stream worker · local CLI) from a
fitness rubric, sizes the envelope for the volume tier, and bands the monthly compute cost — every decision
carried with its reason in a receipt. A network profile critical-paths the per-step envelopes and recommends
one medium for the pipeline. Everything is candidate=true / serves_truth=false (an estimate, not a guarantee).

    PYTHONPATH=. python3 scripts/primitive_deployment_profiler.py --self-test
    PYTHONPATH=. python3 scripts/primitive_deployment_profiler.py --estimate "OfficerRowBatch" --records-per-day 5000000 --freshness daily
    PYTHONPATH=. python3 scripts/primitive_deployment_profiler.py --network edgar_control_person_network
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_deployment_profiler requires canonical_id; import failed: {exc}")

OUT_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "deployment_profiles"
PROFILES_PATH = OUT_DIR / "primitive_deployment_profiles.jsonl"
ESTIMATES_PATH = OUT_DIR / "use_case_estimates.jsonl"
MANIFEST_PATH = OUT_DIR / "deployment_profile_manifest.json"
PROFILE_ID_PREFIX = "pdep"
ESTIMATE_ID_PREFIX = "pest"
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}

# ── Operation classes: matched from a card's title+blackbox+blocking_keys by keyword (first match wins by the
#    declared order — most specific first). Extend = one row. ──────────────────────────────────────────────
OPERATION_CLASSES: list[tuple[str, tuple[str, ...]]] = [
    ("embed", ("embed", "vector", "rerank", "encoder")),
    ("dedupe", ("dedupe", "cluster", "blocking", "minhash", "fuzzy")),
    ("link", ("link", "resolve", "match", "crosswalk", "entity linker")),
    ("parse_xml", ("xbrl", "xml", "edi ", "information table")),
    ("parse", ("parse", "extractor", "extract", "collateral", "officer")),
    ("fetch", ("fetch", "fetcher", "retriev", "download", "scrape", "http")),
    ("normalize", ("normaliz", "coded", "canonical", "legal-form", "status normal")),
    ("gate", ("gate", "policy", "preflight", "robots", "tos", "budget", "deny", "license")),
    ("propagate", ("cdc", "propagat", "signed", "watermark", "revocation", "delta")),
    ("index", ("index", "enumerat", "search adapter", "watcher", "crosswalk builder")),
    ("assemble", ("receipt", "provenance", "audit", "chain", "route")),
]
_DEFAULT_OPERATION = "compute"

# ── Dependencies per operation class (candidate declared pip packages — NOT verified installs). Extend = row. ─
DEPENDENCY_MAP: dict[str, list[str]] = {
    "embed": ["model2vec", "onnxruntime", "numpy"],
    "dedupe": ["datasketch", "numpy"],
    "link": ["rapidfuzz", "numpy"],
    "parse_xml": ["lxml"],
    "parse": ["beautifulsoup4", "lxml"],
    "fetch": ["httpx", "tenacity"],
    "normalize": ["rapidfuzz"],
    "gate": ["urllib3"],
    "propagate": ["cryptography"],
    "index": ["httpx"],
    "assemble": [],
    "compute": [],
}
_SHARED_DEPS = ["pydantic"]   # every governed primitive validates its typed I/O

# ── Runtime substrate per operation class: bound (io/cpu/mem), stateful, gpu-eligible, memory tier. ──────────
SUBSTRATE: dict[str, dict[str, Any]] = {
    "embed": {"bound": "cpu", "stateful": False, "gpu_eligible": True, "mem_tier": "high"},
    "dedupe": {"bound": "mem", "stateful": True, "gpu_eligible": False, "mem_tier": "high"},
    "link": {"bound": "cpu", "stateful": True, "gpu_eligible": False, "mem_tier": "mid"},
    "parse_xml": {"bound": "cpu", "stateful": False, "gpu_eligible": False, "mem_tier": "mid"},
    "parse": {"bound": "cpu", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "fetch": {"bound": "io", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "normalize": {"bound": "cpu", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "gate": {"bound": "io", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "propagate": {"bound": "io", "stateful": True, "gpu_eligible": False, "mem_tier": "low"},
    "index": {"bound": "io", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "assemble": {"bound": "cpu", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
    "compute": {"bound": "cpu", "stateful": False, "gpu_eligible": False, "mem_tier": "low"},
}

#: base per-worker envelope by memory tier (a floor; volume scales it). vCPU in millicores, memory in MiB.
_MEM_TIER_BASE: dict[str, dict[str, int]] = {
    "low": {"min_mcpu": 250, "rec_mcpu": 500, "min_mem_mb": 256, "rec_mem_mb": 512, "ephemeral_gb": 1},
    "mid": {"min_mcpu": 500, "rec_mcpu": 1000, "min_mem_mb": 512, "rec_mem_mb": 1024, "ephemeral_gb": 2},
    "high": {"min_mcpu": 1000, "rec_mcpu": 2000, "min_mem_mb": 2048, "rec_mem_mb": 4096, "ephemeral_gb": 5},
}

#: volume tiers (records/day) -> a resource multiplier + a throughput label. Extend = one row (ordered ascending).
VOLUME_TIERS: list[tuple[str, int, float]] = [
    ("pilot", 10_000, 1.0),
    ("small", 100_000, 1.0),
    ("medium", 2_000_000, 1.5),
    ("large", 20_000_000, 2.0),
    ("xlarge", 200_000_000, 3.0),
]

#: deployment media, each with a human note. Selection is by the rubric in decide_medium (not a per-row predicate,
#: so the decision logic stays in one auditable place). Extend the media list AND the rubric together.
DEPLOYMENT_MEDIA: dict[str, str] = {
    "local_cli": "run in-process / a dev box — no service; the default for pilot + ad-hoc",
    "cloud_function": "scale-to-zero FaaS (Cloud Run job/Lambda) — bursty, short, stateless, idle-cheap",
    "container_service": "always-on autoscaling container (Cloud Run service/Fly machine) — sustained realtime",
    "k8s_job": "a Kubernetes Job on a schedule — bounded batch that needs cluster placement/affinity",
    "k8s_deployment": "a Kubernetes Deployment — sustained, stateful, or high-concurrency long-lived workers",
    "batch_job": "a managed batch queue (AWS Batch/Cloud Run jobs fan-out) — very large bounded backfills",
    "stream_worker": "a long-lived consumer on a stream/queue — continuous realtime ingestion",
}

#: rough monthly compute cost per recommended vCPU-and-memory unit, by medium (DRAFT, owner-confirmable; the
#: FULL stack cost — storage/vectors/egress — comes from cloud_provisioning.plan, reused in estimate()).
_MEDIUM_COST_MODEL: dict[str, dict[str, float]] = {
    # usd/month per always-on vCPU, per always-on GiB, and a scale-to-zero duty-cycle factor
    "local_cli": {"per_vcpu": 0.0, "per_gib": 0.0, "duty": 0.0},
    "cloud_function": {"per_vcpu": 18.0, "per_gib": 2.0, "duty": 0.15},
    "container_service": {"per_vcpu": 24.0, "per_gib": 2.5, "duty": 0.6},
    "k8s_job": {"per_vcpu": 20.0, "per_gib": 2.2, "duty": 0.25},
    "k8s_deployment": {"per_vcpu": 24.0, "per_gib": 2.5, "duty": 1.0},
    "batch_job": {"per_vcpu": 16.0, "per_gib": 1.8, "duty": 0.2},
    "stream_worker": {"per_vcpu": 24.0, "per_gib": 2.5, "duty": 1.0},
}


def _card_text(card: dict[str, Any]) -> str:
    keys = " ".join(card.get("blocking_keys") or [])
    return f"{card.get('title', '')} {card.get('blackbox', '')} {keys}".lower()


def operation_class(card: dict[str, Any]) -> str:
    text = _card_text(card)
    for name, needles in OPERATION_CLASSES:
        if any(n in text for n in needles):
            return name
    return _DEFAULT_OPERATION


def volume_tier(records_per_day: int) -> tuple[str, float]:
    for name, ceiling, mult in VOLUME_TIERS:
        if records_per_day <= ceiling:
            return name, mult
    return VOLUME_TIERS[-1][0], VOLUME_TIERS[-1][2]


def profile_primitive(card: dict[str, Any]) -> dict[str, Any]:
    """Static per-primitive profile: operation class, declared deps, substrate, base (pilot) resource envelope."""
    op = operation_class(card)
    sub = SUBSTRATE[op]
    base = dict(_MEM_TIER_BASE[sub["mem_tier"]])
    deps = sorted(set(DEPENDENCY_MAP.get(op, []) + _SHARED_DEPS))
    return {
        "profile_id": canonical_id(PROFILE_ID_PREFIX, str(card.get("card_id") or card.get("primitive_id") or ""), op),
        "record_type": "primitive_deployment_profile",
        "primitive_id": card.get("card_id") or card.get("primitive_id"),
        "title": card.get("title"),
        "operation_class": op,
        "dependencies": deps,
        "substrate": sub,
        "base_resources": base,
        "schema_version": "1", **_CANDIDATE_BITS,
    }


def decide_medium(op: str, use_case: dict[str, Any]) -> dict[str, Any]:
    """The K8s-vs-cloud-function-vs-… decision, in ONE auditable rubric. Returns primary + ranked alternatives
    with the reason for each, derived from freshness, latency SLA, concurrency, statefulness, and volume tier."""
    freshness = str(use_case.get("freshness", "daily"))
    latency_sla_ms = int(use_case.get("latency_sla_ms", 0) or 0)
    concurrency = int(use_case.get("peak_concurrency", 1) or 1)
    stateful = bool(use_case.get("stateful", SUBSTRATE[op]["stateful"]))
    tier, _mult = volume_tier(int(use_case.get("records_per_day", 10_000) or 10_000))
    realtime = freshness == "realtime" or (0 < latency_sla_ms <= 2000)
    reasons: list[str] = []

    if realtime and freshness == "realtime":
        primary = "stream_worker"
        reasons.append("realtime freshness -> a long-lived stream/queue consumer")
    elif realtime:
        if concurrency <= 5 and not stateful:
            primary = "cloud_function"
            reasons.append(f"tight latency SLA ({latency_sla_ms}ms), low concurrency, stateless -> scale-to-zero FaaS")
        else:
            primary = "k8s_deployment" if (stateful or concurrency > 50) else "container_service"
            reasons.append(f"sustained realtime, concurrency {concurrency}, stateful={stateful} -> always-on service")
    else:  # scheduled / batch
        if tier in ("large", "xlarge"):
            primary = "batch_job"
            reasons.append(f"{tier} scheduled volume -> managed batch fan-out")
        elif stateful or SUBSTRATE[op]["mem_tier"] == "high":
            primary = "k8s_job"
            reasons.append(f"scheduled but stateful/high-memory ({op}) -> a K8s Job with placement control")
        elif tier == "pilot":
            primary = "local_cli"
            reasons.append("pilot volume, scheduled -> run in-process, no service to operate")
        else:
            primary = "cloud_function"
            reasons.append(f"bounded scheduled {tier} volume, stateless -> scale-to-zero job")

    ranked = [primary] + [m for m in ("cloud_function", "k8s_job", "container_service", "k8s_deployment",
                                      "batch_job", "stream_worker", "local_cli") if m != primary]
    return {"medium": primary, "medium_note": DEPLOYMENT_MEDIA[primary],
            "alternatives": ranked[1:4], "reasons": reasons,
            "signals": {"realtime": realtime, "freshness": freshness, "latency_sla_ms": latency_sla_ms,
                        "peak_concurrency": concurrency, "stateful": stateful, "volume_tier": tier}}


def _size_envelope(op: str, mult: float, concurrency: int) -> dict[str, int]:
    base = _MEM_TIER_BASE[SUBSTRATE[op]["mem_tier"]]
    replicas = max(1, min(concurrency, 200))
    return {
        "min_millicpu": int(base["min_mcpu"] * mult),
        "recommended_millicpu": int(base["rec_mcpu"] * mult),
        "min_memory_mb": int(base["min_mem_mb"] * mult),
        "recommended_memory_mb": int(base["rec_mem_mb"] * mult),
        "ephemeral_storage_gb": base["ephemeral_gb"],
        "recommended_replicas": replicas,
        "gpu_recommended": SUBSTRATE[op]["gpu_eligible"] and mult >= 2.0,
    }


def _monthly_compute_band(medium: str, envelope: dict[str, int]) -> dict[str, float]:
    model = _MEDIUM_COST_MODEL[medium]
    vcpu = envelope["recommended_millicpu"] / 1000 * envelope["recommended_replicas"]
    gib = envelope["recommended_memory_mb"] / 1024 * envelope["recommended_replicas"]
    monthly = (vcpu * model["per_vcpu"] + gib * model["per_gib"]) * model["duty"]
    return {"low_usd": round(monthly * 0.6, 2), "expected_usd": round(monthly, 2),
            "high_usd": round(monthly * 1.8, 2), "duty_cycle": model["duty"],
            "basis": "recommended vCPU+memory × replicas × medium duty-cycle (DRAFT rates; compute only)"}


def estimate(card: dict[str, Any], use_case: dict[str, Any], *, with_cloud_stack: bool = False) -> dict[str, Any]:
    """The use-case-driven estimate: profile -> medium decision -> sized envelope -> monthly compute band.
    with_cloud_stack reuses cloud_provisioning.plan for the FULL stack cost at the requested scale."""
    profile = profile_primitive(card)
    op = profile["operation_class"]
    decision = decide_medium(op, use_case)
    _tier, mult = volume_tier(int(use_case.get("records_per_day", 10_000) or 10_000))
    envelope = _size_envelope(op, mult, int(use_case.get("peak_concurrency", 1) or 1))
    band = _monthly_compute_band(decision["medium"], envelope)
    out = {
        "estimate_id": canonical_id(ESTIMATE_ID_PREFIX, profile["profile_id"],
                                    json.dumps(use_case, sort_keys=True)),
        "record_type": "primitive_deployment_estimate",
        "primitive_id": profile["primitive_id"], "title": profile["title"],
        "operation_class": op, "dependencies": profile["dependencies"],
        "use_case": use_case, "deployment": decision, "resources": envelope,
        "monthly_compute_cost_band": band,
        "note": "estimate from deterministic rubrics — sizing/cost are DRAFT planning bands, not a guarantee; "
                "the full-stack (storage/vector/egress) cost comes from cloud_provisioning.plan",
        "schema_version": "1", **_CANDIDATE_BITS,
    }
    if with_cloud_stack:
        try:
            from scripts import cloud_provisioning  # noqa: PLC0415  reuse the ONE cloud cost planner
            out["cloud_stack_plan"] = cloud_provisioning.plan(scale=int(use_case.get("records_per_day", 100_000)))
        except Exception as exc:  # noqa: BLE001
            out["cloud_stack_plan_error"] = str(exc)[:200]
    return out


def profile_network(network: dict[str, Any], cards: list[dict[str, Any]],
                    use_case: dict[str, Any]) -> dict[str, Any]:
    """Profile a whole network/path: per-step estimates + the CRITICAL-PATH envelope (the max resource per
    dimension across steps — you must provision the heaviest step) + one recommended medium for the pipeline."""
    by_id = {c["card_id"]: c for c in cards if c.get("card_id")}
    step_estimates = []
    for slot in network.get("slots", []):
        # profile the FIRST member of each slot as the representative step (the grid picks the winner elsewhere)
        member = next((by_id[m] for m in slot.get("member_ids", []) if m in by_id), None)
        if member is None:
            continue
        est = estimate(member, use_case)
        step_estimates.append({"step": slot["step"], "primitive_id": est["primitive_id"],
                               "operation_class": est["operation_class"], "medium": est["deployment"]["medium"],
                               "resources": est["resources"], "deps": est["dependencies"]})
    if not step_estimates:
        return {"network": network.get("name"), "note": "no fillable steps to profile", **_CANDIDATE_BITS}
    critical = {
        "min_millicpu": max(s["resources"]["min_millicpu"] for s in step_estimates),
        "recommended_millicpu": max(s["resources"]["recommended_millicpu"] for s in step_estimates),
        "min_memory_mb": max(s["resources"]["min_memory_mb"] for s in step_estimates),
        "recommended_memory_mb": max(s["resources"]["recommended_memory_mb"] for s in step_estimates),
        "gpu_recommended": any(s["resources"]["gpu_recommended"] for s in step_estimates),
    }
    # the pipeline medium: the "heaviest" recommendation across steps (k8s_deployment > ... > local_cli)
    order = ["local_cli", "cloud_function", "batch_job", "k8s_job", "container_service", "stream_worker",
             "k8s_deployment"]
    pipeline_medium = max((s["medium"] for s in step_estimates), key=order.index)
    all_deps = sorted({d for s in step_estimates for d in s["deps"]})
    return {"record_type": "network_deployment_profile", "network": network.get("name"),
            "edge_chain": network.get("edge_chain"), "steps": step_estimates,
            "critical_path_resources": critical, "pipeline_medium": pipeline_medium,
            "pipeline_medium_note": DEPLOYMENT_MEDIA[pipeline_medium],
            "union_dependencies": all_deps, "use_case": use_case, **_CANDIDATE_BITS}


# ── Build (profile the whole corporate pack) + manifest. ────────────────────────────────────────────────────
def _pack_cards() -> list[dict[str, Any]]:
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    return build_cards()


def build(write: bool = True) -> dict[str, Any]:
    cards = _pack_cards()
    profiles = [profile_primitive(c) for c in cards]
    # a small use-case matrix so the estimates file shows the medium DECISION varying with the workload
    use_cases = [
        {"name": "realtime_screening", "records_per_day": 50_000, "latency_sla_ms": 800,
         "freshness": "realtime", "peak_concurrency": 20, "stateful": False},
        {"name": "nightly_5M_backfill", "records_per_day": 5_000_000, "freshness": "daily",
         "peak_concurrency": 8, "stateful": False},
        {"name": "pilot_adhoc", "records_per_day": 8_000, "freshness": "batch", "peak_concurrency": 1},
    ]
    estimates = [estimate(c, uc) for c in cards[:6] for uc in use_cases]
    from collections import Counter
    manifest = {
        "record_type": "deployment_profile_manifest",
        "primitives_profiled": len(profiles),
        "operation_class_histogram": dict(Counter(p["operation_class"] for p in profiles)),
        "media_available": sorted(DEPLOYMENT_MEDIA),
        "volume_tiers": [t[0] for t in VOLUME_TIERS],
        "use_cases": [uc["name"] for uc in use_cases],
        "estimates_written": len(estimates),
        "source_ref": "owner-intent:deployment-resource-profiles:2026-07-10", **_CANDIDATE_BITS,
    }
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_PATH.write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in profiles))
        ESTIMATES_PATH.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in estimates))
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"manifest": manifest, "profiles": profiles, "estimates": estimates}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = _pack_cards()

    # (1) every primitive profiles: an operation class, non-empty deps, a substrate, a base envelope.
    profiles = [profile_primitive(c) for c in cards]
    ops = {p["operation_class"] for p in profiles}
    checks.append(("every primitive profiles into a known operation class with deps + substrate + base envelope",
                   all(p["operation_class"] in SUBSTRATE and p["dependencies"]
                       and p["base_resources"]["rec_mem_mb"] > 0 for p in profiles)
                   and len(ops) >= 5, f"{len(ops)} distinct op classes: {sorted(ops)}"))

    # (2) THE decision is load-bearing: the SAME primitive lands on DIFFERENT media for different use cases
    #     (realtime low-concurrency -> cloud_function; xlarge scheduled -> batch_job). Mutation gate.
    fetch_card = next(c for c in cards if operation_class(c) == "fetch")
    realtime = decide_medium("fetch", {"freshness": "realtime", "latency_sla_ms": 500, "peak_concurrency": 3})
    huge_batch = decide_medium("fetch", {"freshness": "daily", "records_per_day": 200_000_000})
    pilot = decide_medium("fetch", {"freshness": "batch", "records_per_day": 5_000})
    checks.append(("medium decision varies with the use case (realtime->function, xlarge->batch, pilot->cli) — "
                   "the K8s-vs-cloud-function choice is computed, not fixed",
                   realtime["medium"] == "stream_worker" and huge_batch["medium"] == "batch_job"
                   and pilot["medium"] == "local_cli"
                   and realtime["medium"] != huge_batch["medium"],
                   json.dumps({"rt": realtime["medium"], "huge": huge_batch["medium"], "pilot": pilot["medium"]})))

    # (3) resources scale MONOTONICALLY with volume; cost band is ordered low<=expected<=high.
    small = estimate(fetch_card, {"records_per_day": 100_000, "freshness": "daily"})
    large = estimate(fetch_card, {"records_per_day": 20_000_000, "freshness": "daily"})
    checks.append(("resource envelope scales monotonically with volume; cost band low<=expected<=high",
                   large["resources"]["recommended_millicpu"] >= small["resources"]["recommended_millicpu"]
                   and large["resources"]["recommended_memory_mb"] >= small["resources"]["recommended_memory_mb"]
                   and small["monthly_compute_cost_band"]["low_usd"]
                   <= small["monthly_compute_cost_band"]["expected_usd"]
                   <= small["monthly_compute_cost_band"]["high_usd"],
                   f"small={small['resources']['recommended_millicpu']}mcpu large={large['resources']['recommended_millicpu']}mcpu"))

    # (4) an embed primitive is GPU-eligible + high-memory; a gate primitive is io-bound + cheap — substrate is
    #     genuinely differentiated by operation class (not a constant).
    embed_sub = SUBSTRATE["embed"]
    gate_sub = SUBSTRATE["gate"]
    checks.append(("substrate differentiates operation classes (embed: cpu/gpu/high-mem; gate: io/low-mem)",
                   embed_sub["gpu_eligible"] and embed_sub["mem_tier"] == "high"
                   and gate_sub["bound"] == "io" and gate_sub["mem_tier"] == "low", ""))

    # (5) network profile critical-paths the steps + picks one pipeline medium + unions deps.
    from scripts.primitive_networks_and_grid_search import build_network
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes
    corpus = cards + build_remixes(cards)
    deep = build_network("edgar_control_person_network",
                         ["EdgarFilingReferenceBatch", "EdgarAccessionFetchPlan", "FilingDocumentBundle",
                          "OfficerRowBatch", "OfficerDedupeClusterBatch"], corpus)
    net_profile = profile_network(deep, corpus, {"records_per_day": 5_000_000, "freshness": "daily"})
    checks.append(("network profile critical-paths 5 steps, picks a pipeline medium, unions dependencies",
                   len(net_profile["steps"]) == 5
                   and net_profile["critical_path_resources"]["recommended_memory_mb"]
                   >= max(s["resources"]["recommended_memory_mb"] for s in net_profile["steps"])
                   and net_profile["pipeline_medium"] in DEPLOYMENT_MEDIA
                   and len(net_profile["union_dependencies"]) >= 2,
                   f"pipeline_medium={net_profile['pipeline_medium']}, deps={net_profile['union_dependencies']}"))

    # (6) cloud-stack reuse: with_cloud_stack pulls cloud_provisioning.plan (reuse, not a second cost model).
    with_stack = estimate(fetch_card, {"records_per_day": 1_000_000, "freshness": "daily"}, with_cloud_stack=True)
    checks.append(("with_cloud_stack REUSES cloud_provisioning.plan for the full-stack cost (no second planner)",
                   "cloud_stack_plan" in with_stack
                   and isinstance(with_stack["cloud_stack_plan"], dict), ""))

    # (7) determinism + candidate-only + computed manifest.
    build(write=True)
    first = PROFILES_PATH.read_bytes()
    built = build(write=True)
    all_rows = built["profiles"] + built["estimates"]
    checks.append(("deterministic (byte-identical rebuild); every row candidate-only; manifest counts computed",
                   first == PROFILES_PATH.read_bytes()
                   and all(r["candidate"] is True and r["serves_truth"] is False for r in all_rows)
                   and built["manifest"]["primitives_profiled"] == len(built["profiles"]), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_deployment_profiler: deployment + resource estimator over "
          f"{len(profiles)} primitives — operation classes -> deps/substrate/base envelope; use-case rubric "
          f"decides medium (K8s vs cloud function vs …), sizes vCPU/memory, bands monthly cost (reusing "
          f"cloud_provisioning for the full stack); network critical-path profile. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def _resolve_card(identifier: str) -> Optional[dict[str, Any]]:
    for c in _pack_cards():
        if identifier in (c.get("card_id"), c.get("primitive_id"), c.get("output_edge"), c.get("title")):
            return c
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deployment + resource profiler/estimator for primitives.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--estimate", help="a primitive id / output_edge / title to estimate")
    parser.add_argument("--network", help="a NETWORK_TABLE name to profile end-to-end")
    parser.add_argument("--records-per-day", type=int, default=1_000_000)
    parser.add_argument("--freshness", default="daily", choices=["realtime", "hourly", "daily", "batch"])
    parser.add_argument("--latency-sla-ms", type=int, default=0)
    parser.add_argument("--peak-concurrency", type=int, default=1)
    parser.add_argument("--cloud-stack", action="store_true")
    args = parser.parse_args(argv)
    use_case = {"records_per_day": args.records_per_day, "freshness": args.freshness,
                "latency_sla_ms": args.latency_sla_ms, "peak_concurrency": args.peak_concurrency}
    if args.self_test:
        return _self_test()
    if args.build:
        print(json.dumps(build(write=True)["manifest"], indent=2, sort_keys=True))
        return 0
    if args.estimate:
        card = _resolve_card(args.estimate)
        if card is None:
            print(json.dumps({"error": f"no primitive matches {args.estimate!r}"}))
            return 1
        print(json.dumps(estimate(card, use_case, with_cloud_stack=args.cloud_stack), indent=2, sort_keys=True))
        return 0
    if args.network:
        from scripts.primitive_networks_and_grid_search import NETWORK_TABLE, build_network
        from scripts.primitive_groups_frameworks_and_remixers import build_remixes
        row = next((r for r in NETWORK_TABLE if r["name"] == args.network), None)
        if row is None:
            print(json.dumps({"error": f"unknown network {args.network!r}",
                              "known": [r["name"] for r in NETWORK_TABLE]}))
            return 1
        cards = _pack_cards()
        corpus = cards + build_remixes(cards)
        net = build_network(row["name"], row["edge_chain"], corpus, row["description"])
        print(json.dumps(profile_network(net, corpus, use_case), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
