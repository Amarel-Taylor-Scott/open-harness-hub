"""src.teleon.runtime.tenancy — single source for the default internal tenant id (no scattered hardcoded literal).

The platform's own internal tenant (dev/demo/exploration) was hardcoded as the literal "baltor-internal" in ~9 places;
a value typed in more than one place drifts. This is the ONE definition; import it everywhere. serves_truth=false.
"""
from __future__ import annotations

#: the platform's internal tenant (dev/demo/exploration runs). Real customer tenants get their own ids.
INTERNAL_TENANT_ID = "baltor-internal"
