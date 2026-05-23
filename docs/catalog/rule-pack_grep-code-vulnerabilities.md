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

