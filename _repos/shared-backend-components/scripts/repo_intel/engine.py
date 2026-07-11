"""scripts.repo_intel.engine — snapshot store + classifier + trend/fit/risk scorers + intake-decision engine +
weekly report. Pure + deterministic (injected `now`, snapshot store path). No network, no GitHub token here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
_A = _resource("architecture")
_FIXTURE = _resource("fixtures") / "repo_intel" / "weekly_github_trend_watch_sample.json"
DEFAULT_STORE = (_REPO / ".agent") / "repo-intel" / "snapshots.jsonl"
DECISIONS = ("ignore", "watch", "classify_only", "intake_as_skill_candidate", "intake_as_tool_candidate",
             "intake_as_harness_candidate", "intake_as_template_candidate", "intake_as_context_candidate",
             "propose_teleon_integration", "propose_baltor_integration", "quarantine")
#: artifact-type per primary hub (for candidate decision naming)
_HUB_ARTIFACT = {"openskillshub": "skill", "opentoolshub": "tool", "openhubforai": "harness",
                 "opencontexthub": "context", "shared-template-registry": "template"}
_OK_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0", "ISC"}


def _load(name: str) -> dict:
    return json.loads((_A / name).read_text(encoding="utf-8"))


def load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def repo_id(full_name: str) -> str:
    return "gh:" + full_name.strip().lower()


def _hash(d: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


# ── snapshot store (append-only JSONL; weekly growth comes from STORED snapshots) ──
def append_snapshot(repo: dict, *, now: str, store: Path = DEFAULT_STORE, source_method: str = "fixture",
                    source_confidence: str = "owner_provided_unverified") -> dict:
    rid = repo_id(repo["full_name"])
    snap = {"schema_version": "RepoSnapshot", "repo_id": rid, "full_name": repo["full_name"],
            "html_url": repo.get("html_url", f"https://github.com/{repo['full_name']}"),
            "description": repo.get("description", ""), "topics": repo.get("topics", []),
            "language_primary": repo.get("language_primary", ""), "license": repo.get("license", ""),
            "stars_count": int(repo.get("stars_count", 0)), "forks_count": int(repo.get("forks_count", 0)),
            "archived": bool(repo.get("archived", False)), "collected_at": now,
            "source_method": source_method, "source_confidence": source_confidence}
    snap["snapshot_id"] = _hash({"r": rid, "t": now, "s": snap["stars_count"]})
    snap["raw_metadata_hash"] = _hash(repo)
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap) + "\n")
    return snap


def snapshots_for(rid: str, *, store: Path = DEFAULT_STORE) -> list[dict]:
    if not store.exists():
        return []
    out = [json.loads(ln) for ln in store.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [s for s in out if s["repo_id"] == rid]


def compute_trend(repo: dict, *, store: Path = DEFAULT_STORE) -> dict:
    """Trend signal from STORED snapshots. <2 snapshots → confidence LOW (delta from owner-reported, unverified)."""
    rid = repo_id(repo["full_name"])
    snaps = sorted(snapshots_for(rid, store=store), key=lambda s: s["collected_at"])
    cur = snaps[-1] if snaps else None
    prev = snaps[-2] if len(snaps) >= 2 else None
    if prev is not None:
        delta = cur["stars_count"] - prev["stars_count"]
        conf = "high"
    else:
        delta = repo.get("owner_reported_growth_7d")  # unverified
        conf = "low"
    # MOVEMENT drives the score — a high-star repo with no recent delta scores ~0 (stars are not proof).
    score = 0.0
    if conf == "high":
        moved = max(0.0, delta) / 1000.0
        score = moved + (0.1 if moved > 0 and cur and not cur.get("archived") else 0.0)  # tiny recency bonus only WITH movement
    elif delta:
        score = (delta / 1000.0) * 0.4  # discount unverified owner-reported growth
    return {"schema_version": "RepoTrendSignal", "repo_id": rid,
            "current_snapshot_id": cur["snapshot_id"] if cur else None,
            "previous_snapshot_id": prev["snapshot_id"] if prev else None,
            "stars_delta_7d": delta, "trend_score": round(score, 3), "confidence": conf,
            "note": "delta from stored snapshots" if conf == "high" else "owner-reported, unverified — needs a 2nd stored snapshot"}


# ── classifier (deterministic keyword → hub; LLM advisory only, not used here) ──
def classify(repo: dict) -> dict:
    text = (repo.get("description", "") + " " + " ".join(repo.get("topics", []))).lower()
    hubs: list[str] = []
    low_priority = False
    for rule in _load("repo_hub_mapping_policy.json")["rules"]:
        if any(k in text for k in rule["any"]):
            for h in rule["hubs"]:
                if h not in hubs:
                    hubs.append(h)
            if rule.get("priority") == "low":
                low_priority = True
    primary = hubs[0] if hubs else "unclassified"
    artifact = _HUB_ARTIFACT.get(primary, "tool" if primary in ("teleon", "baltor") else "unknown")
    return {"schema_version": "RepoClassification", "repo_id": repo_id(repo["full_name"]),
            "portfolio_hubs": hubs or ["unclassified"], "primary_hub": primary, "artifact_type": artifact,
            "low_priority": low_priority, "confidence": "medium" if hubs else "low", "requires_human_review": True}


def trend_score(repo: dict, *, store: Path = DEFAULT_STORE) -> float:
    return compute_trend(repo, store=store)["trend_score"]


def fit_score(repo: dict, classification: dict) -> dict:
    hubs = set(classification["portfolio_hubs"])
    return {"teleon": "teleon" in hubs, "baltor": "baltor" in hubs,
            "open_hub": bool(hubs & {"openskillshub", "opentoolshub", "openhubforai", "opencontexthub", "shared-template-registry"}),
            "low_priority": classification.get("low_priority", False)}


def risk(repo: dict) -> dict:
    lic = (repo.get("license") or "").strip()
    quarantine_reasons = []
    if not lic:
        quarantine_reasons.append("no_license")
    elif lic not in _OK_LICENSES:
        quarantine_reasons.append("license_unknown_or_restrictive")
    if repo.get("archived"):
        quarantine_reasons.append("archived")
    return {"schema_version": "RepoRiskReport", "repo_id": repo_id(repo["full_name"]), "license": lic,
            "license_ok": lic in _OK_LICENSES, "archived": bool(repo.get("archived")),
            "quarantine": bool(quarantine_reasons), "quarantine_reasons": quarantine_reasons}


# ── intake decision engine (NEVER auto-active) ──
def intake_decision(repo: dict, classification: dict, trend: dict, risk_report: dict, *, now: str) -> dict:
    pol = _load("repo_intake_policy.json")
    rid = repo_id(repo["full_name"])
    reasons: list[str] = []
    if risk_report["quarantine"]:
        decision = "quarantine"
        reasons = [f"risk: {r}" for r in risk_report["quarantine_reasons"]]
    elif classification["primary_hub"] == "unclassified":
        decision = "watch"; reasons = ["no confident hub mapping yet"]
    else:
        ph = classification["primary_hub"]
        if ph == "teleon":
            decision = "propose_teleon_integration"
        elif ph == "baltor":
            decision = "propose_baltor_integration"
        else:
            decision = f"intake_as_{_HUB_ARTIFACT.get(ph, 'tool')}_candidate"
        reasons = [f"classified → {ph}", f"trend {trend['confidence']} (score {trend['trend_score']})",
                   "discovery is not trust — candidate only, requires proof_to_promote"]
        if classification.get("low_priority"):
            reasons.append("low priority (media/voice) — watch unless prioritized")
    art = _HUB_ARTIFACT.get(classification["primary_hub"], "")
    proof = list(pol["proof_to_promote_default"]) + pol.get("candidate_requires", {}).get(art, [])
    return {"schema_version": "RepoIntakeDecision", "repo_id": rid, "decision": decision, "reasons": reasons,
            "hub_mappings": classification["portfolio_hubs"], "proof_to_promote": sorted(set(proof)),
            "local_eval_required": decision.startswith("intake_") or decision.startswith("propose_"),
            "sandbox_required": decision in ("intake_as_tool_candidate", "intake_as_skill_candidate"),
            "owner": "repo-intel-agent", "next_review_at": now}


# ── weekly report ──
def weekly_report(*, now: str, store: Path = DEFAULT_STORE, top_n: int = 10) -> dict:
    fx = load_fixture()
    rows = []
    for repo in fx["repos"]:
        c = classify(repo); t = compute_trend(repo, store=store); r = risk(repo)
        d = intake_decision(repo, c, t, r, now=now)
        rows.append({"full_name": repo["full_name"], "primary_hub": c["primary_hub"], "hubs": c["portfolio_hubs"],
                     "trend_score": t["trend_score"], "trend_confidence": t["confidence"],
                     "stars_delta_7d": t["stars_delta_7d"], "decision": d["decision"], "license": r["license"]})
    rows.sort(key=lambda x: (-x["trend_score"], x["full_name"]))
    clusters: dict[str, list[str]] = {}
    for row in rows:
        clusters.setdefault(row["primary_hub"], []).append(row["full_name"])
    report = {"schema_version": "WeeklyGitHubSignalReport", "generated_at": now,
              "data_confidence": fx["source_confidence"],
              "caveats": ["Star counts/growth are OWNER-PROVIDED, UNVERIFIED until a 2nd stored snapshot + live "
                          "GitHub metadata confirm.", "Stars = interest signal, not quality/safety.",
                          "No repo here is active — intake decisions are candidates with proof_to_promote."],
              "top": rows[:top_n], "clusters": clusters,
              "founder_takeaways": ["The signal is operational pressure: context compression, local code graphs, "
                                    "queryable memory, reusable skills, token-cost-per-outcome — directly relevant "
                                    "to Teleon (runtime efficiency) and Baltor (governed context)."],
              "intake_summary": {d: sum(1 for r in rows if r["decision"] == d) for d in {r["decision"] for r in rows}}}
    return report


def weekly_report_markdown(report: dict) -> str:
    md = ["# Weekly GitHub Signal Watch", "", f"_generated {report['generated_at']} · data confidence: "
          f"{report['data_confidence']}_", "", "> " + " ".join(report["caveats"]), "", "## Top fastest-growing"]
    for r in report["top"]:
        md.append(f"- **{r['full_name']}** → {r['primary_hub']} · trend {r['trend_score']} "
                  f"({r['trend_confidence']}) · decision: **{r['decision']}** · {r['license']}")
    md += ["", "## Clusters (by hub)"]
    for hub, names in report["clusters"].items():
        md.append(f"- **{hub}**: {', '.join(names)}")
    md += ["", "## Founder takeaways"] + [f"- {t}" for t in report["founder_takeaways"]]
    md += ["", "## Intake summary", "```", json.dumps(report["intake_summary"], indent=2), "```"]
    return "\n".join(md) + "\n"


__all__ = ["repo_id", "append_snapshot", "snapshots_for", "compute_trend", "classify", "trend_score", "fit_score",
           "risk", "intake_decision", "weekly_report", "weekly_report_markdown", "load_fixture", "DECISIONS", "DEFAULT_STORE"]
