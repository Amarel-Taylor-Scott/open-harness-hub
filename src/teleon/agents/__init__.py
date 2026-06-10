"""src.teleon.agents — the shared AI-AGENT RUNTIME layer (Teleon-owned).

Receives bounded agent requests and PROVISIONS them onto a Teleon execution backend (local emulator / K8s job /
sandbox worker / cloud function) by delegating to the runtime's execution_backend_selector + ExecutionProviderPort.
Candidate agent runtimes (ClawLess/OpenClaw, Hermes) are catalog entries only — never imported/executed; agent
output is never truth (agents PROPOSE, Baltor DISPOSES). Imports only the stdlib + Teleon runtime — never Baltor.
"""
