# Occupation Descriptions to Procedure Objects

Job descriptions are dense sources of reusable pipeline primitives. They describe what workers do, what questions they answer, what facts they use, what evidence they collect, what tools they operate, what policies constrain them, and what outputs they produce.

The practical goal is not literally to store every job description ever as free text. The goal is to normalize occupation and job-posting data into reusable work atoms that can become RAG objects, checklists, question sets, tools, evals, and deployment templates.

## Canonical Sources

Good starting surfaces:

- **O*NET**: occupation descriptions, tasks, knowledge, skills, abilities, work activities, work context, interests, work values, technology skills, and job zones.
- **ESCO**: multilingual occupations, skills, competences, and qualifications with stable concept URIs.
- **BLS ORS**: physical demands, environmental conditions, education/training/experience, and cognitive/mental requirements.
- **SOC / ISCO mappings**: occupation identifiers that let the platform link labor-market data across sources.
- **Public job postings and civil-service classifications**: current operational language, tools, credentials, policies, and domain-specific procedures.
- **Training manuals, certification exams, SOPs, audit programs, and policy manuals**: richer procedural detail than most job ads.

These sources can be combined with signed publisher knowledge objects. An institution could publish its own official job procedures, while the platform uses O*NET/ESCO/ORS as public baselines.

## Work Atom Types

Each occupation profile or job description can be decomposed into:

- `task`: action the worker performs.
- `review_question`: question the worker must answer.
- `fact_dependency`: fact, policy, metric, law, or system record needed for the task.
- `evidence_requirement`: document, log, field, transaction, image, sensor record, or citation needed to justify a decision.
- `decision_gate`: condition that routes work to close, escalate, approve, deny, monitor, or request more information.
- `tool_dependency`: software, instrument, database, API, model, or physical tool.
- `knowledge_area`: domain knowledge needed for reliable work.
- `skill`: capability needed to perform or supervise the task.
- `output_component`: report, case note, filing, diagnosis, inspection result, alert disposition, plan, or generated asset.
- `risk_control`: safety, compliance, privacy, quality, or audit requirement.
- `evaluation_rubric`: criteria used to judge whether the work was done correctly.

This makes “AML analyst,” “SOC analyst,” “claims adjuster,” “clinical coder,” “building inspector,” and “public health analyst” all reducible to searchable and composable primitives.

## Example: AML Analyst

An AML alert-review job description can yield:

- tasks: review alerts, analyze transaction patterns, document findings, escalate suspicious activity;
- questions: Does the activity match the customer profile? Are sanctions hits present? Are counterparties newly added? Is there rapid movement of funds?
- facts: customer risk rating, KYC profile, transaction history, sanctions lists, FATF/FinCEN typologies, institutional policy;
- evidence: transaction edges, graph paths, account opening date, customer occupation, prior alert dispositions;
- outputs: closeout note, enhanced due diligence request, SAR-style draft, sanctions escalation memo;
- controls: no intent assertions, cite evidence, PII redaction, BSA officer review.

## Scaling Strategy

The platform should build an occupation-to-procedure index:

1. ingest canonical occupation taxonomies;
2. normalize occupation IDs, titles, aliases, and crosswalks;
3. extract tasks, skills, tools, facts, questions, evidence, and outputs;
4. map atoms to existing catalog primitives;
5. generate missing primitive candidates;
6. score each candidate by usefulness, demand, complexity, time savings, frequency of deployment, cost savings, and difficulty for an out-of-box LLM;
7. route high-value candidates to curator review, synthetic eval generation, and deployment blueprint generation.

At scale, this becomes a machine-readable map of work. Users can describe a job, role, task, or alert workflow, and the platform can assemble the relevant questions, facts, RAG packs, tools, policies, and evaluation rubrics.

## Governance

Occupation mining needs guardrails:

- respect source licenses and terms;
- store source references, versions, and collection dates;
- distinguish public taxonomy data from proprietary job postings;
- avoid storing applicant PII or employer-confidential details;
- version source facts through archive-backed captures when pages change;
- track whether an object came from a public standard, employer submission, model extraction, or curator review.

The result is a large catalog of work primitives, not a pile of scraped job ads.
