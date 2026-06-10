"""src.teleon.environments — the local-first ENVIRONMENT + REWARD SPINE implementations (Teleon-owned).

The deterministic OFFLINE :class:`local_environment_provider.LocalEnvironmentProvider` is the correctness
invariant + the fallback whenever an external (Repo2RLEnv/Harbor/OpenEnv-style, docker/network) environment is
unavailable; :class:`reward_runner.RewardRunner` is the deterministic scorer. ``baltor_cfpb_context_governance``
models a Baltor-style governed task (Reg E provisional-credit deadline) as Teleon INFRA — it never imports Baltor.

Environments MEASURE agents; an agent/LLM output is never truth, and a held-out contradiction (the stale "30 days")
is never served. Imports only the stdlib + Teleon id helpers — never Baltor. Deterministic when ``now`` is injected.
"""
