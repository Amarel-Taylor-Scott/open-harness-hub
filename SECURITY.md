# Security policy

## Supported versions

The Open Harness Hub is a content catalog plus tooling. Security
patches land on `main` only; consumers pin to a release tag and
upgrade.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| latest `v0.x` tagged release | ✅ |
| older tagged releases | best-effort |

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Report privately via GitHub Security Advisories at
[Report a vulnerability](https://github.com/TaylorAmarelTech/open-harness-hub/security/advisories/new),
or email `amarel.taylor.s@gmail.com` with subject prefix
`[open-harness-hub security]`.

We aim to acknowledge reports within **3 business days** and have a
fix or mitigation plan within **30 days**.

## Scope

In scope:

- Manifests in `catalog/` that could mislead downstream pipelines
  (e.g. a privacy rule pack with a missing pattern, a tool with
  unsafe defaults).
- Tooling under `scripts/` and `scripts/emit/` (validator,
  emitters, runners).
- Generated standards artifacts (Croissant, MCP, Agent Skills, AIBOM)
  that could mislead downstream consumers.
- CI workflows in `.github/workflows/`.

Out of scope:

- Third-party tools the hub emits to (file issues with them
  upstream).
- Models loaded via configured `adapter/*` manifests (the model
  provider is responsible).
- Sample / synthetic data in tests and `samples/` (these are
  deliberately fake).

## Responsible disclosure

We follow standard coordinated-disclosure practice. We credit
reporters in release notes unless they prefer otherwise.
