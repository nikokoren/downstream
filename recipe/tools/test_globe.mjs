// Geometry and Liquid regressions from the committed Munich payload and captured OSM points.
// Run with Ruby + Liquid 5.14.0 on PATH: node recipe/tools/test_globe.mjs
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const shared = fs.readFileSync(path.join(root, "recipe/src/shared.liquid"), "utf8");
const land = JSON.parse(shared.match(/var WORLD_LAND = (.*);/)[1]);
const bundle = shared.split("// BEGIN bundled globe projection")[1].split("// END bundled globe projection.")[0];
const context = {};
vm.runInNewContext(bundle.slice(bundle.indexOf("\n")), context);
const payload = JSON.parse(fs.readFileSync(path.join(root, "recipe/preview/munich.json"), "utf8"));
const osm = fs.readFileSync(path.join(root, "pipeline/tests/fixtures/osm_starnberg.osm"), "utf8");
const locations = [[payload.town.lon, payload.town.lat], ...[...osm.matchAll(/<node[^>]*lat="([^"]+)"[^>]*lon="([^"]+)"/g)].map(m => [+m[2], +m[1]])];
// Optional real location catalogues, e.g. Ridgelines' published entries, broaden projection
// coverage without making the normal Downstream checks depend on a second checkout.
for (const file of process.argv.slice(2)) {
  for (const entry of JSON.parse(fs.readFileSync(file, "utf8")).entries) {
    locations.push([((entry.lon + 180) % 360 + 360) % 360 - 180, entry.lat]);
  }
}
// Include the actual downstream route's endpoints and all its intermediate coordinates.
let lat = 0, lon = 0, i = 0;
while (i < payload.polyline.length) {
  const delta = () => {
    let n = 0, shift = 0, b;
    do { b = payload.polyline.charCodeAt(i++) - 63; n |= (b & 31) << shift; shift += 5; } while (b >= 32);
    return n & 1 ? ~(n >> 1) : n >> 1;
  };
  lat += delta(); lon += delta();
  locations.push([lon / 1e5, lat / 1e5]);
}
const silhouettes = new Set();
for (const [lon, lat] of locations) {
  const r = context.DownstreamGlobe.project(land, lon, lat, 37);
  assert.ok(r.path && !/NaN|Infinity/.test(r.path));
  assert.ok(Math.hypot(...r.marker) < 1e-9, "location must be centred");
  assert.ok(r.path.match(/-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi).map(Number).every(n => Math.abs(n) <= 37.01), "coasts must stay inside the hemisphere bounds");
  silhouettes.add(r.path);
}
assert.ok(silhouettes.size > 1, "the globe must rotate with location");
console.log(`${locations.length} captured locations / route points centred and clipped correctly`);
const [lon0, lat0] = locations[0];
const normal = context.DownstreamGlobe.createProjection(lon0, lat0, 37, 1);
const focused = context.DownstreamGlobe.createProjection(lon0, lat0, 37);
const rad = Math.PI / 180;
let visible = 0, nearby = 0;
for (const location of locations) {
  const [lon, lat] = location;
  const facing = Math.sin(lat0 * rad) * Math.sin(lat * rad) + Math.cos(lat0 * rad) * Math.cos(lat * rad) * Math.cos((lon - lon0) * rad);
  if (facing <= 0) continue;
  const a = normal(location), b = focused(location), ra = Math.hypot(...a), rb = Math.hypot(...b);
  assert.ok(rb >= ra - 1e-9 && rb <= 37 + 1e-9);
  assert.ok(Math.abs(a[0] * b[1] - a[1] * b[0]) < 1e-9, "magnification must preserve direction");
  if (ra > 0.01 && ra < 1) { assert.ok(rb / ra > 2.8); nearby++; }
  visible++;
}
assert.ok(visible > 0 && nearby > 0);
console.log(`${visible} visible points preserve direction and bounds; ${nearby} nearby points magnified by over 2.8x`);

// One Ruby process uses the same loader and strict parser as the real render helper.
const ruby = String.raw`
require "json"
require "liquid"
src = File.join(ARGV.fetch(0), "recipe", "src")
partials = {}
shared = File.read(File.join(src, "shared.liquid")).gsub(/\{%-?\s*template\s+(\w+)\s*-?%\}(.*?)\{%-?\s*endtemplate\s*-?%\}/m) { partials[Regexp.last_match(1)] = Regexp.last_match(2); "" }
loader = Object.new
loader.define_singleton_method(:read_template_file) { |name| partials.fetch(name) }
env = Liquid::Environment.build { |e| e.file_system = loader }
templates = %w[full half_horizontal half_vertical quadrant].to_h { |v| [v, Liquid::Template.parse(shared + File.read(File.join(src, "#{v}.liquid")), environment: env, error_mode: :strict)] }
results = JSON.parse($stdin.read).map { |c| templates.fetch(c.fetch("view")).render!(c.fetch("payload"), strict_filters: true) }
print JSON.generate(results)
`;
const cases = [];
for (const view of ["full", "half_horizontal", "half_vertical", "quadrant"])
  for (const lang of ["en", "de"]) for (const units of ["metric", "imperial"])
    for (const value of [null, false, "false", "no", "", true, "true", "yes"]) {
      cases.push({view, expected: view === "full" && [true, "true", "yes"].includes(value), payload: {...payload,
        trmnl: {plugin_settings: {custom_fields_values: {language: lang, units, world_map: value}}}}});
    }
for (const missing of ["lat", "lon"]) {
  const town = {...payload.town}; delete town[missing];
  cases.push({view: "full", expected: false, payload: {...payload, town, trmnl: {plugin_settings: {custom_fields_values: {world_map: true}}}}});
}
cases.push({view: "full", expected: false, payload});
for (const language of ["en", "de"]) cases.push({view: "full", expected: false,
  payload: {trmnl: {plugin_settings: {custom_fields_values: {language, world_map: true}}}}});
const run = spawnSync("ruby", ["-e", ruby, root], {input: JSON.stringify(cases), encoding: "utf8", maxBuffer: 32 * 1024 * 1024});
assert.equal(run.status, 0, run.stderr || "Ruby / Liquid unavailable");
const results = JSON.parse(run.stdout);
assert.equal(results.length, cases.length);
results.forEach((html, i) => {
  assert.equal(/data-world-lat=/.test(html), cases[i].expected, `globe setting ${i}`);
  if (cases[i].view === "full") assert.equal(/portrait:w--\[70cqw\]/.test(html), cases[i].expected, `portrait box ${i}`);
});
console.log(`${cases.length} Liquid renders: defaults, boolean formats, languages, units, layouts and missing coordinates passed`);
