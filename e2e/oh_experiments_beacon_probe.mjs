/* e2e/oh_experiments_beacon_probe.mjs — REAL-JS proof that the kit's experiment + analytics
   wiring beacons to the governed events plane. Loads the ACTUAL shipped kit files
   (dist/sites/openharness-design/shared/oh-identity.js + oh-experiments.js) in a tiny browser
   stub, drives OHExp exactly as the React SPA does (useExperiment → define/variant/exposure, then
   an attributed .track), and captures every beacon the site would send. Prints the captured
   payloads as JSON on stdout so the Python gate (scripts/check_events_beacon_wiring.py) can POST
   them to the real events plane and assert the A/B readout — no mocks in the critical path.

   Run: node e2e/oh_experiments_beacon_probe.mjs   (exit 0 + JSON, or exit 1 + {error}). */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const REPO = dirname(dirname(fileURLToPath(import.meta.url)));
const SHARED = join(REPO, "dist", "sites", "openharness-design", "shared");

// ---- minimal browser stub (only what the two kit files touch) -------------------------------
const captured = [];                              // every beacon body the site emits, in order
const store = new Map();
const localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
};
// navigator WITHOUT sendBeacon → oh-identity.js takes the fetch() fallback, whose body is the raw
// JSON string (no async Blob read needed). We capture it verbatim.
const navigator = {};
const fetch = (url, opts) => {
  try { captured.push({ url, body: JSON.parse(opts.body) }); } catch (e) { /* ignore */ }
  return Promise.resolve({ ok: true });
};
const location = { pathname: "/", hash: "", search: "" };
const win = {
  OHH_EVENTS_BASE: "http://127.0.0.1:9420",       // same value the porter injects (window.OHH_EVENTS_BASE='/analytics' at deploy)
  PORTFOLIO: { GROUP: { name: "AIDoneRight" } },
  localStorage, navigator, location, fetch,
};
win.window = win;                                  // self-reference like a real browser
const sandbox = { window: win, globalThis: win, localStorage, navigator, location, fetch,
                  console, module: { exports: {} }, Math, Date, JSON, String, Object, Array };
vm.createContext(sandbox);

function load(name) { vm.runInContext(readFileSync(join(SHARED, name), "utf8"), sandbox, { filename: name }); }

try {
  // load order mirrors index.html: oh-identity.js (defines OHEvents) BEFORE oh-experiments.js (bridge)
  load("oh-identity.js");                           // OHEvents.page() auto-fires here → a page beacon
  load("oh-experiments.js");                        // registers the OHExp→OHEvents bridge

  const OHExp = win.OHExp, OHEvents = win.OHEvents;
  if (!OHEvents) throw new Error("window.OHEvents not defined by oh-identity.js");
  if (!OHExp) throw new Error("window.OHExp not defined by oh-experiments.js");

  // drive it exactly like useExperiment(): define → sticky assign → exposure → attributed conversion
  OHExp.define("ohh_hero", ["A", "B"]);
  const v1 = OHExp.variant("ohh_hero");
  const v2 = OHExp.variant("ohh_hero");             // sticky: must equal v1
  OHExp.exposure("ohh_hero");                       // → an exposure beacon via the bridge
  OHExp.track("build_submit", { experiment: "ohh_hero", variant: v1 });  // → a conversion beacon

  const page = captured.find((c) => c.body.event === "page");
  const exposure = captured.find((c) => c.body.event === "exposure" && c.body.experiment === "ohh_hero");
  const conversion = captured.find((c) => c.body.event === "conversion" && c.body.experiment === "ohh_hero");

  process.stdout.write(JSON.stringify({
    ok: true,
    sticky: v1 === v2 && v1 != null,
    variant: v1,
    page: page ? page.body : null,
    exposure: exposure ? exposure.body : null,
    conversion: conversion ? conversion.body : null,
    all_events: captured.map((c) => c.body.event),
    // every beacon must be anon-only (an anon id, never an email/key shape)
    anon_only: captured.every((c) => typeof c.body.anon === "string" && !/[\w.+-]+@[\w-]+\.[\w.-]+/.test(JSON.stringify(c.body))),
  }));
  process.exit(0);
} catch (e) {
  process.stdout.write(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
  process.exit(1);
}
