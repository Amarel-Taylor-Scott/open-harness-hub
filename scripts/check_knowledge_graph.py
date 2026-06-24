"""check_knowledge_graph — proof for the Global Software Knowledge Graph engines (#91-93, §2/§9).

Runs every engine's self-test (dependency_graph / product_distance / repo_similarity / code_genome) + checks the
backing registries exist and are catalog-shaped (auto-discoverable into the federation). Embedding engines use the
deterministic lexical floor in their self-tests so the gate is reproducible without Ollama. serves_truth=false.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.knowledge import code_genome, dependency_graph, product_distance, repo_similarity  # noqa: E402

_REGISTRIES = ["global_repository_registry", "product_similarity_registry", "package_dependency_seed",
               "agent_frameworks_registry"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()

    fails: list[str] = []
    # backing registries exist + are governed
    for name in _REGISTRIES:
        p = _REPO / "architecture" / f"{name}.json"
        if not p.exists():
            fails.append(f"missing registry {name}.json")
            continue
        data = json.loads(p.read_text())
        if data.get("serves_truth") is not False:
            fails.append(f"{name}: serves_truth must be false")
        if not any(isinstance(v, list) and v for v in data.values()):
            fails.append(f"{name}: no non-empty record list (not catalog-shaped)")

    # engines
    for mod in (dependency_graph, product_distance, repo_similarity, code_genome):
        fails.extend(mod._self_test())

    if fails:
        print(f"\nFAIL - check_knowledge_graph: {len(fails)} failures")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("PASS - check_knowledge_graph: 4 engines green — dependency-graph (transitive 'stack exists') + "
          "product-distance (latent-space product overlap) + repo-similarity (semantic equivalents) + code-genome "
          "(architectural-primitive fingerprints); 4 backing registries catalog-shaped + governed; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
