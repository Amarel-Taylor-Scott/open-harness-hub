# Anti-pattern: Silent tool failure (empty result == success)

*pattern* · `pattern/anti-silent-tool-failure` · v0.1.0 · stable

Tool returns an empty list or null on error; the calling agent treats empty as 'nothing found' and continues. Sanctions lookup that times out returns []; agent reports 'no matches' + approves the customer. The blast radius is enormous.

| axis | value |
|---|---|
| industry | cross_industry, compliance |
| capability | safety_gating |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



