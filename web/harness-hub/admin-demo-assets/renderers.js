import { $, esc, setText } from "./dom.js";

function chips(items, cls) {
  return '<div class="ad-chip-row">' + (items || []).map(function (item) {
    return '<span class="ad-chip ' + (cls || "") + '">' + esc(item) + '</span>';
  }).join("") + '</div>';
}

function metric(label, value) {
  return '<div class="ad-metric"><strong>' + esc(value) + '</strong><span>' + esc(label) + '</span></div>';
}

function money(value) {
  var n = Number(value || 0);
  if (!n) return "$0.00";
  return "$" + n.toFixed(n < 0.01 ? 4 : 2);
}

export function renderHomeCards(state) {
  var summary = state.latestSummary || {};
  setText("#homeSources", state.selectedSources.length ? state.selectedSources.length + " selected" : "No sources yet");
  setText("#homeProcessing", state.activeRunId ? (state.latestStatus || "Run active") : "No active run");
  setText("#homeOutputs", summary.claims ? summary.claims + " claims" : "Waiting for run");
  setText("#homeDownload", summary.claims ? "4 packages · " + money(summary.estimated_cost_usd) : "No package yet");
  setText("#homeExplore", summary.claims ? "Graph + RAG ready" : "No index yet");
  setText("#homeTesting", summary.claims ? "Run checks available" : "Not tested");
}

export function renderSources(state, onRemove) {
  setText("#sourceCount", String(state.selectedSources.length));
  $("#sourceList").innerHTML = state.selectedSources.map(function (source, index) {
    return '<div class="ad-source-row">' +
      '<span>' + esc(source.type) + '</span>' +
      '<strong>' + esc(source.name) + '</strong>' +
      '<small>' + esc(source.status) + '</small>' +
      '<button type="button" data-remove-source="' + index + '">Remove</button>' +
    '</div>';
  }).join("") || '<div class="ad-empty-source">No source selected</div>';
  Array.prototype.forEach.call(document.querySelectorAll("[data-remove-source]"), function (btn) {
    btn.addEventListener("click", function () {
      onRemove(Number(btn.getAttribute("data-remove-source")));
    });
  });
}

export function renderSync(sources) {
  var list = sources || [];
  setText("#syncCount", String(list.length));
  $("#syncList").innerHTML = list.map(function (source) {
    var stateClass = source.sync_state === "synced" ? "ad-sync-ok" : "ad-sync-wait";
    return '<div class="ad-sync-row">' +
      '<div><strong>' + esc(source.name) + '</strong><small>' + esc(source.type) + ' · ' + esc(source.version || "unversioned") + '</small></div>' +
      '<span class="ad-sync-state ' + stateClass + '">' + esc(source.sync_state || "queued") + '</span>' +
      '<p>' + esc(source.last_sync_label || "not synced yet") + ' · ' + esc(source.change_state || "waiting") + ' · ' + esc(source.content_hash || "no hash") + '</p>' +
      '<em>' + esc(source.next_action || "") + '</em>' +
    '</div>';
  }).join("") || '<div class="ad-empty-source">Sources will appear after a run starts.</div>';
}

export function renderMetrics(summary) {
  $("#metrics").innerHTML = [
    metric("chunks", summary.chunks || 0),
    metric("sources", summary.sources || 0),
    metric("entities", summary.entities || 0),
    metric("claims", summary.claims || 0),
    metric("verify", summary.fragile_facts || 0),
    metric("worker jobs", summary.worker_updates || 0),
    metric("approvals", summary.queue_approval_required || 0),
    metric("est. run cost", money(summary.estimated_cost_usd)),
    metric("budget used", (summary.budget_used_pct || 0) + "%")
  ].join("");
}

export function renderRunCard(run, startedAt) {
  var progress = Math.max(0, Math.min(100, Number((run && run.progress) || 0)));
  setText("#runId", run && run.run_id ? run.run_id : "not started");
  $("#runProgressBar").style.width = progress + "%";
  setText("#runEta", etaLabel(run, startedAt));
}

function etaLabel(run, startedAt) {
  if (!run || run.status === "complete") return "ETA: done";
  if (!run.progress || run.progress < 8 || !startedAt) return "ETA: calculating";
  var elapsed = (Date.now() - startedAt) / 1000;
  var remaining = Math.max(0, Math.round((elapsed / run.progress) * (100 - run.progress)));
  return "ETA: " + remaining + "s";
}

export function renderWorkerPlan(plan) {
  $("#workerPlan").innerHTML = (plan || []).map(function (stage) {
    return '<div class="ad-stage">' +
      '<div class="ad-stage-code">' + esc(stage.stage) + '<br><span class="ad-tag">' + esc(stage.status) + '</span></div>' +
      '<div class="ad-stage-output">' + esc(stage.output) + '</div>' +
    '</div>';
  }).join("") || '<div class="ad-item"><p>No worker stages yet.</p></div>';
}

export function renderModelRoutes(routes) {
  var list = routes || [];
  setText("#modelRouteCount", list.length + (list.length === 1 ? " route" : " routes"));
  $("#modelRouteList").innerHTML = list.map(function (route) {
    var status = String(route.status || "selected").replace(/_/g, "-");
    var reasons = (route.fallback_reasons || []).map(function (reason) { return reason.replace(/_/g, " "); });
    var meta = [
      route.quality_tier || "model",
      route.trust_boundary || "policy",
      money(route.estimated_cost_usd)
    ];
    if (route.fallback_count) meta.push(route.fallback_count + " rejected");
    return '<div class="ad-route-card ad-route-card-' + esc(status) + '">' +
      '<div><strong>' + esc(route.label || route.task_type || "Model route") + '</strong>' +
      '<small>' + esc(route.task_type || "context task") + '</small></div>' +
      '<span>' + esc((route.status || "selected").replace(/_/g, " ")) + '</span>' +
      '<p>' + esc(route.selected_adapter === "none" ? "No compliant route under current policy" : route.selected_adapter || "selected route") + '</p>' +
      chips(meta.concat(reasons), status === "approval-required" ? "ad-chip-high" : "ad-chip-normal") +
    '</div>';
  }).join("") || '<div class="ad-item"><p>Model route decisions will appear after processing starts.</p></div>';
}

export function renderCostEstimate(cost) {
  var estimate = cost || {};
  setText("#costTotal", money(estimate.estimated_total_usd));
  setText("#costBudget", (estimate.budget_used_pct || 0) + "% of $" + Number(estimate.budget_ceiling_usd || 5).toFixed(0) + " demo ceiling");
  $("#costLineItems").innerHTML = (estimate.line_items || []).map(function (item) {
    return '<div class="ad-cost-row">' +
      '<div><strong>' + esc(item.label) + '</strong><small>' + esc(item.basis) + '</small></div>' +
      '<span>' + money(item.amount_usd) + '</span>' +
    '</div>';
  }).join("") || '<div class="ad-item"><p>Run cost will appear after processing starts.</p></div>';
  $("#costGuardrails").innerHTML = (estimate.guardrails || []).slice(0, 4).map(function (item) {
    return '<li>' + esc(item) + '</li>';
  }).join("") || '<li>Use deterministic workers before expensive model or browser lanes.</li>';
}

export function renderQueuePlan(queuePlan) {
  var plan = queuePlan || {};
  var summary = plan.summary || {};
  var tasks = plan.tasks || [];
  var total = Number(summary.total || tasks.length || 0);
  setText("#queueControlCount", total + (total === 1 ? " task" : " tasks"));
  $("#queueSummary").innerHTML = [
    ["Queued", summary.queued || 0],
    ["Batched", summary.batched || 0],
    ["Needs approval", summary.approval_required || 0],
    ["Blocked", summary.blocked || 0],
    ["Est. follow-up", money(summary.estimated_total_usd)]
  ].map(function (item) {
    return '<div class="ad-queue-stat"><strong>' + esc(item[1]) + '</strong><span>' + esc(item[0]) + '</span></div>';
  }).join("");
  $("#queueTaskList").innerHTML = tasks.slice(0, 8).map(function (task) {
    var action = String(task.action || "allow").replace(/_/g, "-");
    var reasons = (task.reason_codes || []).map(function (reason) { return reason.replace(/_/g, " "); });
    var op = task.operator_action || {};
    var buttons = (op.actions || []).map(function (item) {
      return '<button type="button" data-queue-action="' + esc(item.action) + '" data-queue-task="' + esc(task.fact_id || task.dedupe_key || "") + '">' + esc(item.label) + '</button>';
    }).join("");
    return '<div class="ad-queue-task ad-queue-task-' + esc(action) + '">' +
      '<div><strong>' + esc(task.target || "Follow-up task") + '</strong>' +
      '<small>' + esc(task.task_type || "context task") + ' · ' + esc(task.lane || "queue") + ' · ' + esc(task.priority || "normal") + '</small></div>' +
      '<span>' + esc(task.action_label || task.action || "Queued") + '</span>' +
      '<p>' + esc(task.claim || "") + '</p>' +
      chips(reasons.concat([money(task.estimated_total_usd), op.status || "pending"]), action === "require-approval" || action === "block" ? "ad-chip-high" : "ad-chip-normal") +
      (buttons ? '<div class="ad-queue-actions">' + buttons + '</div>' : '') +
    '</div>';
  }).join("") || '<div class="ad-item"><p>No follow-up tasks have been planned yet.</p></div>';
  $("#queueActionPlaybook").innerHTML = [
    ["approval_required", "Approve and requeue after policy or budget review"],
    ["budget_blocked", "Increase budget or narrow scope, then requeue"],
    ["failed_permanently", "Inspect failure, fix producer or worker, then requeue"]
  ].map(function (item) {
    return '<div><strong>' + esc(item[0]) + '</strong><span>' + esc(item[1]) + '</span></div>';
  }).join("");
}

export function renderExplore(data) {
  var summary = (data && data.summary) || {};
  var facts = (data && data.facts) || [];
  var nodes = (data && data.nodes) || [];
  var chunks = (data && data.chunks) || [];
  var sources = (data && data.sources) || [];
  var updates = (data && data.updates) || [];
  var ready = Boolean(summary.claims || facts.length || chunks.length);
  setText("#exploreGraphStats", ready ? nodes.length + " nodes" : "No run");
  setText("#exploreDataStats", ready ? facts.length + " facts" : "Waiting");
  setText("#exploreRagStats", ready ? chunks.length + " chunks" : "No index");
  setText("#exploreGraphState", ready
    ? "Graph is built from source chunks, extracted entities, candidate facts, and support edges for scoped retrieval."
    : "Open entities, claims, source links, supporting evidence, and provenance paths from the processed corpus.");
  $("#exploreFactList").innerHTML = facts.slice(0, 6).map(function (fact) {
    return '<div class="ad-browser-row">' +
      '<div><strong>' + esc(fact.subject || "Fact") + '</strong><span>' + esc(fact.state || fact.confidence || "candidate") + '</span></div>' +
      '<p>' + esc(fact.claim || "") + '</p>' +
      '<small>' + esc(fact.source_chunk || "source") + ' · ' + esc((fact.signals || []).slice(0, 3).join(", ") || "lineage retained") + '</small>' +
    '</div>';
  }).join("") || '<div class="ad-empty-source">Run processing to browse extracted facts.</div>';
  var strongest = facts.find(function (fact) { return fact.confidence === "medium"; }) || facts[0];
  var answer = ready
    ? "RAG preview: this package has " + chunks.length + " chunk" + (chunks.length === 1 ? "" : "s") +
      ", " + facts.length + " fact" + (facts.length === 1 ? "" : "s") +
      ", and " + updates.length + " automated refresh job" + (updates.length === 1 ? "" : "s") +
      ". " + (strongest ? "Example cited fact: " + strongest.claim : "No cited facts are available yet.")
    : "Ask a question against the generated context package after a run completes.";
  setText("#exploreChatAnswer", answer);
  return { sources: sources.length, chunks: chunks.length, facts: facts.length, nodes: nodes.length };
}

export function renderIntegrationTests(data) {
  var summary = (data && data.summary) || {};
  var queue = (data && data.queue_plan && data.queue_plan.summary) || {};
  var sources = (data && data.sources) || [];
  var routes = (data && data.model_routes) || [];
  var packsReady = Number(summary.claims || 0) > 0;
  setText("#testConnectors", sources.length
    ? sources.length + " source" + (sources.length === 1 ? "" : "s") + " synced with version/hash metadata"
    : "No connector run yet");
  setText("#testWorkers", Number(summary.worker_updates || 0)
    ? summary.worker_updates + " follow-up jobs planned · " + (queue.blocked || 0) + " blocked by policy"
    : "Queues, retries, priority routing, model fallback");
  setText("#testServing", packsReady
    ? "4 export contracts available: text, RAG, graph, audit"
    : "Text, RAG, graph, audit, API contracts");
  setText("#testGovernance", routes.length
    ? routes.length + " model route decisions · " + (summary.queue_approval_required || 0) + " approval gate" + (summary.queue_approval_required === 1 ? "" : "s")
    : "Source trust, provenance, approval gates, cache scope");
}

export function renderGraph(data) {
  var svg = $("#graphSvg");
  var nodes = (data.nodes || []).slice(0, 42);
  var nodeById = {};
  nodes.forEach(function (node, index) { nodeById[node.id] = Object.assign({}, node, { i: index }); });
  var edges = (data.edges || []).filter(function (edge) { return nodeById[edge.from] && nodeById[edge.to]; }).slice(0, 90);
  var width = 720;
  var height = 300;
  var cx = width / 2;
  var cy = height / 2;
  var placed = nodes.map(function (node, index) {
    var angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1);
    var radius = node.type === "chunk" ? 78 : node.type === "claim" ? 126 : 112;
    return Object.assign({}, node, { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius });
  });
  placed.forEach(function (node) { nodeById[node.id] = node; });
  var edgeHtml = edges.map(function (edge) {
    var a = nodeById[edge.from];
    var b = nodeById[edge.to];
    return '<line x1="' + a.x.toFixed(1) + '" y1="' + a.y.toFixed(1) + '" x2="' + b.x.toFixed(1) + '" y2="' + b.y.toFixed(1) + '" stroke="#ccd4c8" stroke-width="1" />';
  }).join("");
  var nodeHtml = placed.map(function (node) {
    var fill = node.type === "chunk" ? "#a66a12" : node.type === "claim" ? "#b84f3e" : "#126b5f";
    var size = node.type === "chunk" ? 7 : node.type === "claim" ? 6 : 8;
    var label = node.label.length > 18 ? node.label.slice(0, 17) + "..." : node.label;
    return '<g><circle cx="' + node.x.toFixed(1) + '" cy="' + node.y.toFixed(1) + '" r="' + size + '" fill="' + fill + '" />' +
      '<text x="' + (node.x + 10).toFixed(1) + '" y="' + (node.y + 4).toFixed(1) + '" fill="#4b5449" font-size="10" font-family="JetBrains Mono, monospace">' + esc(label) + '</text></g>';
  }).join("");
  svg.innerHTML = edgeHtml + nodeHtml;
  setText("#graphCount", nodes.length + " nodes");
}

export function renderVerificationQueue(items) {
  setText("#fragileCount", String((items || []).length));
  $("#fragileList").innerHTML = (items || []).map(function (item) {
    return '<div class="ad-item"><strong>' + esc(item.claim) + '</strong><p>' +
      'Source chunk ' + esc(item.source_chunk) + ' · original customer-source claim retained in export provenance</p>' +
      chips((item.reasons || []).concat(["history retained"]), "ad-chip-high") + '</div>';
  }).join("") || '<div class="ad-item"><p>No items need evidence in this pass.</p></div>';
}

export function renderUpdates(items) {
  setText("#updateCount", String((items || []).length));
  $("#updateList").innerHTML = (items || []).map(function (item) {
    var cls = item.priority === "high" ? "ad-chip-high" : "ad-chip-normal";
    return '<div class="ad-item"><strong>' + esc(item.target) + '</strong><p>' +
      esc(item.query) + '</p>' + chips([item.worker, item.priority, item.budget_action || "budgeted"], cls) + '</div>';
  }).join("") || '<div class="ad-item"><p>No automated refresh jobs queued.</p></div>';
}

export function renderClaims(items) {
  setText("#claimCount", String((items || []).length));
  $("#claimList").innerHTML = (items || []).slice(0, 40).map(function (item) {
    return '<div class="ad-item"><strong>' + esc(item.subject) + '</strong><p>' +
      esc(item.claim) + '</p><p>Lineage: ' + esc(item.source_chunk) + ' · confidence ' + esc(item.confidence || "candidate") + '</p>' +
      chips((item.signals || []).concat([item.confidence, "provenance"])) + '</div>';
  }).join("") || '<div class="ad-item"><p>No claims extracted yet.</p></div>';
}

export function renderServing(data) {
  var summary = data.summary || {};
  var claims = summary.claims || 0;
  var chunks = summary.chunks || 0;
  var nodes = (data.nodes || []).length;
  var sources = (data.sources || []).length || summary.sources || 0;
  var packs = [
    ["Text context pack", claims ? "ready after promotion" : "waiting", claims + " claims · current facts with optional provenance history", "Serve to prompts, tools, and agent instructions"],
    ["RAG index", chunks ? "indexable" : "waiting", chunks + " chunks · embeddings, keywords, citations, freshness metadata", "Serve via vector, keyword, or reranked retrieval"],
    ["Graph / hybrid retrieval", nodes ? "graph ready" : "waiting", nodes + " nodes · entities, claims, source links, procedure edges", "Use for relationship lookup, impact analysis, and scoped retrieval"],
    ["Audit packet", sources ? "traceable" : "waiting", sources + " sources · provenance, diffs, worker trace, approvals", "Use for review, export, and regulated workflows"]
  ];
  setText("#servingCount", packs.filter(function (pack) { return pack[1] !== "waiting"; }).length + " packs");
  $("#servingList").innerHTML = packs.map(function (pack) {
    return '<div class="ad-serving-card">' +
      '<div><strong>' + esc(pack[0]) + '</strong><span>' + esc(pack[1]) + '</span></div>' +
      '<p>' + esc(pack[2]) + '</p><small>' + esc(pack[3]) + '</small></div>';
  }).join("");
}
