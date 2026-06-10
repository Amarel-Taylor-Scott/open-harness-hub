"""End-to-end proof for the standalone Baltor admin demo.

The test intentionally uses only the Python standard library so it can run when
Playwright is not installed. It can either target an existing server or spawn a
temporary local demo server.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass


ROUTES = {
    "/admin-demo/": "Load data",
    "/admin-demo/sources": "Gateway connector envelope",
    "/admin-demo/monitoring": "Processing pipeline",
    "/admin-demo/outputs": "Extracted claims",
    "/admin-demo/download": "Download context package",
    "/admin-demo/explore": "Document hierarchy",
    "/admin-demo/testing": "Integration readiness",
    "/admin-dashboard/monitor": "Live action monitor",
    "/api/context-gateway/status": "baltor-context-gateway",
    "/api/context-gateway/connectors": "indexed_mirror_first",
    "/api/context-gateway/sync-contracts": "baltor.context-sync-contracts.v1",
    "/api/context-gateway/context-object-schema": "baltor.context-object-schema.v1",
    "/api/context-gateway/context-schema-catalog": "baltor.context-schema-catalog.v1",
    "/api/context-gateway/product-surface": "baltor.context-product-surface.v1",
    "/api/debug/heartbeat": "baltor.debug_heartbeat.v1",
    "/api/context-gateway/glossary": "baltor.context-glossary.v1",
    "/api/context-gateway/dimensions": "baltor.context-dimensions.v1",
    "/api/context-gateway/model-routing": "baltor.context-model-routing.v1",
    "/api/context-gateway/reranking": "baltor.context-reranking.v1",
    "/api/context-gateway/local-memory": "baltor.context-local-memory.v1",
    "/api/admin-dashboard/queue-health": "baltor.queue-health.v1",
}

EXPORTS = ["manifest", "text", "rag", "graph", "audit", "safe-context", "context-pack", "glossary", "context-objects"]


@dataclass
class Response:
    status: int
    body: bytes
    headers: dict[str, str]

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> dict:
        return json.loads(self.text)


def request(base_url: str, path: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None, follow: bool = True) -> Response:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    opener = urllib.request.build_opener()
    if not follow:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):  # type: ignore[no-untyped-def]
                return None
        opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with opener.open(req, timeout=10) as resp:
            return Response(resp.status, resp.read(), dict(resp.headers.items()))
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read(), dict(exc.headers.items()))


def make_zip() -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "company/acme-profile.txt",
            "Acme Bank is headquartered at 100 Market Street. The website is https://example.com/acme.\n\n"
            "Jane Doe joined Acme Bank as Chief Compliance Officer in 2021.",
        )
        zf.writestr(
            "company/leadership/current-officers.md",
            "# Officers\n\nJohn Smith is currently listed as Chief Compliance Officer as of 2025-10-15.\n\n"
            "This may supersede older leadership records.",
        )
        zf.writestr(
            "company/ownership/employment-agency-network.md",
            "# Employment Agency Network Ownership Timeline\n\n"
            "Northstar Staffing acquired Harbor Temps on 2022-04-01.\n\n"
            "Harbor Temps merged with Lakeside Workforce to form Harbor Lakeside Workforce on 2023-08-15.\n\n"
            "In 2024, the healthcare staffing division was split into CareShift Partners.\n\n"
            "As of 2025-11-20, Acme Bank vendor records list Northstar Staffing as the parent company for CareShift Partners.\n\n"
            "A later supplier portal export dated 2026-02-10 lists CareShift Partners as independently owned.\n\n"
            "These ownership facts are time-sensitive and should not be treated as current without refresh.",
        )
        zf.writestr(
            "policies/access-control.md",
            "# Access Control\n\nContractor SharePoint access must be reviewed every 90 days.\n\n"
            "The current escalation threshold is $25,000 as of 2026-05-31.",
        )
        zf.writestr(
            "policies/vendor-terms.md",
            "# Vendor Terms\n\n"
            "The term agency may mean the staffing office, a legal authority, or the recruiting vendor depending on context.\n\n"
            "Active vendor status must be reviewed before onboarding a worker.\n\n"
            "The CCO approves exceptions when the affiliate is managed by a partner.",
        )
        zf.writestr(
            "policies/archived/old-access-control.md",
            "# Old Policy\n\nThe escalation threshold was $10,000 in 2023.",
        )
        zf.writestr("web/domain-record.txt", "The public website for Acme Bank is https://example.com/acme.")
    return payload.getvalue()


def multipart_zip(zip_bytes: bytes) -> tuple[bytes, str]:
    boundary = "----baltor-proof-boundary"
    chunks = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file"; filename="baltor-proof.zip"\r\n',
        b"Content-Type: application/zip\r\n\r\n",
        zip_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def multipart_fields(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----baltor-fields-proof-boundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode(),
            b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def wait_for_server(base_url: str, seconds: float = 8.0) -> None:
    deadline = time.time() + seconds
    last = ""
    while time.time() < deadline:
        try:
            resp = request(base_url, "/api/health")
            if resp.status == 200:
                return
            last = f"HTTP {resp.status}"
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
        time.sleep(0.2)
    raise AssertionError(f"server did not become ready at {base_url}: {last}")


def isolated_env(queue_key: str, stream_key: str, ledger_path: str, upload_dir: str) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["CONTEXT_QUEUE_KEY"] = queue_key
    env["CONTEXT_WORKER_EVENT_STREAM"] = stream_key
    env["CONTEXT_WORKER_LEDGER"] = ledger_path
    env["ADMIN_DEMO_UPLOAD_DIR"] = upload_dir
    env.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
    env.setdefault("CONTEXT_ENABLED_ADAPTERS", "local")
    env.setdefault("NODE_RESEARCH_ENABLE_EXTERNAL", "false")
    env.setdefault("CONTEXT_AUTO_APPROVE_LOCAL", "true")
    env.setdefault("OH_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    env.setdefault("OH_LLM_MODEL", "batiai/gemma4-e2b:q4")
    env.setdefault("OH_LLM_ROUTES", json.dumps([
        {
            "adapter": "proof-ollama-gemma4-e2b-local",
            "lane": "local_efficient",
            "backend": "http-openai",
            "model": env["OH_LLM_MODEL"],
            "base_url": env["OH_LLM_BASE_URL"],
            "provider": "ollama",
            "trust_boundary": "local",
            "quality_tier": "small_open_weight",
            "capabilities": ["*"],
            "modalities": ["text"],
            "data_retention": "local",
            "estimated_cost_usd": 0.0,
        },
        {
            "adapter": "proof-ollama-gemma4-e2b-mid",
            "lane": "open_weight_medium",
            "backend": "http-openai",
            "model": env["OH_LLM_MODEL"],
            "base_url": env["OH_LLM_BASE_URL"],
            "provider": "ollama",
            "trust_boundary": "local",
            "quality_tier": "mid_open_weight_cpu",
            "capabilities": ["*"],
            "modalities": ["text"],
            "data_retention": "local",
            "estimated_cost_usd": 0.0,
        },
    ]))
    return env


def clear_queue_state(env: dict[str, str]) -> None:
    try:
        import redis  # type: ignore
    except ImportError:
        return
    client = redis.from_url(env["REDIS_URL"], decode_responses=True)
    keys = [
        env["CONTEXT_QUEUE_KEY"],
        env["CONTEXT_QUEUE_KEY"] + ":approval-required",
        env["CONTEXT_QUEUE_KEY"] + ":budget-blocked",
        env["CONTEXT_QUEUE_KEY"] + ":failed-permanently",
        env["CONTEXT_WORKER_EVENT_STREAM"],
    ]
    if keys:
        client.delete(*keys)


def start_server(port: int, env: dict[str, str] | None = None) -> subprocess.Popen[bytes]:
    proc_env = env or os.environ.copy()
    proc_env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(
        [sys.executable, "scripts/baltor_admin_demo_server.py", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=proc_env,
    )


def start_worker(env: dict[str, str], *, max_jobs: int) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [sys.executable, "-m", "scripts.context_workers.runner", "--watch", "--max-jobs", str(max_jobs), "--idle-sleep", "0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def assert_routes(base_url: str) -> None:
    for path, marker in ROUTES.items():
        resp = request(base_url, path)
        assert resp.status == 200, f"{path} returned HTTP {resp.status}"
        assert marker in resp.text, f"{path} missing marker {marker!r}"
        assert len(resp.body) > 300, f"{path} looked blank"


def upload_zip(base_url: str) -> str:
    body, ctype = multipart_zip(make_zip())
    resp = request(base_url, "/admin-demo/runs", method="POST", body=body, headers={"Content-Type": ctype}, follow=False)
    assert resp.status == 303, f"upload returned HTTP {resp.status}: {resp.text[:300]}"
    location = resp.headers.get("Location", "")
    match = re.search(r"run=(adm-[a-f0-9]+)", location)
    assert match, f"redirect did not include run id: {location}"
    return match.group(1)


def register_connector(base_url: str) -> str:
    body, ctype = multipart_fields({
        "connector": "gitlab",
        "connector_url": "https://gitlab.example.com/context-control/baltor",
        "connector_action": "register",
    })
    resp = request(base_url, "/admin-demo/runs", method="POST", body=body, headers={"Content-Type": ctype}, follow=False)
    assert resp.status == 303, f"connector returned HTTP {resp.status}: {resp.text[:300]}"
    location = resp.headers.get("Location", "")
    match = re.search(r"run=(adm-[a-f0-9]+)", location)
    assert match, f"connector redirect did not include run id: {location}"
    return match.group(1)


def poll_run(base_url: str, run_id: str) -> dict:
    deadline = time.time() + 12
    last: dict = {}
    while time.time() < deadline:
        resp = request(base_url, f"/api/admin-demo/runs/{run_id}")
        assert resp.status == 200, f"run API returned HTTP {resp.status}"
        last = resp.json()
        if last.get("status") == "complete" and int(last.get("progress") or 0) >= 100:
            return last
        time.sleep(0.3)
    raise AssertionError(f"run did not complete: {json.dumps(last, indent=2)[:1200]}")


def assert_run(run: dict) -> None:
    tree = run.get("document_tree") or {}
    summary = tree.get("summary") or {}
    assert summary.get("files", 0) >= 5, f"expected nested ZIP files, got {summary}"
    assert summary.get("folders", 0) >= 3, f"expected nested ZIP folders, got {summary}"
    assert summary.get("pages", 0) >= 5, f"expected page records, got {summary}"
    assert summary.get("components", 0) >= 5, f"expected page components, got {summary}"
    assert run.get("queue_job_id"), "run did not record queue job id"
    assert run.get("queue_published") in {True, False}, "run did not record queue publish state"
    assert (run.get("summary") or {}).get("claims", 0) >= 3, "run did not extract claims"
    ownership_records = run.get("ownership_change_records") or []
    ownership_claims = [claim for claim in run.get("claims") or [] if claim.get("claim_type") == "ownership_change"]
    assert len(ownership_records) >= 3, f"run did not detect ownership change records: {ownership_records}"
    assert any(item.get("event_type") == "acquisition" for item in ownership_records), f"missing acquisition ownership event: {ownership_records}"
    assert any(item.get("event_type") == "merger" for item in ownership_records), f"missing merger ownership event: {ownership_records}"
    assert any(item.get("event_type") == "independent_ownership_record" for item in ownership_records), f"missing independent ownership event: {ownership_records}"
    assert any(item.get("requires_refresh") for item in ownership_records), f"ownership records did not flag refresh: {ownership_records}"
    assert ownership_claims, "ownership claims were not typed as ownership_change"
    assert any((item.get("entity_candidates") or []) for item in ownership_records), f"ownership records did not include entity candidates: {ownership_records}"
    term_concerns = run.get("term_clarity_concerns") or []
    assert term_concerns, "run did not detect term clarity concerns"
    assert any(item.get("type") == "MULTI_MEANING_TERM" and str(item.get("term") or "").lower() == "agency" for item in term_concerns), f"missing multi-meaning agency concern: {term_concerns}"
    assert any(item.get("type") == "UNDEFINED_DOMAIN_TERM" and str(item.get("term") or "").lower() == "active vendor" for item in term_concerns), f"missing undefined active vendor concern: {term_concerns}"
    assert any(item.get("type") == "ACRONYM_WITHOUT_DEFINITION" and item.get("term") == "CCO" for item in term_concerns), f"missing acronym concern: {term_concerns}"
    glossary_packets = run.get("glossary_resolution_packets") or []
    assert glossary_packets, "run did not create glossary resolution packets"
    assert any(packet.get("term") == "agency" and packet.get("status") == "needs_glossary_review" for packet in glossary_packets), f"missing agency glossary packet: {glossary_packets}"
    assert all((packet.get("safe_context_policy") or {}).get("block_global_memory_promotion") is True for packet in glossary_packets), f"glossary packets do not block global memory promotion: {glossary_packets}"
    conflict_groups = run.get("ownership_conflict_groups") or []
    assert conflict_groups, "run did not group conflicting dated ownership records"
    assert any("CareShift Partners" in str(group.get("target_entity") or "") for group in conflict_groups), f"missing CareShift ownership conflict group: {conflict_groups}"
    care_shift_group = next(group for group in conflict_groups if "CareShift Partners" in str(group.get("target_entity") or ""))
    assert care_shift_group.get("resolution_suggestion") == "newer_independent_record_likely_supersedes_parent_record", f"unexpected supersession scoring: {care_shift_group}"
    assert care_shift_group.get("latest_claim_id") == "fact-010", f"expected newer independent ownership claim as latest: {care_shift_group}"
    assert "fact-009" in (care_shift_group.get("superseded_claim_ids") or []), f"expected parent record as superseded candidate: {care_shift_group}"
    refresh_jobs = run.get("refresh_jobs") or []
    ownership_refresh_jobs = [job for job in refresh_jobs if str(job.get("refresh_reason") or "").startswith("ownership_")]
    assert len(ownership_refresh_jobs) >= 3, f"ownership refresh jobs were not planned: {refresh_jobs}"
    assert any(job.get("refresh_reason") == "ownership_conflict_reconciliation" for job in ownership_refresh_jobs), f"missing ownership conflict refresh job: {ownership_refresh_jobs}"
    assert all((job.get("adapter_plan") or {}).get("person_level_osint") == "disabled" for job in ownership_refresh_jobs), f"ownership refresh jobs did not preserve privacy gate: {ownership_refresh_jobs}"
    assert all(job.get("task") == "context.search.verify" for job in ownership_refresh_jobs), f"ownership refresh jobs used unexpected task shape: {ownership_refresh_jobs}"


def assert_exports(base_url: str, run_id: str) -> dict[str, dict]:
    payloads: dict[str, dict] = {}
    for kind in EXPORTS:
        resp = request(base_url, f"/api/admin-demo/runs/{run_id}/exports/{kind}")
        assert resp.status == 200, f"export {kind} returned HTTP {resp.status}"
        payload = resp.json()
        assert payload.get("package_type") == f"baltor.{kind}.v1", f"export {kind} had wrong package type"
        assert payload.get("run_id") == run_id, f"export {kind} had wrong run id"
        payloads[kind] = payload
    assert payloads["manifest"].get("document_tree_summary", {}).get("files", 0) >= 5
    assert "context-pack" in payloads["manifest"].get("exports", [])
    assert payloads["rag"].get("record_count", 0) >= 5
    assert all(str(record.get("handle") or "").startswith("ctx://baltor/") for record in payloads["rag"].get("records", [])[:5])
    assert "nodes" in payloads["graph"] and "edges" in payloads["graph"]
    assert any(str(node.get("handle") or "").startswith("ctx://baltor/") for node in payloads["graph"].get("nodes", []))
    assert any(node.get("type") == "OwnershipChangeEvent" for node in payloads["graph"].get("nodes", [])), "graph export missing OwnershipChangeEvent node"
    assert any(node.get("type") == "OwnershipConflictGroup" for node in payloads["graph"].get("nodes", [])), "graph export missing OwnershipConflictGroup node"
    assert any(node.get("type") == "TermClarityConcern" for node in payloads["graph"].get("nodes", [])), "graph export missing TermClarityConcern node"
    assert any(edge.get("type") == "HAS_TERM_CLARITY_CONCERN" for edge in payloads["graph"].get("edges", [])), "graph export missing term clarity edge"
    assert any(node.get("type") == "GlossaryResolutionPacket" for node in payloads["graph"].get("nodes", [])), "graph export missing GlossaryResolutionPacket node"
    assert any(edge.get("type") == "HAS_GLOSSARY_RESOLUTION_PACKET" for edge in payloads["graph"].get("edges", [])), "graph export missing glossary packet edge"
    assert any(edge.get("type") == "MAY_SUPERSEDE_OWNERSHIP_CLAIM" for edge in payloads["graph"].get("edges", [])), "graph export missing ownership supersession edge"
    assert payloads["graph"].get("ownership_change_records"), "graph export missing ownership_change_records"
    assert payloads["graph"].get("ownership_conflict_groups"), "graph export missing ownership_conflict_groups"
    assert "worker_records" in payloads["audit"]
    assert "approved_context" in payloads["safe-context"]
    assert payloads["safe-context"].get("ownership_change_records"), "safe-context export missing ownership_change_records"
    assert payloads["safe-context"].get("term_clarity_concerns"), "safe-context export missing term_clarity_concerns"
    assert payloads["glossary"].get("glossary_resolution_packets"), "glossary export missing glossary_resolution_packets"
    assert payloads["audit"].get("refresh_jobs"), "audit export missing refresh_jobs"
    assert any(str(job.get("refresh_reason") or "").startswith("ownership_") for job in payloads["audit"].get("refresh_jobs") or []), "audit export missing ownership refresh jobs"
    assert payloads["context-pack"].get("context_pack", {}).get("source_handles")
    assert payloads["context-pack"].get("context_pack", {}).get("ownership_change_records"), "context-pack export missing ownership_change_records"
    assert payloads["context-pack"].get("context_pack", {}).get("term_clarity_concerns"), "context-pack export missing term_clarity_concerns"
    assert payloads["context-pack"].get("context_pack", {}).get("glossary_resolution_packets"), "context-pack export missing glossary_resolution_packets"
    assert payloads["context-pack"].get("gateway_policy", {}).get("retrieval_policy_owned_by_baltor") is True
    context_objects = payloads["context-objects"]
    assert context_objects.get("kind") == "baltor.context-object-graph-records.v1", f"context-objects export wrong kind: {context_objects}"
    assert context_objects.get("counts", {}).get("objects", 0) >= 5, f"context-objects export missing objects: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("versions") == context_objects.get("counts", {}).get("objects"), f"context object versions should match objects: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("artifacts", 0) >= 5, f"context-objects export missing artifacts: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("relationships", 0) >= 5, f"context-objects export missing relationships: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("assertions", 0) >= 5, f"context-objects export missing assertions: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("dimension_definitions", 0) >= 7, f"context-objects export missing dimension definitions: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("dimension_values", 0) >= 20, f"context-objects export missing dimension values: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("events", 0) >= 2, f"context-objects export missing events: {context_objects.get('counts')}"
    assert context_objects.get("counts", {}).get("packs", 0) == 1, f"context-objects export missing pack: {context_objects.get('counts')}"
    assert all(item.get("kind") == "baltor.context-object.v1" for item in context_objects.get("objects", [])[:5]), "context object records missing kind"
    assert all(item.get("kind") == "baltor.context-version.v1" for item in context_objects.get("versions", [])[:5]), "context version records missing kind"
    assert all(item.get("facets") for item in context_objects.get("objects", [])[:5]), "context object records missing flexible facets"
    assert all(item.get("five_w_one_h") for item in context_objects.get("objects", [])[:5]), "context object records missing 5W1H projection"
    assert any(item.get("kind") == "baltor.context-relationship.v1" and item.get("relationship_type") == "MAY_SUPERSEDE" for item in context_objects.get("relationships", [])), "context relationships missing MAY_SUPERSEDE"
    assert any(item.get("kind") == "baltor.context-assertion.v1" and item.get("predicate") == "states" for item in context_objects.get("assertions", [])), "context assertions missing source-linked claim statements"
    assert any(item.get("kind") == "baltor.context-dimension-definition.v1" and item.get("dimension_id") == "dim://baltor/trust/verifiability" for item in context_objects.get("dimension_definitions", [])), "context dimension definitions missing verifiability"
    assert any(item.get("kind") == "baltor.context-dimension-value.v1" and item.get("dimension_id") == "dim://baltor/risk/operational" for item in context_objects.get("dimension_values", [])), "context dimension values missing operational risk"
    assert context_objects.get("packs", [{}])[0].get("kind") == "baltor.context-pack.v1", "context pack projection missing kind"
    assert context_objects.get("policy", {}).get("versions_are_immutable") is True, f"context object policy incomplete: {context_objects.get('policy')}"
    assert context_objects.get("policy", {}).get("flexible_facets_are_namespaced") is True, f"context object policy missing facets rule: {context_objects.get('policy')}"
    assert context_objects.get("policy", {}).get("dimensions_are_first_class_records") is True, f"context object policy missing dimension rule: {context_objects.get('policy')}"
    assert context_objects.get("policy", {}).get("assertions_are_source_linked") is True, f"context object policy missing assertion rule: {context_objects.get('policy')}"
    return payloads


def assert_connector_run(base_url: str) -> dict:
    catalog_resp = request(base_url, "/api/context-gateway/connectors")
    assert catalog_resp.status == 200, f"connector catalog returned HTTP {catalog_resp.status}"
    catalog = catalog_resp.json()
    assert catalog.get("policy", {}).get("unrestricted_raw_tools_exposed") is False
    assert len(catalog.get("connectors") or []) >= 5, "connector catalog looked incomplete"
    repo_wiki = [
        item for item in catalog.get("connectors") or []
        if item.get("source_system") == "repo_wiki"
    ]
    assert repo_wiki, f"connector catalog missing repo_wiki connector: {catalog}"
    assert repo_wiki[0].get("retrieval_policy", {}).get("raw_source_access") == "fallback"
    assert repo_wiki[0].get("safety", {}).get("generated_repo_docs_are_derived_context") is True
    sync_triggers = set(repo_wiki[0].get("sync_policy", {}).get("supported_triggers") or [])
    assert {"post_commit_hook", "push_webhook", "pipeline_artifact"}.issubset(sync_triggers), f"repo_wiki connector missing event triggers: {repo_wiki[0]}"
    assert repo_wiki[0].get("sync_policy", {}).get("commit_scoped_outputs_required") is True
    sync_resp = request(base_url, "/api/context-gateway/sync-contracts")
    assert sync_resp.status == 200, f"sync contracts returned HTTP {sync_resp.status}"
    sync = sync_resp.json()
    assert sync.get("kind") == "baltor.context-sync-contracts.v1", f"wrong sync contract kind: {sync}"
    assert {"push", "pull", "push_then_pull"}.issubset(set(sync.get("sync_modes") or [])), f"sync modes incomplete: {sync}"
    assert {"post_commit_hook", "push_webhook", "pipeline_artifact"}.issubset(set(sync.get("trigger_types") or [])), f"sync trigger types incomplete: {sync}"
    assert "baltor.repo-wiki-artifact-manifest.v1" in (sync.get("artifact_manifest_kinds") or []), f"repo wiki artifact manifest not declared: {sync}"
    assert sync.get("policies", {}).get("commit_scoped_outputs_required_for_repo_wiki") is True, f"sync policy missing commit-scoped requirement: {sync}"
    schema_resp = request(base_url, "/api/context-gateway/context-object-schema")
    assert schema_resp.status == 200, f"context object schema returned HTTP {schema_resp.status}"
    schema = schema_resp.json()
    assert schema.get("kind") == "baltor.context-object-schema.v1", f"wrong context object schema kind: {schema}"
    assert schema.get("context_object_kind") == "baltor.context-object.v1", f"wrong context object kind: {schema}"
    assert schema.get("source_handle_pattern") == "^ctx://", f"context object source handle pattern missing: {schema}"
    assert schema.get("policy", {}).get("durable_claims_require_source_handles") is True, f"context object policy incomplete: {schema}"
    schema_catalog_resp = request(base_url, "/api/context-gateway/context-schema-catalog")
    assert schema_catalog_resp.status == 200, f"context schema catalog returned HTTP {schema_catalog_resp.status}"
    schema_catalog = schema_catalog_resp.json()
    assert schema_catalog.get("kind") == "baltor.context-schema-catalog.v1", f"wrong context schema catalog kind: {schema_catalog}"
    expected_schema_kinds = {
        "baltor.context-object.v1",
        "baltor.context-version.v1",
        "baltor.context-artifact.v1",
        "baltor.context-relationship.v1",
        "baltor.context-assertion.v1",
        "baltor.context-dimension-definition.v1",
        "baltor.context-dimension-value.v1",
        "baltor.context-model-profile.v1",
        "baltor.context-model-routing-policy.v1",
        "baltor.context-reranker-profile.v1",
        "baltor.context-reranking-policy.v1",
        "baltor.context-local-memory-profile.v1",
        "baltor.context-local-sync-policy.v1",
        "baltor.context-event.v1",
        "baltor.context-pack.v1",
        "baltor.context-provider.v1",
        "baltor.context-pack-builder.v1",
        "baltor.context-product-surface.v1",
    }
    assert expected_schema_kinds.issubset(set(schema_catalog.get("schema_kinds") or [])), f"context schema catalog incomplete: {schema_catalog}"
    assert schema_catalog.get("storage_agnostic") is True, f"context schema catalog should be storage agnostic: {schema_catalog}"
    product_resp = request(base_url, "/api/context-gateway/product-surface")
    assert product_resp.status == 200, f"context product surface returned HTTP {product_resp.status}"
    product = product_resp.json()
    assert product.get("kind") == "baltor.context-product-surface.v1", f"wrong context product surface kind: {product}"
    assert "mcp" in (product.get("interfaces") or []), f"product surface missing MCP interface: {product}"
    assert "atlassian_rovo_team" in (product.get("deployment_models") or []), f"product surface missing Atlassian/Rovo deployment: {product}"
    assert product.get("product_invariants", {}).get("durable_claims_require_source_handles") is True, f"product surface invariants incomplete: {product}"
    assert product.get("product_invariants", {}).get("model_routing_is_provider_neutral") is True, f"product surface missing model-routing invariant: {product}"
    assert product.get("product_invariants", {}).get("reranking_is_source_aware_not_embedding_only") is True, f"product surface missing reranking invariant: {product}"
    assert product.get("product_invariants", {}).get("private_e2ee_memory_is_not_cloud_searchable") is True, f"product surface missing local memory invariant: {product}"
    run_id = register_connector(base_url)
    run = poll_run(base_url, run_id)
    manifest = request(base_url, f"/api/admin-demo/runs/{run_id}/exports/manifest").json()
    envelopes = manifest.get("connector_envelopes") or []
    assert envelopes, "connector run did not export connector envelopes"
    envelope = envelopes[0]
    assert envelope.get("source_system") == "gitlab", f"expected GitLab envelope, got {envelope}"
    assert envelope.get("retrieval_policy", {}).get("raw_source_access") == "fallback"
    assert envelope.get("acl_policy", {}).get("filter_before_model") is True
    assert str(envelope.get("handle") or "").startswith("ctx://baltor/")
    graph = request(base_url, f"/api/admin-demo/runs/{run_id}/exports/graph").json()
    assert any(node.get("type") == "ConnectorEnvelope" for node in graph.get("nodes", [])), "graph export missing ConnectorEnvelope node"
    return {"run_id": run_id, "summary": (run.get("document_tree") or {}).get("summary"), "handle": envelope.get("handle")}


def assert_context_gateway(base_url: str, run_id: str) -> dict:
    query = urllib.parse.urlencode({
        "run_id": run_id,
        "query": "Acme Bank compliance officer current threshold",
        "task_type": "code_change",
        "token_budget": "1600",
    })
    search_resp = request(base_url, f"/api/context-gateway/search?{query}")
    assert search_resp.status == 200, f"context gateway search returned HTTP {search_resp.status}"
    search = search_resp.json()
    assert search.get("ok") is True, f"context gateway search failed: {search}"
    assert search.get("context_pack", {}).get("source_handles"), "context gateway did not return source handles"
    assert search.get("gateway_policy", {}).get("retrieval_policy_owned_by_baltor") is True
    assert search.get("retrieval", {}).get("acl_filter_applied") is True
    handle = search["context_pack"]["source_handles"][0]
    fetch_resp = request(base_url, "/api/context-gateway/fetch?" + urllib.parse.urlencode({"handle": handle, "run_id": run_id}))
    assert fetch_resp.status == 200, f"context gateway fetch returned HTTP {fetch_resp.status}"
    fetch = fetch_resp.json()
    assert fetch.get("ok") is True, f"context gateway fetch failed: {fetch}"
    assert fetch.get("handle") == handle, "context gateway fetch returned the wrong handle"
    assert fetch.get("gateway_policy", {}).get("bounded_fetch") is True
    trace_resp = request(base_url, "/api/context-gateway/trace")
    assert trace_resp.status == 200, f"context gateway trace returned HTTP {trace_resp.status}"
    trace = trace_resp.json()
    assert trace.get("policy", {}).get("raw_source_access_is_fallback") is True
    glossary_resp = request(base_url, "/api/context-gateway/glossary?" + urllib.parse.urlencode({"run_id": run_id, "term": "agency"}))
    assert glossary_resp.status == 200, f"context gateway glossary returned HTTP {glossary_resp.status}"
    glossary = glossary_resp.json()
    assert glossary.get("ok") is True, f"context gateway glossary failed: {glossary}"
    assert glossary.get("kind") == "baltor.context-glossary.v1"
    assert glossary.get("packet_count", 0) >= 1, f"context gateway glossary returned no packets: {glossary}"
    assert (glossary.get("packets") or [{}])[0].get("term") == "agency", f"context gateway glossary did not filter agency: {glossary}"
    assert glossary.get("gateway_policy", {}).get("block_global_memory_promotion") is True
    dimensions_resp = request(base_url, "/api/context-gateway/dimensions?" + urllib.parse.urlencode({"run_id": run_id, "dimension_id": "dim://baltor/trust/verifiability", "max_values": "5"}))
    assert dimensions_resp.status == 200, f"context gateway dimensions returned HTTP {dimensions_resp.status}"
    dimensions = dimensions_resp.json()
    assert dimensions.get("ok") is True, f"context gateway dimensions failed: {dimensions}"
    assert dimensions.get("kind") == "baltor.context-dimensions.v1", f"wrong dimensions kind: {dimensions}"
    assert dimensions.get("counts", {}).get("dimension_definitions", 0) >= 1, f"dimensions missing definitions: {dimensions}"
    assert dimensions.get("counts", {}).get("dimension_values", 0) >= 1, f"dimensions missing values: {dimensions}"
    assert dimensions.get("gateway_policy", {}).get("scores_are_assessments_not_source_facts") is True, f"dimensions policy incomplete: {dimensions}"
    model_routing_resp = request(base_url, "/api/context-gateway/model-routing?" + urllib.parse.urlencode({"run_id": run_id, "task_type": "claim_review"}))
    assert model_routing_resp.status == 200, f"context gateway model routing returned HTTP {model_routing_resp.status}"
    model_routing = model_routing_resp.json()
    assert model_routing.get("ok") is True, f"context gateway model routing failed: {model_routing}"
    assert model_routing.get("kind") == "baltor.context-model-routing.v1", f"wrong model routing kind: {model_routing}"
    assert len(model_routing.get("model_profiles") or []) >= 7, f"model routing missing ladder profiles: {model_routing}"
    assert model_routing.get("routing_policy", {}).get("policy", {}).get("provider_neutral") is True, f"model routing policy is not provider neutral: {model_routing}"
    assert model_routing.get("routing_policy", {}).get("policy", {}).get("do_not_escalate_by_brand_or_prestige") is True, f"model routing policy missing brand-neutral rule: {model_routing}"
    assert model_routing.get("sample_route_decision", {}).get("recommended_route"), f"model routing missing route decision: {model_routing}"
    reranking_resp = request(base_url, "/api/context-gateway/reranking?" + urllib.parse.urlencode({"run_id": run_id, "query": "Acme Bank compliance officer current threshold", "task_type": "implementation_pack"}))
    assert reranking_resp.status == 200, f"context gateway reranking returned HTTP {reranking_resp.status}"
    reranking = reranking_resp.json()
    assert reranking.get("ok") is True, f"context gateway reranking failed: {reranking}"
    assert reranking.get("kind") == "baltor.context-reranking.v1", f"wrong reranking kind: {reranking}"
    assert len(reranking.get("reranker_profiles") or []) >= 7, f"reranking missing ladder profiles: {reranking}"
    assert reranking.get("reranking_policy", {}).get("policy", {}).get("source_aware_not_embedding_only") is True, f"reranking policy is not source-aware: {reranking}"
    assert reranking.get("reranking_policy", {}).get("policy", {}).get("lora_adapters_require_eval_and_lineage") is True, f"reranking policy missing LoRA evaluation rule: {reranking}"
    assert reranking.get("sample_rerank_decision", {}).get("recommended_stage"), f"reranking missing route decision: {reranking}"
    local_memory_resp = request(base_url, "/api/context-gateway/local-memory?" + urllib.parse.urlencode({"run_id": run_id, "scope": "personal"}))
    assert local_memory_resp.status == 200, f"context gateway local memory returned HTTP {local_memory_resp.status}"
    local_memory = local_memory_resp.json()
    assert local_memory.get("ok") is True, f"context gateway local memory failed: {local_memory}"
    assert local_memory.get("kind") == "baltor.context-local-memory.v1", f"wrong local memory kind: {local_memory}"
    assert len(local_memory.get("memory_profiles") or []) >= 4, f"local memory missing profiles: {local_memory}"
    assert local_memory.get("sync_policy", {}).get("cloud_visibility", {}).get("private_e2ee_memory_plaintext_visible_to_cloud") is False, f"local memory should keep private plaintext hidden from cloud: {local_memory}"
    assert local_memory.get("sync_policy", {}).get("cloud_visibility", {}).get("encrypted_sync_blobs_are_not_server_searchable") is True, f"encrypted sync blobs should not be server searchable: {local_memory}"
    assert local_memory.get("gateway_policy", {}).get("company_context_index_is_separate") is True, f"company context tier should be separate: {local_memory}"
    assert local_memory.get("cache_status", {}).get("offline_safe") is True, f"local memory cache should be offline safe for current run: {local_memory}"
    return {"search": search, "fetch": fetch, "trace": trace, "glossary": glossary, "dimensions": dimensions, "model_routing": model_routing, "reranking": reranking, "local_memory": local_memory}


def assert_dimension_ui(base_url: str, run_id: str) -> None:
    for path in [f"/admin-demo/explore?run={run_id}", f"/admin-dashboard/monitor?run={run_id}"]:
        resp = request(base_url, path)
        assert resp.status == 200, f"{path} returned HTTP {resp.status}"
        assert "Dimension engine" in resp.text, f"{path} missing Dimension engine panel"
        assert "Highest operational risk" in resp.text, f"{path} missing risk ranking"
        assert "Lowest verifiability" in resp.text, f"{path} missing verifiability ranking"


def assert_context_cache_writer(base_url: str, run_id: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="baltor-context-cache-proof-") as temp_dir:
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/baltor_context_cache.py",
                "--base-url",
                base_url,
                "--run-id",
                run_id,
                "--query",
                "agency active vendor CCO ownership",
                "--out-dir",
                temp_dir,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        payload = json.loads(proc.stdout)
        assert payload.get("ok") is True, f"context cache writer failed: {payload}"
        context_path = payload.get("context_path")
        glossary_path = payload.get("glossary_path")
        audit_log = payload.get("audit_log")
        manifest_path = payload.get("manifest_path")
        assert context_path and os.path.exists(context_path), f"context cache file missing: {payload}"
        assert glossary_path and os.path.exists(glossary_path), f"glossary cache file missing: {payload}"
        assert audit_log and os.path.exists(audit_log), f"audit log missing: {payload}"
        assert manifest_path and os.path.exists(manifest_path), f"cache manifest missing: {payload}"
        context_text = open(context_path, encoding="utf-8").read()
        glossary_text = open(glossary_path, encoding="utf-8").read()
        manifest = json.loads(open(manifest_path, encoding="utf-8").read())
        audit_line = open(audit_log, encoding="utf-8").read().strip().splitlines()[-1]
        audit = json.loads(audit_line)
        assert "ctx://baltor/" in context_text, "context cache did not retain source handles"
        assert "Do not paste raw source-system dumps" in context_text, "context cache missing cache policy"
        assert "agency" in glossary_text and "source_local" in glossary_text, "glossary cache missing source-scoped agency packet"
        assert manifest.get("kind") == "baltor.local-context-cache-manifest.v1", f"wrong cache manifest kind: {manifest}"
        assert manifest.get("latest_run_id") == run_id, f"cache manifest latest run mismatch: {manifest}"
        assert manifest.get("policy", {}).get("stores_raw_source_dump") is False, f"manifest policy allows raw dumps: {manifest}"
        assert manifest.get("policy", {}).get("stores_source_handles") is True, f"manifest policy missing source handles: {manifest}"
        assert manifest.get("entry_count", 0) >= 1, f"cache manifest missing entries: {manifest}"
        assert audit.get("event") == "baltor.context_cache.write", f"wrong audit event: {audit}"
        assert audit.get("manifest_path") == manifest_path, f"audit did not link manifest path: {audit}"
        assert audit.get("policy", {}).get("stores_raw_source_dump") is False, f"audit policy allows raw dumps: {audit}"
        assert audit.get("policy", {}).get("stores_source_handles") is True, f"audit policy missing source handles: {audit}"
        return payload


def assert_heartbeat(base_url: str, run_id: str) -> dict:
    resp = request(base_url, "/api/debug/heartbeat?" + urllib.parse.urlencode({"run_id": run_id}))
    assert resp.status == 200, f"heartbeat returned HTTP {resp.status}"
    payload = resp.json()
    assert payload.get("kind") == "baltor.debug_heartbeat.v1", f"wrong heartbeat kind: {payload}"
    assert payload.get("server", {}).get("uptime_seconds", -1) >= 0
    assert payload.get("run", {}).get("run_id") == run_id
    assert "last_worker_event" in payload.get("run", {})
    assert isinstance(payload.get("run", {}).get("recent_worker_events"), list)
    assert "queue" in payload and "worker" in payload and "events" in payload
    assert "oldest_pending_age_seconds" in payload.get("queue", {})
    assert isinstance(payload.get("queue", {}).get("pending_sample"), list)
    assert isinstance(payload.get("queue", {}).get("recent_worker_events"), list)
    assert isinstance(payload.get("queue", {}).get("active_worker_jobs"), list)
    assert "active_worker_job_count" in payload.get("queue", {})
    assert "stale_active_worker_job_count" in payload.get("queue", {})
    assert "stale_pending_job_count" in payload.get("queue", {})
    assert "thresholds" in payload.get("queue", {})
    assert "trend" in payload.get("queue", {})
    assert payload.get("queue", {}).get("trend", {}).get("status") in {"unknown", "flat", "growing", "shrinking"}
    assert "throughput" in payload.get("queue", {})
    assert payload.get("queue", {}).get("throughput", {}).get("status") in {"unknown", "drained", "estimated"}
    assert isinstance(payload.get("queue", {}).get("throughput", {}).get("by_family"), dict)
    assert "history" in payload.get("queue", {})
    assert payload.get("queue", {}).get("history", {}).get("loaded") in {True, False}
    assert isinstance(payload.get("queue", {}).get("pending_family_counts"), dict)
    assert isinstance(payload.get("queue", {}).get("recent_samples"), list)
    assert isinstance(payload.get("queue", {}).get("warnings"), list)
    assert payload.get("contracts", {}).get("worker_event_stream")
    return payload


def wait_for_worker_artifacts(base_url: str, run_id: str, seconds: float) -> tuple[dict, dict]:
    deadline = time.time() + seconds
    last_run: dict = {}
    last_events: dict = {}
    while time.time() < deadline:
        run_resp = request(base_url, f"/api/admin-demo/runs/{run_id}")
        events_resp = request(base_url, "/api/admin-dashboard/events")
        assert run_resp.status == 200, f"run API returned HTTP {run_resp.status}"
        assert events_resp.status == 200, f"events API returned HTTP {events_resp.status}"
        last_run = run_resp.json()
        last_events = events_resp.json()
        counts = last_events.get("artifact_counts") or {}
        queue = last_events.get("queue") or {}
        worker_ready = counts.get("worker_records", 0) > 0
        enrichment_ready = counts.get("node_evidence", 0) > 0 or counts.get("llm_claim_reviews", 0) > 0
        no_holds = queue.get("approval_required", 0) == 0 and queue.get("budget_blocked", 0) == 0 and queue.get("failed_permanently", 0) == 0
        if worker_ready and enrichment_ready and no_holds:
            return last_run, last_events
        time.sleep(1)
    raise AssertionError(
        "worker artifacts did not become ready: "
        + json.dumps({
            "run_id": run_id,
            "artifact_counts": (last_events or {}).get("artifact_counts"),
            "queue": (last_events or {}).get("queue"),
            "heartbeat": request(base_url, "/api/debug/heartbeat?" + urllib.parse.urlencode({"run_id": run_id})).json(),
        }, indent=2, sort_keys=True)
    )


def run_proof(base_url: str, *, wait_worker_seconds: float = 0.0) -> dict:
    wait_for_server(base_url)
    assert_routes(base_url)
    connector: dict = {}
    if wait_worker_seconds <= 0:
        connector = assert_connector_run(base_url)
    run_id = upload_zip(base_url)
    run = poll_run(base_url, run_id)
    assert_run(run)
    exports = assert_exports(base_url, run_id)
    gateway = assert_context_gateway(base_url, run_id)
    assert_dimension_ui(base_url, run_id)
    cache = assert_context_cache_writer(base_url, run_id)
    heartbeat = assert_heartbeat(base_url, run_id)
    events = request(base_url, "/api/admin-dashboard/events").json()
    assert events.get("latest_run_id") == run_id
    if wait_worker_seconds > 0:
        run, events = wait_for_worker_artifacts(base_url, run_id, wait_worker_seconds)
        connector = assert_connector_run(base_url)
    if not connector:
        connector = assert_connector_run(base_url)
    queue = events.get("queue") or {}
    return {
        "ok": True,
        "base_url": base_url,
        "run_id": run_id,
        "routes": sorted(ROUTES),
        "exports": sorted(exports),
        "context_gateway": {
            "result_id": gateway["search"].get("result_id"),
            "handles": len(gateway["search"].get("context_pack", {}).get("source_handles") or []),
            "fetch_kind": gateway["fetch"].get("kind"),
        },
        "context_cache": {
            "context_path": cache.get("context_path"),
            "glossary_path": cache.get("glossary_path"),
            "audit_log": cache.get("audit_log"),
            "manifest_path": cache.get("manifest_path"),
            "manifest_kind": cache.get("manifest_kind"),
            "manifest_entry_count": cache.get("manifest_entry_count"),
            "source_handle_count": cache.get("source_handle_count"),
        },
        "heartbeat": {
            "server_uptime_seconds": heartbeat.get("server", {}).get("uptime_seconds"),
            "run_stage": heartbeat.get("run", {}).get("heartbeat", {}).get("stage"),
            "worker_heartbeat_count": heartbeat.get("worker", {}).get("recent_heartbeat_count"),
        },
        "connector_envelope": connector,
        "document_tree_summary": (run.get("document_tree") or {}).get("summary"),
        "queue": queue,
        "queue_health": {
            "active_worker_job_count": queue.get("active_worker_job_count"),
            "stale_active_worker_job_count": queue.get("stale_active_worker_job_count"),
            "stale_pending_job_count": queue.get("stale_pending_job_count"),
            "pending_sample_missing_timestamps": queue.get("pending_sample_missing_timestamps"),
            "warning_count": len(queue.get("warnings") or []),
            "trend_status": (queue.get("trend") or {}).get("status"),
            "trend_pending_delta": (queue.get("trend") or {}).get("pending_delta"),
            "trend_sample_count": (queue.get("trend") or {}).get("sample_count"),
            "throughput_status": (queue.get("throughput") or {}).get("status"),
            "jobs_per_minute": (queue.get("throughput") or {}).get("jobs_per_minute"),
            "estimated_drain_seconds": (queue.get("throughput") or {}).get("estimated_drain_seconds"),
            "throughput_families": sorted(((queue.get("throughput") or {}).get("by_family") or {}).keys()),
            "history_exists": (queue.get("history") or {}).get("exists"),
            "history_loaded_samples": (queue.get("history") or {}).get("loaded_sample_count"),
        },
        "ownership_change_records": {
            "count": len(run.get("ownership_change_records") or []),
            "event_types": sorted({item.get("event_type") for item in run.get("ownership_change_records") or [] if item.get("event_type")}),
            "requires_refresh": sum(1 for item in run.get("ownership_change_records") or [] if item.get("requires_refresh")),
            "conflict_groups": len(run.get("ownership_conflict_groups") or []),
            "refresh_jobs": len([job for job in run.get("refresh_jobs") or [] if str(job.get("refresh_reason") or "").startswith("ownership_")]),
        },
        "term_clarity_concerns": {
            "count": len(run.get("term_clarity_concerns") or []),
            "types": sorted({item.get("type") for item in run.get("term_clarity_concerns") or [] if item.get("type")}),
        },
        "glossary_resolution_packets": {
            "count": len(run.get("glossary_resolution_packets") or []),
            "gateway_packet_count": gateway["glossary"].get("packet_count"),
        },
        "artifact_counts": events.get("artifact_counts"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--port", type=int, default=9314)
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--wait-worker-seconds", type=float, default=0.0, help="wait for worker ledger/artifacts and assert no approval/budget/failed queues")
    parser.add_argument("--isolated-worker", action="store_true", help="when starting a temporary server, use an isolated Redis queue and local worker")
    parser.add_argument("--worker-max-jobs", type=int, default=80)
    args = parser.parse_args(argv)

    proc: subprocess.Popen[bytes] | None = None
    worker: subprocess.Popen[bytes] | None = None
    base_url = args.base_url or f"http://127.0.0.1:{args.port}"
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if not args.base_url:
            env = None
            if args.isolated_worker:
                temp_dir = tempfile.TemporaryDirectory(prefix="baltor-admin-proof-")
                run_key = "proof:" + str(int(time.time() * 1000))
                env = isolated_env(
                    queue_key=f"ohh:context:jobs:{run_key}",
                    stream_key=f"ohh:context:events:{run_key}",
                    ledger_path=os.path.join(temp_dir.name, "context-workers-ledger.jsonl"),
                    upload_dir=os.path.join(temp_dir.name, "uploads"),
                )
                clear_queue_state(env)
                worker = start_worker(env, max_jobs=args.worker_max_jobs)
            proc = start_server(args.port, env=env)
        result = run_proof(base_url, wait_worker_seconds=args.wait_worker_seconds)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    finally:
        if worker is not None:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
        if proc is not None and not args.keep_server:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
