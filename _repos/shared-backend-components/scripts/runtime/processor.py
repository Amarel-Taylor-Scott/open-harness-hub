#!/usr/bin/env python3
"""scripts.runtime.processor — the Processor port + ProcessorSpec (small protocol, not a deep hierarchy).

Every step — SourceAdapter, ParserProvider, Decomposer, VectorProvider, GraphBuilder, ConflictDetector,
Reconciler, ContextPackBuilder, ReceiptRenderer — is a Processor with the SAME signature:
``handle(command: CommandEnvelope, ctx: RuntimeContext) -> ProcessorResult``. The runner/harness only ever
calls that, so it never knows whether it is processing CFPB records, PDFs, LLM output, vectors, or edges.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from scripts.runtime.envelopes import CommandEnvelope, ProcessorResult


@dataclass
class ProcessorSpec:
    processor_id: str
    processor_version: str
    input_artifact_types: list = field(default_factory=list)
    output_artifact_types: list = field(default_factory=list)
    deterministic: bool = True
    side_effects: bool = False
    allowed_data_classifications: list = field(default_factory=lambda: ["public", "internal", "customer_confidential", "restricted"])
    network_access: bool = False
    data_access: str = "tenant"

    @property
    def ref(self) -> str:
        return f"{self.processor_id}@{self.processor_version}"


class Processor:
    spec: ProcessorSpec

    @property
    def processor_id(self) -> str:
        return self.spec.processor_id

    @property
    def processor_version(self) -> str:
        return self.spec.processor_version

    def handle(self, command: CommandEnvelope, ctx) -> ProcessorResult:  # noqa: D401
        raise NotImplementedError
