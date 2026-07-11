"""src.teleon.ports — the shared TELEON capability PORTS (Protocols + contract dataclasses).

A port is the contract-compatible seam behind which interchangeable providers sit (local-first golden path +
governed candidates), chosen by policy/telemetry. This package holds the Environment + Reward Spine ports:
:class:`environment_provider.EnvironmentProviderPort` and :class:`reward_provider.RewardProviderPort`. Providers
MEASURE agents; their output is never truth (``serves_truth``/``is_truth`` pinned False). Stdlib only; never Baltor.
"""
