# Audio to text (Whisper)

*processor* · `processor/audio-to-text-whisper` · v0.1.0 · beta

Speech-to-text via a Whisper-family model. Returns transcript +
per-segment timestamps + detected language. Wraps `openai-whisper`,
`faster-whisper`, or `distil-whisper` based on the implementation
chosen at runtime.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, translation |
| modality | audio, text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



