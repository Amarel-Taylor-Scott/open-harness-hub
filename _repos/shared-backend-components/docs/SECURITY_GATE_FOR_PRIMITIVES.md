# Security Gate for Generated Primitives

> Generated/minted primitive bodies are **untrusted supply-chain artifacts** until scanned. This gate is the
> hard requirement before a primitive may be certified or serve truth. Grounded in OWASP LLM Top-10,
> Skill-Inject (80% attack success on skill files), Snyk ClawHub (76 malicious payloads), MCP Security Bench.
> Engine: `scripts/primitive_security_gate.py`. Policy: `security/primitive_code_policy.yaml`.

## Threat model

A primitive body is code we (or an LLM, or a community contributor) generated. Executing it can run arbitrary
code (`eval`/`exec`), exfiltrate data (`socket`/`requests`), execute shells (`subprocess`), deserialize
payloads to RCE (`pickle`/`marshal`/`ctypes`), read secrets (`os.environ`), write outside a sandbox, leak a
system prompt via a canary, or embed a hardcoded credential. A prompt-injection marker in a comment/docstring
can hijack a downstream agent that reads the body.

## The layered gate

- **INPUT** — reject canary / prompt-injection / hidden-instruction markers in the spec or body.
- **CODE** — AST policy (banned imports/calls), the shared `code_safety_scan` (single source in
  `primitive_package_contract`), a secrets scan, a size cap, and **optional** Bandit + Semgrep (recorded as
  `skipped: binary_not_found` when absent — the AST policy is authoritative, the external scanners are
  defense-in-depth).
- **OUTPUT** — at promotion time: output-schema validation, canary check, deterministic-replay, verifier
  pass. Owned by `promote_primitive` (lifecycle); this module owns INPUT+CODE and reports the verdict.

## Verdicts

| Status | Trigger | Action |
|---|---|---|
| **quarantine** | any *critical* finding — `dynamic_exec`, `unsafe_deserialize`, `secret_literal`, `canary_leak` | reject; never auto-promote; human security review |
| **fail** | any *high/medium* — banned import, `subprocess`, `network`, `filesystem_write`, `environment_read`, `unsafe_yaml_load`, `oversize`, `unparseable` | block promotion beyond candidate until resolved or waived |
| **pass** | no findings | eligible for candidate→validated (other gates still apply) |

## Run it

```bash
python3 scripts/primitive_security_gate.py --self-test          # gate's own mutation-gated proof
python3 scripts/primitive_security_gate.py --scan-pool          # verdict over all live pack cards
python3 scripts/primitive_security_gate.py --path body.py --out artifacts/security/report.json --strict
```

The report is deterministic (byte-stable) except the CLI-added `scanned_at` timestamp: `artifact_hash`,
`policy_hash`, `status`, `highest_severity`, `findings[]`, `scanner_results[]`, `recommended_action`.

## Current state (2026-07-08)

All **141** live pack cards → **pass (1.0)**. Our primitives are pure (stdlib + `re`/`decimal` + sibling
packs). Note: the first run flagged 28 cards as `dynamic_exec` — a **false positive** on `re.compile(...)`
(an attribute call, not the builtin `compile`). The scanner was corrected to flag only the *bare builtins*
`eval/exec/compile/__import__`; this is the kind of gate error that verify-the-verifier exists to catch
before it quarantines legitimate primitives.

## Waiver policy

A `fail` on a genuinely-needed capability (e.g. a tool wrapper that must reach the network) is waived by
declaring the capability in the primitive's `permission_manifest` and recording a waiver in the promotion
receipt with a reviewer identity. A `quarantine` is **not** waivable without human security review — it means
arbitrary code execution, deserialization RCE, a leaked secret, or an injection marker.

## Promotion integration

`serves_truth = true` requires (among the lifecycle gates) `security_gate.status == pass`. See
`docs/PRIMITIVE_LIFECYCLE.md`. `scan_pool()` yields `security_gate_pass_rate` for the benchmark taxonomy.

## Known limitations

- The AST scan is deterministic and conservative; it does not do full taint analysis (Bandit/Semgrep add
  depth when installed).
- It scans the *body text*; it does not execute the body (sandbox smoke execution is the `execute_lane` in
  `real_buildout_ab_harness`, a separate stage).
- Policy is a single YAML; per-domain policies are a future extension.
