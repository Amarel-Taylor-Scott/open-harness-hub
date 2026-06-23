"""src.teleon.resolution — registry-driven entity resolution / record linkage.

entity_resolver: match records robust to typos in any column, using per-entity-type rulesets (architecture/
entity_resolution_rules.json) — comparators (Jaro-Winkler / token-set / phonetic) + normalizers (person nicknames,
company legal-suffix stripping) + weighted column scoring + thresholds + an identifier override + blocking for scale.
A 'review' tier sends ambiguous pairs to a human; serves_truth=false (it proposes matches, governance disposes).
"""

__all__ = ["entity_resolver"]
