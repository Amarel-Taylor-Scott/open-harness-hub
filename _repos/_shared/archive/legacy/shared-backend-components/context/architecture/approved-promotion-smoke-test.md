# Approved Promotion Smoke Test

The promotion path now has a repeatable synthetic proof. The smoke runner creates one approved component candidate and runs it through:

1. active component promotion;
2. component version creation;
3. subcomponent preservation;
4. promotion-to-CDC bridging;
5. component change event emission;
6. freshness/index projection;
7. review ticket routing.

## Why This Exists

Most real generated candidates should not become active components immediately. The current seed batch correctly produces zero active components because the candidates still require review. That means the happy path needs a synthetic fixture so the loader, CDC, and index projections can be tested without weakening the review boundary.

## Expected Output

The smoke run should produce:

- 1 component row;
- 1 component version row;
- 1 subcomponent row;
- 1 component change event;
- 1 freshness/index row;
- 1 review ticket.

The review ticket is intentional. The fixture includes a previous version baseline, so the CDC planner treats the new approved version as an update rather than a first create.

## Command

```bash
python3 -m scripts.db.approved_promotion_smoke_plan --output-dir dist/approved-promotion-smoke
```

This writes staging data only. It does not connect to Postgres or publish rows by itself.
