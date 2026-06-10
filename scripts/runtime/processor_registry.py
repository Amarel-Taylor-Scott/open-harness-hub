#!/usr/bin/env python3
"""scripts.runtime.processor_registry — the ONLY way the runner loads a processor.

Runner/harness code may load processors only from here (by ``processor_id@version``); it must never import a
CFPB-specific (or any domain) module directly. An unknown ref returns a permanent ``unavailable_processor``
error, not a crash.
"""
from __future__ import annotations

from scripts.runtime.processor import Processor


class UnavailableProcessor(Exception):
    pass


class ProcessorRegistry:
    def __init__(self) -> None:
        self._by_ref: dict[str, Processor] = {}

    def register(self, processor: Processor) -> None:
        self._by_ref[processor.spec.ref] = processor

    def get(self, processor_id: str, processor_version: str) -> Processor:
        return self.resolve(f"{processor_id}@{processor_version}")

    def resolve(self, ref: str) -> Processor:
        if ref not in self._by_ref:
            raise UnavailableProcessor(ref)
        return self._by_ref[ref]

    def has(self, ref: str) -> bool:
        return ref in self._by_ref

    def refs(self) -> list[str]:
        return sorted(self._by_ref)


def default_registry() -> ProcessorRegistry:
    from scripts.runtime.builtin_processors import BUILTINS
    r = ProcessorRegistry()
    for p in BUILTINS:
        r.register(p)
    return r
