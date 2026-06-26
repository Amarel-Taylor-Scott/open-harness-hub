# Portfolio website rubrics

Seven rubrics (`rubrics/portfolio/*.json`), each item: rubric_id · description · weight · blocker ·
evidence_required · proof_script · pass_condition · fail_message. Engine: `scripts/portfolio_checks.py`.

| Rubric | Proof | Gate |
|---|---|---|
| Reuse / no-reinvention | `check_portfolio_reuse_no_reinvention.py` | discovery exists · no duplicate brand folder · existing scripts preserved · single render source · boundary configs intact |
| Brand boundaries | `check_portfolio_brand_boundaries.py` | each site owns its signature; no foreign signature in the IDENTITY zone; Teleon≠agent-deploy; Baltor≠compute-runtime; OHH≠hosted-runtime; CIE owns no runtime; cross-links present |
| Site quality (>=90) | `check_portfolio_site_quality_rubric.py` | html/title/hero/one-liner/what-is(+not)/audience/CTA/cross-links/phrases/viewport/CSS/links/no-TODO/disclaimer/boundary |
| Technical launch | `check_portfolio_technical_launch_rubric.py` | build manifest · ports 9100-9104 unique · serve exact-PID · logs/manifests · full-stack table |
| TryCloudflare | `check_portfolio_trycloudflare_rubric.py` | cloudflared detected · real-URL-only (no fakes) · honest missing/unreachable · manifests · caveat · exact tunnel-PID |
| Security / privacy | `check_portfolio_security_privacy_rubric.py` | no external JS/CSS/analytics/secrets/private-content/POST-forms |
| Customer readiness | `check_portfolio_customer_readiness_rubric.py` | one-liner+audience+problem+use-case+CTA · no production overclaim · Teleon bounded · Baltor receipts · OHH discovery-not-trust · CIE portfolio-level |

Plus: `check_portfolio_website_discovery.py`, `check_portfolio_sites_static.py`,
`check_portfolio_websites_are_distinct.py`, `check_portfolio_site_screenshots.py` (honest Playwright
limitation), `check_portfolio_launch_full_stack.py` (the SITE | LOCAL | TRYCLOUDFLARE | BRAND | QUALITY |
SECURITY | STATUS | SCREENSHOT table). All registered in the flywheel.

**GREEN / PARTIAL / RED:** GREEN = all blockers pass; PARTIAL = built/served but a non-blocker is short or
tunnels not launched; RED = a blocker fails — do not launch.
