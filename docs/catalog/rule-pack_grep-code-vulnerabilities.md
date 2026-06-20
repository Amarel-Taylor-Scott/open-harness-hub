# Code vulnerability + secret-detection GREP pack

*rule-pack* · `rule-pack/grep-code-vulnerabilities` · v0.1.0 · beta

GREP detectors for the highest-leverage source-code vulnerabilities
+ hardcoded secrets + dangerous-function calls. Pair with
`pipeline/code-security-review`. Cite each rule with its CWE.

Covers (cross-language: Python / JS / TS / Java / Go / shell):
 - **Secrets** (CWE-798): AWS keys, generic API tokens, JWT,
   private keys, Slack tokens, GitHub tokens
 - **Injection** (CWE-89 / CWE-78): SQL string concat, shell
   command via os.system / subprocess shell=True
 - **Deserialization** (CWE-502): pickle.loads on untrusted input
 - **Code execution** (CWE-94): eval, exec, Function() in JS
 - **XSS** (CWE-79): innerHTML / dangerouslySetInnerHTML
 - **Cryptography** (CWE-327 / CWE-326): MD5, SHA1, DES, RC4 for
   security; weak random.random for tokens
 - **Auth** (CWE-306 / CWE-287): missing @login_required, blank
   password defaults
 - **SSRF** (CWE-918): requests.get(user_url)
 - **Path traversal** (CWE-22): open(user_path) without check
 - **CSRF** (CWE-352): missing csrf_token in forms

These TRIGGER review, not block — paired with a real SAST tool
(Semgrep, Bandit, Snyk Code) for authoritative scanning.

| axis | value |
|---|---|
| industry | security, security.appsec, software |
| capability | safety_gating, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `aws_access_key_id` | critical | secrets.aws.access_key | `(?i)\b(AKIA|ASIA)[A-Z0-9]{16}\b` |
| `aws_secret_key` | critical | secrets.aws.secret_key | `(?i)aws_secret_access_key\s*[:=]\s*['"]?[A-Za-z0-9/+=]{40}['"]?` |
| `generic_api_token` | critical | secrets.generic.token | `(?i)(api[_-]?key|api[_-]?token|access[_-]?token|secret[_-]?token)\s*[:=]\s*['...` |
| `private_key_block` | critical | secrets.private_key | `-----BEGIN (RSA |EC |OPENSSH |DSA |ENCRYPTED |PGP )?PRIVATE KEY-----` |
| `jwt_token_in_code` | high | secrets.jwt | `\beyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b` |
| `slack_token` | critical | secrets.slack | `(xox[baprs]-[A-Za-z0-9-]{10,})` |
| `github_pat` | critical | secrets.github | `ghp_[A-Za-z0-9]{30,}` |
| `sqli_python_format` | critical | injection.sql.python_percent | `(?i)(execute|cursor\.execute|raw_sql)\(\s*['"][^'"]*%[sd][^'"]*['"]\s*%` |
| `sqli_python_fstring` | critical | injection.sql.python_fstring | `(?i)(execute|cursor\.execute|raw_sql)\(\s*f['"](?:[^'"\\]|\\.)*?\{(?:user|inp...` |
| `sqli_js_concat` | critical | injection.sql.js_concat | `(?i)(query|exec(?:sql)?|raw)\([\s\S]{0,80}?['"`]\s*\+\s*(req\.|request\.|inpu...` |
| `cmd_injection_shell_true` | high | injection.cmd.subprocess_shell_true | `(?i)subprocess\.(?:run|Popen|call|check_(?:call|output))\([^)]*shell\s*=\s*True` |
| `cmd_injection_os_system` | critical | injection.cmd.os_system_with_input | `(?i)os\.system\([\s\S]{0,80}?\+\s*(?:user|input|request|param)` |
| `pickle_loads_untrusted` | critical | deserialization.pickle | `(?i)pickle\.loads?\([^)]*(?:request|user|input|body|payload|message)` |
| `yaml_unsafe_load` | high | deserialization.yaml | `(?i)yaml\.load\([^)]*(?!Loader\s*=\s*SafeLoader|Loader\s*=\s*yaml\.SafeLoader)` |
| `eval_in_python` | critical | code_execution.eval | `(?i)\b(eval|exec)\([\s\S]{0,80}?(?:user|input|request|param|content)` |
| `function_constructor_js` | high | code_execution.function_constructor | `(?i)new Function\(|Function\(['"`]` |
| `xss_innerhtml` | high | xss.innerhtml | `(?i)\.innerHTML\s*=\s*(?:[^;]*?(?:user|input|request|param|response))` |
| `xss_dangerously_set` | medium | xss.react_dangerous_html | `(?i)dangerouslySetInnerHTML\s*[:=]\s*\{` |
| `weak_hash_md5` | medium | crypto.weak_hash.md5 | `(?i)\bhashlib\.md5\b|\bcrypto\.createHash\(['"]md5['"]\)|MessageDigest\.getIn...` |
| `weak_hash_sha1` | medium | crypto.weak_hash.sha1 | `(?i)\bhashlib\.sha1\b|crypto\.createHash\(['"]sha1['"]\)` |
| `weak_random_for_token` | high | crypto.weak_random_for_token | `(?i)\brandom\.random\b[\s\S]{0,80}?(?:token|password|key|secret|nonce|session)` |
| `weak_cipher_des_rc4` | high | crypto.weak_cipher | `(?i)\b(DES|RC4|Blowfish|TripleDES)\b.{0,40}(?:cipher|encrypt|decrypt)` |
| `missing_auth_decorator_django` | low | auth.missing_decorator_heuristic | `(?i)def\s+\w+\(request[\s\S]{0,300}?(?:return\s+(?:HttpResponse|JsonResponse|...` |
| `default_password_blank` | high | auth.blank_password_default | `(?i)(password|pwd|pass)\s*[:=]\s*['"]['"]` |
| `ssrf_requests_get_user_url` | high | ssrf.requests_user_controlled | `(?i)requests\.(get|post|put|delete|patch)\(\s*(?:url\s*=\s*)?(?:user|input|re...` |
| `path_traversal_open` | medium | path_traversal.open_user_path | `(?i)open\(\s*(?:user|input|request|param|filename)[\s\S]{0,40}?,\s*['"]r['"]` |
| `csrf_exempt_marker` | high | csrf.exempted | `(?i)@csrf_exempt|csrfmiddlewaretoken\s*[:=]\s*['"]?'?\bnull\b'?['"]?|csrf\s*[...` |
| `debug_true_in_prod_config` | medium | config.debug_true | `(?i)\bDEBUG\s*=\s*True\b` |
| `scale_expansion_v1_critical_signal_01` | high | grep-code-vulnerabilities.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-code-vulnerabilities.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-code-vulnerabilities.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-code-vulnerabilities.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-code-vulnerabilities.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-code-vulnerabilities.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-code-vulnerabilities.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}code.{0,24}vulnerabilities).{0,160}...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-code-vulnerabilities.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-code-vulnerabilities.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-code-vulnerabilities.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-code-vulnerabilities.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-code-vulnerabilities.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-code-vulnerabilities.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-code-vulnerabilities.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-code-vulnerabilities.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}code.{0,24}vulnerabilities).{0,160}...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-code-vulnerabilities.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-code-vulnerabilities.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-code-vulnerabilities.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-code-vulnerabilities.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-code-vulnerabilities.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-code-vulnerabilities.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-code-vulnerabilities.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-code-vulnerabilities.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}code.{0,24}vulnerabilities).{0,160}...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-code-vulnerabilities.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-code-vulnerabilities.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-code-vulnerabilities.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-code-vulnerabilities.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-code-vulnerabilities.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-code-vulnerabilities.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-code-vulnerabilities.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-code-vulnerabilities.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}code.{0,24}vulnerabilities).{0,160}...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-code-vulnerabilities.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-code-vulnerabilities.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-code-vulnerabilities.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-code-vulnerabilities.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-code-vulnerabilities.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-code-vulnerabilities.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-code-vulnerabilities.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-code-vulnerabilities.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}code.{0,24}vulnerabilities).{0,160}...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-code-vulnerabilities.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}code.{0,24}vulnerabilities).{0,160}(...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-code-vulnerabilities.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-code-vulnerabilities.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-code-vulnerabilities.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-code-vulnerabilities.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-code-vulnerabilities.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-code-vulnerabilities.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-code-vulnerabilities.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-code-vulnerabilities.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-code-vulnerabilities.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-code-vulnerabilities.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

