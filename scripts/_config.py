"""Single source of truth for shared constants across Open Harness Hub scripts.

Per `docs/codex/no-magic-values.md`: any value used in more than one place gets
ONE definition here and is imported everywhere else — never re-typed as a
literal, and never embedded in a parallel string. Strings that include one of
these values must be built from the constant (e.g. `pgvector_type(dim)`), not
hand-copied.

Import convention matches the rest of the package (scripts are run as modules
from the repo root, e.g. `python -m scripts.db.<name>`):

    from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, pgvector_type
"""
from __future__ import annotations

from pathlib import Path

# --- Canonical repo paths ---------------------------------------------------
# Resolve from this file's location so callers never string-concatenate or rely
# on the current working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "catalog"
SCHEMAS_DIR = REPO_ROOT / "schemas"
VOCAB_DIR = REPO_ROOT / "vocabularies"
DIST_DIR = REPO_ROOT / "dist"
DOCS_DIR = REPO_ROOT / "docs"

# --- Embedding / vector configuration ---------------------------------------
# The canonical pgvector dimension for the default local embedding model. This
# is THE definition; load plans, workers, smoke tests, and audits import it
# rather than re-typing 384. Changing the default model below should be the
# only edit needed to move the whole fleet to a new dimension.
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Registry of known embedding models -> their output dimension. Add a row to
# swap or offer a model; do not scatter model-id string literals across scripts.
EMBEDDING_MODELS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,            # sentence-transformers, local default
    "bge-small-en-v1.5": 384,           # local alternative, same dimension
    "all-minilm": 384,                  # Ollama tag (served via /v1/embeddings)
    "nomic-embed-text": 768,            # Ollama tag, stronger 768-dim option
    "text-embedding-3-small": 1536,     # OpenAI-compatible hosted route
    "text-embedding-ada-002": 1536,     # legacy OpenAI-compatible route
}

DEFAULT_EMBEDDING_DIMENSIONS: int = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]


def pgvector_type(dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> str:
    """Render the pgvector column type for a dimension, e.g. ``vector(384)``.

    Always build pgvector type strings through this helper so a dimension
    change can never leave a stale ``vector(384)`` literal behind in a message,
    comment, or SQL fragment.
    """
    return f"vector({int(dimensions)})"
