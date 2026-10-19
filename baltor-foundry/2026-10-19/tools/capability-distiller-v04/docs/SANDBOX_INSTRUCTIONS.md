# Reference OCI deployment (not executed in this environment)

The Go CLI is statically linked and can run from the included scratch Containerfile. This is a reference container recipe, not a claim of already-secured execution. Here is a Linux Docker invocation for a scanner job:

```bash
# From the distiller project root. Ensure output folder is writable by UID 65534.
mkdir -p ./work && chmod 0777 ./work

docker build -f Containerfile -t baltor-distill:v0.4 .
docker run --rm \
  --network=none --read-only --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=32 --memory=256m --cpus=1 \
  --mount type=bind,src="$PWD/testdata/skills",dst=/inputs,readonly \
  --mount type=bind,src="$PWD/work",dst=/outputs \
  baltor-distill:v0.4 scan --root /inputs --out /outputs/skills.json
```

For real deployment, set owner/group ACLs instead of broad mode 0777 and provide a proper seccomp/AppArmor/gVisor/microVM policy. Keep external scripts unavailable to the tool runner; the parser will not execute them anyway. Do not grant broad home-directory access or secrets mounts.

**This OCI configuration has not been runtime-tested:** no Docker/Podman runtime was available here.
