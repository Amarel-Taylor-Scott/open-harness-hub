#!/usr/bin/env python3
"""scripts.runtime.ports — the capability ports every processor depends on (never globals/SDKs/the admin bus).

Processors receive a RuntimeContext holding these ports and reach the outside world ONLY through them, so a
processor can be tested with in-memory adapters and run in production against SQLite/object-store/broker
without changing a line. Ports are structural (duck-typed Protocols) — DurableStore, LocalObjectStore,
context_events.EventBus, the LLM gateway, etc. already satisfy them.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ArtifactStorePort(Protocol):
    def write(self, artifact) -> None: ...
    def load_inputs(self, command) -> list: ...


@runtime_checkable
class ObjectStorePort(Protocol):
    def put(self, tenant_id: str, data: Any, *, mime_type: str = ...) -> dict: ...
    def get(self, ref: str) -> bytes: ...


@runtime_checkable
class EventBusPort(Protocol):
    def publish_event(self, event) -> None: ...


@runtime_checkable
class DurableStorePort(Protocol):
    def enqueue(self, queue: str, payload: dict, *, idempotency_key: str = ..., max_attempts: int = ...) -> dict: ...
    def append_event(self, ev: dict) -> None: ...
    def mark_processed(self, consumer: str, message_id: str) -> bool: ...


@runtime_checkable
class LoggerPort(Protocol):
    def info(self, event: str, **fields) -> None: ...
    def warn(self, event: str, **fields) -> None: ...
    def error(self, event: str, **fields) -> None: ...


@runtime_checkable
class SecretsResolverPort(Protocol):
    def get(self, ref: str) -> str: ...
    def has(self, ref: str) -> bool: ...


@runtime_checkable
class LLMGatewayPort(Protocol):
    def complete(self, request, ctx) -> Any: ...


@runtime_checkable
class ClockPort(Protocol):
    def now_iso(self) -> str: ...
