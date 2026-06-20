"""src.baltor.observability.projections.standards — deterministic mappers from Baltor's internal
lineage/claim records into the four adopted interchange standards:

  * W3C PROV-JSON          — provenance (entity/activity/agent + used/wasGeneratedBy/…)
  * OpenLineage RunEvent   — runtime lineage events (run/job/inputs/outputs + custom facets)
  * W3C Web Annotation      — anchor a claim to a source span (FragmentSelector / TextQuoteSelector)
  * RFC 6902 JSON Patch     — express a fact/version delta (supersession, reconciliation change)

Every rendering carries Baltor GOVERNANCE facets (authority / claim_status / receipt_id / held_out /
verified_current) so a portable receipt survives the trip through any external tool — and so an
*allegation* can never be laundered into a *verified* record just by passing through a standard format.
These functions DESCRIBE; they never mutate canonical state and never decide truth.

Pure + deterministic: ids are content hashes of the input, time is taken from the input record (which
was injected upstream), never wall-clock. No RNG.
"""
from __future__ import annotations

import hashlib
import json

# ── single-source constants (no magic values; reused across renderings) ──────────────────────────
NAMESPACE = "baltor"                                   # OpenLineage/PROV namespace for Baltor datasets
PROV_NS = "https://baltor.ai/prov#"                    # PROV-JSON prefix IRI for Baltor terms
PROV_STD_NS = "http://www.w3.org/ns/prov#"             # the W3C PROV core namespace
OPENLINEAGE_PRODUCER = "https://baltor.ai/openlineage"
OPENLINEAGE_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/definitions/RunEvent"
WEB_ANNOTATION_CONTEXT = "http://www.w3.org/ns/anno.jsonld"
CTX_FRAGMENT_CONFORMS = "https://baltor.ai/spec/ctx-fragment"   # conformsTo for ctx:// fragment handles
BALTOR_FACET_SCHEMA_URL = "https://baltor.ai/spec/facets/1-0-0/GovernanceFacet.json"

#: the governance facets Baltor attaches to EVERY exported record — the single source of truth for the
#: portable-receipt fields. Imported by the provider seam and every proof; never re-typed elsewhere.
GOVERNANCE_FACET_KEYS: tuple[str, ...] = (
    "authority",         # which Baltor authority vouches (e.g. "deterministic_reconciliation")
    "claim_status",      # verified_current | allegation | conflicted | stale | unpromoted
    "receipt_id",        # the portable receipt this record is bound to
    "held_out",          # bool: a held-out control — must never be served as truth
    "verified_current",  # bool: passed continuous verification at occurred_at
)


def _hid(prefix: str, *parts: str) -> str:
    """Stable content-hash id: prefix + first 16 hex of sha256 over the joined parts."""
    h = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{h}"


def _det_uuid(seed: str) -> str:
    """A deterministic UUID-shaped string (8-4-4-4-12) derived from `seed` — OpenLineage wants a UUID
    for runId, but the demo must be reproducible, so we hash instead of using a random uuid4."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def governance_facet(governance: dict) -> dict:
    """Filter an arbitrary attributes dict down to ONLY the allowed governance keys. This is the
    laundering guard: no caller can smuggle extra/forged authority fields into a standards record."""
    return {k: governance[k] for k in GOVERNANCE_FACET_KEYS if k in governance}


def _openlineage_facet(governance: dict) -> dict:
    """A governance facet in OpenLineage custom-facet shape (_producer + _schemaURL required)."""
    return {"_producer": OPENLINEAGE_PRODUCER, "_schemaURL": BALTOR_FACET_SCHEMA_URL, **governance_facet(governance)}


# ── W3C PROV-JSON ────────────────────────────────────────────────────────────────────────────────
def to_prov_json(event) -> dict:
    """Map a LineageEvent (or any object exposing .activity/.occurred_at/.inputs/.outputs/.agent/
    .governance) to a W3C PROV-JSON document. Outputs are entities generated-by the activity and
    attributed-to the agent; inputs are entities used by the activity; each output wasDerivedFrom each
    input. Baltor governance facets ride on the output entities."""
    gov = governance_facet(getattr(event, "governance", {}) or {})
    act = _hid(f"{NAMESPACE}:act:", event.activity, event.occurred_at)
    agent = f"{NAMESPACE}:agent:{event.agent}"
    entity: dict = {}
    gen: dict = {}
    used: dict = {}
    att: dict = {}
    der: dict = {}
    in_ids, out_ids = [], []
    for i, src in enumerate(event.inputs):
        eid = f"{NAMESPACE}:in:{_hid('', src)}"
        in_ids.append(eid)
        entity[eid] = {f"{PROV_NS.rstrip('#')}#type": "baltor:Source", "baltor:ref": src}
        used[f"{NAMESPACE}:use:{i}"] = {"prov:activity": act, "prov:entity": eid}
    for j, out in enumerate(event.outputs):
        eid = f"{NAMESPACE}:out:{_hid('', out)}"
        out_ids.append(eid)
        entity[eid] = {"prov:type": "baltor:ContextArtifact", "baltor:ref": out,
                       **{f"baltor:{k}": v for k, v in gov.items()}}
        gen[f"{NAMESPACE}:gen:{j}"] = {"prov:entity": eid, "prov:activity": act}
        att[f"{NAMESPACE}:att:{j}"] = {"prov:entity": eid, "prov:agent": agent}
    k = 0
    for oid in out_ids:
        for iid in in_ids:
            der[f"{NAMESPACE}:der:{k}"] = {"prov:generatedEntity": oid, "prov:usedEntity": iid}
            k += 1
    return {
        "prefix": {NAMESPACE: PROV_NS, "prov": PROV_STD_NS},
        "entity": entity,
        "activity": {act: {"prov:label": event.activity, "prov:startTime": event.occurred_at}},
        "agent": {agent: {"prov:type": "prov:SoftwareAgent"}},
        "used": used,
        "wasGeneratedBy": gen,
        "wasAttributedTo": att,
        "wasDerivedFrom": der,
    }


# ── OpenLineage RunEvent ─────────────────────────────────────────────────────────────────────────
def to_openlineage_run_event(event, *, event_type: str = "COMPLETE") -> dict:
    """Map a LineageEvent to an OpenLineage RunEvent (spec 2-0-2). The run + every output dataset carry
    a `baltor_governance` custom facet so the receipt is portable into any OpenLineage backend."""
    gov_facet = _openlineage_facet(getattr(event, "governance", {}) or {})
    return {
        "eventType": event_type,
        "eventTime": event.occurred_at,
        "producer": OPENLINEAGE_PRODUCER,
        "schemaURL": OPENLINEAGE_SCHEMA_URL,
        "run": {"runId": _det_uuid(event.event_id), "facets": {"baltor_governance": gov_facet}},
        "job": {"namespace": NAMESPACE, "name": event.activity},
        "inputs": [{"namespace": NAMESPACE, "name": i} for i in event.inputs],
        "outputs": [{"namespace": NAMESPACE, "name": o, "facets": {"baltor_governance": gov_facet}}
                    for o in event.outputs],
    }


# ── W3C Web Annotation ───────────────────────────────────────────────────────────────────────────
def to_web_annotation(*, annotation_id: str, claim_body: str, source_iri: str, fragment: str,
                      created: str, governance: dict, quote: str | None = None) -> dict:
    """Anchor a claim to a source span as a W3C Web Annotation. `fragment` is the ctx:// fragment
    (e.g. "page=3&block=7"); an optional exact `quote` adds a TextQuoteSelector. Governance rides on
    the annotation body so an allegation stays an allegation when shared."""
    selector: list[dict] = [{"type": "FragmentSelector", "conformsTo": CTX_FRAGMENT_CONFORMS, "value": fragment}]
    if quote:
        selector.append({"type": "TextQuoteSelector", "exact": quote})
    return {
        "@context": WEB_ANNOTATION_CONTEXT,
        "id": annotation_id,
        "type": "Annotation",
        "motivation": "linking",
        "created": created,
        "body": {"type": "TextualBody", "value": claim_body, "format": "text/plain",
                 "baltor:governance": governance_facet(governance)},
        "target": {"source": source_iri, "selector": selector},
    }


# ── RFC 6902 JSON Patch ──────────────────────────────────────────────────────────────────────────
def _esc(token: str) -> str:
    """RFC 6901 JSON Pointer escaping: ~ -> ~0, / -> ~1."""
    return token.replace("~", "~0").replace("/", "~1")


def json_patch_ops(before: dict, after: dict) -> list[dict]:
    """Deterministic RFC 6902 op list turning a flat `before` fact dict into `after`. Keys sorted so
    the same delta always serializes identically (CDC-friendly, content-hashable)."""
    ops: list[dict] = []
    for key in sorted(before):
        if key not in after:
            ops.append({"op": "remove", "path": f"/{_esc(key)}"})
        elif before[key] != after[key]:
            ops.append({"op": "replace", "path": f"/{_esc(key)}", "value": after[key]})
    for key in sorted(after):
        if key not in before:
            ops.append({"op": "add", "path": f"/{_esc(key)}", "value": after[key]})
    return ops


def to_json_patch(*, before: dict, after: dict, governance: dict,
                  from_version: str | None = None, to_version: str | None = None) -> dict:
    """Wrap an RFC 6902 patch with Baltor provenance — a portable, deterministic FACT DELTA. The bare
    `patch` array is standards-conformant; the wrapper records who/what authorized the change."""
    return {
        "schema": "baltor/FactDelta.v1",
        "from_version": from_version,
        "to_version": to_version,
        "patch": json_patch_ops(before, after),
        "governance": governance_facet(governance),
    }


def canonical_hash(obj: dict) -> str:
    """Content hash of any rendering (sorted-key JSON) — proves determinism and feeds CDC."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
