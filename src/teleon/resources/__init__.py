"""src.teleon.resources — the Shared Resource Spine: declare and reference shared resources (tables, buckets,
queues, vector indexes, graph stores, sandbox volumes, temp datasets) through ResourceRef / ResourceBinding /
DataResourceSpec / SecretRef / KeyRef / ResourceProvisionReceipt — NEVER raw table/bucket/path names or raw keys
in business logic. Lives in Teleon (shared-infra layer); Baltor consumes via Baltor->Teleon. No src.baltor import.
"""
from .resource_ref import (make_resource_ref, make_secret_ref, make_key_ref, make_data_resource_spec,
                           validate_resource_spec, provision_receipt, has_raw_secret,
                           OWNERSHIP, KIND, EXTERNAL_EXISTING, MANAGED_PERSISTENT, MANAGED_EPHEMERAL,
                           PIPELINE_TEMP, TENANT_DEDICATED)

__all__ = ["make_resource_ref", "make_secret_ref", "make_key_ref", "make_data_resource_spec",
           "validate_resource_spec", "provision_receipt", "has_raw_secret",
           "OWNERSHIP", "KIND", "EXTERNAL_EXISTING", "MANAGED_PERSISTENT", "MANAGED_EPHEMERAL",
           "PIPELINE_TEMP", "TENANT_DEDICATED"]
