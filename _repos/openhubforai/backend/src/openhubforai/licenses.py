"""src.openhubforai.licenses — the SINGLE source for license classification (permissive / copyleft / unstated).

One classifier used everywhere a governance decision depends on license: _repos/teleon/backend/src/teleon/repo_strategy (repo intake),
src/openhubforai/browsing_registry (the browsing stack), and any future intake. Lives in the open layer so OHH
modules use it WITHOUT importing Teleon (dependency law); Teleon may import it. The org-guardrail rule it encodes:
COPYLEFT and UNSTATED licenses are NOT vendorable (technique-only — study behind a port, never vendor the code);
only PERMISSIVE is vendorable. serves_truth=false (a classification is a candidate signal, not adjudicated truth).
"""
from __future__ import annotations

#: license family → class. Extend conservatively; an unknown token defaults to 'unstated' (NOT vendorable).
PERMISSIVE = ("MIT", "APACHE", "BSD", "ISC", "UNLICENSE", "0BSD", "ZLIB", "PYTHON-2", "MIT-0", "WTFPL", "BSL")
COPYLEFT = ("GPL", "AGPL", "LGPL", "MPL", "EPL", "CDDL", "OSL", "EUPL", "CC-BY-SA", "SSPL")
#: explicitly non-commercial / restrictive → never vendorable (treated as its own class).
NONCOMMERCIAL = ("CC-BY-NC", "NC-", "NONCOMMERCIAL", "BUSL", "ELASTIC", "PROPRIETARY", "COMMERCIAL")


def classify_license(license_str: str | None) -> tuple[str, bool]:
    """Return (license_class, vendorable). permissive ⇒ vendorable; copyleft/noncommercial/unstated ⇒ NOT vendorable."""
    s = (license_str or "").upper().strip()
    if not s or s in ("NOASSERTION", "NONE", "UNKNOWN", "OTHER", "NULL"):
        return "unstated", False
    if any(k in s for k in NONCOMMERCIAL):
        return "noncommercial", False
    if any(k in s for k in COPYLEFT):
        return "copyleft", False
    if any(k in s for k in PERMISSIVE):
        return "permissive", True
    return "unstated", False


__all__ = ["classify_license", "PERMISSIVE", "COPYLEFT", "NONCOMMERCIAL"]
