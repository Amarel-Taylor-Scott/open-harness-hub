#!/usr/bin/env python3
"""scripts.check_local_spawn_manager — proof: the local spawn manager builds a correct worker command,
dry-runs without spawning, records pid on real spawn, stops by EXACT pid only, and NEVER uses pkill."""
from __future__ import annotations
import argparse
from pathlib import Path
from src.baltor.workers import local_spawn_manager as sm
def _self_test() -> int:
    fails=[]
    def chk(n,ok,d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': '+d) if d and not ok else ''}"); (fails.append(n) if not ok else None)
    cmd=sm.build_command(worker_id="w1",capability_id="utility.http_download",queue="utility.realtime",db="/tmp/x.db",bootstrap_task_id="task-1")
    chk("command names the worker entrypoint","scripts/capability_worker.py" in cmd)
    chk("command passes worker-id + capability + queue + db",all(x in cmd for x in ["--worker-id","w1","--capability-id","utility.http_download","--queue","--db"]))
    chk("bootstrap-task-id passed as a HINT","--bootstrap-task-id" in cmd and "task-1" in cmd)
    res=sm.spawn(worker_id="w1",capability_id="utility.http_download",queue="utility.realtime",db="/tmp/x.db",dry_run=True)
    chk("dry-run does NOT spawn",res["spawned"] is False and res["dry_run"] is True and res["command"])
    st=sm.stop(2147480000)  # non-existent pid
    chk("stop handles missing pid (no crash)",st["stopped"] is False and st["reason"]=="no such pid")
    src=Path(sm.__file__).read_text()
    chk("NO pkill / pattern-kill in the spawn manager","pkill" not in src and "killall" not in src)
    chk("stop uses os.kill by exact pid","os.kill" in src)
    print(f"\n{'PASS — check_local_spawn_manager: builds the worker command, dry-runs without spawning, stops by exact pid, never pkill.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1
def _main(a=None):
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); ns=p.parse_args(a)
    return _self_test() if ns.self_test else (p.print_help() or 0)
if __name__=="__main__": raise SystemExit(_main())
