# `src/openharnesshub/` — the OpenHarnessHub ecosystem layer

**OpenHarnessHub** is the open ecosystem for purpose-driven compute: eval harnesses, task templates,
conformance tests, skills, runtime-adapter examples, example CapabilityTasks, and the **open CapabilityTask
spec**. It is the neutral home of the standard.

> **Architectural law** (`architecture/portfolio_dependency_law.json`, enforced by
> `scripts/check_portfolio_dependency_law.py`): OpenHarnessHub depends on **neither Teleon nor Baltor**.
> Teleon *consumes* OHH artifacts; OHH never imports them. This import-freedom is what makes the spec
> credibly neutral ("Teleon implements the Open CapabilityTask Spec" — not "Teleon invented a proprietary
> task YAML").

## What OpenHarnessHub owns
public eval harnesses · open task examples · standard CapabilityTask examples · skill packs · runtime-adapter
examples · template registry · benchmark suites · conformance tests · community contributions · reference task
packages · **the open CapabilityTask spec**.

## Relationship
`OpenHarnessHub publishes reusable evidence assets → Teleon runs and governs them → Baltor consumes the result
in a vertical product.` Canonical design: `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`.
