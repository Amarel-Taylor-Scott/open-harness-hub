# Person-name canonicalize (Western + East-Asian)

*processor* · `processor/name-canonicalize` · v0.1.0 · stable

Canonicalize a person name string into structured components:
given_name, family_name, middle_names, suffix, honorific. Handles
the East-Asian convention where family name comes first; Spanish
/ Portuguese double-family-name; Arabic / Hebrew patronymics;
honorifics (Dr / Sir / Hon). Output Title-Cases each component.

NEVER assigns gender from name (this is a known bias trap).

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, extraction |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



