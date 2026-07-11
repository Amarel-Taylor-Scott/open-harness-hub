// platform-core — the shared backend plane for the AI Done Right family.
// One small, honest service: auth + registration, user API keys, standardized
// product↔product service handshakes (Baltor↔Teleon↔hubs), user-managed
// MCP/tool connections, analytics + A/B event ingest, and the Shared LLM Plane
// (an OpenAI-compatible router that REQUIRES real provider keys — no fake providers).
//
// Storage: a JSON file (swap for Postgres in production — see terraform/).
// Receipts: HMAC-signed records (an honest local stand-in for Sigstore/Rekor; gap ledger item G-3).
//
// Run: node server.js   (PORT=8787, DATA_FILE=./data/core.json)
'use strict';
const express = require('express');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8787;
const DATA_FILE = process.env.DATA_FILE || path.join(__dirname, 'data', 'core.json');
const JWT_SECRET = process.env.CORE_JWT_SECRET || crypto.randomBytes(32).toString('hex');
const SIGNING_SECRET = process.env.CORE_SIGNING_SECRET || JWT_SECRET;

// ---------- tiny persistence ----------
let db = { users: [], keys: [], serviceConnections: [], connections: [], events: [], receipts: [] };
try { db = Object.assign(db, JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'))); } catch (e) { /* fresh */ }
let saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
    fs.writeFileSync(DATA_FILE, JSON.stringify(db, null, 1));
  }, 50);
}
const id = (p) => p + '_' + crypto.randomBytes(8).toString('hex');
const now = () => new Date().toISOString();

// ---------- crypto helpers ----------
function hashPassword(pw) {
  const salt = crypto.randomBytes(16).toString('hex');
  return salt + ':' + crypto.scryptSync(pw, salt, 32).toString('hex');
}
function checkPassword(pw, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(pw, salt, 32);
  const expected = Buffer.from(hash, 'hex');
  return candidate.length === expected.length && crypto.timingSafeEqual(candidate, expected);
}
const b64u = (b) => Buffer.from(b).toString('base64url');
function jwtSign(payload, ttlSec = 60 * 60 * 24 * 7) {
  const body = { ...payload, iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + ttlSec };
  const head = b64u(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const pay = b64u(JSON.stringify(body));
  const sig = crypto.createHmac('sha256', JWT_SECRET).update(head + '.' + pay).digest('base64url');
  return head + '.' + pay + '.' + sig;
}
function jwtVerify(token) {
  const [head, pay, sig] = String(token).split('.');
  if (!head || !pay || !sig) return null;
  const expect = crypto.createHmac('sha256', JWT_SECRET).update(head + '.' + pay).digest('base64url');
  if (expect !== sig) return null;
  const body = JSON.parse(Buffer.from(pay, 'base64url').toString());
  if (body.exp && body.exp < Date.now() / 1000) return null;
  return body;
}
const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');

// receipt: HMAC-signed record. NOT Sigstore/Rekor — documented gap G-3.
function receipt(kind, body) {
  const rec = { id: id('rcpt'), kind, at: now(), body };
  rec.sig = 'hmac-sha256:' + crypto.createHmac('sha256', SIGNING_SECRET).update(JSON.stringify({ kind, at: rec.at, body })).digest('hex').slice(0, 32);
  db.receipts.push(rec); save();
  return rec;
}

// ---------- service registry (standardized admin credentials) ----------
// Every product/hub gets a service account via env: SERVICE_<ID>_SECRET.
// e.g. SERVICE_BALTOR_SECRET, SERVICE_TELEON_SECRET, SERVICE_OPENCONTEXTHUB_SECRET
const KNOWN_SERVICES = ['parent', 'baltor', 'teleon',
  'opencontexthub', 'openskillshub', 'opentoolshub', 'openskilltotool', 'openmcphub',
  'opencompressionhub', 'openbenchmarkhub', 'openreviewhub', 'openharnesshub',
  'opentemplateshub', 'openendpointhub', 'openenvhub', 'opensandboxhub', 'openagenthub',
  'openreceipthub', 'openstatehub', 'openreconciliationhub', 'openhardeninghub',
  'openenrichmenthub', 'openoptimizationhub', 'openverificationhub'];
function serviceSecret(svc) { return process.env['SERVICE_' + svc.toUpperCase() + '_SECRET'] || null; }

// ---------- app ----------
const app = express();
app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => { // permissive CORS for local prototyping
  res.set('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.set('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

const bearer = (req) => (req.headers.authorization || '').replace(/^Bearer\s+/i, '') || null;
function userAuth(req, res, next) {
  const tok = bearer(req); const body = tok && jwtVerify(tok);
  const user = body && db.users.find((u) => u.id === body.sub);
  if (!user) return res.status(401).json({ error: 'invalid or expired token' });
  req.user = user; next();
}
// API key OR user token OR service key — for the LLM plane
function anyAuth(req, res, next) {
  const tok = bearer(req);
  if (!tok) return res.status(401).json({ error: 'missing Authorization bearer' });
  if (tok.startsWith('sk_')) {
    const k = db.keys.find((k) => !k.revoked && k.hash === sha256(tok));
    if (!k) return res.status(401).json({ error: 'unknown or revoked API key' });
    k.lastUsed = now(); save();
    req.principal = { type: k.kind, keyId: k.id, owner: k.owner, product: k.product, scopes: k.scopes };
    return next();
  }
  const body = jwtVerify(tok);
  const user = body && db.users.find((u) => u.id === body.sub);
  if (!user) return res.status(401).json({ error: 'invalid token' });
  req.principal = { type: 'user', owner: user.id, scopes: ['*'] };
  next();
}

app.get('/healthz', (req, res) => res.json({ ok: true, service: 'platform-core', at: now(),
  llm: { anthropic: !!process.env.ANTHROPIC_API_KEY, openai: !!process.env.OPENAI_API_KEY } }));

// ---------- auth & registration ----------
app.post('/v1/auth/register', (req, res) => {
  const { email, password, name, product } = req.body || {};
  if (!email || !password) return res.status(400).json({ error: 'email and password required' });
  if (db.users.find((u) => u.email === email.toLowerCase())) return res.status(409).json({ error: 'account exists' });
  const user = { id: id('usr'), email: email.toLowerCase(), name: name || email.split('@')[0],
    password: hashPassword(password), products: [product || 'parent'], createdAt: now() };
  db.users.push(user); save();
  receipt('user.registered', { user: user.id, product: product || 'parent' });
  res.json({ token: jwtSign({ sub: user.id }), user: { id: user.id, email: user.email, name: user.name } });
});
app.post('/v1/auth/login', (req, res) => {
  const { email, password } = req.body || {};
  const user = db.users.find((u) => u.email === String(email).toLowerCase());
  if (!user || !checkPassword(password || '', user.password)) return res.status(401).json({ error: 'invalid credentials' });
  res.json({ token: jwtSign({ sub: user.id }), user: { id: user.id, email: user.email, name: user.name } });
});
app.get('/v1/auth/me', userAuth, (req, res) =>
  res.json({ id: req.user.id, email: req.user.email, name: req.user.name, products: req.user.products }));

// ---------- user API keys (self-service, per product) ----------
app.post('/v1/keys', userAuth, (req, res) => {
  const { name, product, scopes } = req.body || {};
  const secret = 'sk_live_' + crypto.randomBytes(18).toString('base64url');
  const key = { id: id('key'), kind: 'user', owner: req.user.id, name: name || 'default',
    product: product || 'parent', scopes: scopes || ['llm:invoke'], prefix: secret.slice(0, 12),
    hash: sha256(secret), createdAt: now(), lastUsed: null, revoked: false };
  db.keys.push(key); save();
  receipt('key.created', { key: key.id, owner: req.user.id, product: key.product, scopes: key.scopes });
  res.json({ ...key, hash: undefined, secret }); // secret shown once
});
app.get('/v1/keys', userAuth, (req, res) =>
  res.json(db.keys.filter((k) => k.owner === req.user.id && !k.revoked).map(({ hash, ...k }) => k)));
app.delete('/v1/keys/:id', userAuth, (req, res) => {
  const k = db.keys.find((k) => k.id === req.params.id && k.owner === req.user.id);
  if (!k) return res.status(404).json({ error: 'not found' });
  k.revoked = true; save();
  receipt('key.revoked', { key: k.id, owner: req.user.id });
  res.json({ ok: true });
});

// ---------- standardized service↔service handshake ----------
// Baltor needs a key from Teleon (and vice versa); hubs need keys from products.
// Caller authenticates with ITS service secret and names the target. The issued
// sk_svc key is scoped from→to and recorded with a receipt both sides can list.
app.post('/v1/service/handshake', (req, res) => {
  const { from, to, scopes } = req.body || {};
  if (!KNOWN_SERVICES.includes(from) || !KNOWN_SERVICES.includes(to))
    return res.status(400).json({ error: 'unknown service', known: KNOWN_SERVICES });
  const secret = serviceSecret(from);
  if (!secret) return res.status(501).json({ error: `SERVICE_${from.toUpperCase()}_SECRET not configured — set it in .env (no bypass)` });
  if (bearer(req) !== secret) return res.status(401).json({ error: 'service secret mismatch' });
  const svcKey = 'sk_svc_' + crypto.randomBytes(18).toString('base64url');
  const key = { id: id('key'), kind: 'service', owner: from, product: to,
    name: `${from} → ${to}`, scopes: scopes || ['llm:invoke', 'events:write'],
    prefix: svcKey.slice(0, 11), hash: sha256(svcKey), createdAt: now(), lastUsed: null, revoked: false };
  db.keys.push(key);
  const conn = { id: id('conn'), from, to, keyId: key.id, scopes: key.scopes, createdAt: now(), status: 'active' };
  db.serviceConnections.push(conn); save();
  const rec = receipt('service.handshake', { from, to, key: key.id, scopes: key.scopes });
  res.json({ connection: conn, secret: svcKey, receipt: rec.id }); // secret shown once
});
app.get('/v1/service/connections', (req, res) => res.json(db.serviceConnections));

// ---------- user-managed connections (MCP servers, tools, webhooks) ----------
app.post('/v1/connections', userAuth, (req, res) => {
  const { kind, name, endpoint, scopes } = req.body || {};
  if (!['mcp', 'tool', 'webhook'].includes(kind)) return res.status(400).json({ error: 'kind must be mcp|tool|webhook' });
  if (!endpoint) return res.status(400).json({ error: 'endpoint required' });
  const conn = { id: id('conn'), owner: req.user.id, kind, name: name || endpoint, endpoint,
    scopes: scopes || [], createdAt: now(), status: 'configured' };
  db.connections.push(conn); save();
  receipt('connection.created', { connection: conn.id, owner: req.user.id, kind, endpoint });
  res.json(conn);
});
app.get('/v1/connections', userAuth, (req, res) => res.json(db.connections.filter((c) => c.owner === req.user.id)));
app.delete('/v1/connections/:id', userAuth, (req, res) => {
  const i = db.connections.findIndex((c) => c.id === req.params.id && c.owner === req.user.id);
  if (i < 0) return res.status(404).json({ error: 'not found' });
  db.connections.splice(i, 1); save();
  res.json({ ok: true });
});

// ---------- analytics + A/B events (sink for shared/oh-experiments.js dataLayer) ----------
app.post('/v1/events', (req, res) => {
  const events = Array.isArray(req.body) ? req.body : (req.body && req.body.events) || [req.body];
  const cleaned = events.filter(Boolean).map((e) => ({
    id: id('evt'), at: now(), site: e.site || 'unknown', type: e.event || e.type || 'custom',
    name: e.name || null, experiment: e.experiment || null, variant: e.variant || null,
    props: e.props || e, anon: e.anon || null,
  }));
  db.events.push(...cleaned);
  if (db.events.length > 50000) db.events = db.events.slice(-50000);
  save();
  res.json({ ok: true, ingested: cleaned.length });
});
app.get('/v1/events/summary', (req, res) => {
  const by = {};
  for (const e of db.events) {
    const k = e.site + ' · ' + e.type + (e.experiment ? ' · ' + e.experiment + ':' + e.variant : '');
    by[k] = (by[k] || 0) + 1;
  }
  res.json({ total: db.events.length, by });
});

// ---------- Shared LLM Plane (OpenAI-compatible router) ----------
// Routes by model prefix to a REAL provider. If no provider key is configured,
// returns 501 with instructions — never a fake completion.
app.post('/llm/v1/chat/completions', anyAuth, async (req, res) => {
  const { model } = req.body || {};
  if (!model) return res.status(400).json({ error: 'model required' });
  let provider, url, headers;
  // model-prefix routing. openrouter/* and ollama/* are OpenAI-compatible (no payload transform);
  // claude* → Anthropic (transformed below). Each provider 501s honestly when its key is unset.
  if (/^openrouter\//i.test(model)) {
    if (!process.env.OPENROUTER_API_KEY) return res.status(501).json({ error: 'OPENROUTER_API_KEY not set. Add it to production/.env to enable OpenRouter models (e.g. openrouter/anthropic/claude-3.5-sonnet) on the LLM plane.' });
    provider = 'openrouter'; url = 'https://openrouter.ai/api/v1/chat/completions';
    req.body.model = model.replace(/^openrouter\//i, '');   // OpenRouter wants the bare model id
    headers = { authorization: 'Bearer ' + process.env.OPENROUTER_API_KEY, 'content-type': 'application/json',
      'HTTP-Referer': 'https://aidoneright.dev', 'X-Title': 'AI Done Right' };
  } else if (/^ollama\//i.test(model)) {
    // Ollama Cloud (OLLAMA_API_KEY → ollama.com) or local Ollama (OLLAMA_HOST, default host docker bridge)
    const cloud = !!process.env.OLLAMA_API_KEY;
    const baseRaw = cloud ? 'https://ollama.com' : (process.env.OLLAMA_HOST || 'http://host.docker.internal:11434');
    const base = baseRaw.replace(/\/$/, '');
    provider = 'ollama'; url = base + '/v1/chat/completions';
    req.body.model = model.replace(/^ollama\//i, '');
    headers = { 'content-type': 'application/json', ...(cloud ? { authorization: 'Bearer ' + process.env.OLLAMA_API_KEY } : {}) };
  } else if (/^claude/i.test(model)) {
    if (!process.env.ANTHROPIC_API_KEY) return res.status(501).json({ error: 'ANTHROPIC_API_KEY not set. Add it to production/.env to enable claude* models on the LLM plane.' });
    provider = 'anthropic'; url = 'https://api.anthropic.com/v1/messages';
    headers = { 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' };
  } else {
    if (!process.env.OPENAI_API_KEY) return res.status(501).json({ error: 'OPENAI_API_KEY not set. Use an openrouter/* or ollama/* model, or add OPENAI_API_KEY to production/.env.' });
    provider = 'openai'; url = 'https://api.openai.com/v1/chat/completions';
    headers = { authorization: 'Bearer ' + process.env.OPENAI_API_KEY, 'content-type': 'application/json' };
  }
  const started = Date.now();
  try {
    let payload = req.body;
    if (provider === 'anthropic') {
      const msgs = (req.body.messages || []).filter((m) => m.role !== 'system');
      const sys = (req.body.messages || []).filter((m) => m.role === 'system').map((m) => m.content).join('\n') || undefined;
      payload = { model, max_tokens: req.body.max_tokens || 1024, system: sys, messages: msgs };
    }
    const r = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
    const out = await r.json();
    const rec = receipt('llm.invocation', { provider, model, principal: req.principal,
      ms: Date.now() - started, status: r.status,
      usage: out.usage || null });
    res.status(r.status).json(provider === 'anthropic' && r.ok ? {
      id: out.id, object: 'chat.completion', model,
      choices: [{ index: 0, message: { role: 'assistant', content: (out.content || []).map((c) => c.text || '').join('') }, finish_reason: out.stop_reason }],
      usage: out.usage, receipt: rec.id,
    } : { ...out, receipt: rec.id });
  } catch (err) {
    res.status(502).json({ error: 'provider unreachable: ' + err.message });
  }
});

// ---------- receipts ----------
app.get('/v1/receipts', (req, res) => res.json(db.receipts.slice(-200).reverse()));

app.listen(PORT, () => console.log(`platform-core listening on :${PORT} · data=${DATA_FILE}`));
