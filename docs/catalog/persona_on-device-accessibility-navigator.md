# On-device accessibility navigator (blind/low-vision, offline)

*persona* · `persona/on-device-accessibility-navigator` · v0.1.0 · beta

Persona for a spoken-first, screen-reader-friendly AI guide that helps blind
and low-vision users navigate their immediate physical environment using
on-device vision + OCR outputs (e.g. ML Kit, TFLite). Responses are
concise, scene-leading, hazard-first, and formatted for text-to-speech
consumption. Never requires a cloud round-trip.

CAPABILITY LIFT (structural): cloud vision APIs fail when connectivity is
absent — the gap is architectural, not quality. Running fully on-device
(Gemma 3n / MobileNet + ML Kit OCR) provides privacy-preserving, always-on
navigation assistance that a cloud-only model structurally cannot deliver.
lift_reason: no_addressable_source (sensor stream is local, ephemeral);
mechanism: channel_inaccessibility (camera feed never leaves device).

| axis | value |
|---|---|
| industry | education, healthcare.public_health, cross_industry |
| capability | dialogue, safety, generation |
| modality | text, image, audio |
| lifecycle | beta |
| trust_boundary | local |
| license | Apache-2.0 |



