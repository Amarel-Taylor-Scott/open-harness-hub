# Phone number normalize → E.164 (Google libphonenumber)

*processor* · `processor/phone-normalize-e164` · v0.1.0 · stable

Parse free-form phone numbers into E.164 international format
(+CCNNNNNNNNNNNN) using Google libphonenumber conventions.
Returns the E.164 string + country code + number type (mobile /
fixed-line / VoIP / toll-free) + validity boolean. Handles
common formatting variants (spaces, dashes, parens, country
codes spelled out, extensions).

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, verification |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



