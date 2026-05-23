# Synthetic code-review samples (3 cases)

*dataset* · `dataset/code-review-samples` · v0.1.0 · experimental

Three synthetic code bundles for testing
`pipeline/code-security-review`. Fully synthetic — values that
look like AWS keys / JWT / Slack tokens follow the format
documented in AWS / RFC 7519 / Slack docs but are not real
credentials.

Cases:
 - sample-clean-python.json — Flask endpoint with parameterized
   SQL, env-based secrets, hashed passwords, @login_required,
   CSRF-honoring. Expected 0 findings.
 - sample-vulnerable-python.json — Django views with hardcoded
   AWS access key + secret + GitHub PAT + Slack token + private
   key block, SQL string-format injection, MD5 password hashing,
   pickle.loads on request.body, eval of user query, subprocess
   with shell=True + format-string, DEBUG=True. Expected many
   critical findings.
 - sample-mixed-js.json — Node/Express + React with SQL string
   concat (CWE-89), Function() constructor on user input
   (CWE-94), dangerouslySetInnerHTML + innerHTML XSS (CWE-79),
   hardcoded JWT. Expected mixed signals.

| axis | value |
|---|---|
| industry | security, security.appsec, software |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



