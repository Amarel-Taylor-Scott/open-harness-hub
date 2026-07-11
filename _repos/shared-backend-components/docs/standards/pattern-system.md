# The Pattern System

> How a one-off becomes a governed standard in the Baltor Context Engine monorepo, and how the
> registry + miner keep us honest about which shapes are actually load-bearing.

This is a **meta layer over existing code**. The pattern system does not add a runtime, bus, worker
framework, artifact ledger, LLM gateway, optimizer, parser, or consumption service. It only *names*,
*grades*, and *governs* the shapes the working code already repeats, and points at the real
implementations.

## Why patterns

At factory scale, a value typed twice drifts and a shape built twice diverges. When two source
adapters, two API routes, or two proof scripts are written by different turns with slightly different
conventions, the divergence becomes the bug surface. The pattern system makes the second occurrence a
*decision*: either follow the named standard or record a waiver.

## The loop: build twice -> pattern -> standard -> template -> enforced-or-waiver

```
one-off            built once. Watched, not governed. A second occurrence promotes it.
   |  (built again)
   v
candidate          the same shape exists >= 2 times. Registered with a pattern_id, but not yet the
   |               blessed way to do it. The miner flags it as an "unstandardized repetition".
   |  (a real implemented example + a passing proof)
   v
standard           the named, blessed way. Has an owner_folder, required contracts/ports/adapters/
   |               registries/proofs/docs, and a proof that the example holds. New instances SHOULD
   |               follow it.
   |  (a template that emits a conforming instance)
   v
standard+template  new instances START conforming because they are generated from a template
   |               (template_ids on the registry entry). Lowers the cost of doing it right.
   |  (an anti-bypass / CI check that fails a non-conforming new instance)
   v
enforced           a non-conforming new instance FAILS CI. This is the strongest grade. Today only
                   proof_script_pattern is enforced (scripts/check_scripts_are_entrypoints.py +
                   the determinism/offline bar gate every check_*.py).
```

A `deprecated` pattern is one that has been superseded; it is kept only so the miner can flag old
instances that still use it.

### Waivers

A new instance may deviate from a `standard`/`enforced` pattern when `waiver_allowed: true` on the
registry entry **and** the deviation is recorded (in the change ledger, per the change-verification
contract). A waiver is a dated exception, not a silent escape hatch — the intent is that it expires:
the next turn that touches the area either brings the instance into conformance or re-justifies the
waiver. Patterns whose deviation would break governance (tenant isolation, source artifacts, durable
commands, etc.) set `waiver_allowed: false`.

## The two single sources

| File | Role |
|---|---|
| `architecture/pattern_registry.json` | The source of truth: one entry per canonical pattern with its contracts/ports/adapters/registries/proofs/docs, real `detected_examples`, `maturity`, `waiver_allowed`, and `done_when`. |
| `architecture/pattern_maturity_matrix.json` | A compact projection of the registry: `pattern_id -> {maturity, has_standard, has_template, has_proof, has_docs, examples_count}`. Derived, never hand-edited. |

`scripts/check_pattern_registry.py --self-test` proves the registry holds its contract: all 25
canonical ids present, every required key present, **every `detected_examples` path exists on disk**
(the no-fake gate — a fabricated example fails the proof), maturity in the enum, and the matrix in
sync with the registry.

## The miner

`scripts/pattern_miner.py` scans `scripts/`, `_repos/baltor/backend/src/baltor/`, `architecture/`, `schemas/`,
`_repos/baltor/frontend/`, and `docs/` and grades what it finds against the registry. It is deterministic and
offline (no network, no wall-clock in output, sorted results). Run it with:

```bash
python3 scripts/pattern_miner.py --scan          # writes .agent/pattern_miner_report.json + docs/status/pattern-miner-report.md
python3 scripts/pattern_miner.py --self-test     # deterministic fixture self-test
```

The report (`.agent/pattern_miner_report.json`) has seven keys, each entry referencing **real** paths:

| Key | Meaning |
|---|---|
| `detected_patterns` | shapes seen `>= 2` times, with real example paths + their registry maturity |
| `unstandardized_repetitions` | repeated shapes whose registry entry is still `candidate` — promote to `standard` |
| `one_offs` | shapes seen exactly once — the watch list; a second occurrence makes a pattern |
| `candidate_templates` | detected patterns with no `template_ids` yet — a template would let new instances start standard |
| `anti_patterns` | real violations: raw provider/network import outside an adapter, raw sqlite in a processor, vague filenames |
| `recommended_standards` | next promotions: `candidate` patterns that now have `>= 2` real examples |
| `waivers_needed` | a registry pattern claimed `standard`/`enforced` whose scan turned up `< 2` examples — confirm the detector or file a waiver |

`scripts/check_pattern_miner.py --self-test` (run as `python3 -m scripts.check_pattern_miner
--self-test`) proves the miner returns the seven keys, detects the proof/api/docs/source/web shapes,
references the registry, is deterministic, and **never reports a path that does not exist**.

## How they fit together

```
real code  --scanned by-->  pattern_miner.py  --graded against-->  pattern_registry.json
                                   |                                       |
                                   v                                       v
                  .agent/pattern_miner_report.json            pattern_maturity_matrix.json
                  docs/status/pattern-miner-report.md          (compact roll-up)
                                   |                                       |
                                   +----------- proofs gate both ---------+
                              check_pattern_miner.py        check_pattern_registry.py
```

The registry says what the patterns *should* be; the miner says what the code *actually* repeats; the
two proofs keep both honest, and the no-fake gate guarantees every claimed example is a path you can
open. When the miner reports an `unstandardized_repetition` or a `recommended_standard`, that is the
backlog for promoting the pattern system toward full enforcement.
