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
    py_const_src_teleon_registry_port__CATALOGS,
    py_class_src_teleon_registry_port__JsonCatalogRegistry,
    py_class_src_teleon_registry_port__RegistryPort,
    py_function_src_teleon_registry_port__all_catalogs,
    py_function_src_teleon_registry_port__available,
    py_function_src_teleon_registry_port__available_all,
    py_function_src_teleon_registry_port__catalog,
    py_function_src_teleon_registry_port__discover_catalogs,
)

__all__ = ["py_class_src_teleon_registry_port__RegistryPort", "py_class_src_teleon_registry_port__JsonCatalogRegistry", "py_function_src_teleon_registry_port__catalog", "py_function_src_teleon_registry_port__available", "py_function_src_teleon_registry_port__available_all",
           "py_function_src_teleon_registry_port__discover_catalogs", "py_function_src_teleon_registry_port__all_catalogs", "py_const_src_teleon_registry_port__CATALOGS",
           "RegistryPort", "JsonCatalogRegistry", "catalog", "available", "available_all", "discover_catalogs", "all_catalogs", "CATALOGS"]
