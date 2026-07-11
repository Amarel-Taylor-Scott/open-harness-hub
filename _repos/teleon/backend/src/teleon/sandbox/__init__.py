"""src.teleon.sandbox — the shared Sandbox Gateway: run candidates (skills/tools/templates/repos/implementations)
in a GOVERNED sandbox BEFORE promotion. Nothing promotes without a sandbox run + contract + eval + redteam.

Local sandbox (tempdir, deny-by-default: no network, no secrets, bounded time) is the golden path; Docker/
OpenShell/E2B/Daytona/CubeSandbox/K8s are CANDIDATE providers behind the same SandboxProviderPort, each with a
local_equivalent + proof_to_promote. Discovery is not trust; sandbox output is NOT truth — it is evidence the
promotion gate consumes. Lives in Teleon (eval/runtime concern); never imports src.baltor.
"""
from .gateway import (SandboxProviderPort, run_in_sandbox, load_catalog, select_provider, LocalTempdirProvider,
                      OFFLINE_DEFAULT_PROVIDER)

__all__ = ["SandboxProviderPort", "run_in_sandbox", "load_catalog", "select_provider", "LocalTempdirProvider",
           "OFFLINE_DEFAULT_PROVIDER"]
