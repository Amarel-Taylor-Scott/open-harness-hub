# Expert Email and Grounded Verification

Some knowledge objects should not be promoted just because a model extracted
them cleanly. High-risk facts, civil-society context, legal rules, public-health
guidance, labor-rights indicators, and safety-critical workflow objects need
external verification channels.

The DueCare/OpenClaw pattern is useful here: maintain a vetted reviewer network,
send small review questions by email, ingest replies, and digest the responses
into structured knowledge-object review evidence. For example:

- "Does this context fact make sense to you?"
- "Which of these indicators matters most in practice?"
- "Is this source still current?"
- "What would make this pipeline unsafe or misleading?"

The same verification gate can require additional machine checks for important
objects: grounded search, multiple LLM reviewers, source conflict checks,
archive comparison, and citation validation.

## Contact Governance

The platform should not publish scraped personal contact data. Reviewer outreach
should use consented subscribers, organization-approved contacts, role accounts,
or tenant-private contact lists with unsubscribe and suppression handling. Public
catalog seed data should store contact-policy patterns, not real email
addresses.

Each reviewer response should become a source record with:

- consent or lawful-basis metadata;
- reviewer role class rather than private identity by default;
- received timestamp and message hash;
- privacy boundary;
- permitted downstream uses;
- confidence, disagreement, and review status.

## Verification Gate

A high-risk object can require one or more gates before promotion:

1. source governance and sensitive-data screening;
2. grounded search or official-source retrieval;
3. independent model reviews with disagreement detection;
4. expert email review campaign;
5. inbound response digest into structured evidence;
6. curator review ticket when evidence conflicts or confidence is low.

The output is not just an approval. It is a review packet: evidence spans,
rankings, dissent, source freshness, and promotion constraints that downstream
RAG and pipelines can consume.
