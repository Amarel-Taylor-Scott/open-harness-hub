# Address parse + standardize (USPS Pub 28 / libpostal)

*processor* · `processor/address-parse-standardize` · v0.1.0 · stable

Parse a free-form postal address into components (street_number,
street_name, suite, city, state, postal_code, country) and
standardize them to USPS Pub 28 + libpostal conventions. Handles
international addresses via libpostal's CRF parser.

Output components are normalized: state → 2-letter abbrev,
street_type expanded then re-abbreviated, suite/apt normalized.
Used as a pre-step for geocoding + dedup + USPS deliverable check.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, extraction |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



