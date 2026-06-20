# Oracle C2PA attest (bind C2PA signed provenance + attestation-registry hash so an agent verifies a corpus by hash)

*processor* · `processor/oracle-c2pa-attest` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. Binds C2PA signed provenance to a governed corpus
object and records an attestation in a hash-addressed registry, so that a
downstream agent can verify a corpus BY HASH and see WHO certified it and WHEN.
This is the signed-provenance axis of context assurance.

WHAT C2PA GIVES, AND WHAT IT DOES NOT (honest framing): C2PA is a signed
provenance standard — it binds ORIGIN (who produced / signed this content,
using a certificate-backed signature) into a tamper-evident manifest. C2PA
attests origin, NOT correctness. This processor therefore does TWO things and
is explicit that they are different:
  1. C2PA signing — produce a C2PA manifest over the corpus object's
     content_hash and origin metadata, signed by the certifying party
     ("oracle"); this proves origin and tamper-evidence.
  2. Attestation registry — record an attestation row keyed by the corpus
     content_hash: who certified it, against which authoritative
     source_record(s) it was checked (the freshness / integrity / reconcile
     verdicts), and when. An agent then verifies a corpus by presenting its
     hash and reading back the attestation: identity of the certifier PLUS the
     assurance verdicts the certification covered.

REGULATORY CONTEXT: EU AI Act Article 50 (applicable 2026-08-02) requires
machine-readable disclosure of AI-generated/manipulated content. A C2PA
manifest is a machine-readable provenance carrier that supports such
disclosure. This component records that binding; it does not itself adjudicate
legal compliance.

GOVERNANCE (honest framing): this is a governed DEFINITION of a signing +
attestation binding, not a measured-lift claim. It describes the inputs
(corpus content_hash, certifier identity, the source_record(s) and verdicts
the attestation covers), the signed artifact (C2PA manifest), and the
hash-addressed registry record. It does NOT assert a populated metric, and it
explicitly does NOT claim that a signature proves the corpus is correct — only
that origin and the recorded assurance verdicts are verifiable by hash.

| axis | value |
|---|---|
| industry | cross_industry, ai, media, government.regulatory |
| capability | verification, governance |
| modality | text, structured, image |
| lifecycle | experimental |
| trust_boundary | hub |
| license | Apache-2.0 |



