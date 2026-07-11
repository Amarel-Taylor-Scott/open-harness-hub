"""src.teleon.templates — the Shared Template Registry instantiator (canonical object shell + mixins).

Composes the canonical 14-section object shell (templates/schema-objects/) from standardized mixins and renders
CANDIDATE starting shapes — never active, never truth. Safe: refuses path traversal + overwrite, never
substitutes a raw secret, writes a TemplateInstantiationReceipt. Pure + deterministic (injected `now`).

ARCHITECTURAL LAW: lives in Teleon (scaffolding/runtime concern); never imports src.baltor. Reuses the existing
templates/ tree + _repos/shared-backend-components/scripts/{check_template_catalog,generate_from_template} (the registry adds the canonical
schema-object shell those lacked — not a second template framework).
"""
from .instantiator import (compose_object_shell, instantiate_schema_object, load_shell, load_mixins,
                           load_schema_object_templates, CANDIDATE_STATUS, INTERNAL_VISIBILITY)

__all__ = ["compose_object_shell", "instantiate_schema_object", "load_shell", "load_mixins",
           "load_schema_object_templates", "CANDIDATE_STATUS", "INTERNAL_VISIBILITY"]
