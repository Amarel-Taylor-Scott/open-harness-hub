# Promotion Decision Load Plan

Promotion scoring is the bridge between high-volume generated candidates and active database-backed components. The scorer can evaluate many candidates, but the database needs a repeatable load boundary before any candidate becomes visible as a reusable component.

The promotion decision load planner turns scored JSONL into:

- `promotion-decisions.csv`
- `promotion-index-records.csv`
- `promotion-review-tickets.csv`
- `load-promotion-decisions.sql`
- `promotion-decision-load-plan.json`

The SQL loads three operational tables:

- `promotion_decision`: the score, decision, criteria, risk flags, and recommended outputs.
- `index_record`: quality search rows used by review queues and ranking.
- `review_ticket`: human or policy review tasks for risky, ambiguous, held, or rejected candidates.

## Review Boundary

Promotion decisions are not automatic publication. They are evidence for review and ranking:

1. candidate generation
2. promotion scoring
3. promotion decision load planning
4. staged database load
5. count audit
6. curator or policy approval
7. active component promotion
8. component version history and index update

This keeps the million-component factory additive without turning every generated row into a published component.

## Why This Matters At Scale

At 1M to 100M components, rebuilding search after every scoring run is too expensive. Loading promotion decisions and quality index rows incrementally lets the platform prioritize what to review next by:

- promotion score
- capability gap
- review risk
- source trust
- expected deployment frequency
- cost savings
- model-swap value

The planner is side-effect free. It writes CSV and SQL only; database execution remains a separate worker or operator step.
