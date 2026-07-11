# Tiltfile — one command (`tilt up`) brings up the FULL AI Done Right stack locally with the live go-live seams
# emulated (no GPU, no API key, no paid cloud). The base deploy compose runs identity/registry/receipt/state/
# Postgres/Teleon-runtime/Baltor/web; the emulators overlay adds the deterministic local LLM + the authoritative-
# source/CDC server. Local resources run the in-process emulation proof + the descent demo so `tilt up` is a green
# end-to-end smoke. Requires Docker. Emulators NEVER serve truth — dev scaffolding only.
#
#   tilt up        # bring the stack up, watch the proofs go green
#   tilt down      # tear it down
#
# Pure container-free check (no Docker needed): PYTHONPATH=. python3 scripts/check_teleon_local_emulation.py --self-test

docker_compose([
    "deploy/docker-compose.deploy.yml",
    "deploy/docker-compose.emulators.yml",
])

# Give the emulator services explicit labels so they group in the Tilt UI.
dc_resource("model-emulator", labels=["emulators"])
dc_resource("source-emulator", labels=["emulators"])
dc_resource("postgres", labels=["data"])
dc_resource("identity", labels=["platform"])
dc_resource("teleon-runtime", labels=["platform"])
dc_resource("baltor-backend", labels=["platform"])

# In-process proof that every BLOCKING go-live seam maps to a built local emulator (LLM + source/CDC + Postgres +
# auth + hosting), and the freshness + model seams wire end-to-end locally. This is the gate for "emulated locally".
local_resource(
    "local-emulation-proof",
    cmd="PYTHONPATH=. python3 scripts/check_teleon_local_emulation.py --self-test",
    labels=["proofs"],
    allow_parallel=True,
)

# The real assurance/descent engine running on the seed skills (rule-guided -> deterministic, open-ended -> cheaper
# model, fragile -> freshness-synced). Proves the product loop locally, not just the infra.
local_resource(
    "assurance-descent-demo",
    cmd="PYTHONPATH=. python3 scripts/demo_assurance_descent.py --run",
    labels=["proofs"],
    allow_parallel=True,
)
