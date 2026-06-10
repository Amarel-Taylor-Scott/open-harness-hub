# Deterministic markdown fixture for source.markdown_folder@v1 / source.obsidian_vault@candidate

This file stands in for one note in a markdown folder / Obsidian vault.

## Section: governed ingest

Headings become record/field source handles; each section gets a per-section content_hash. A wikilink like
[[another-note]] is recorded as LINEAGE (a provenance edge), never promoted to a served fact. Lane B builds
the real markdown adapter this batch; this fixture proves the connector contract until then.
