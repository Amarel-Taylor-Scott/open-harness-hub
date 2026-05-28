"""scripts.wedge — Lane A Sanctions Screening Scaffold.

Demonstrates structural capability lift a bare frontier model lacks in two ways:

1. DETERMINISTIC AGGREGATION GUARANTEE (lift_reason='deterministic_guarantee'):
   The OFAC 50% Rule requires recursive, exact arithmetic over a beneficial-ownership
   graph.  A sampler cannot guarantee the recursion terminates with the correct number;
   a deterministic graph traversal always does.  Two 30%-blocked co-owners of the same
   unlisted entity aggregate to 60% -> BLOCKED — a naive string-match (what a bare
   model attempts) silently misses this.

2. SANCTIONS-DELTA-LIST FRESHNESS (lift_reason='volatile_fact'):
   Sanctions lists mutate daily.  A model's parametric knowledge is a snapshot;
   any entity designated after its training cutoff is invisible to a bare model.
   Only a pipeline with a live-update loop catches these designations.

Durability class for both: 'structural' — more model / more data will NOT close
the gap.  The first is a verifiability moat; the second is a recency moat.

Modules:
  sanctions_screen.py   deterministic fuzzy-name + 50%-rule screener
  benchmark.py          pipeline vs. bare-model baseline; computes lift_delta
"""
from __future__ import annotations
