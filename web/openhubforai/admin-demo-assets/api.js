export async function createRun(payload) {
  var res = await fetch("/api/admin-demo/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  var run = await res.json();
  if (!res.ok) throw new Error(run.error || "run failed");
  return run;
}

export async function getRun(runId) {
  var res = await fetch("/api/admin-demo/runs/" + encodeURIComponent(runId));
  var run = await res.json();
  if (!res.ok) throw new Error(run.error || "run status failed");
  return run;
}
