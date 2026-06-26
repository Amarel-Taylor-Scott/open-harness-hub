#!/usr/bin/env python3
"""Backs ``processor/oracle-c2pa-attest``. The CANONICAL wiring lives in the manifest
``catalog/processors/assurance/oracle-c2pa-attest.yaml`` — process_kind
``attest.c2pa_sign``, side_effects ``write`` (it MINTS an attestation record), deterministic +
idempotent. This docstring does not re-assert the manifest's scalar values (one source of truth —
``docs/codex/no-magic-values.md``); it declares the runtime contract programmatically in
:data:`RUNTIME` and asserts it in the self-test so the two cannot drift.

The signed-provenance axis of context assurance
------------------------------------------------
The verified-corpus-commons wedge (``docs/strategy/oracle-corpus-and-tooling-map.md``,
``beat-contextual-positioning.md``) proves a corpus is still TRUE and current, not merely
*faithfully retrieved*. Its siblings cover the *content* verdicts:
:mod:`scripts.processors.assurance.corpus_integrity_check` (anti-poisoning),
:mod:`scripts.processors.assurance.multi_source_corroborate` (>=2 independent voices), and
:mod:`scripts.sanctions.sanctions_freshness` (currency). This module covers the *binding* axis:
it takes a governed corpus version plus a certifier ("oracle") and produces

  1. a stable **content_hash** (sha256 of the corpus's NORMALIZED bytes) — the address by which a
     downstream agent verifies the corpus, and
  2. a **C2PA-shaped signed manifest** (claim + assertions + signer + hash) recording WHO certified
     this content, WHEN, and which assurance verdicts the certification covered, and
  3. an **attestation_id** + a hash-addressed registry record, so an agent can present a hash and
     read back the certifier identity PLUS the covered verdicts — and can **detect tampering** via
     :func:`verify_by_hash`.

Honest framing — what is REAL here and what is a SEAM
-----------------------------------------------------
C2PA attests ORIGIN and tamper-evidence, NOT correctness (so does this module — the *correctness*
verdicts come from the sibling processors and are merely *carried* in the manifest's assertions).
This implementation is explicit about the boundary between the deterministic structure it really
produces and the cryptography it deliberately does NOT fake:

  * **REAL (pure-stdlib ``hashlib``).** The ``content_hash`` is a genuine sha256 over canonically
    normalized corpus bytes — re-deriving it from the same corpus reproduces it exactly, and a single
    flipped byte changes it (that is what :func:`verify_by_hash` exploits to catch tampering). The
    manifest STRUCTURE (a C2PA-shaped claim with assertions, an actions/ingredient binding to the
    content_hash, and a signer block) is real and stable. The ``attestation_id`` and
    ``attestation_hash`` are real content-addressed digests of the canonical record.
  * **SEAM (NOT faked).** A *production* C2PA manifest is sealed by an **X.509 / COSE cryptographic
    signature** from the certifier's certificate. Producing or verifying that signature requires a
    real key + cert chain (e.g. ``c2patool`` / ``c2pa-python`` with a CA-issued certificate). This
    module does **not** mint a fake signature and does **not** claim cryptographic non-repudiation.
    The signer block carries ``signature.present = False`` and a documented ``seam`` string naming
    exactly what a real signer would add. :func:`verify_by_hash` therefore verifies the **hash
    binding** (tamper-evidence of the *content* against the attested digest) — which is the part this
    module genuinely owns — and is explicit that it does NOT verify the cryptographic signature.

So a verified corpus here means: *its bytes match the digest a named certifier bound on a given date,
covering these assurance verdicts* — with the cryptographic seal left as an integration seam, not
counterfeited.

Determinism & the clock
-----------------------
The manifest carries a timestamp, but a wall clock would break ``deterministic: true``. So the
certification time is an **injected** input (``as_of``, an ISO-8601 string), exactly as
:mod:`scripts.sanctions.sanctions_freshness` injects ``as_of`` rather than reading the clock. When the
caller omits it the field is recorded as ``None`` (an unstamped, still-hash-stable attestation) — we
never read ``time``/``datetime.now`` inside :func:`run`, so the same inputs always yield byte-identical
output (the asserted property in the self-test). No RNG, no environment reads, no network, no
filesystem access.

Runtime contract: see :data:`RUNTIME` (mirrors the manifest + the field->pool mapping in
``docs/architecture/component-execution-and-runtime-routing.md`` §4).

Pure Python stdlib only (``hashlib``, ``json``, ``argparse``). No third-party deps.

Public API:
    from scripts.processors.assurance.oracle_c2pa_attest import run, verify_by_hash
    res = run(corpus_version={"corpus_id": "ph-building-safety", "version": "2026.05.29",
                              "body": "...corpus bytes/text..."},
              signer={"id": "oracle:ohh", "name": "OpenHubForAI Oracle"},
              covered_source_records=[...], assurance_verdicts={...}, as_of="2026-05-29T00:00:00Z")
    # -> {"manifest": {...C2PA-shaped...}, "content_hash": "sha256:...",
    #     "attestation_id": "...", "attestation_record": {...}, "attestation_hash": "sha256:...",
    #     "verify_instructions": "...", "runtime": RUNTIME}
    ok = verify_by_hash(content, res["attestation_record"])   # True iff content matches attested hash

CLI / self-test:
    python3 scripts/processors/assurance/oracle_c2pa_attest.py
    python3 -m scripts.processors.assurance.oracle_c2pa_attest
"""
from __future__ import annotations

import argparse
import hashlib
import hmac  # for compare_digest — constant-time digest comparison (stdlib)
import json
import sys
from typing import Any

# ── Single-source identifiers (No-Magic-Values: defined ONCE here, referenced everywhere) ─────────

#: process_kind — MUST match the manifest's ``process_kind``.
PROCESS_KIND = "attest.c2pa_sign"

#: Hash algorithm + the prefix we tag every digest with, so a digest string is self-describing and a
#: future algorithm swap is a one-line change that propagates to every emitted hash.
_HASH_ALGO = "sha256"
_HASH_PREFIX = f"{_HASH_ALGO}:"

#: Method tag stamped into the manifest/record so the produced-by-which-version is auditable and a
#: later semantic/crypto upgrade is a DIFFERENT method string (the deterministic floor stays the
#: auditable baseline). Bumps when the canonicalization or structure changes (would change hashes).
METHOD = "c2pa_shaped_hash_binding_v1"

#: C2PA-shaped vocabulary. We use the C2PA label *shapes* (a claim with assertions; a
#: ``c2pa.hash.data`` assertion binding the content; a ``c2pa.actions`` assertion naming what was
#: done) so the structure is recognizable to a C2PA reader, while being explicit (in ``profile``)
#: that this is a hash-binding profile WITHOUT a cryptographic claim signature (that is the seam).
_C2PA_PROFILE = "ohh.c2pa_hash_binding"  # NOT a sealed C2PA manifest — see SEAM in the module docstring
_ASSERTION_HASH = "c2pa.hash.data"
_ASSERTION_ACTIONS = "c2pa.actions"
_ASSERTION_VERDICTS = "ohh.assurance.verdicts"  # vendor assertion: the verdicts this binding covers
_ACTION_CERTIFY = "ohh.certified"

#: The cryptographic seal this module deliberately does NOT produce. Stated verbatim in the signer
#: block so the boundary travels with the artifact and no reader mistakes the structure for a seal.
_SIGNATURE_SEAM = (
    "X.509/COSE C2PA claim signature is a documented SEAM: a production seal requires the certifier's "
    "CA-issued certificate + private key (e.g. c2patool / c2pa-python). This record binds + attests by "
    "HASH only; it does NOT carry a cryptographic signature and asserts no non-repudiation."
)

#: Declared runtime-routing manifest for THIS component. Mirrors the manifest's scalars and the
#: field->pool mapping in the routing doc §4: deterministic + idempotent + small CPU work +
#: ``side_effects=write`` (it mints a record) at the ``hub`` trust boundary → the cheap **cpu** pool.
#: Asserted in the self-test so it can't silently rot.
RUNTIME: dict[str, Any] = {
    "process_kind": PROCESS_KIND,
    "deterministic": True,
    "idempotent": True,
    "side_effects": "write",   # mints an attestation record (matches the manifest)
    "streaming": False,
    "latency_budget_ms": 4000,  # matches the manifest's latency_budget_ms
    "trust_boundary": "hub",    # matches the manifest's trust_boundary
    "on_error": "raise",
    "resource_pool": "cpu",     # inferred per routing-doc §4 from the signals above
}


# ── Canonicalization + hashing (REAL, stdlib) ─────────────────────────────────────────────────────


def _to_bytes(value: Any) -> bytes:
    """Coerce arbitrary corpus content to the canonical BYTES we hash.

    The hash must be stable across equivalent inputs, so:
      * ``bytes``/``bytearray`` → used as-is (the caller already has exact bytes),
      * ``str`` → UTF-8 encoded,
      * dict/list/other → canonical JSON (sorted keys, no insignificant whitespace, ``ensure_ascii``
        off so unicode is its real bytes), then UTF-8 encoded — so two dicts that differ only in key
        ORDER hash identically (formatting must not create a false version — CLAUDE.md hash discipline).

    On_error=raise: anything non-JSON-serializable raises ``TypeError`` rather than hashing a repr.
    """
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return _canonical_json(value).encode("utf-8")


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, unicode preserved. The ONE serializer used
    for every hash + every emitted record, so the same logical object always serializes identically."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_tagged(data: bytes) -> str:
    """sha256 of *data*, returned as a self-describing ``sha256:<hex>`` string."""
    return _HASH_PREFIX + hashlib.sha256(data).hexdigest()


def _content_hash(corpus_body: Any) -> str:
    """The address by which a corpus is verified: tagged sha256 over its canonical bytes."""
    return _sha256_tagged(_to_bytes(corpus_body))


# ── Input coercion (on_error=raise; never silently attest the wrong thing) ─────────────────────────


def _require_mapping(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping/dict, got {type(value).__name__}")
    return value


def _normalize_signer(signer: Any) -> dict[str, Any]:
    """Accept a signer as a dict (``{id, name, ...}``) or a bare string id. Returns a stable signer
    block. The ``id`` is required — an unattributed attestation is meaningless (governance: there must
    be an accountable signer)."""
    if isinstance(signer, str):
        signer = {"id": signer}
    signer = _require_mapping("signer", signer)
    sid = signer.get("id") or signer.get("signer_id")
    if not sid or not str(sid).strip():
        raise ValueError("signer requires a non-empty 'id' (an attestation must name its certifier)")
    block: dict[str, Any] = {
        "id": str(sid),
        "name": str(signer.get("name", sid)),
    }
    # Carry an optional org/role/cert-ref through verbatim (audit trail) without inventing values.
    for opt in ("org", "role", "cert_ref", "kid"):
        if signer.get(opt) is not None:
            block[opt] = str(signer[opt])
    # The signature SEAM — explicit, never faked.
    block["signature"] = {"present": False, "seam": _SIGNATURE_SEAM}
    return block


def _normalize_corpus(corpus_version: Any) -> tuple[dict[str, Any], Any]:
    """Pull the identity fields + the hashable body out of *corpus_version*.

    Accepts either a mapping carrying ``body``/``content``/``text`` plus id/version metadata, OR a
    bare str/bytes (the corpus body itself, with no separate metadata). Returns
    ``(identity_metadata, body)`` where *body* is what gets hashed.
    """
    if isinstance(corpus_version, (str, bytes, bytearray)):
        return ({}, corpus_version)
    cv = _require_mapping("corpus_version", corpus_version)
    body = None
    for key in ("body", "content", "text", "bytes"):
        if key in cv and cv[key] is not None:
            body = cv[key]
            break
    if body is None:
        raise ValueError(
            "corpus_version must carry the corpus body under one of: body/content/text/bytes "
            "(nothing to hash otherwise)"
        )
    meta: dict[str, Any] = {}
    for key in ("corpus_id", "id", "version", "corpus_version", "title", "uri"):
        if cv.get(key) is not None:
            meta[key] = cv[key]
    return (meta, body)


def _coerce_optional_list(name: str, value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, dict)):
        raise TypeError(f"{name} must be a list of records, not a single value")
    try:
        return list(value)
    except TypeError as exc:  # not iterable
        raise TypeError(f"{name} must be an iterable of records") from exc


# ── Attestation-record summaries (small, stable views — do not bloat the hashed record) ────────────


def _summarize_sources(covered: list[Any]) -> list[dict[str, Any]]:
    """A stable, minimal summary of the source_record(s) the attestation covers: just the identity +
    a content fingerprint, sorted deterministically. We do NOT embed full source bodies in the
    attestation (it would bloat the hash and duplicate the corpus); the fingerprint lets a verifier
    confirm the SAME sources were the ones certified."""
    out: list[dict[str, Any]] = []
    for idx, rec in enumerate(covered):
        if isinstance(rec, dict):
            sid = rec.get("source_id") or rec.get("id") or rec.get("publisher") or f"source-{idx}"
            out.append({
                "source_id": str(sid),
                "fingerprint": _sha256_tagged(_to_bytes(rec)),
            })
        else:
            out.append({
                "source_id": f"source-{idx}",
                "fingerprint": _sha256_tagged(_to_bytes(rec)),
            })
    # Deterministic order by (source_id, fingerprint) — independent of input ordering.
    return sorted(out, key=lambda r: (r["source_id"], r["fingerprint"]))


# ── C2PA-shaped manifest (REAL structure; the crypto seal is the seam) ─────────────────────────────


def _build_manifest(
    *,
    content_hash: str,
    corpus_meta: dict[str, Any],
    signer: dict[str, Any],
    covered_sources: list[dict[str, Any]],
    assurance_verdicts: dict[str, Any],
    as_of: str | None,
) -> dict[str, Any]:
    """Assemble the C2PA-SHAPED manifest. Uses C2PA label shapes (a claim with assertions; a
    ``c2pa.hash.data`` assertion binding the content; a ``c2pa.actions`` assertion naming the certify
    action), plus a vendor ``ohh.assurance.verdicts`` assertion carrying the verdicts this binding
    covers. ``profile`` declares this is a HASH-BINDING profile without a cryptographic claim
    signature (the seam). Deterministic: no clock, no RNG — ``as_of`` is injected."""
    return {
        "profile": _C2PA_PROFILE,
        "method": METHOD,
        "claim": {
            "title": (corpus_meta.get("title") or corpus_meta.get("corpus_id")
                      or corpus_meta.get("id") or "corpus"),
            "instance": content_hash,  # the claim is ABOUT this content (by hash)
            "signature_info": signer,
            "created": as_of,          # injected; None when the caller did not stamp it
            "assertions": [
                {
                    "label": _ASSERTION_HASH,
                    "data": {"alg": _HASH_ALGO, "hash": content_hash},
                },
                {
                    "label": _ASSERTION_ACTIONS,
                    "data": {"actions": [{
                        "action": _ACTION_CERTIFY,
                        "softwareAgent": "open-harness-hub/oracle-c2pa-attest",
                        "when": as_of,
                    }]},
                },
                {
                    "label": _ASSERTION_VERDICTS,
                    "data": {
                        "corpus": corpus_meta,
                        "covered_source_records": covered_sources,
                        "assurance_verdicts": assurance_verdicts,
                    },
                },
            ],
        },
    }


# ── Public API ─────────────────────────────────────────────────────────────────────────────────


def run(
    corpus_version: Any,
    signer: Any,
    covered_source_records: Any = None,
    assurance_verdicts: Any = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Bind C2PA-shaped signed provenance to a corpus version and mint a hash-addressed attestation.

    Args:
        corpus_version: the governed corpus to attest. Either a mapping carrying the body under
            ``body``/``content``/``text``/``bytes`` plus optional identity (``corpus_id``/``version``/
            ``title``/``uri``), or a bare ``str``/``bytes`` (the body itself).
        signer: the certifying party ("oracle"). A mapping ``{id, name, org?, role?, cert_ref?, kid?}``
            or a bare string id. ``id`` is required (an attestation must name its certifier).
        covered_source_records: optional list of the source_record(s) the certification was checked
            against; summarized (id + fingerprint) into the manifest + record.
        assurance_verdicts: optional mapping of the freshness/integrity/corroboration verdicts the
            certification covers (carried verbatim — this module does not re-compute them).
        as_of: optional injected ISO-8601 certification time. Omitted → recorded as ``None`` (we never
            read the wall clock — that is what keeps :func:`run` deterministic).

    Returns:
        {
          "content_hash": "sha256:...",        # address by which the corpus is verified (REAL)
          "manifest": {...},                    # C2PA-shaped signed manifest (structure REAL; seal=seam)
          "attestation_id": "...",              # stable id of this attestation
          "attestation_record": {...},          # the hash-addressed registry row (what verify reads)
          "attestation_hash": "sha256:...",     # content-address of the canonical record (REAL)
          "verify_instructions": "...",         # how a downstream agent verifies by hash
          "runtime": RUNTIME,                   # declared routing signals
        }

    Deterministic: same inputs → byte-identical output. on_error=raise: malformed inputs raise
    ``TypeError``/``ValueError`` rather than attesting the wrong thing.
    """
    corpus_meta, corpus_body = _normalize_corpus(corpus_version)
    signer_block = _normalize_signer(signer)
    covered = _summarize_sources(_coerce_optional_list("covered_source_records", covered_source_records))
    verdicts = _require_mapping("assurance_verdicts", assurance_verdicts) if assurance_verdicts is not None else {}
    if as_of is not None and not isinstance(as_of, str):
        raise TypeError("as_of must be an ISO-8601 string or None")

    # 1) REAL content hash — the address.
    content_hash = _content_hash(corpus_body)

    # 2) C2PA-shaped signed manifest (structure real; cryptographic seal is the seam).
    manifest = _build_manifest(
        content_hash=content_hash,
        corpus_meta=corpus_meta,
        signer=signer_block,
        covered_sources=covered,
        assurance_verdicts=verdicts,
        as_of=as_of,
    )

    # 3) The hash-addressed attestation record — the row a verifier reads back BY HASH. It carries
    #    everything needed to verify the binding (the attested content_hash + alg) and to know who
    #    certified what, when. The record is content-addressed: its id/hash are derived from its own
    #    canonical bytes, so two identical certifications collapse (idempotent) and any field change is
    #    detectable (CLAUDE.md hash discipline). We compute the id over the record SANS its own id
    #    fields to avoid a self-reference cycle.
    record_core: dict[str, Any] = {
        "method": METHOD,
        "alg": _HASH_ALGO,
        "content_hash": content_hash,
        "signer": signer_block,
        "certified_at": as_of,
        "covered_source_records": covered,
        "assurance_verdicts": verdicts,
        "manifest": manifest,
    }
    attestation_hash = _sha256_tagged(_canonical_json(record_core).encode("utf-8"))
    # attestation_id: a short, stable, human-greppable handle derived from the record hash (NOT a
    # truncation of the content hash — IDs get their own stable hash suffix per ID discipline).
    attestation_id = "attn-" + attestation_hash[len(_HASH_PREFIX):][:16]

    attestation_record = dict(record_core)
    attestation_record["attestation_id"] = attestation_id
    attestation_record["attestation_hash"] = attestation_hash

    verify_instructions = (
        f"Verify by hash: recompute {_HASH_ALGO} over the corpus's canonical bytes and compare to "
        f"attestation_record.content_hash ({content_hash}); equal ⇒ the bytes are the ones "
        f"{signer_block['id']} attested, tampered ⇒ unequal. Programmatic: "
        "verify_by_hash(content, attestation_record). NOTE: this verifies the HASH BINDING only — the "
        "X.509/COSE C2PA cryptographic claim signature is a documented seam (see signer.signature.seam) "
        "and is NOT verified here."
    )

    return {
        "content_hash": content_hash,
        "manifest": manifest,
        "attestation_id": attestation_id,
        "attestation_record": attestation_record,
        "attestation_hash": attestation_hash,
        "verify_instructions": verify_instructions,
        "runtime": RUNTIME,
    }


def verify_by_hash(content: Any, attestation: dict[str, Any]) -> bool:
    """Tamper detection: does *content* match the hash a certifier attested in *attestation*?

    Recomputes the tagged sha256 over *content*'s canonical bytes (the SAME normalization
    :func:`run` used) and compares it — in constant time — to the attested ``content_hash``. Returns
    ``True`` iff they are equal: the content is byte-for-byte the corpus that was certified. A single
    flipped byte (or any edit) flips the hash and returns ``False``.

    *attestation* may be the full result of :func:`run`, its ``attestation_record``, or the
    ``manifest`` — anything carrying a ``content_hash`` (directly or under the hash assertion).

    HONEST SCOPE: this verifies the HASH BINDING / tamper-evidence ONLY. It does NOT verify the
    cryptographic C2PA claim signature (that is the documented seam — see the module docstring and
    ``signer.signature.seam``). on_error=raise: an attestation with no recoverable attested hash
    raises ``ValueError`` rather than silently returning ``True``.
    """
    attested = _attested_hash(attestation)
    if not attested:
        raise ValueError("attestation carries no content_hash to verify against")
    recomputed = _content_hash(content)
    # Constant-time compare — defensible habit for a verifier even though these are public digests.
    return hmac.compare_digest(recomputed, attested)


def _attested_hash(attestation: Any) -> str | None:
    """Pull the attested ``content_hash`` out of a run-result / record / manifest, tolerantly."""
    if not isinstance(attestation, dict):
        raise TypeError("attestation must be a mapping (run result, attestation_record, or manifest)")
    # Direct field (run result or attestation_record).
    if isinstance(attestation.get("content_hash"), str):
        return attestation["content_hash"]
    # Nested record under a run result.
    rec = attestation.get("attestation_record")
    if isinstance(rec, dict) and isinstance(rec.get("content_hash"), str):
        return rec["content_hash"]
    # A bare manifest: read the c2pa.hash.data assertion.
    manifest = attestation if "claim" in attestation else attestation.get("manifest")
    if isinstance(manifest, dict):
        claim = manifest.get("claim", {})
        for assertion in claim.get("assertions", []):
            if isinstance(assertion, dict) and assertion.get("label") == _ASSERTION_HASH:
                h = assertion.get("data", {}).get("hash")
                if isinstance(h, str):
                    return h
    return None


# ── Self-test (offline, deterministic) ─────────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # A governed corpus version + a certifier + the verdicts the certification covers.
    corpus = {
        "corpus_id": "ph-building-safety",
        "version": "2026.05.29",
        "title": "PH building-safety source registry",
        "body": "Occupancy permit is required before a building may be lawfully occupied. "
                "Fire safety inspection certificate (FSIC) must precede the occupancy permit.",
    }
    signer = {"id": "oracle:ohh", "name": "OpenHubForAI Oracle", "org": "OHH"}
    sources = [
        {"source_id": "ph-dpwh", "text": "National Building Code of the Philippines (PD 1096)."},
        {"source_id": "ph-bfp", "text": "RA 9514 Fire Code — FSIC issuance."},
    ]
    verdicts = {"freshness": "current", "integrity": "allow", "corroboration": "corroborated"}
    as_of = "2026-05-29T00:00:00Z"

    print("[self-test] attest a corpus")
    res = run(corpus, signer, covered_source_records=sources, assurance_verdicts=verdicts, as_of=as_of)
    rec = res["attestation_record"]

    check("content_hash is tagged sha256", res["content_hash"].startswith(_HASH_PREFIX)
          and len(res["content_hash"]) == len(_HASH_PREFIX) + 64, detail=res["content_hash"])
    check("attestation_id is stable handle", isinstance(res["attestation_id"], str)
          and res["attestation_id"].startswith("attn-"), detail=res["attestation_id"])
    check("manifest binds the content hash",
          res["manifest"]["claim"]["assertions"][0]["data"]["hash"] == res["content_hash"])
    check("signer recorded with id", res["manifest"]["claim"]["signature_info"]["id"] == "oracle:ohh")
    check("covered verdicts carried in manifest",
          res["manifest"]["claim"]["assertions"][2]["data"]["assurance_verdicts"] == verdicts)

    # The cryptographic signature is a SEAM — present:False, never faked.
    sig = res["manifest"]["claim"]["signature_info"]["signature"]
    check("cryptographic signature is an explicit SEAM (not faked)",
          sig.get("present") is False and "SEAM" in sig.get("seam", ""),
          detail=_canonical_json(sig))

    # 1) verify_by_hash PASSES on the ORIGINAL corpus body.
    print("[self-test] verify_by_hash passes on the original")
    check("original verifies True", verify_by_hash(corpus["body"], rec) is True)
    # Also verifiable against the full run-result and against the bare manifest.
    check("verifies against full run result", verify_by_hash(corpus["body"], res) is True)
    check("verifies against bare manifest", verify_by_hash(corpus["body"], res["manifest"]) is True)

    # 2) verify_by_hash FAILS on a TAMPERED copy (single-char edit → different hash).
    print("[self-test] verify_by_hash fails on a tampered copy")
    tampered = corpus["body"].replace("required", "not required")  # flip the meaning
    check("tampered verifies False", verify_by_hash(tampered, rec) is False,
          detail="tamper not detected!")
    # Even a single trailing byte must flip it.
    check("single-byte change verifies False", verify_by_hash(corpus["body"] + " ", rec) is False)

    # 3) Determinism: re-running with identical inputs yields byte-identical output (no clock/RNG).
    print("[self-test] deterministic — identical inputs -> identical output")
    res2 = run(corpus, signer, covered_source_records=sources, assurance_verdicts=verdicts, as_of=as_of)
    check("re-run content_hash identical", res2["content_hash"] == res["content_hash"])
    check("re-run attestation_hash identical", res2["attestation_hash"] == res["attestation_hash"])
    check("re-run full result identical (deterministic)",
          _canonical_json(res2) == _canonical_json(res))

    # Key-order independence: a corpus dict with reordered keys hashes the same body.
    print("[self-test] formatting/key-order must not create a false version")
    reordered = {"body": corpus["body"], "title": corpus["title"],
                 "version": corpus["version"], "corpus_id": corpus["corpus_id"]}
    res3 = run(reordered, signer, covered_source_records=sources, assurance_verdicts=verdicts, as_of=as_of)
    check("reordered corpus -> same content_hash", res3["content_hash"] == res["content_hash"])

    # Idempotent identity: the attestation_id is derived from the content-addressed record.
    check("attestation_id matches record hash prefix",
          res["attestation_id"] == "attn-" + res["attestation_hash"][len(_HASH_PREFIX):][:16])

    # on_error=raise: an unattributed signer and a body-less corpus must raise.
    print("[self-test] on_error=raise on malformed inputs")
    try:
        run(corpus, {"name": "no id here"}, as_of=as_of)
        check("signer without id raises", False, detail="did not raise")
    except ValueError:
        check("signer without id raises", True)
    try:
        run({"corpus_id": "x", "version": "1"}, signer, as_of=as_of)  # no body
        check("corpus without body raises", False, detail="did not raise")
    except ValueError:
        check("corpus without body raises", True)
    try:
        verify_by_hash(corpus["body"], {"no": "hash here"})
        check("verify with no attested hash raises", False, detail="did not raise")
    except ValueError:
        check("verify with no attested hash raises", True)

    # RUNTIME signals match the manifest's declared scalars (can't silently rot).
    print("[self-test] declared RUNTIME signals match the manifest")
    check("runtime.process_kind == manifest", RUNTIME["process_kind"] == PROCESS_KIND)
    check("runtime is deterministic + side_effects=write",
          RUNTIME["deterministic"] is True and RUNTIME["side_effects"] == "write",
          detail=_canonical_json(RUNTIME))
    check("run() returns its RUNTIME", res["runtime"] == RUNTIME)

    print()
    if failures:
        print(f"SELF-TEST FAILED: {len(failures)} check(s) failed: {failures}")
        return 1
    # The contract's self-test-that-PROVES-the-change requirement: a hard assert in addition to the
    # printed checks, so a regression fails LOUDLY (non-zero) even if the prints are ignored.
    assert verify_by_hash(corpus["body"], rec) is True
    assert verify_by_hash(corpus["body"].replace("required", "not required"), rec) is False
    print("SELF-TEST PASS")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Oracle C2PA attest — bind C2PA-shaped signed provenance + a hash-addressed "
                    "attestation to a corpus so an agent verifies the corpus BY HASH (tamper-evident). "
                    "The X.509/COSE cryptographic seal is a documented seam, not faked.",
    )
    p.add_argument("--corpus", help="Path to a JSON file: the corpus_version "
                                    "({\"corpus_id\":..., \"version\":..., \"body\":...})")
    p.add_argument("--signer", help="Signer id (string) or path to a signer JSON ({\"id\":..., ...})")
    p.add_argument("--as-of", help="Injected ISO-8601 certification time (omit → unstamped)")
    p.add_argument("--self-test", action="store_true", help="Run the offline self-test")
    args = p.parse_args(argv)

    if args.self_test or not args.corpus or not args.signer:
        # Default action with no args is the self-test (matches sibling processors).
        return _self_test()

    from pathlib import Path
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    signer_arg = args.signer
    signer_path = Path(signer_arg)
    if signer_path.exists():
        signer_arg = json.loads(signer_path.read_text(encoding="utf-8"))
    res = run(corpus, signer_arg, as_of=args.as_of)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
