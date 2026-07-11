# Configuration standards (the shape every config must satisfy)

## Purpose

Config is the seam where operators tune the system **without editing code** — so config drift is as
dangerous as code drift, and a leaked secret in config is as dangerous as one in source. The
configuration standards (`architecture/configuration_standards.json`) declare the canonical shape
every config of a given type must satisfy, and `_repos/dev-rules-context/templates/configs/` ships starting templates that
already obey those standards.

Standards that apply to **every** config type:

- declares `schema` + `version` + `owner` + `environment_scope`;
- `environment_scope` is one of the declared enum values (`local`/`test`/`demo`/`staging`/`production`/`all`);
- **no raw secret values** — credentials appear only as references (`env://…` or `secret://…`),
  resolved at runtime by `SecretsResolver` (see `scripts/llm_gateway/secrets.py`), never logged or
  echoed.

Type-specific standards:

| Config type | Extra requirement |
|---|---|
| `source_connector_config` | declares `tenant_scope` and a deterministic `fallback_fixture` |
| `provider_config` / `llm_provider_config` / `object_store_config` / `vector_store_config` | declares an `emulator` (offline stand-in) and a `fallback` (graceful degradation) |
| `sync_policy` | declares a `cursor_strategy` and an `idempotency_strategy` |
| `retry_policy` | declares `dlq_behavior` (what happens after `max_attempts`); attempts are finite |
| `queue_policy` | declares `lease_seconds` and whether idempotency is required |
| `security_policy` | declares encryption + PII redaction + secret resolution |
| `reconciliation_policy` | declares `authority_order`, `freshness_window_seconds`, and `held_out_on_loss=true` |
| `optimization_policy` | declares a `regression_gate` and an `answer_coverage_floor` |

## Templates

`_repos/dev-rules-context/templates/configs/<config_type>/template.json` is the fill-in starting point; several types also
ship a filled-in `example.*.json`. The shipped templates today cover
`source_connector_config`, `provider_config`, `llm_provider_config`, `sync_policy`, and
`retry_policy` — these exercise every special rule (tenant scope, emulator/fallback, secret-ref,
cursor/idempotency, DLQ). Every template references its secret via `env://…` and declares its
fallback, so the proofs run offline and green.

## Proof

```bash
python3 scripts/check_configuration_standards.py --self-test
```

The proof enforces: the standards file parses; every config type declares the four required fields
and a valid `environment_scope`; every provider-style type requires a `fallback`; every template
under `_repos/dev-rules-context/templates/configs/` parses and is **secret-clean**; and — as a negative test in a temp dir —
a synthetic template carrying a raw `api_key` is **detected** (proving the secret detector bites).

## Limitations

- The standards enforce *shape and secret hygiene*, not full JSON-Schema validation of every field's
  type — the `schema` pointer names the schema that would do deep validation.
- The raw-secret detector is pattern-based (it flags inline `api_key`/`token`/`secret`/… values that
  are not `env://`/`secret://` refs); an unusually-named secret field would need the pattern
  extended. The default posture is conservative: prefer secret refs everywhere.
- Templates are starting points, not live config — the runtime loads real config elsewhere; these
  templates exist so new config is born conforming.
