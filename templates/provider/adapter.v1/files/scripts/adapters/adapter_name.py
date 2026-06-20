#!/usr/bin/env python3
"""scripts.adapters.{{adapter_name}} — provider adapter for {{title}} behind {{port_name}}.

GENERATED STUB (standard.provider_adapter.v1). Satisfies the structural {{port_name}} from
scripts/runtime/ports.py (duck-typed, runtime_checkable) so a processor reaches this capability ONLY through
the port — never a global SDK. Swappable: this adapter and an in-memory test adapter satisfy the SAME port.
Secrets are resolved by REF through a SecretsResolverPort, never hard-coded. No live network in --self-test.

TODO(stub): implement the {{port_name}} methods against the real {{capability}} provider.
"""
from __future__ import annotations

CAPABILITY = "{{capability}}"
PORT_NAME = "{{port_name}}"


class {{adapter_name}}Adapter:
    """A provider adapter that satisfies {{port_name}} (structural). Construct with a secrets resolver; never
    embed a key literal."""

    capability = CAPABILITY

    def __init__(self, secrets=None, *, secret_ref: str = "{{capability}}_credentials"):
        # secrets: a SecretsResolverPort (.get(ref)/.has(ref)); resolved lazily, never logged.
        self._secrets = secrets
        self._secret_ref = secret_ref

    # TODO(stub): implement the {{port_name}} method surface (see scripts/runtime/ports.py for the contract).
    def _not_ready(self, op: str):
        raise NotImplementedError(f"{{adapter_name}}Adapter.{op} is a generated stub — implement {{port_name}}")
