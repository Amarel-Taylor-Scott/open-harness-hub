#!/usr/bin/env python3
"""scripts.check_contextops_research_agent_provider — proof (CONTEXTOPS RESEARCH-AGENT MODE): the deterministic
OFFLINE local research stub satisfies the ResearchAgentProviderPort, and the candidate research agents are
catalog entries that are NEVER imported/executed and can NEVER serve a fact.

THE INVARIANT made checkable: **Agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES,
CONSUMES.** Concretely:
  - research.local_stub@v1 is a ResearchAgentProviderPort whose research() returns a SCHEMA-VALID
    SourceDiscoveryReport.v1 with serves_truth pinned False, an attributable discovered_by, a replayable
    trace_ref, and every candidate carrying a source_handle — and it runs OFFLINE/deterministically (same
    task + same now -> byte-identical report).
  - each candidate provider (hermes/openclaw/claude_code/openhands/open_swe) is a catalog entry only: its
    status() reports unavailable with imported=False / executed=False naming an env:// ref, and its research()
    RAISES ResearchAgentUnavailable — it never returns a report and never serves a fact.
  - the stub never accepts a secrets-bearing task; it never sets serves_truth True; all output is candidate.

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 scripts/check_contextops_research_agent_provider.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402
from src.baltor.contextops import research_stub  # noqa: E402
from src.baltor.contextops.research_stub import (  # noqa: E402
    CANDIDATE_PROVIDERS,
    LOCAL_STUB_PROVIDER_ID,
    LocalResearchStub,
    make_provider,
)
from src.baltor.ports.research_agent_provider import (  # noqa: E402
    AGENT_SERVES_TRUTH,
    RESEARCH_PRODUCES,
    ResearchAgentProviderPort,
    ResearchAgentUnavailable,
)

_SCHEMA = _REPO / "schemas" / "contextops" / "SourceDiscoveryReport.v1.schema.json"
_NOW = "2026-06-05T00:00:00Z"

#: the bounded task the proof runs (the CFPB verified fact_key); offline + no secrets.
_TASK = {
    "schema_version": "ResearchTask.v1",
    "task_id": "rtask-cfpb-deadline-proof",
    "tenant_id": "acme",
    "source_scope": "global_public",
    "triage_id": "triage-cfpb-faq30-proof",
    "fact_key": "reg_e.error_resolution.deadline",
    "question": "What is the official Regulation E deadline for resolving an alleged error?",
    "authority_bar": "source_of_law",
    "bounds": {"max_steps": 8, "allowed_access": ["fixture"], "offline": True, "secrets_allowed": False},
    "produces": "source_discovery_report",
    "agent_may_serve_truth": False,
    "created_at": _NOW,
}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    sdr_schema = json.loads(_SCHEMA.read_text())

    # ── the local stub satisfies the port (structurally) + runs offline. ──
    stub = LocalResearchStub()
    check("research.local_stub satisfies ResearchAgentProviderPort (Protocol)",
          isinstance(stub, ResearchAgentProviderPort))
    check("research.local_stub provider_id is the canonical local-stub id",
          stub.provider_id == LOCAL_STUB_PROVIDER_ID, stub.provider_id)
    card = stub.describe()
    check("local stub describe() reports offline + not imported + not executed",
          card.get("offline") is True and card.get("imported") is False and card.get("executed") is False)
    check("local stub describe() pins produces=source_discovery_report + agent_may_serve_truth=false",
          card.get("produces") == RESEARCH_PRODUCES and card.get("agent_may_serve_truth") is AGENT_SERVES_TRUTH)
    st = stub.status()
    check("local stub status() == active, imported/executed False",
          st.get("status") == "active" and st.get("imported") is False and st.get("executed") is False)

    # ── research() returns a SCHEMA-VALID SourceDiscoveryReport with serves_truth pinned false. ──
    report = stub.research(_TASK, now=_NOW)
    errs = _validate(report, sdr_schema)
    check("local stub research() output validates against SourceDiscoveryReport.v1", errs == [], str(errs[:4]))
    check("report serves_truth is pinned FALSE (a discovery report is NEVER served as truth)",
          report.get("serves_truth") is False)
    check("report discovered_by names the attributable agent (research.local_stub@v1)",
          report.get("discovered_by") == LOCAL_STUB_PROVIDER_ID)
    check("report carries a replayable trace_ref (all agent actions traced)",
          bool(report.get("trace_ref")) and report["trace_ref"].startswith("objref:sha256:"))
    check("report has >=1 candidate and EVERY candidate carries a source_handle",
          len(report.get("candidates", [])) >= 1
          and all(c.get("source_handle") for c in report["candidates"]))
    check("report carries NO served/canonical fact field (it proposes candidates, never a fact)",
          "fact" not in report and "canonical_fact" not in report and "value" not in report)

    # ── determinism: same task + same now -> byte-identical report. ──
    report2 = stub.research(_TASK, now=_NOW)
    check("local stub research() is deterministic (same task+now -> byte-identical report)",
          json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True))

    # ── red-team: the stub refuses a secrets-bearing task (raises, never returns a report). ──
    secrets_task = json.loads(json.dumps(_TASK))
    secrets_task["bounds"]["secrets_allowed"] = True
    try:
        stub.research(secrets_task, now=_NOW)
        check("local stub REJECTS a secrets-bearing task (red-team)", False, "no exception raised")
    except ResearchAgentUnavailable as e:
        check("local stub REJECTS a secrets-bearing task by raising ResearchAgentUnavailable (red-team)",
              "secrets" in str(e).lower())

    # ── each candidate provider is a CATALOG ENTRY ONLY — never imported/executed, never serves a fact. ──
    check("exactly 5 candidate research agents are cataloged (hermes/openclaw/claude_code/openhands/open_swe)",
          len(CANDIDATE_PROVIDERS) == 5, str(sorted(CANDIDATE_PROVIDERS)))
    expected_candidates = {"research.hermes@candidate", "research.openclaw@candidate",
                           "research.claude_code@candidate", "research.openhands@candidate",
                           "research.open_swe@candidate"}
    check("the cataloged candidate ids are exactly the expected five",
          set(CANDIDATE_PROVIDERS) == expected_candidates, str(set(CANDIDATE_PROVIDERS) ^ expected_candidates))
    for pid in sorted(CANDIDATE_PROVIDERS):
        cand = make_provider(pid)
        check(f"candidate {pid} satisfies ResearchAgentProviderPort (typed slot, not imported)",
              isinstance(cand, ResearchAgentProviderPort))
        cstat = cand.status()
        check(f"candidate {pid} status() == unavailable, imported/executed False, names an env:// ref",
              cstat.get("status") == "unavailable" and cstat.get("imported") is False
              and cstat.get("executed") is False
              and str(cstat.get("credential_ref", "")).startswith("env://"))
        cdesc = cand.describe()
        check(f"candidate {pid} describe() pins agent_may_serve_truth=false",
              cdesc.get("agent_may_serve_truth") is AGENT_SERVES_TRUTH)
        # red-team: a candidate provider can NEVER run / return a fact — research() must raise, not produce.
        try:
            cand.research(_TASK, now=_NOW)
            check(f"candidate {pid} research() RAISES (never serves a fact / runs an external runtime)",
                  False, "no exception raised — a candidate agent must not execute")
        except ResearchAgentUnavailable as e:
            check(f"candidate {pid} research() raises ResearchAgentUnavailable naming its env:// ref (red-team)",
                  cand.provider_id == pid and str(e.credential_ref).startswith("env://"))

    # ── the module imports NO external research runtime (catalog stubs only). ──
    ext = [m for m in ("hermes", "openclaw", "openhands", "open_swe", "litellm", "anthropic", "requests")
           if getattr(research_stub, m, None) is not None]
    check("research_stub imports NO external research runtime/SDK (candidates are catalog stubs)", ext == [], str(ext))

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_research_agent_provider: research.local_stub@v1 satisfies the "
                "ResearchAgentProviderPort and returns a schema-valid SourceDiscoveryReport offline + "
                "deterministically with serves_truth pinned false, an attributable discoverer, a replayable "
                "trace_ref, and a source_handle on every candidate; it refuses a secrets-bearing task; the five "
                "candidate research agents (hermes/openclaw/claude_code/openhands/open_swe) are catalog entries "
                "only — status()=unavailable (imported/executed False, env:// ref) and research() RAISES "
                "ResearchAgentUnavailable, never serving a fact; no external research runtime is imported — THE "
                "INVARIANT (agents discover/propose; Baltor stores/verifies/reconciles/proves/consumes) holds."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the ContextOps research-agent provider port + local stub + candidate stubs.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
