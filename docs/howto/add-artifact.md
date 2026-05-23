# Add an artifact

```bash
# 1. Scaffold a new manifest.
python scripts/new.py harness my-new-harness
# Or:
python scripts/new.py pipeline format-response
python scripts/new.py rule-pack grep my-grep-pack

# 2. Edit the generated YAML.
$EDITOR catalog/harnesses/my-new-harness.yaml

# 3. Validate.
python scripts/validate.py

# 4. Rebuild docs.
python scripts/build_catalog_pages.py
mkdocs serve   # http://127.0.0.1:8000
```

## Required fields

Every manifest starts with the [common envelope](../reference/spec.md#30-common-envelope-all-artifact-types).
Beyond that, see the schema for your artifact type in `schemas/`.

## Lifecycle promotion

A manifest enters at `experimental`. To promote:

| To | Requires |
|---|---|
| `beta` | External review + at least one sample run committed. |
| `stable` | Used in production; at least one benchmark referencing it. |
| `deprecated` | Must declare `superseded_by` and `deprecated_on`. |

## When in doubt

- **Volatile facts** (hotline numbers, fee caps, current advisories) go
  in tools or knowledge packs, never in personas.
- **Trust boundaries travel with the artifact**, not the deployment.
- **Reproducibility is a first-class field** - every benchmark
  declares `(commit_sha, dataset_version, run_date)`.
