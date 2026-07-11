"""observability/projections — see the layer README + _repos/shared-backend-components/architecture/project_spine.json for what belongs here.

Exposes the LINEAGE PROVIDER seam + the four standards mappers (PROV-JSON, OpenLineage RunEvent, W3C Web
Annotation, RFC 6902 JSON Patch). Renderings are read-only projections carrying Baltor governance facets.
"""
from src.baltor.observability.projections.lineage import (  # noqa: F401
    BaltorLocalLineage,
    LineageEvent,
    LineageFacet,
    LineageProvider,
)
from src.baltor.observability.projections.standards import (  # noqa: F401
    GOVERNANCE_FACET_KEYS,
    governance_facet,
    to_json_patch,
    to_openlineage_run_event,
    to_prov_json,
    to_web_annotation,
)

__all__ = [
    "LineageEvent", "LineageFacet", "LineageProvider", "BaltorLocalLineage",
    "to_prov_json", "to_openlineage_run_event", "to_web_annotation", "to_json_patch",
    "governance_facet", "GOVERNANCE_FACET_KEYS",
]
