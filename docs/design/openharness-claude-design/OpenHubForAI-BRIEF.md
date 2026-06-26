# OpenHubForAI build brief (browse every record, many ways)

> The executable spec for the OpenHubForAI surface (the open store both products consume). Pair with `DESIGN-BIBLE.md`
> (the kit), `DESIGN-ASSETS.md` (the source), `INTEGRATION-BIBLE.md` (the seams), and `ARCHITECTURE-AND-PAGES.md`
> (the whole product). Accent for this surface: `#3b6fd4`. serves_truth=false (a registry or record is a pointer plus
> a shape, not asserted truth; discovery is not trust).

## What you are building

OpenHubForAI lets anyone browse **every record in the family** in multiple visually styled ways, with filters and
search. There are **242 registry records today** and the number grows. Build it in the shared kit (accent `#3b6fd4`).
A basic faceted browse already exists at `scripts/openhub_browse_server.py` (older, dark, superseded); rebuild it rich
in the kit with several layouts. Wrap every record browser in `OhLayout variant="no-sidebar"` (full-width content with
the top nav and footer, the right shape for wide tables and browsers), and render the faceted table browser with
`OhTable` (the standardized data table).

## The data (real, from the reconciled spine)

- Each item is a **`RegistryObject`**: `{ id, type, name, status, version, holds, categories[], component }`. A record
  can be in MULTIPLE categories at once (it is faceted, not a single tree).
- **242 records**, across **5 facet dimensions** (the browse axes), with these real live counts:

| Dimension | Values (with counts) |
|---|---|
| **category** | General 141, Discovery 32, Execution 29, Verification 19, Optimization 19, Governance 19 |
| **kind** | static 74, discovery 18, meta 11 |
| **layer** | cross_cutting 39, runtime 23, pre_llm 20, post_llm 12, model 9 (plus uncategorized 139) |
| **status** | live 152, partial 88, gap 2 |
| **type** | one per registry (242 distinct types, for example `access_policy`, `adapter_layers`, `adversarial`) |

- A real record (shape): `{ "id": "access_policy", "type": "access_policy", "status": "live", "categories": ["General"] }`.

## The browse layouts (build several; variety is the point)

1. **Faceted table browser (the default).** A left facet sidebar (the 5 dimensions; each value is a checkbox with its
   live count) plus a main `OhTable` of records (`cols`: name, type, status, category, layer, all `sortable`; `onRow`
   opens the record detail), a search box, and pagination or virtualization (242 rows now, design for thousands).
   Multi-select facets combine: AND across dimensions, OR within a dimension. Counts update as filters change. This is
   the visually styled table browser.
2. **Card grid (alternate view).** The same filtered records as cards (name, type, a status badge, the categories),
   for visual scanning. A view toggle switches table and cards.
3. **Browse-by-area landing.** A directory that lets a user enter the records by area: by **Category** (6 tiles with
   counts), by **Status** (live / partial / gap), by **Layer** (the 6 layers), by **Kind** (static / discovery /
   meta), or **All registries** (the 242 as a list). Picking an area scopes the table and cards.
4. **Record detail.** A single `RegistryObject`: a header (name, type, status, version), the `holds` description, the
   `component` payload rendered, the categories, and the cross-references (which registries relate to or depend on it).

## Filters and search

- **Facet filters:** multi-select per dimension, with live counts that update as you filter.
- **Search:** full text across name, id, and holds, plus the federated search endpoint.
- **Combine:** facets and search together; a record in multiple categories appears under each.
- **Sort:** by name, status, type, or category.

## The API (real endpoints over the reconciled spine; reached via the `/registry/` seam)

Backed by `scripts/registry_api_server.py` and `src/teleon/registry/browse.py`. See `INTEGRATION-BIBLE.md` for the seam.

- `GET /registry/registries` returns the list of registries as `RegistryObject`s.
- `GET /registry/registries/{id}/records` returns the records for one registry.
- `GET /registry/search?q=...` returns federated search hits across all registries.
- `GET /registry/reconciliation` returns the spine reconciliation (counts and overlap).

Sample of the facet payload the browse uses (real shape):

```json
{
  "count": 242,
  "facets": {
    "category": { "General": 141, "Discovery": 32, "Execution": 29, "Verification": 19, "Optimization": 19, "Governance": 19 },
    "kind": { "static": 74, "discovery": 18, "meta": 11 },
    "layer": { "cross_cutting": 39, "runtime": 23, "pre_llm": 20, "post_llm": 12, "model": 9 },
    "status": { "live": 152, "partial": 88, "gap": 2 }
  },
  "items": [ { "id": "access_policy", "type": "access_policy", "status": "live", "categories": ["General"] } ]
}
```

## States (every data view needs them)

Empty (no results for the current filter, with a "clear filters" action), loading (skeleton table or cards),
populated, error (the message plus retry).

## Acceptance checklist (this is "done")

- [ ] The faceted table browser: facet sidebar with live counts, sortable table, search, and pagination, over the real 242-record spine.
- [ ] Built with OhLayout (no-sidebar) + OhTable.
- [ ] The card-grid alternate view, with a table/cards toggle.
- [ ] The browse-by-area landing (category, status, layer, kind, all registries).
- [ ] The record-detail view (the `RegistryObject` plus its `component` and cross-references).
- [ ] Filters and search combine; counts update live; a record in multiple categories shows under each.
- [ ] It scales: virtualize the table so thousands of rows stay smooth.
- [ ] Shared kit, accent `#3b6fd4`, and the copy rules pass.

## Copy rules and governance

1. No placeholders ("OpenHubForAI", never "OpenHubForAI registries"); no em or en dashes; no strategy leakage; real copy.
2. serves_truth=false. A registry or record is a pointer and a shape, not asserted truth. Show `status` honestly
   (live / partial / gap); never present a `gap` or `partial` record as verified.
