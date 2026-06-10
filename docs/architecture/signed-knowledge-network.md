# Signed Knowledge Network

Open Harness Hub can become a network for signed RAG and LLM pipeline objects: people, organizations, projects, governments, and agents publish knowledge objects that can be verified, indexed, embedded, composed into pipelines, and revoked when stale or unauthorized.

This is not only a content upload feature. It is an identity, provenance, consent, and trust layer for reusable AI context.

## Core Idea

A publisher should be able to publish:

- personal profile facts, preferences, constraints, work history, credentials, public contact rules, and portfolio components;
- organizational facts, policies, service descriptions, pricing, schemas, APIs, compliance rules, and support procedures;
- government or institutional facts, laws, forms, eligibility rules, public notices, and regulatory interpretations;
- project-specific objects such as READMEs, runbooks, deployment blueprints, eval results, model cards, and component manifests.

Each object carries a signature envelope, provenance metadata, usage permissions, privacy boundary, expiration or refresh policy, and revocation handle. Pipelines can then decide which objects are safe to retrieve, quote, summarize, transform, or use as decision context.

## Why This Matters

LLM systems are increasingly limited by trustworthy context, not only by model quality. A signed knowledge network gives the platform a way to answer:

- who asserted this fact;
- when it was asserted;
- whether the publisher still stands behind it;
- what the object may be used for;
- whether a downstream pipeline can disclose, cache, transform, or cite it;
- whether another publisher, registry, DNS record, repository, DID document, certificate, or manual review supports the claim.

For individuals, this can become a portable personal RAG profile. For organizations, it becomes a machine-readable trust surface. For the platform, it becomes the substrate for verified primitive discovery and deployment.

## Object Model

Minimum fields for a signed knowledge object:

- `object_id`: stable identifier for the published object.
- `publisher_id`: person, organization, agency, project, or agent.
- `subject`: the person, organization, domain, asset, law, service, or component the object is about.
- `claims`: structured facts, documents, links, schemas, embeddings, or manifests.
- `signature`: cryptographic signature or attestation reference.
- `verification_methods`: DNS, repository signature, DID, WebAuthn, certificate, government registry, OAuth domain proof, manual review, or delegated publisher authority.
- `license`: reuse terms for the object.
- `usage_policy`: whether it may be retrieved, summarized, quoted, embedded, fine-tuned on, cached, transformed, or exported.
- `privacy_boundary`: public, link-shared, tenant-private, user-private, confidential, regulated, or forbidden for model context.
- `freshness`: stable, periodic, volatile, or event-driven.
- `revocation`: URL, registry entry, signed tombstone, or key rotation record.

## Trust Levels

The platform should separate authenticity from correctness.

- **Unsigned**: useful for drafts and private notes, not public trust.
- **Self-signed**: publisher controls the key, but claims are not independently verified.
- **Domain-verified**: publisher controls a DNS domain, repository, package, or website.
- **Registry-verified**: publisher is matched to a government, corporate, academic, package, or standards registry.
- **Delegated authority**: a verified publisher grants another party publishing rights for a scope.
- **Community-reviewed**: claims have curator, user, or expert review signals.
- **Evaluated**: claims or primitives have benchmark, transformation, reproducibility, or deployment evidence.

## Pipeline Implications

Signed knowledge objects should flow through the same pipeline substrate as primitives:

1. publisher identity proof;
2. signature and revocation verification;
3. privacy and usage policy classification;
4. claim normalization;
5. embedding and keyword indexing;
6. graph edge extraction;
7. LLM-polished search summaries;
8. human or automated review;
9. deployment into RAG, agent, workflow, or evaluation pipelines.

This lets a user say: “build a pipeline that can use my verified professional profile, my organization’s current policies, and the latest government rule pack, but do not leak private notes into model context.”

## Product Direction

This creates a “network of RAG objects”:

- personal AI context profiles;
- signed organization knowledge hubs;
- verified government fact feeds;
- portable pipeline dependency manifests;
- public and private primitive registries;
- trust-aware search, ranking, and recommendations;
- revocable knowledge packages for deployed agents.

The competitive angle is that most workflow builders focus on execution. This layer focuses on portable, signed, evaluated, cost-aware, and policy-aware context that can improve any downstream LLM pipeline.
