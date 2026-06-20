#!/usr/bin/env python3
"""scripts.llm_gateway.secrets — SecretsResolver: provider configs reference secrets, never contain them.

Provider config carries ``api_key_ref="env://OPENAI_API_KEY"`` (or ``secret://…`` later) — NEVER a raw key.
The resolver reads the value at runtime only; it never logs or echoes the value, and a missing secret raises
a clear ``UnavailableSecret`` (the system stays green; the provider is simply unavailable). No key is ever
written to code, config, artifacts, receipts, logs, or the dashboard.
"""
from __future__ import annotations

import os


class UnavailableSecret(Exception):
    """A referenced secret is not present in the environment (provider stays unavailable, not a crash)."""


class SecretsResolver:
    SCHEMES = ("env://",)

    @staticmethod
    def is_ref(value: str) -> bool:
        return isinstance(value, str) and value.startswith(SecretsResolver.SCHEMES)

    @staticmethod
    def has(ref: str) -> bool:
        if not SecretsResolver.is_ref(ref):
            return False
        if ref.startswith("env://"):
            return bool(os.environ.get(ref[len("env://"):], ""))
        return False

    @staticmethod
    def get(ref: str) -> str:
        if not SecretsResolver.is_ref(ref):
            raise UnavailableSecret(f"not a secret ref (must be env://…): {ref!r}")
        if ref.startswith("env://"):
            name = ref[len("env://"):]
            val = os.environ.get(name, "")
            if not val:
                raise UnavailableSecret(f"env var {name} is not set")  # message names the var, NOT the value
            return val
        raise UnavailableSecret(f"unsupported secret scheme: {ref!r}")
