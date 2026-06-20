# Portfolio brand boundaries (websites)

Proven by `scripts/check_portfolio_brand_boundaries.py`. Each page carries delimited `<!--IDENTITY-->`
(positive: hero + what-it-is + what-it-owns) and `<!--RELATIONSHIP-->` zones. A site may reference other brands
in its relationship/footer + its "what it is **not**" / "does not own" — but its IDENTITY zone must never claim
another brand's signature.

| Brand | Owns (signature) | Must NOT claim as identity | Explicit "not" |
|---|---|---|---|
| AI Done Right (founding thesis: ContextIsEverything) | portfolio · holding company · "Infrastructure for governed, self-improving AI systems" | self-adaptive capabilities · governed context · open capability ecosystem | "owns no runtime code" |
| Teleon | self-adaptive capabilities · CapabilityTask · intent-native, eval-gated, self-adaptive compute | governed context · open capability ecosystem · holding company | "Not a generic AI-agent deployment" |
| Baltor | governed context · source-grounded · reconciled | self-adaptive capabilities · purpose-defined compute · open capability ecosystem | "Not a generic compute runtime"; uses Teleon via PurposeTaskProviderPort |
| OpenHarnessHub | open capability ecosystem · open skills · harnesses/templates/rubrics | self-adaptive capabilities · governed context · holding company | "Not a hosted runtime" |

Relationship (allowed, in the relationship zone): OpenHarnessHub → Teleon → Baltor; AI Done Right
(founding thesis: ContextIsEverything) coordinates the portfolio. Teleon returns evidence/candidate/result, never Baltor truth.
