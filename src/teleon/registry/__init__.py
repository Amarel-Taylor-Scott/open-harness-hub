"""teleon.registry — the universal Registry<T> menu (the buffet's ordering protocol).

One agnostic interface over the federation's source catalogs so an agent picks ingredients UNIFORMLY
(search / lookup / list / explain) instead of bespoke access per registry. See port.py.
"""
from .port import (
    CATALOGS,
    JsonCatalogRegistry,
    RegistryPort,
    all_catalogs,
    available,
    available_all,
    catalog,
    discover_catalogs,
)

__all__ = ["RegistryPort", "JsonCatalogRegistry", "catalog", "available", "available_all",
           "discover_catalogs", "all_catalogs", "CATALOGS"]
