"""src.teleon.runtime.execution_providers — Teleon execution-backend ADAPTERS (runtime layer).

Concrete backends behind src.teleon.runtime.execution_provider.ExecutionProviderPort: local function emulator,
managed venv, local job/worker-pool emulators, container/cloud candidates, and the unavailable sentinel. Being
extracted _repos/baltor/backend/src/baltor/workers/execution_providers → here one module at a time, losslessly, with Baltor re-export
shims (_repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status). Teleon imports only Teleon/stdlib.
"""
