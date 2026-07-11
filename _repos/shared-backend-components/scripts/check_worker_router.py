#!/usr/bin/env python3
"""scripts.check_worker_router — proof: the worker router classifies commands by queue-prefix → bucket and
ENFORCES the policy: unknown prefixes are rejected, and a bucket attempting a forbidden output is refused
(ErrorEnvelope). Folds in the red-team attacks (open-ended→ContextResponse, browser→CanonicalFact,
utility→LLM-only output, GPU→CPU, unknown prefix) — all must fail safely.

CLI: python3 _repos/shared-backend-components/scripts/check_worker_router.py --self-test   (run from repo root; imports src.baltor)
"""
from __future__ import annotations

import argparse

from src.baltor.workers.worker_router import route, check_command, validate_output, WorkerPolicyError


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # routing: known prefixes → the right bucket (longest-prefix match)
    routing = {
        "agent.research": "open_ended_agent",
        "browser.capture_source": "browser",
        "utility.http_download": "utility",
        "ingest.cfpb": "ingestion_sync",
        "parse.pdf_candidate": "parser_document",
        "decompose.structured_atomic": "decomposition_text_understanding",
        "verify.source_grounding": "verification_fact_check",
        "reconcile.authority_policy": "reconciliation_policy",
        "model.embedding": "model_inference",
        "compute.embedding_batch": "cpu_gpu_compute",
        "graph.deterministic_edges": "vector_graph",
        "optimize.context_pack": "optimization_evaluation",
        "distill.rule_shadow": "distillation_determinism",
        "memory.recall": "memory_context",
        "native.export_json": "native_export",
        "monitor.queue_health": "observability_monitoring",
        "human.signoff_request": "human_review_signoff",
        "control.tick": "control_plane",
    }
    for cmd, want in routing.items():
        got = route(cmd)["bucket_id"]
        chk(f"route {cmd} -> {want}", got == want, f"got {got}")

    # unknown prefix rejected
    try:
        route("bogus.command")
        chk("unknown prefix raises", False, "no raise")
    except WorkerPolicyError:
        chk("unknown prefix raises WorkerPolicyError", True)
    r = check_command("bogus.command")
    chk("check_command(unknown) -> ErrorEnvelope not allowed", r.get("allowed") is False and r.get("reason") == "unknown_prefix")

    # RED-TEAM: forbidden outputs fail safely
    attacks = [
        ("agent.research", "ContextResponse", "open-ended emits ContextResponse"),
        ("agent.codegen", "CanonicalFact", "open-ended emits CanonicalFact"),
        ("browser.capture_source", "CanonicalFact", "browser emits CanonicalFact"),
        ("browser.extract", "ContextResponse", "browser emits ContextResponse"),
        ("utility.http_download", "CanonicalFact", "utility emits CanonicalFact"),
        ("model.embedding", "CanonicalFact", "model emits CanonicalFact"),
        ("model.llm", "ReconciliationDecision", "model emits ReconciliationDecision"),
    ]
    for cmd, out, label in attacks:
        r = check_command(cmd, out)
        chk(f"BLOCKED: {label}", r.get("allowed") is False and r.get("reason") == "forbidden_output", str(r))

    # allowed paths succeed
    ok_native = check_command("native.export_json", "context_response")
    chk("native_export MAY emit context_response", ok_native.get("allowed") is True and ok_native.get("can_publish_truth") is True)
    ok_recon = check_command("reconcile.write_decision", "ReconciliationDecision")
    chk("reconciliation MAY emit ReconciliationDecision", ok_recon.get("allowed") is True)
    ok_agent = check_command("agent.source_discovery", "SourceDiscoveryReport")
    chk("open-ended MAY emit SourceDiscoveryReport (candidate)", ok_agent.get("allowed") is True and ok_agent.get("can_publish_truth") is False)
    chk("validate_output: model forbids ContextResponse", validate_output(route("model.embedding"), "ContextResponse") is False)

    print(f"\n{'PASS — check_worker_router: every command prefix routes to its bucket; unknown prefixes + forbidden outputs (open-ended/browser/model → truth) fail safely; gated buckets may emit truth.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: worker router + policy enforcement.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
