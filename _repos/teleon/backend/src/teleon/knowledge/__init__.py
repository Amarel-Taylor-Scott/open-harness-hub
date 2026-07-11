"""teleon.knowledge — the Global Software Knowledge Graph (the owner's "computational cognition mapping").

A system that understands global computational capability so a human/agent asking "build X" gets grounded against
what already exists. Four engines, each grounded in a real registry + governed (serves_truth=false, candidate-only):

  dependency_graph  (#92) — package -> requires graph; transitive closure; 'this whole stack already exists'
  product_distance  (#93) — latent-space distance to existing PRODUCTS ('overlaps 0.88 with Cursor')
  repo_similarity   (§2)  — semantic similarity of an intent to existing REPOSITORIES (equivalents + confidence)
  code_genome       (§9)  — decompose code into architectural primitives -> fingerprint -> software similarity

These feed the Observer/Spotter reinvention modules with deeper grounding (stack-level, product-level, genome-level)
than the single-message federation search.
"""
from . import code_genome, dependency_graph, product_distance, repo_similarity

__all__ = ["dependency_graph", "product_distance", "repo_similarity", "code_genome"]
