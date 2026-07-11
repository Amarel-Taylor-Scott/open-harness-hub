# CubeSandbox (TencentCloud) — sandbox provider candidate
- Source: github.com/TencentCloud/CubeSandbox
- Summary: RustVMM/KVM micro-VM sandbox service; single + multi-node cluster; **E2B-SDK-compatible**; sub-60ms create; <5MB overhead; eBPF network isolation + egress filtering; snapshot/clone/rollback.
- Capability slot: `sandboxed_execution` (high-density micro-VM tier).
- Useful: hardware isolation, snapshot/rollback for parallel candidate-eval forks, E2B compatibility.
- Risks: heavy host setup (XFS reflink, PVM host kernel, KVM/PVM modules, root, template images) — NOT pip-installable.
- Local equivalent: `sandbox.local_tempdir@v1` / `sandbox.managed_venv@v1`.
- Teleon relevance: high-density candidate testing + snapshot/rollback for the Parallel-Path Engine.
- Baltor relevance: indirect (sandbox produces evidence; Baltor governs truth).
- **Adoption: catalog candidate (`sandbox.cubesandbox@candidate`)** behind SandboxProviderPort; NOT golden path until a dedicated host/cluster is configured + adapter/contract/network/snapshot/no-secret-leak proofs pass.
