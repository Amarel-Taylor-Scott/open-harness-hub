# Stream 6 — GREP / pattern-detection libraries (gitleaks / trufflehog / Presidio / Semgrep / LLM-guard / garak)

## Headline: top 12 new rule-packs (ROI-sorted)

| # | Proposed slug | Coverage |
|---|---|---|
| 1 | `rule-pack/grep-secrets-cloud-keys` | AWS `AKIA`/`ASIA`, GCP service-account JSON, Azure connection strings, DigitalOcean |
| 2 | `rule-pack/grep-secrets-ai-vendor-keys` | Anthropic `sk-ant-api03-`, OpenAI `sk-`, HF `hf_`, Cohere, Replicate |
| 3 | `rule-pack/grep-secrets-vcs-platform-pats` | GitHub `gh[ousp]_`, GitLab `glpat-`, Bitbucket, Atlassian `ATATT3` |
| 4 | `rule-pack/grep-prompt-injection-heuristics` | "ignore previous", base64-instructions, ANSI escape, invisible-Unicode |
| 5 | `rule-pack/grep-secrets-payment-saas` | Stripe `sk_live_`, Square, Twilio `SK`, SendGrid `SG.`, Slack `xox[baprs]-` |
| 6 | `rule-pack/grep-private-key-blocks` | RSA/EC/OPENSSH/PGP private-key headers, Age `AGE-SECRET-KEY-1` |
| 7 | `rule-pack/grep-jwt-and-bearer` | JWT pattern + `Authorization: Bearer` + `alg:none` |
| 8 | `rule-pack/grep-crypto-wallets` | BTC bech32/legacy, ETH, Solana, tx hashes |
| 9 | `rule-pack/grep-pii-intl-id-numbers` | Aadhaar, CPF, UK NINO/NHS, FR INSEE, JP MyNumber, DE Steuer-ID |
| 10 | `rule-pack/grep-phi-clinical-codes` | ICD-10, CPT, HCPCS, DEA, NPI, MRN heuristics |
| 11 | `rule-pack/grep-financial-banking` | IBAN+mod-97, SWIFT/BIC, ABA routing, SEPA, PAN+Luhn |
| 12 | `rule-pack/grep-llm-output-canaries` | Rebuff-style canaries, leaked system-prompt markers, refusal bypasses |

## Source breakdown

### Secrets
- **gitleaks** (gitleaks/gitleaks) — 800+ rules in `config/gitleaks.toml`. Families: cloud, platform PATs, AI vendors, payment, comms, package registries, password managers, generic high-entropy.
- **trufflehog** (trufflesecurity/trufflehog) — 800+ live-verified detectors in `pkg/detectors/`. Differentiator: per-detector `IsVerified()` calls real API.
- **Yelp/detect-secrets** — ~20 plugins.
- **GitHub native secret scanning** — partner program with 200+ token issuers and canonical prefixes (`ghp_`, `glpat-`, `AKIA`, `xoxb-`, `sk_live_`, `EAACEd...`, `AIza...`).

### PII
- **Microsoft Presidio** — `presidio-analyzer/presidio_analyzer/predefined_recognizers/`. Generic (email, phone, credit_card, IBAN, IP, MAC, URL, date, crypto) + country-specific recognizers for `us, uk, india, au, ca, fi, de, it, kr, ng, pl, sg, es, se, th, tr`.
- **scrubadub** (LeapBeyond/scrubadub) — credential, credit_card, DOB, drivers_licence, email, phone, postalcode, skype, twitter, URL, vehicle_licence_plate, plus en_GB/en_US locale packs.
- **PII-Catcher / common-clinical-pii (NLM)** — clinical-PII focus: MRN, patient name, dates-of-service, hospital codes, provider names, NPI, accession numbers.
- **Google Cloud DLP infoTypes** — 150+ codes for international ID/financial/contact types.

### Code-level security
- **Semgrep** (semgrep/semgrep-rules) — heavily used families: `python/lang/security/audit/*` (SQL injection, command injection, XSS, SSRF, path traversal), insecure crypto, deserialization (pickle, yaml.load), JWT `alg:none`, hardcoded credentials, `ai/security/*` (prompt-injection, unsafe model load).
- **bandit** (PyCQA/bandit) — ~35 plugins.
- **njsscan** (ajinabraham/njsscan) — 17 categories.
- **GitHub CodeQL** — `security-extended` + `security-and-quality` suites per language; covers CWE Top-25.

### Prompt-injection / LLM defense
- **LLM Guard** (protectai/llm-guard) — input scanners (Anonymize, BanCode, BanCompetitors, BanSubstrings, BanTopics, Code, Gibberish, InvisibleText, Language, PromptInjection, Regex, Secrets, Sentiment, TokenLimit, Toxicity) + output scanners (Bias, Deanonymize, FactualConsistency, JSON, MaliciousURLs, NoRefusal, Relevance, Sensitive, URLReachability).
- **garak** (NVIDIA/garak) — probe families: `promptinject`, `dan`, `latentinjection`, `goat`, `tap`, `atkgen`, `encoding`, `ansiescape`, `glitch`, `divergence`, `donotanswer`, `realtoxicityprompts`, `malwaregen`, `packagehallucination`, `leakreplay`, `sysprompt_extraction`, `visual_jailbreak`, `grandma`, `snowball`, `fitd`, `dra`.
- **Rebuff** (protectai/rebuff) — 4-layer defense: regex → vector-sim → LLM judge → canary leak detection.
- **NeMo Guardrails** (NVIDIA/NeMo-Guardrails) — Colang rails: input self check, output self check, topical, dialog, retrieval, fact-checking, jailbreak detection, hallucination, sensitive data, moderation.

### Domain-specific canonical regexes
- **Email**: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`
- **E.164 phone**: `\+?[1-9]\d{1,14}`
- **SWIFT/BIC**: `[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?`
- **IBAN**: `[A-Z]{2}\d{2}[A-Z0-9]{1,30}` + mod-97
- **PAN**: `\b(?:\d[ -]?){13,19}\b` + Luhn
- **US routing (ABA)**: `\b[0-9]{9}\b` + checksum
- **NPI**: `\b[1-9]\d{9}\b` + Luhn mod-10
- **DEA**: `\b[A-Z][A-Z9][0-9]{7}\b`
- **ICD-10**: `\b[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?\b`
- **CPT/HCPCS**: `\b\d{5}\b` / `\b[A-V]\d{4}\b`
- **US SSN**: `\b([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})\b`
- **UK NHS**: `\b\d{3}[- ]?\d{3}[- ]?\d{4}\b` (mod-11)
- **Aadhaar**: `\b[0-9]{4}[- :][0-9]{4}[- :][0-9]{4}\b`
- **CPF**: `\b\d{3}\.\d{3}\.\d{3}-\d{2}\b`
- **BTC**: `(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,59}`
- **ETH**: `0x[a-fA-F0-9]{40}`
- **Tx hash**: `0x[a-fA-F0-9]{64}`
