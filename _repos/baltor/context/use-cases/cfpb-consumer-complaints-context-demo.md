# CFPB Consumer Complaints Context Demo

Date: 2026-06-04

This demo shows how Baltor can process a public corpus into governed context
artifacts without pretending the corpus is verified truth.

The example corpus is the CFPB Consumer Complaint Database:

<https://www.consumerfinance.gov/data-research/consumer-complaints/>

The database is useful for a Baltor demo because it is public, structured,
officially published, and large enough to show why source handles, freshness,
aggregate-only claims, and receipts matter.

## Demo Boundary

Baltor should treat CFPB complaint records as public source records with
important limits:

- A complaint is a consumer-submitted report, not a verified finding.
- A consumer narrative is an allegation and should not be promoted as a durable
  fact about a company.
- Small API samples are not representative of the whole database.
- Live records can change, so every pack needs retrieval time, content hashes,
  source handles, and a receipt.

Safe pack-level claims are aggregate and source-qualified:

```text
The sample contains N complaint records.
X of N records are marked timely by the source field.
Y of N records include a public consumer narrative.
The top product/issue/state values in this sample are ...
```

Unsafe claims are blocked:

```text
The complaint narrative is true.
The company did the alleged act.
This small sample represents national complaint trends.
This sample proves misconduct.
```

## Script

The demo builder is:

```bash
python3 _repos/shared-backend-components/scripts/demo_cfpb_context_pack.py
```

Default mode is offline and uses:

```text
_repos/shared-backend-components/data/cfpb-demo/complaints-fixture.json
```

Output goes to:

```text
site/baltor-demos/cfpb-complaints/
```

Emitted files:

```text
source-records.json
context-objects.json
context-pack.json
context-receipt.json
README.md
```

## Optional Live Fetch

Live mode fetches a small public sample from the CFPB API:

```bash
python3 _repos/shared-backend-components/scripts/demo_cfpb_context_pack.py --live --limit 5
```

Optional filters:

```bash
python3 _repos/shared-backend-components/scripts/demo_cfpb_context_pack.py --live --limit 10 --state CA
python3 _repos/shared-backend-components/scripts/demo_cfpb_context_pack.py --live --limit 10 --product "Mortgage"
```

The script caps `--limit` at 50 and refuses oversized responses. This prevents a
demo from accidentally downloading a raw corpus dump.

## Baltor Flow

The demo maps to the Baltor flow:

```text
CFPB API / fixture
-> source records
-> normalized context objects
-> aggregate claims
-> risk controls
-> context pack
-> context receipt
```

This is the same pattern Baltor should use for example repos:

```text
GitHub repo
-> repository source records
-> CodeGraph objects
-> DocGraph objects
-> OrgGraph hints
-> implementation/review pack
-> context receipt
```

## Why This Matters

The CFPB demo gives Baltor a clean public proof:

- raw source data is preserved as source records
- raw narratives are not blindly trusted
- every object has source handles
- every aggregate claim has traceable evidence
- the pack states what it excluded
- the receipt explains the policy decision

That is the core Baltor claim: context is built, checked, and released like a
CI/CD artifact.
