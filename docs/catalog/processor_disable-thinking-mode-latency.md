# Disable thinking mode for sub-second on-device latency

*processor* · `processor/disable-thinking-mode-latency` · v0.1.0 · experimental

Injects a prompt prefix that suppresses extended chain-of-thought / thinking
mode on models that support it (Gemma, Gemini, Claude extended thinking),
and sets inference parameters (temperature, max_tokens, num_beams) for
sub-second response latency on low-power on-device hardware. Documented
real-world win: 20 s → <1 s on Gemma 3n mobile, enabling interactive
accessibility and real-time voice UX.

Emits a modified InferenceRequest with the prefix injected and parameters
overridden. Passthrough when thinking mode is not detected or not applicable.

CAPABILITY LIFT (structural): a bare cloud model call cannot be tuned for
sub-second on-device latency; the hardware and network round-trip are fixed.
On-device, the thinking-mode suppression prefix + param override is the
architectural mechanism that crosses the interactive latency threshold.
The lift is structural because it is a configuration fact about the local
hardware + model combination — not something a larger model makes
unnecessary. lift_reason: deterministic_guarantee (the parameter injection
is deterministic); mechanism: sub_token (response length is bounded).

| axis | value |
|---|---|
| industry | ai, education, cross_industry |
| capability | format_conversion, routing, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



