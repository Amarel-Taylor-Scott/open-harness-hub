# Recipient tone-history loader

*processor* · `processor/recipient-tone-history` · v0.1.0 · experimental

Load the user's prior N email / chat exchanges with a specific
recipient, summarize the tone signals (formality, length,
warmth, sign-off style), and emit a tone-profile that downstream
draft-generation steps consult. Avoids drafting in the wrong
register (formal to a longtime peer, casual to a board member).

| axis | value |
|---|---|
| industry | personal_productivity |
| capability | memory, extraction |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



