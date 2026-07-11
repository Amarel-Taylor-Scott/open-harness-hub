# Hook Policy

AIDevObserver hooks are non-blocking and read-only by default.

Use hooks for:
- reinvention hints;
- wasted-context hints;
- cheaper registry-route hints.

Do not use hooks as promotion or truth gates.

## Hook Enforcement Boundary

Some teams also need deterministic local guard hooks, such as
backup-before-delete or private-memory redaction before a tool call. Keep those
separate from AIDevObserver's default advisory hook:

- **Advisory hook:** non-blocking reuse, token, and registry-route hints.
- **Guard hook:** optional local policy enforcement for destructive actions.
- **Compiler/proof gate:** Teleon execution truth and promotion truth.

The staged-memory pattern is documented in
`docs/codex/hook-enforced-staged-memory-system.md`.
