"""local_emulators — importable, dependency-free local stand-ins for the LIVE go-live seams (LLM inference and
authoritative-source + CDC freshness), so the whole stack can run locally (Docker / Tilt / in-process) without a
GPU, an API key, a network call, or paid cloud. Each emulator is in-process testable AND runnable as a tiny
stdlib-only HTTP container. Emulators are dev scaffolding — they NEVER serve truth.
"""
from local_emulators.model_emulator import ModelEmulator
from local_emulators.source_of_truth_emulator import SourceOfTruthEmulator

__all__ = ["ModelEmulator", "SourceOfTruthEmulator"]
