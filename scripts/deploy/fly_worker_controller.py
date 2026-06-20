#!/usr/bin/env python3
"""Fly worker-fleet controller — the KEDA replacement for the Machines platform.

On K8s, `infra/k8s/worker.yaml`'s KEDA ScaledObject scales the foundry worker fleet 0→N on
Redis queue depth. Fly has no KEDA and its official fly-autoscaler cannot reach zero, so this
controller does the same reconciliation against the Machines API:

    depth = LLEN <queue>                      (raw-socket RESP, no redis dependency)
    desired = clamp(ceil(depth / jobs_per_worker), min_workers, max_workers.fly)
    reconcile: START stopped machines first → CREATE only when the pool is short (image known)
               → STOP the fleet only after the queue has been empty for a full cooldown window

Every scaling number comes from `architecture/deploy_topology.json` (the same block the KEDA
manifest is cross-checked against — one source, two providers). Every decision appends a JSONL
receipt to stdout (and FLY_CONTROLLER_RECEIPTS path if set): depth, desired, actions, errors.
Operational records, not truth claims.

Failure policy (the Jun-2026 Fly incident review drove these):
  * HTTP 429 → honor Retry-After, back off, never hammer (Machines API: ~1 rps/action burst 3).
  * Capacity errors on create/start (412/422/insufficient) → exponential backoff up to
    CAPACITY_BACKOFF_MAX_S; the queue simply drains slower — jobs are not lost (they sit in Redis).
  * Network/API blips → backoff and retry forever; the controller must never crash-loop.
  * Stops by EXACT machine id only, and only machines whose config metadata marks them ours.

Env contract (set by fly/aidr-worker-controller.fly.toml + `fly secrets set`):
  FLY_API_TOKEN        (secret) deploy-scoped token for the worker app
  REDIS_URL            (secret) redis://[:pass@]host:port[/db]
  FLY_WORKER_APP       worker app name        (default: topology fly prefix + '-worker')
  FLY_MACHINES_API     API base               (default: https://api.machines.dev;
                                               on Fly use http://_api.internal:4280)
  FLY_WORKER_IMAGE     image for NEW machines (default: learned from an existing machine)
  FLY_WORKER_REGION    region for NEW machines (default: topology fly.primary_region)

Run modes:
  python3 scripts/deploy/fly_worker_controller.py              # reconcile loop (cloud role)
  python3 scripts/deploy/fly_worker_controller.py --once       # single tick (cron-shaped)
  python3 scripts/deploy/fly_worker_controller.py --self-test  # offline: fake API + fake Redis
"""
from __future__ import annotations

import json
import math
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOPOLOGY_PATH = REPO / "architecture" / "deploy_topology.json"

MANAGED_BY_KEY = "managed_by"            # machine metadata marker — we only touch our own
MANAGED_BY_VALUE = "fly_worker_controller"
RETRY_BASE_S = 2.0                        # first backoff step on API errors
CAPACITY_BACKOFF_MAX_S = 300.0            # cap for capacity-error backoff (queue waits in Redis)
CREATES_PER_TICK_MAX = 2                  # gentle fleet growth; API burst limit is ~3/action


def _load_worker_config() -> dict:
    topo = json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
    worker = next(s for s in topo["services"] if s["name"] == "worker")
    scaling = worker["scaling"]
    return {
        "app": os.environ.get("FLY_WORKER_APP", f"{topo['fly']['app_prefix']}-worker"),
        "region": os.environ.get("FLY_WORKER_REGION", topo["fly"]["primary_region"]),
        "queue_key": scaling["queue_key"],
        "jobs_per_worker": int(scaling["jobs_per_worker"]),
        "poll_seconds": float(scaling["poll_seconds"]),
        "cooldown_seconds": float(scaling["cooldown_seconds"]),
        "min_workers": int(scaling["min_workers"]),
        "max_workers": int(scaling["max_workers"]["fly"]),
        "guest": {"cpu_kind": worker.get("cpu_kind", "shared"), "cpus": int(worker.get("cpus", 1)),
                  "memory_mb": int(worker.get("memory_mb", 2048))},
        "command": worker["command"],
    }


# ---------------------------------------------------------------- redis depth (RESP, stdlib)

def redis_llen(url: str, key: str, timeout: float = 5.0) -> int:
    """LLEN over a raw socket — RESP2, supports redis://[user][:password]@host[:port][/db]."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("redis", "rediss"):
        raise ValueError(f"unsupported redis url scheme: {parsed.scheme}")
    if parsed.scheme == "rediss":
        import ssl
        raw = socket.create_connection((parsed.hostname, parsed.port or 6379), timeout=timeout)
        sock = ssl.create_default_context().wrap_socket(raw, server_hostname=parsed.hostname)
    else:
        sock = socket.create_connection((parsed.hostname, parsed.port or 6379), timeout=timeout)
    try:
        buf = sock.makefile("rb")

        def send(*parts: str) -> None:
            out = f"*{len(parts)}\r\n".encode()
            for part in parts:
                data = part.encode()
                out += b"$%d\r\n%s\r\n" % (len(data), data)
            sock.sendall(out)

        def reply() -> bytes:
            line = buf.readline().rstrip(b"\r\n")
            if line.startswith(b"-"):
                raise RuntimeError(f"redis error: {line[1:].decode()}")
            if line.startswith(b"$"):  # bulk string
                length = int(line[1:])
                return buf.read(length + 2)[:-2] if length >= 0 else b""
            return line[1:]

        if parsed.password:
            send(*((("AUTH", parsed.username, parsed.password) if parsed.username
                    else ("AUTH", parsed.password))))
            reply()
        db = (parsed.path or "/").lstrip("/")
        if db and db != "0":
            send("SELECT", db)
            reply()
        send("LLEN", key)
        return int(reply())
    finally:
        sock.close()


# ---------------------------------------------------------------- machines api (stdlib)

class MachinesAPI:
    """Thin Machines-API client. Raises CapacityError/RateLimited so the loop can back off."""

    class RateLimited(RuntimeError):
        def __init__(self, retry_after: float):
            super().__init__(f"rate limited, retry after {retry_after}s")
            self.retry_after = retry_after

    class CapacityError(RuntimeError):
        pass

    def __init__(self, base: str, token: str, app: str):
        self.base = base.rstrip("/")
        self.token = token
        self.app = app

    def _call(self, method: str, path: str, body: dict | None = None) -> dict | list:
        req = urllib.request.Request(
            f"{self.base}/v1/apps/{self.app}{path}",
            data=json.dumps(body).encode() if body is not None else None, method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            if exc.code == 429:
                raise self.RateLimited(float(exc.headers.get("Retry-After") or RETRY_BASE_S)) from exc
            if exc.code in (412, 422) or "capacity" in detail.lower() or "insufficient" in detail.lower():
                raise self.CapacityError(f"{exc.code}: {detail}") from exc
            raise RuntimeError(f"machines api {method} {path} → {exc.code}: {detail}") from exc

    def list_machines(self) -> list[dict]:
        return self._call("GET", "/machines")  # type: ignore[return-value]

    def start(self, machine_id: str) -> None:
        self._call("POST", f"/machines/{machine_id}/start")

    def stop(self, machine_id: str) -> None:
        self._call("POST", f"/machines/{machine_id}/stop")

    def create(self, config: dict, region: str) -> dict:
        return self._call("POST", "/machines", {"region": region, "config": config})  # type: ignore[return-value]


# ---------------------------------------------------------------- controller

UP_STATES = {"started", "starting", "replacing"}
STARTABLE_STATES = {"stopped", "suspended", "created"}


class Controller:
    def __init__(self, cfg: dict, api, depth_fn, clock=time.monotonic, receipts_path: str = ""):
        self.cfg = cfg
        self.api = api
        self.depth_fn = depth_fn
        self.clock = clock
        self.receipts_path = receipts_path or os.environ.get("FLY_CONTROLLER_RECEIPTS", "")
        self.empty_since: float | None = None   # queue-empty stopwatch for the drain cooldown
        self.capacity_backoff_until = 0.0
        # first capacity error pauses scale-up for TWO polling cycles (a sub-poll backoff would
        # be invisible — the next tick would retry immediately), doubling on repeats up to the cap
        self.capacity_backoff_initial = max(RETRY_BASE_S, 2.0 * self.cfg["poll_seconds"])
        self.capacity_backoff_s = self.capacity_backoff_initial

    def receipt(self, record: dict) -> None:
        record = {"at_monotonic_s": round(self.clock(), 1), "role": MANAGED_BY_VALUE, **record}
        line = json.dumps(record, separators=(",", ":"))
        print(line, flush=True)
        if self.receipts_path:
            try:
                with open(self.receipts_path, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError:
                pass  # receipts must never take the fleet down

    def desired_for(self, depth: int) -> int:
        raw = math.ceil(depth / self.cfg["jobs_per_worker"]) if depth > 0 else 0
        return max(self.cfg["min_workers"], min(self.cfg["max_workers"], raw))

    def _ours(self, machine: dict) -> bool:
        meta = (machine.get("config") or {}).get("metadata") or {}
        return meta.get(MANAGED_BY_KEY) == MANAGED_BY_VALUE

    def _new_machine_config(self, image: str) -> dict:
        return {
            "image": image,
            "guest": dict(self.cfg["guest"]),
            "metadata": {MANAGED_BY_KEY: MANAGED_BY_VALUE},
            "restart": {"policy": "no"},        # the controller owns lifecycle, not the platform
            "auto_destroy": False,               # stopped machines restart warm (rootfs pennies)
            "init": {"cmd": list(self.cfg["command"])},
        }

    def tick(self) -> dict:
        """One reconcile pass. Returns the receipt record (also emitted)."""
        try:
            depth = self.depth_fn()
        except Exception as exc:
            record = {"event": "tick_error", "stage": "queue_depth", "error": str(exc)[:200]}
            self.receipt(record)
            return record
        desired = self.desired_for(depth)
        try:
            machines = [m for m in self.api.list_machines() if self._ours(m)]
        except Exception as exc:
            record = {"event": "tick_error", "stage": "list_machines", "error": str(exc)[:200]}
            self.receipt(record)
            return record
        up = [m for m in machines if m.get("state") in UP_STATES]
        startable = [m for m in machines if m.get("state") in STARTABLE_STATES]
        actions: list[str] = []
        errors: list[str] = []

        if depth > 0:
            self.empty_since = None
            shortfall = desired - len(up)
            if shortfall > 0 and self.clock() >= self.capacity_backoff_until:
                started, created = self._scale_up(shortfall, startable, machines, actions, errors)
                if not errors:
                    self.capacity_backoff_s = self.capacity_backoff_initial  # healthy tick resets the ladder
            elif shortfall > 0:
                actions.append(f"hold:capacity_backoff({max(0.0, self.capacity_backoff_until - self.clock()):.0f}s left)")
            elif len(up) > desired:
                for machine in up[desired:]:
                    self._stop(machine, actions, errors)   # queue shrank — drain the excess now
        else:
            if up:
                if self.empty_since is None:
                    self.empty_since = self.clock()
                    actions.append("drain:cooldown_started")
                elif self.clock() - self.empty_since >= self.cfg["cooldown_seconds"]:
                    for machine in up:
                        self._stop(machine, actions, errors)
                    self.empty_since = None
                else:
                    actions.append(f"drain:cooldown({self.clock() - self.empty_since:.0f}s/"
                                   f"{self.cfg['cooldown_seconds']:.0f}s)")
            else:
                self.empty_since = None
        record = {"event": "tick", "depth": depth, "desired": desired, "up": len(up),
                  "pool": len(machines), "actions": actions or ["none"], **({"errors": errors} if errors else {})}
        self.receipt(record)
        return record

    def _scale_up(self, shortfall: int, startable: list[dict], pool: list[dict],
                  actions: list[str], errors: list[str]) -> tuple[int, int]:
        started = created = 0
        for machine in startable[:shortfall]:           # warm machines first — cheapest + fastest
            try:
                self.api.start(machine["id"])
                actions.append(f"start:{machine['id']}")
                started += 1
            except MachinesAPI.RateLimited as exc:
                errors.append(str(exc)); time.sleep(min(exc.retry_after, 10.0)); break
            except MachinesAPI.CapacityError as exc:
                self._capacity_hit(exc, errors); break
            except Exception as exc:
                errors.append(str(exc)[:200]); break
        remaining = shortfall - started
        if remaining > 0:
            image = os.environ.get("FLY_WORKER_IMAGE") or next(
                ((m.get("config") or {}).get("image") for m in pool if (m.get("config") or {}).get("image")), None)
            if not image:
                errors.append("no_image: set FLY_WORKER_IMAGE or deploy the worker app once")
            else:
                for _ in range(min(remaining, CREATES_PER_TICK_MAX)):
                    try:
                        machine = self.api.create(self._new_machine_config(image), self.cfg["region"])
                        actions.append(f"create:{machine.get('id', '?')}")
                        created += 1
                    except MachinesAPI.RateLimited as exc:
                        errors.append(str(exc)); time.sleep(min(exc.retry_after, 10.0)); break
                    except MachinesAPI.CapacityError as exc:
                        self._capacity_hit(exc, errors); break
                    except Exception as exc:
                        errors.append(str(exc)[:200]); break
        return started, created

    def _capacity_hit(self, exc: Exception, errors: list[str]) -> None:
        errors.append(f"capacity: {str(exc)[:160]}")
        self.capacity_backoff_until = self.clock() + self.capacity_backoff_s
        self.capacity_backoff_s = min(self.capacity_backoff_s * 2, CAPACITY_BACKOFF_MAX_S)

    def _stop(self, machine: dict, actions: list[str], errors: list[str]) -> None:
        try:
            self.api.stop(machine["id"])                 # exact id only, ours only
            actions.append(f"stop:{machine['id']}")
        except Exception as exc:
            errors.append(str(exc)[:200])

    def run_forever(self) -> None:
        self.receipt({"event": "controller_start", "app": self.cfg["app"],
                      "queue_key": self.cfg["queue_key"], "max_workers": self.cfg["max_workers"]})
        while True:
            try:
                self.tick()
            except Exception as exc:                     # belt-and-braces: the loop never dies
                self.receipt({"event": "tick_error", "stage": "tick", "error": str(exc)[:200]})
            time.sleep(self.cfg["poll_seconds"])


# ---------------------------------------------------------------- self-test (offline)

def _self_test() -> int:
    cfg = _load_worker_config()
    cfg.update({"poll_seconds": 15.0, "cooldown_seconds": 120.0})  # deterministic regardless of topology edits

    class FakeClock:
        now = 0.0
        def __call__(self) -> float:
            return self.now

    class FakeAPI:
        """Machines-API double: 2 pre-existing stopped machines, capacity error on first
        create, 429 on one start — the failure modes the June 2026 incidents exercised."""
        def __init__(self):
            self.machines = {
                "m1": {"id": "m1", "state": "stopped",
                       "config": {"image": "img:v1", "metadata": {MANAGED_BY_KEY: MANAGED_BY_VALUE}}},
                "m2": {"id": "m2", "state": "stopped",
                       "config": {"image": "img:v1", "metadata": {MANAGED_BY_KEY: MANAGED_BY_VALUE}}},
                "alien": {"id": "alien", "state": "started", "config": {"image": "img:v1", "metadata": {}}},
            }
            self.create_calls = 0
            self.rate_limited_once = False
            self.counter = 2

        def list_machines(self):
            return [dict(m) for m in self.machines.values()]

        def start(self, machine_id):
            if not self.rate_limited_once and machine_id == "m2":
                self.rate_limited_once = True
                raise MachinesAPI.RateLimited(0.0)
            self.machines[machine_id]["state"] = "started"

        def stop(self, machine_id):
            assert machine_id != "alien", "stopped a machine we don't manage"
            self.machines[machine_id]["state"] = "stopped"

        def create(self, config, region):
            self.create_calls += 1
            if self.create_calls == 1:
                raise MachinesAPI.CapacityError("412: insufficient capacity in iad")
            assert config["metadata"][MANAGED_BY_KEY] == MANAGED_BY_VALUE
            assert config["guest"] == cfg["guest"] and config["init"]["cmd"] == cfg["command"]
            self.counter += 1
            mid = f"m{self.counter}"
            self.machines[mid] = {"id": mid, "state": "started", "config": dict(config)}
            return {"id": mid}

    clock = FakeClock()
    api = FakeAPI()
    depths = iter([0, 25, 25, 25, 120, 0, 0, 0, 0, 0, 0, 0, 0])
    current = {"d": 0}

    def depth_fn():
        current["d"] = next(depths, current["d"])
        return current["d"]

    ctl = Controller(cfg, api, depth_fn, clock=clock)
    results = []
    for _ in range(15):  # enough ticks for scale-up, capacity hold, and a full 120s drain cooldown
        results.append(ctl.tick())
        clock.now += cfg["poll_seconds"]

    ups = lambda: sum(1 for m in api.machines.values() if m["state"] == "started" and m["id"] != "alien")  # noqa: E731
    checks = [
        ("idle tick takes no action", results[0]["actions"] == ["none"]),
        ("depth 25 → desired 3 (ceil 25/10)", results[1]["desired"] == 3),
        ("starts the two warm machines before creating", any(a.startswith("start:m1") for a in results[1]["actions"])),
        ("429 on start is survived and retried later", any("rate limited" in e for e in results[1].get("errors", []))
         and any(a == "start:m2" for r in results for a in r["actions"])),
        ("capacity error on create backs off (no thrash)", any("capacity" in e for r in results[1:4] for e in r.get("errors", []))
         and any("hold:capacity_backoff" in a for r in results[2:5] for a in r["actions"])),
        ("recovers and reaches desired after backoff", any(a.startswith("create:") for r in results for a in r["actions"])),
        ("depth 120 → desired capped at fly max", max(r["desired"] for r in results) == cfg["max_workers"] <= 8),
        ("creates are throttled per tick", api.create_calls <= 1 + CREATES_PER_TICK_MAX * 13),
        ("drain waits a full cooldown before stopping", any("drain:cooldown" in a for r in results for a in r["actions"])),
        ("fleet reaches zero after sustained empty queue", ups() == 0),
        ("never touches machines it does not manage", api.machines["alien"]["state"] == "started"),
        ("every tick emitted a receipt", all(r.get("event") in ("tick", "tick_error") for r in results)),
    ]
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print(("PASS — " if not failed else "FAIL — ") + f"{len(checks) - len(failed)}/{len(checks)} controller self-test checks")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = set(argv if argv is not None else sys.argv[1:])
    if "--self-test" in args:
        return _self_test()
    cfg = _load_worker_config()
    token = os.environ.get("FLY_API_TOKEN", "")
    redis_url = os.environ.get("REDIS_URL", "")
    if not token or not redis_url:
        print("fly_worker_controller: FLY_API_TOKEN and REDIS_URL are required (fly secrets set). "
              "Run --self-test for the offline check.")
        return 2
    api = MachinesAPI(os.environ.get("FLY_MACHINES_API", "https://api.machines.dev"), token, cfg["app"])
    ctl = Controller(cfg, api, lambda: redis_llen(redis_url, cfg["queue_key"]))
    if "--once" in args:
        record = ctl.tick()
        return 0 if record.get("event") == "tick" else 1
    ctl.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
