# Implementation matrix — Baltor Harness Tools 0.3.1

| Capability | Status | Technology | Validation |
|---|---|---|---|
| DAG schema and cycle/dependency checks | Executable | Go stdlib | Go unit tests |
| Local bounded workspace / symlink checks | Executable | Go stdlib | Traversal/symlink tests |
| Typed-ish operator args with strict operation allowlists | Executable | Go stdlib | Invalid-operator/param tests |
| Deterministic procedural frame generation | Executable | Go native image/png | Repeated image bytes + independent run comparison |
| Stage-independent post-render camera and grade | Executable | Go native | Composed-demo stage output |
| Ordered graphics layers, z-index, anchors, padding, timed elements | Executable (limited kinds) | Go native | Layered-demo stage output |
| Node/connection motion, stick animation, articulated-arm illustration | Executable procedural demonstration | Go native | Rendered video only; no physics-model validation |
| Procedural PCM soundtrack | Executable | Go stdlib WAV | Independent hash-repeat comparison |
| H264+AAC encoding | Executable with FFmpeg installed | ffmpeg libx264/aac | Repeated identical MP4 on this container |
| Ingested reference frame sampling | Executable with FFmpeg installed | ffmpeg | Existing Baltor Spatial v0.2 reference audit |
| Pixel-level temporal and spatial heuristics | Executable | Go native | CSV, JSON, contact sheet |
| Import v0.2 JSON layout lint | Executable basic parser | Go native | 10 layouts / 66 elements audited |
| Runtime SHA256 manifest + cache verification | Executable | Go stdlib | Tamper negative test |
| Normalized `.tar.gz` run packaging | Executable | Go stdlib | Identical bundle bytes |
| Cross-target standalone Go binaries | Built, foreign-target execution unverified | go build CGO_ENABLED=0 | Linux/amd64 executed here only |
| Docker container confinement | Containerfile + runtime script provided; **not tested here** | Docker / Podman | Needs host with runtime |
| True OS/VM isolation on this session | Not available | --- | No container runtime present |
| Articulation from an arbitrary static mesh | Not implemented | Potential Particulate adapter | Requires separate model runtime |
| Neural high-quality TTS and word alignment | Not implemented | Optional separate worker | Requires voice assets/model + licensing review |
| Automatic copyrighted video downloads | Intentionally not included | --- | Rights/terms review required |
| 3D Blender/Godot/Three.js adapters | Planned | External render workers | No end-to-end verification |
| Semantic face/subject-aware text avoidance | Planned | Computer vision / masks | Not implemented |
| Full 300s finished film | Not produced by this release | --- | 20s executable example only |

## Confinement boundaries

Paths are normalized and symlink traversals blocked under declared workspace subpaths; subprocess arguments use fixed templates, with timeouts and a reduced environment; the operator catalog contains no arbitrary command runner. These controls reduce accidental abuse, **but are not a security sandbox**. FFmpeg decoders process untrusted files and require separate container/VM and kernel policies for real isolation. The runtime does not automatically remove host network access. The example container launcher provides `--network none`, a read-only root FS, user separation, no-new-privileges, limits and dropped caps, but has not been run here.
