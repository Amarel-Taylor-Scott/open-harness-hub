# US CBP Withhold Release Order + UFLPA Entity List lookup

*tool* · `tool/cbp-wro-lookup` · v0.1.0 · experimental

Check a supplier name + geography against:
 - US CBP Withhold Release Orders (active)
 - US CBP Findings list (escalated WROs that became confirmed
   forced-labor determinations)
 - US UFLPA Entity List (Xinjiang-region production and high-
   priority sector entities; goods presumed inadmissible under
   19 USC §1307)

Returns matches with the order ID, date, target commodity, target
geography, and current status. A hit on any list HALTS the routine
grading flow per the lead company's US-customs counsel protocol
(see `persona/esg-auditor` hard rule).

Implementation pulls from the offline snapshot in
`knowledge-pack/high-risk-corridors-and-sectors` (data/cbp-wro-
active-snapshot.jsonl + data/uflpa-entity-list-snapshot.jsonl).
For live checks, the implementation can scrape cbp.gov directly
(rate-limited) or use a paid data vendor; both kept out of the
default callable to avoid surprise egress.

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | verification, safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



