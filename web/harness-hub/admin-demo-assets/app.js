import { createRun, getRun } from "./api.js";
import { $, setText } from "./dom.js";
import {
  renderClaims,
  renderCostEstimate,
  renderExplore,
  renderGraph,
  renderHomeCards,
  renderIntegrationTests,
  renderMetrics,
  renderModelRoutes,
  renderQueuePlan,
  renderRunCard,
  renderServing,
  renderSources,
  renderSync,
  renderUpdates,
  renderVerificationQueue,
  renderWorkerPlan
} from "./renderers.js";
import { sample } from "./sample.js";

var state = {
  fileName: "",
  activeRunId: "",
  activeStartedAt: 0,
  latestStatus: "",
  latestSummary: {},
  selectedSources: []
};

function routeView() {
  if (location.pathname === "/admin-demo" || location.pathname === "/admin-demo/") return "home";
  if (location.pathname.indexOf("/admin-demo/monitoring") === 0) return "monitoring";
  if (location.pathname.indexOf("/admin-demo/outputs") === 0) return "outputs";
  if (location.pathname.indexOf("/admin-demo/download") === 0) return "download";
  if (location.pathname.indexOf("/admin-demo/explore") === 0) return "explore";
  if (location.pathname.indexOf("/admin-demo/testing") === 0) return "testing";
  return "sources";
}

function setStatus(text) {
  state.latestStatus = text;
  setText("#statusLine", text);
  renderHomeCards(state);
}

function setView(view, push) {
  var target = view || "sources";
  document.body.setAttribute("data-admin-view", target);
  Array.prototype.forEach.call(document.querySelectorAll("[data-view-section]"), function (section) {
    section.hidden = !(target !== "home" && section.getAttribute("data-view-section") === target);
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-view-link]"), function (link) {
    link.classList.toggle("ad-flow-card-active", link.getAttribute("data-view-link") === target);
  });
  if (push) {
    var path = target === "home" ? "/admin-demo/" : target === "sources" ? "/admin-demo/sources" : "/admin-demo/" + target;
    history.pushState(null, "", path + (state.activeRunId ? "#run=" + encodeURIComponent(state.activeRunId) : ""));
  }
}

function sourceText() {
  var raw = $("#contextInput").value.trim();
  if (raw) return raw;
  return state.selectedSources.filter(function (source) { return source.text; }).map(function (source) {
    return "# Source: " + source.name + "\n\n" + source.text;
  }).join("\n\n---\n\n").trim();
}

function sourcePayload() {
  return state.selectedSources.map(function (source) {
    return {
      type: source.type,
      name: source.name,
      status: source.status,
      size: source.size || (source.text ? source.text.length : 0),
      last_modified: source.last_modified || "",
      text: source.text || ""
    };
  });
}

function redrawSources() {
  renderSources(state, function (index) {
    state.selectedSources.splice(index, 1);
    redrawSources();
  });
  renderHomeCards(state);
}

function addSource(source) {
  state.selectedSources.push(source);
  redrawSources();
}

function setRawText(text) {
  $("#contextInput").value = text;
}

function renderResult(data) {
  state.latestSummary = data.summary || {};
  state.latestSources = data.sources || [];
  renderMetrics(state.latestSummary);
  renderSync(data.sources || []);
  renderWorkerPlan(data.worker_plan || []);
  renderModelRoutes(data.model_routes || []);
  renderCostEstimate(data.cost_estimate || {});
  renderQueuePlan(data.queue_plan || {});
  renderGraph(data);
  renderExplore(data);
  renderIntegrationTests(data);
  renderVerificationQueue(data.fragile_facts || []);
  renderUpdates(data.updates || []);
  renderClaims(data.facts || []);
  renderServing(data);
  renderDownloadState();
  renderHomeCards(state);
}

function renderRunState(run) {
  state.latestSummary = run.summary || {};
  state.latestSources = (run.result && run.result.sources) || run.sources || [];
  renderRunCard(run, state.activeStartedAt);
  renderMetrics(state.latestSummary);
  renderSync((run.result && run.result.sources) || run.sources || []);
  renderWorkerPlan(run.worker_plan || []);
  renderModelRoutes((run.result && run.result.model_routes) || []);
  renderCostEstimate((run.result && run.result.cost_estimate) || {});
  renderQueuePlan((run.result && run.result.queue_plan) || {});
  renderExplore(run.result || run);
  renderIntegrationTests(run.result || run);
  setStatus((run.status || "running") + " · " + (run.progress || 0) + "%");
  if (run.result) renderResult(run.result);
  else renderDownloadState();
}

function renderDownloadState() {
  var ready = Boolean(state.activeRunId && state.latestSummary && state.latestSummary.claims);
  Array.prototype.forEach.call(document.querySelectorAll("[data-export-kind]"), function (btn) {
    btn.disabled = !ready;
    btn.textContent = ready ? "Export" : "Waiting";
    if (btn.getAttribute("data-export-kind") === "manifest") btn.textContent = ready ? "Export manifest" : "Waiting";
  });
  setText("#exportTextState", ready ? "Includes facts, state, confidence, and provenance history." : "Run a context analysis first.");
  setText("#exportRagState", ready ? "JSONL chunks with claims, source metadata, and freshness fields." : "Use for vector and keyword stores.");
  setText("#exportGraphState", ready ? "GraphML entities, claims, chunks, and support edges." : "Use for hybrid retrieval.");
  setText("#exportAuditState", ready ? "ZIP with sources, worker trace, claims, verification queue, and refresh jobs." : "Use for review workflows.");
  renderExportManifest(ready);
}

function renderExportManifest(ready) {
  var node = $("#exportManifestPreview");
  if (!node) return;
  if (!ready) {
    node.textContent = "Run a context analysis to generate package endpoints and governance metadata.";
    return;
  }
  var summary = state.latestSummary || {};
  var base = "/api/admin-demo/runs/" + encodeURIComponent(state.activeRunId) + "/exports";
  node.textContent = JSON.stringify({
    package_type: "baltor.serving_manifest.v1",
    run_id: state.activeRunId,
    summary: {
      sources: summary.sources || 0,
      chunks: summary.chunks || 0,
      claims: summary.claims || 0,
      verification_queue: summary.fragile_facts || 0,
      refresh_jobs: summary.worker_updates || 0
    },
    contracts: [
      { kind: "text", content_type: "application/json", path: base + "/text" },
      { kind: "rag", content_type: "application/x-ndjson", path: base + "/rag" },
      { kind: "graph", content_type: "application/graphml+xml", path: base + "/graph" },
      { kind: "audit", content_type: "application/zip", path: base + "/audit" }
    ],
    governance: {
      state_history_included: true,
      source_versions_included: true,
      cost_estimate_included: true
    }
  }, null, 2);
}

async function analyze() {
  var text = sourceText();
  if (!text) {
    setStatus("Upload a file or connect a source first");
    $("#fileInput").focus();
    return;
  }
  setStatus("Creating run...");
  $("#analyzeBtn").disabled = true;
  try {
    var run = await createRun({
      text: text,
      filename: state.fileName || state.selectedSources.map(function (source) { return source.name; }).join(", "),
      sources: sourcePayload()
    });
    state.activeRunId = run.run_id;
    state.activeStartedAt = Date.now();
    history.replaceState(null, "", location.pathname + "#run=" + encodeURIComponent(state.activeRunId));
    renderRunState(run);
    setView("monitoring", true);
    await pollRun(state.activeRunId);
  } catch (err) {
    setStatus(String(err.message || err));
    $("#analyzeBtn").disabled = false;
  }
}

async function pollRun(runId) {
  for (var attempt = 0; attempt < 300; attempt += 1) {
    await new Promise(function (resolve) { setTimeout(resolve, 450); });
    var run = await getRun(runId);
    renderRunState(run);
    if (run.status === "complete") {
      setStatus("Analysis complete · " + run.run_id);
      setView("outputs", true);
      $("#analyzeBtn").disabled = false;
      return;
    }
    if (run.status === "error") throw new Error(run.error || "run failed");
  }
  throw new Error("run status timed out");
}

async function resumeRun(runId) {
  if (!runId) return;
  state.activeRunId = runId;
  state.activeStartedAt = Date.now();
  $("#analyzeBtn").disabled = true;
  try {
    var run = await getRun(runId);
    renderRunState(run);
    if (run.status !== "complete" && run.status !== "error") await pollRun(runId);
    else $("#analyzeBtn").disabled = false;
  } catch (err) {
    setStatus(String(err.message || err));
    $("#analyzeBtn").disabled = false;
  }
}

function bindEvents() {
  $("#sampleBtn").addEventListener("click", function () {
    state.fileName = "baltor-policy-sample.txt";
    setRawText("");
    state.selectedSources = [{
      type: "sample",
      name: state.fileName,
      status: "921 characters ready",
      size: sample.length,
      last_modified: "2026-05-31T00:00:00Z",
      text: sample
    }];
    redrawSources();
    analyze();
  });
  $("#analyzeBtn").addEventListener("click", analyze);
  $("#copyRunBtn").addEventListener("click", function () {
    if (!state.activeRunId) return;
    var url = location.origin + location.pathname + "#run=" + encodeURIComponent(state.activeRunId);
    navigator.clipboard && navigator.clipboard.writeText(url);
    setStatus("Run link copied");
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-view-link]"), function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      setView(link.getAttribute("data-view-link"), true);
    });
  });
  window.addEventListener("popstate", function () {
    setView(routeView(), false);
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-connector]"), function (btn) {
    btn.addEventListener("click", function () {
      var name = btn.getAttribute("data-connector");
      addSource({ type: "connector", name: name, status: "configured placeholder", size: 0, text: "" });
      setStatus(name + " connector selected; local demo needs extracted text or uploaded files");
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-export-kind]"), function (btn) {
    btn.addEventListener("click", function () {
      if (!state.activeRunId || btn.disabled) return;
      var kind = btn.getAttribute("data-export-kind");
      window.location.href = "/api/admin-demo/runs/" + encodeURIComponent(state.activeRunId) + "/exports/" + encodeURIComponent(kind);
    });
  });
  $("#exploreChatForm").addEventListener("submit", function (event) {
    event.preventDefault();
    var query = $("#exploreChatInput").value.trim();
    if (!query) return;
    var summary = state.latestSummary || {};
    if (!summary.claims) {
      setText("#exploreChatAnswer", "Run processing before asking the generated RAG package.");
      return;
    }
    setText("#exploreChatAnswer", "RAG preview for \"" + query + "\": answer from the served package with cited chunks, fact lineage, and provenance history. Live model answering is intentionally outside this static demo.");
  });
  $("#fileInput").addEventListener("change", onFiles);
}

async function onFiles(event) {
  var files = Array.prototype.slice.call((event.target.files || []));
  if (!files.length) return;
  state.selectedSources = [];
  state.fileName = files.map(function (file) { return file.name; }).join(", ");
  for (var i = 0; i < files.length; i += 1) {
    var file = files[i];
    if (/\.zip$/i.test(file.name) || /\.pdf$/i.test(file.name) || /\.docx$/i.test(file.name)) {
      addSource({
        type: "file",
        name: file.name,
        status: "queued for extractor worker",
        size: file.size,
        last_modified: new Date(file.lastModified || Date.now()).toISOString(),
        text: ""
      });
      continue;
    }
    try {
      addSource({
        type: "file",
        name: file.name,
        status: Number(file.size).toLocaleString() + " bytes ready",
        size: file.size,
        last_modified: new Date(file.lastModified || Date.now()).toISOString(),
        text: await file.text()
      });
    } catch (err) {
      addSource({ type: "file", name: file.name, status: "read failed", size: file.size, text: "" });
    }
  }
  setRawText("");
  setStatus(files.length + " source file(s) selected");
}

function init() {
  setView(routeView(), false);
  renderMetrics({});
  renderRunCard({}, 0);
  redrawSources();
  renderSync([]);
  renderWorkerPlan([]);
  renderModelRoutes([]);
  renderCostEstimate({});
  renderQueuePlan({});
  renderGraph({ nodes: [], edges: [] });
  renderVerificationQueue([]);
  renderUpdates([]);
  renderClaims([]);
  renderServing({ summary: {}, nodes: [], sources: [] });
  renderDownloadState();
  bindEvents();
  var match = location.hash.match(/run=([^&]+)/);
  if (match) resumeRun(decodeURIComponent(match[1]));
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
