# SaaS launch landing-page anti-pattern detectors

*rule-pack* · `rule-pack/grep-saas-launch-antipatterns` · v0.1.0 · experimental

Regex heuristics that catch the most common SaaS / micro-SaaS / AI-
app launch landing-page failure patterns. Designed to be run over
landing-page copy, tagline strings, feature lists, pricing pages,
and "Show HN" / Product Hunt launch posts.

Catches buzzword overload, generic ICP, hidden pricing, vague
social proof, AI-as-tagline, broken proof-of-product, and the
typical 2024-2026 AI-launch anti-patterns.

FAST first-pass heuristics. Pair with `persona/saas-launch-critic`
for full review.

| axis | value |
|---|---|
| industry | software, creative, cross_industry |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `tagline_ai_powered` | high | tagline.ai_as_value_prop | `(?i)\b(AI[- ]powered|powered by AI|AI[- ]driven|AI[- ]first|AI[- ]native|GPT[...` |
| `tagline_revolutionize` | high | tagline.buzzword_verb | `(?i)\b(revolutionize|transform|reimagine|reinvent|redefine|disrupt|democratiz...` |
| `tagline_platform_for` | medium | tagline.vague_for_who | `(?i)\b(platform|solution|software|tool|app|service|system) for\s+(your|all|ev...` |
| `icp_for_everyone` | high | icp.no_specific_persona | `(?i)\bfor (teams|businesses|companies|organizations|individuals) of (any|all|...` |
| `icp_kitchen_sink` | high | icp.persona_kitchen_sink | `(?i)\bfor\s+(marketers?,?\s+){1,}(developers?|designers?|founders?|product ma...` |
| `feature_smart_intelligent` | medium | value_prop.capability_not_outcome | `(?i)\b(smart|intelligent|automated|automatic|self[- ]driving|auto[- ])\s+\w{3...` |
| `feature_seamless_effortless` | medium | value_prop.handwave_adverb | `(?i)\b(seamless|seamlessly|effortless|effortlessly|with one click|in seconds|...` |
| `pricing_contact_us` | medium | pricing.contact_sales_hidden | `(?i)\bcontact\s+(us|sales|our team)\s+for\s+(pricing|a quote|details)\b` |
| `pricing_starting_at` | medium | pricing.starting_at_no_anchor | `(?i)\bstarting at\b(?!.{0,50}\$\d|\d+ ?\$)` |
| `pricing_no_dollar_sign` | low | pricing.no_visible_dollar_amount_check | `(?i)\b(pricing|plans|tiers|subscriptions)\b(?!.{0,500}\$\d)` |
| `social_proof_trusted_by` | low | social_proof.aggregate_number_verify_date | `(?i)\b(trusted by|loved by|used by|join over) \d{1,3}[,.]?\d{0,3}\+? (?:compa...` |
| `social_proof_world_class` | high | social_proof.peacock | `(?i)\b(trusted by (the )?(world's|industry'?s)? (best|leading|top|fastest[- ]...` |
| `demo_join_waitlist` | high | demo.waitlist_no_product | `(?i)\b(join (the |our )?waitlist|join early access|get early access|request a...` |
| `demo_request_demo` | medium | demo.no_self_serve | `(?i)\b(request a demo|book a demo|schedule a demo|talk to (sales|us|an expert...` |
| `comparison_only_competitor` | high | competitive.competitive_blindness | `(?i)\b(the (only|first|best|leading|premier)|there'?s no other) (?:tool|produ...` |
| `comparison_no_mention` | low | competitive.competitor_mention_verify | `(?i)\b(vs\.?|versus|compared to|compare to|alternative to) ([A-Z][a-zA-Z]+)\b` |
| `buzz_word_revolutionary` | high | buzzword.peacock_terms | `(?i)\b(revolutionary|groundbreaking|game[- ]changing|disruptive|next[- ]gener...` |
| `buzz_word_modern` | medium | buzzword.modern_workplace | `(?i)\b(modern|future[- ]ready|future[- ]proof|next[- ]gen)\s+(workplace|compa...` |
| `ai_specific_gpt_wrapper` | high | ai_specific.model_as_differentiator | `(?i)\b(built (on|with|using) (GPT[- ]?[345]|Claude|Gemini|Llama|Mistral))\b` |
| `ai_specific_custom_gpt` | high | ai_specific.custom_gpt_wrapper | `(?i)\b(custom GPT|GPT for [A-Z]|specialized GPT|fine[- ]tuned GPT)\b` |
| `ai_specific_no_accuracy` | medium | ai_specific.high_stakes_no_accuracy_disclosure | `(?i)\b(AI|GPT|LLM|model)\b(?!.{0,500}\b(accuracy|hallucination|evaluation|ben...` |
| `onboarding_get_started_vague` | low | onboarding.cta_no_promise | `(?i)>\s*(get started|start now|try it free|sign up|register)\s*<` |
| `trial_credit_card_required` | high | trial.cc_required_friction | `(?i)\b(\d{1,2})[- ]day (?:free )?trial\b.{0,150}\b(credit card|payment) (requ...` |
| `guarantee_money_back` | medium | guarantee.terms_unclear | `(?i)\b(money[- ]back|satisfaction) guarantee\b(?!.{0,200}\b\d+ days?\b)` |
| `vague_outcome_save_time` | medium | value_prop.vague_time_save_no_number | `(?i)\bsave (you )?(hours|time|countless hours|so much time)\b(?!.{0,80}\b\d+%...` |
| `vague_outcome_increase_x` | medium | value_prop.vague_outcome_no_number | `(?i)\b(increase|boost|grow|improve|enhance|maximize) (your )?(revenue|sales|c...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-saas-launch-antipatterns.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-saas-launch-antipatterns.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0,16...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-saas-launch-antipatterns.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-saas-launch-antipatterns.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)....` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-saas-launch-antipatterns.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-saas-launch-antipatterns.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-saas-launch-antipatterns.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}saas.{0,24}launch.{0,24}antipattern...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-saas-launch-antipatterns.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-saas-launch-antipatterns.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-saas-launch-antipatterns.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0,16...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-saas-launch-antipatterns.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-saas-launch-antipatterns.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)....` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-saas-launch-antipatterns.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-saas-launch-antipatterns.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-saas-launch-antipatterns.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}saas.{0,24}launch.{0,24}antipattern...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-saas-launch-antipatterns.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-saas-launch-antipatterns.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-saas-launch-antipatterns.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0,16...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-saas-launch-antipatterns.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-saas-launch-antipatterns.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)....` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-saas-launch-antipatterns.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-saas-launch-antipatterns.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-saas-launch-antipatterns.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}saas.{0,24}launch.{0,24}antipattern...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-saas-launch-antipatterns.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-saas-launch-antipatterns.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-saas-launch-antipatterns.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0,16...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-saas-launch-antipatterns.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-saas-launch-antipatterns.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)....` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-saas-launch-antipatterns.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-saas-launch-antipatterns.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-saas-launch-antipatterns.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}saas.{0,24}launch.{0,24}antipattern...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-saas-launch-antipatterns.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-saas-launch-antipatterns.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-saas-launch-antipatterns.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0,16...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-saas-launch-antipatterns.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-saas-launch-antipatterns.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns)....` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-saas-launch-antipatterns.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-saas-launch-antipatterns.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns).{0...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-saas-launch-antipatterns.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}saas.{0,24}launch.{0,24}antipattern...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-saas-launch-antipatterns.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}saas.{0,24}launch.{0,24}antipatterns...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-saas-launch-antipatterns.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-saas-launch-antipatterns.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-saas-launch-antipatterns.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-saas-launch-antipatterns.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-saas-launch-antipatterns.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-saas-launch-antipatterns.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-saas-launch-antipatterns.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

