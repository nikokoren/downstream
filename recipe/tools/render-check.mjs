// Render check (DESIGN_PHILOSOPHY part A §7): every view × device × town × language, rendered in
// Chromium against TRMNL Framework 3.4.0's own plugins.css/plugins.js, with real town files from
// the pipeline (data/site/eu/t/*.json), the smaller views inside real mashups (the plugin twice or
// four times, so ids can't collide). A case fails when a map isn't drawn, part of the path is off
// screen or under the text box (D19), text is cut off, or the number of maps is wrong.
//
// Usage: node render-check.mjs [--quick]   (npm run check = --quick; needs `python -m downstream.fetch framework` and a site
// build). Screenshots and results go to recipe/tools/out/ (git-ignored).
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const FW = path.join(root, "data/raw/framework/3.4.0");
const SITE = path.join(root, "data/site/eu");
const OUT = path.join(here, "out");
const CHROME = process.env.CHROME || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";

// Liquid is rendered by Ruby Liquid (render.rb), the engine TRMNL runs: liquidjs accepted a `}`
// inside `{{ }}` that TRMNL rejected on the author's device (2026-09-30).
function renderLiquid(view, ctx) {
  const r = spawnSync("ruby", [path.join(here, "render.rb"), view], { input: JSON.stringify(ctx), encoding: "utf8" });
  if (r.status !== 0) throw new Error(`Ruby Liquid, ${view}: ${(r.stderr || "").split("\n")[0]}`);
  return r.stdout;
}

// Towns by English name from the rotation list; "(error)" = no payload (R18).
const rotation = fs.readFileSync(path.join(SITE, "rotation.csv"), "utf8").trim().split("\n").slice(1)
  .map((l) => { const [n, gid, ...t] = l.split(","); return { n: +n, gid, town: t.join(",").replace(/^"|"$/g, "") }; });
function payload(town) {
  if (town === "(error)") return {};
  const r = rotation.find((x) => x.town === town);
  if (!r) throw new Error(`town not in rotation: ${town}`);
  return JSON.parse(fs.readFileSync(path.join(SITE, "t", `${r.n}.json`), "utf8"));
}

const DEVICES = {
  og_1bit: { cls: "screen--og screen--md screen--1bit", w: 800, h: 480, dpr: 1 },
  og_2bit: { cls: "screen--og screen--md screen--2bit", w: 800, h: 480, dpr: 1 },
  // The Framework scales the X's 1040×780 CSS layout by its 1.8 pixel ratio itself, so the page
  // is 1872×1404 at 1× (measured 2026-09-30: .screen is 1872×1404).
  x_land: { cls: "screen--v2 screen--lg screen--density-2x screen--4bit", w: 1872, h: 1404, dpr: 1 },
  x_port: { cls: "screen--v2 screen--lg screen--density-2x screen--4bit screen--portrait", w: 1404, h: 1872, dpr: 1 },
};
const LAYOUTS = { // view → mashup wrapper and how many copies of the plugin share the screen
  full: { mashup: null, copies: 1 },
  half_horizontal: { mashup: "mashup--1Tx1B", copies: 2 },
  half_vertical: { mashup: "mashup--1Lx1R", copies: 2 },
  quadrant: { mashup: "mashup--2x2", copies: 4 },
};

async function page(view, device, town, lang, units) {
  const ctx = { ...payload(town), trmnl: { plugin_settings: { custom_fields_values: { language: lang, units } } } };
  const body = renderLiquid(view, ctx);
  const one = `<div class="view view--${view}">${body}</div>`;
  const L = LAYOUTS[view];
  const inner = L.mashup ? `<div class="mashup ${L.mashup}">${one.repeat(L.copies)}</div>` : one;
  return `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="/fw/plugins.css"><script src="/fw/plugins.js"></script></head>
<body class="environment trmnl"><div class="screen ${DEVICES[device].cls}">${inner}</div></body></html>`;
}

const pages = new Map();
const server = http.createServer((req, res) => {
  if (req.url.startsWith("/fonts/")) { // plugins.css loads its fonts from the site root
    const f = path.join(FW, "fonts", path.basename(req.url));
    if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "content-type": f.endsWith(".woff2") ? "font/woff2" : "font/ttf" });
    return fs.createReadStream(f).pipe(res);
  }
  if (req.url.startsWith("/fw/")) {
    const f = path.join(FW, path.basename(req.url));
    res.writeHead(200, { "content-type": f.endsWith(".css") ? "text/css" : "text/javascript" });
    return fs.createReadStream(f).pipe(res);
  }
  const html = pages.get(req.url);
  res.writeHead(html ? 200 : 404, { "content-type": "text/html; charset=utf-8" });
  res.end(html || "");
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

// --quick: after each change (author 2026-09-30); the full sweep only before shipping a version.
// The hardest cases: the reference path, the longest path, the longest town line, the longest
// 5-step path; one OG and one X screen, both languages (64 cases, ~5 min).
const quick = process.argv.includes("--quick");
const TOWNS = process.env.ONLY ? [process.env.ONLY] : quick ? ["Munich", "Iisalmi", "Saint-Quentin-en-Yvelines", "Cambridge"] : ["Munich", "Löbau", "Cetinje", "Limhamn", "Konstanz", "Iisalmi", "Lisbon", "Vihti", "Woluwe-Saint-Lambert", "Saint-Quentin-en-Yvelines", "Cambridge", "Milton Keynes", "(error)"];
const cases = [];
for (const view of (process.env.VIEW ? [process.env.VIEW] : Object.keys(LAYOUTS))) for (const device of (process.env.DEVICE ? [process.env.DEVICE] : quick ? ["og_1bit", "x_land"] : Object.keys(DEVICES)))
  for (const town of TOWNS) for (const lang of ["en", "de"])
    cases.push({ view, device, town, lang, units: lang === "de" ? "metric" : "imperial" });

// No proxy option: Chromium picks up the environment's proxy for outside hosts (MapLibre, tiles)
// and goes direct to the local server (checked 2026-09-30; an explicit proxy broke loopback).
const browser = await chromium.launch({
  executablePath: CHROME, args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
});
fs.mkdirSync(OUT, { recursive: true });
const results = [];
// One context for all cases, so tiles fetched once stay in its HTTP cache (a fresh context per
// case made the sweep take hours). Every device renders at dpr 1, so one context fits all.
if (new Set(Object.values(DEVICES).map((d) => d.dpr)).size !== 1) throw new Error("one dpr per run");
const ctx = await browser.newContext({ deviceScaleFactor: Object.values(DEVICES)[0].dpr, ignoreHTTPSErrors: true });
// Map tiles, glyphs and styles from TRMNL through a disk cache (data/, git-ignored), fetched by
// Node with retries: Chromium's own fetches through this sandbox's proxy failed with
// ERR_TOO_MANY_RETRIES, which left maps half drawn (water only, no path). Needs Node's env proxy
// support (run with NODE_USE_ENV_PROXY=1, as `npm run check` does).
const CACHE = path.join(root, "data/cache/trmnl-maps");
fs.mkdirSync(CACHE, { recursive: true });
async function cached(url) {
  const key = path.join(CACHE, crypto.createHash("sha1").update(url).digest("hex"));
  if (fs.existsSync(key + ".json")) return { meta: JSON.parse(fs.readFileSync(key + ".json", "utf8")), body: fs.readFileSync(key) };
  let last;
  for (let i = 0; i < 5; i++) {
    try {
      const r = await fetch(url);
      const body = Buffer.from(await r.arrayBuffer());
      const meta = { status: r.status, type: r.headers.get("content-type") || "application/octet-stream", enc: r.headers.get("content-encoding") };
      if (r.status < 500) {
        if (r.ok) { fs.writeFileSync(key, body); fs.writeFileSync(key + ".json", JSON.stringify(meta)); }
        return { meta, body };
      }
      last = new Error(`HTTP ${r.status}`);
    } catch (e) { last = e; }
    await new Promise((res) => setTimeout(res, 500 * 2 ** i));
  }
  throw last;
}
await ctx.route(/^https:\/\/(maps\.)?trmnl\.com\//, async (route) => {
  try {
    const { meta, body } = await cached(route.request().url());
    route.fulfill({ status: meta.status, contentType: meta.type, body, headers: { "access-control-allow-origin": "*" } });
  } catch { route.abort(); }
});
// MapLibre from the local copy of the exact file the recipe loads (the proxy dropped it once).
// Registered last, so it wins over the cache route for these files.
await ctx.route("https://trmnl.com/js/maplibre-gl/5.24.0/*", (route) => {
  const f = path.join(FW, path.basename(new URL(route.request().url()).pathname));
  route.fulfill({ path: f, contentType: f.endsWith(".css") ? "text/css" : "text/javascript" });
});
async function runCase(c) {
  const id = `${c.view}.${c.device}.${c.town.replace(/[^\w]+/g, "")}.${c.lang}`;
  const D = DEVICES[c.device];
  pages.set(`/${id}`, await page(c.view, c.device, c.town, c.lang, c.units));
  const p = await ctx.newPage();
  await p.setViewportSize({ width: D.w, height: D.h });
  if (process.env.DEBUG) p.on("requestfailed", (r) => console.log("   failed:", r.url().slice(0, 120), r.failure()?.errorText));
  const errors = [];
  p.on("pageerror", (e) => errors.push(String(e)));
  if (process.env.DEBUG) p.on("console", (m) => console.log("   console:", m.type(), m.text().slice(0, 200)));
  const t0 = Date.now(); const lap = (n) => process.env.DEBUG && console.log(`   ${n} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await p.goto(`${base}/${id}`);
  await p.waitForFunction(() => window.TRMNL_PLUGINS_READY === true, null, { timeout: 30000 }).catch(() => errors.push("TRMNL_PLUGINS_READY never true"));
  lap("ready");
  // Software WebGL here is slower than TRMNL's renderer: give tiles up to 20 s more to arrive.
  await p.waitForFunction(() => [...document.querySelectorAll("[data-downstream-map]")].every((el) => el.__downstreamMap && el.__downstreamMap.loaded() && el.__downstreamMap.areTilesLoaded()), null, { timeout: 20000 }).catch(() => {});
  lap("tiles");
  // As TRMNL's screenshot service does after setting the capture pixel ratio (TRMNLMaps.refresh
  // JSDoc, plugins.js 3.4.0): rebuild watched
  // maps against the screen's final paint and wait for them to settle.
  if (!process.env.NO_REFRESH) await p.evaluate(() => window.TRMNLMaps && TRMNLMaps.refresh({ maxWaitMs: 60000 }));
  lap("refresh");
  // Then MapLibre's own "idle" (nothing left to load or paint) on every map, up to 20 s: under
  // parallel load, software WebGL was still painting some X maps when settle() resolved.
  await p.evaluate(() => Promise.race([
    Promise.all([...document.querySelectorAll("[data-downstream-map]")].map((el) => new Promise((r) => {
      const m = el.__downstreamMap;
      if (!m || (m.loaded() && m.areTilesLoaded() && !m.isMoving())) return r();
      m.once("idle", r);
    }))),
    new Promise((r) => setTimeout(r, 20000)),
  ]));
  lap("idle");
  const check = await p.evaluate(({ isError, copies }) => {
    const fails = [];
    const maps = [...document.querySelectorAll("[data-downstream-map]")];
    if (isError) {
      if (maps.length) fails.push("error case shows a map");
      return { fails, maps: maps.length };
    }
    if (maps.length !== copies) fails.push(`maps ${maps.length} != ${copies}`);
    const accepted = [];
    const inkAt = []; // visible path points, checked against the screenshot's pixels below
    for (const el of maps) {
      const m = el.__downstreamMap;
      if (!m || !el.querySelector("canvas")) { fails.push("map not built"); continue; }
      if (!m.loaded() || !m.areTilesLoaded()) fails.push("map not fully drawn");
      const routeLayers = m.getStyle().layers.filter((l) => l.id.startsWith("trmnl-route")).length;
      if (!routeLayers) fails.push("path not drawn");
      const coords = TRMNLMaps.decodePolyline(el.getAttribute("data-polyline"));
      const r = el.getBoundingClientRect();
      const box = el.querySelector("[data-downstream-box]").getBoundingClientRect();
      let off = 0, under = 0;
      for (const c of coords) {
        // project() is in the map's own CSS px; the screen may be scaled, so map to page px.
        const pt = m.project(c), x = r.left + pt.x * (r.width / el.clientWidth), y = r.top + pt.y * (r.height / el.clientHeight);
        if (x < r.left || x > r.right || y < r.top || y > r.bottom) off++;
        else if (x >= box.left && x <= box.right && y >= box.top && y <= box.bottom) under++;
        else inkAt.push([Math.round(x), Math.round(y)]);
      }
      if (off) fails.push(`${off}/${coords.length} path points off the map`);
      if (under) fails.push(`${under}/${coords.length} path points under the text box`);
      // The OpenStreetMap credit (TRMNLMaps' .map__attribution) must stay visible (D20).
      const credit = el.querySelector(".map__attribution");
      if (!credit) fails.push("map credit missing");
      else {
        const a = credit.getBoundingClientRect();
        if (a.left < box.right && a.right > box.left && a.top < box.bottom && a.bottom > box.top) fails.push("map credit covered by the text box");
      }
      if (box.left < r.left - 1 || box.right > r.right + 1 || box.top < r.top - 1 || box.bottom > r.bottom + 1) fails.push("text box outside the map");
      // Cut-off text: the Framework's clamp engine trimmed it (data-clamp-lines-trimmed, or the
      // shown text differs from data-clamp-original), or it runs past its box horizontally.
      for (const t of el.querySelectorAll("[data-downstream-box] > *")) {
        const orig = t.getAttribute("data-clamp-original");
        const trimmed = t.hasAttribute("data-clamp-lines-trimmed") || (orig !== null && orig.trim() !== t.textContent.trim());
        if (!(trimmed || t.scrollWidth > t.clientWidth + 2)) continue;
        // Town lines over 45 characters (15 towns in German, 1 in English, 2026-09-30) may be
        // shortened by the clamp, as TEXT_REQUIREMENTS slot 1 allows; counted, not failed.
        if (Number(t.getAttribute("data-downstream-place")) > 45) accepted.push(`town line shortened: "${orig.trim().slice(0, 40)}"`);
        else fails.push(`text cut: "${(orig || t.textContent).trim().slice(0, 40)}"`);
      }
    }
    return { fails, accepted, inkAt, maps: maps.length, zoom: maps.map((el) => el.__downstreamMap && el.__downstreamMap.getZoom()) };
  }, { isError: c.town === "(error)", copies: LAYOUTS[c.view].copies });
  const png = await p.screenshot({ path: path.join(OUT, `${id}.png`) });
  // Layers can exist without being painted (seen on the X: water only, no path), so check the
  // pixels: a visible path point counts as drawn when a dark pixel lies within 3 px of it.
  if (check.inkAt && check.inkAt.length) {
    const inked = await p.evaluate(async ({ b64, pts }) => {
      const img = new Image();
      img.src = "data:image/png;base64," + b64;
      await img.decode();
      const cv = document.createElement("canvas");
      cv.width = img.width; cv.height = img.height;
      const g = cv.getContext("2d");
      g.drawImage(img, 0, 0);
      const px = g.getImageData(0, 0, cv.width, cv.height).data;
      let n = 0;
      for (const [x, y] of pts) {
        let hit = false;
        for (let dy = -3; dy <= 3 && !hit; dy++) for (let dx = -3; dx <= 3 && !hit; dx++) {
          const xx = x + dx, yy = y + dy;
          if (xx < 0 || yy < 0 || xx >= cv.width || yy >= cv.height) continue;
          const i = (yy * cv.width + xx) * 4;
          if (px[i] + px[i + 1] + px[i + 2] < 150) hit = true;
        }
        if (hit) n++;
      }
      return n;
    }, { b64: png.toString("base64"), pts: check.inkAt });
    if (inked < 0.9 * check.inkAt.length) check.fails.push(`path not painted (${inked}/${check.inkAt.length} points inked)`);
  }
  const fails = [...check.fails, ...errors];
  results.push({ id, ...c, ok: fails.length === 0, fails, accepted: check.accepted || [], zoom: check.zoom });
  console.log(`${fails.length ? "FAIL" : "ok  "} ${id}${fails.length ? "  " + fails.join("; ") : ""}`);
  await p.close();
}
// A few cases at a time (JOBS, default 3): software WebGL is CPU-bound.
const queue = [...cases];
await Promise.all(Array.from({ length: Number(process.env.JOBS || 3) }, async () => {
  while (queue.length) {
    const c = queue.shift();
    // A case that throws (a timeout, a Liquid error) is a failed case, not the end of the sweep.
    await runCase(c).catch((e) => {
      const id = `${c.view}.${c.device}.${c.town.replace(/[^\w]+/g, "")}.${c.lang}`;
      results.push({ id, ...c, ok: false, fails: [`error: ${String(e.message || e).split("\n")[0]}`] });
      console.log(`FAIL ${id}  error: ${String(e.message || e).split("\n")[0]}`);
    });
  }
}));
await browser.close();
server.close();
results.sort((a, b) => a.id.localeCompare(b.id));
fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 1));
const bad = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - bad}/${results.length} cases pass`);
const acc = results.filter((r) => r.ok && r.accepted && r.accepted.length);
if (acc.length) console.log(`${acc.length} of them with an accepted shortened town line: ${[...new Set(acc.map((r) => r.town + "." + r.lang))].join(", ")}`);
process.exit(bad ? 1 : 0);
