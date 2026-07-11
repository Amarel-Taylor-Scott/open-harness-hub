#!/usr/bin/env python3
"""local_emulators.rapidapi_hub_emulator — the OFFLINE local equivalent of the live RapidAPI catalog harvest.

The live harvest (Playwright driving the owner's authenticated Chrome/Chromium session over RapidAPI's catalog) is a
real-network + owner-credential seam, OWNER-LAUNCHED and out of sandbox. Per the DEFER GATE, that real candidate has
a built local equivalent: this emulator returns representative OpenAPI specs (RapidAPI-shaped) so the deconstruct →
capability-seed pipeline (src.teleon.seeds.openapi_deconstructor) is fully testable offline. Importable + stdlib-only;
never serves truth (the specs are sample scaffolding).

Owner-run live path (sketch, not executed here): launch Playwright with the owner's browser session
(`browser = playwright.chromium.launch_persistent_context(user_data_dir=...)` or a captured `storage_state`),
browse the hub, capture each endpoint's OpenAPI/spec, and feed it to `deconstruct_api`. That run needs Playwright +
network + the owner's session + acceptance of the hub's ToS, so it stays owner-launched.
"""
from __future__ import annotations

#: representative RapidAPI-shaped OpenAPI specs (one per sample API). Sample scaffolding — never truth.
_SPECS = {
    "whois-lookup": {
        "openapi": "3.0.0", "info": {"title": "WHOIS Lookup"},
        "servers": [{"url": "https://whois-lookup.p.rapidapi.com"}],
        "components": {"securitySchemes": {"key": {"type": "apiKey", "name": "X-RapidAPI-Key", "in": "header"}}},
        "paths": {
            "/whois": {"get": {"operationId": "getWhois", "summary": "Look up WHOIS registration for a domain",
                               "parameters": [{"name": "domain", "in": "query"}],
                               "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/rdap": {"get": {"operationId": "getRdap", "summary": "Structured RDAP record for a domain",
                              "parameters": [{"name": "domain", "in": "query"}],
                              "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}},
        },
    },
    "telecom-location": {
        "openapi": "3.0.0", "info": {"title": "Network-as-Code Location"},
        "servers": [{"url": "https://network-as-code.p.rapidapi.com"}],
        "components": {"securitySchemes": {"key": {"type": "apiKey", "name": "X-RapidAPI-Key", "in": "header"}}},
        "paths": {
            "/location/verify": {"post": {"operationId": "verifyLocation",
                                          "summary": "Verify a device is within a geofence (CAMARA)",
                                          "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                                          "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}},
            "/sim-swap/check": {"get": {"operationId": "checkSimSwap", "summary": "Check recent SIM-swap for a number",
                                        "parameters": [{"name": "phoneNumber", "in": "query"}],
                                        "responses": {"200": {"content": {"application/json": {"schema": {"type": "boolean"}}}}}}},
        },
    },
}


class RapidApiHubEmulator:
    """Offline stand-in for browsing the live RapidAPI catalog. ``openapi`` returns a sample OpenAPI doc per API."""

    serves_truth = False

    def list_apis(self) -> list[str]:
        return sorted(_SPECS)

    def openapi(self, api_name: str) -> dict:
        return _SPECS[api_name]

    def all_specs(self) -> dict:
        """{api_name: openapi_doc} for the whole emulated hub — what the live harvest would yield."""
        return {k: dict(v) for k, v in _SPECS.items()}
