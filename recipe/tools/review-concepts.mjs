// Build a portable visual walkthrough from real Framework renders and captured route facts.
// First run the --preview render sweep and the insight variant documented in docs/UX_CONCEPTS.md.
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import {chromium} from "playwright-core";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const out = path.join(root, "recipe/tools/out"), review = path.join(out, "review");
const fw = path.join(root, "data/raw/framework/3.4.0");
fs.mkdirSync(review, {recursive: true});
const captured = JSON.parse(fs.readFileSync(path.join(root, "fixtures/review/routes.json"), "utf8"));
const template = `<div class="layout layout--col gap--large">
  <span class="title title--large" data-clamp="2">{{ heading | escape }}</span>
  <div class="grid grid--cols-2 gap--large">
    {% for town in towns %}
    <div class="flex flex--col gap--small p--3 outline">
      <span class="label">{{ country | escape }}</span>
      <span class="title title--large" data-clamp="2">{{ town.name | escape }}</span>
      <span class="description" data-clamp="4">{{ town.chain | escape }}</span>
      <span class="label">{{ ending | escape }}</span>
      <span class="title" data-clamp="2">{{ town.end | escape }}</span>
      <span class="label">{{ town.distance | escape }}</span>
    </div>
    {% endfor %}
  </div>
</div>`;
const contexts = {};
for (const lang of ["en", "de"]) {
  contexts[lang] = {
    heading: lang === "en" ? "Same country. Different seas." : "Zwei Städte. Zwei Meere.",
    country: lang === "en" ? "Germany" : "Deutschland", ending: lang === "en" ? "Ends in" : "Endet in",
    towns: ["Munich", "Nuremberg"].map(name => {
      const r = captured.towns.find(r => r.en === name);
      let chain = r.chain.replace("(stream)", lang === "en" ? "a stream" : "ein Bach");
      if (lang === "de") chain = chain.replace("Danube", "Donau").replace("Rhine", "Rhein");
      const end = lang === "en" ? r.end_name : {"Black Sea": "Schwarzes Meer", "North Sea": "Nordsee"}[r.end_name];
      return {name: r[lang], chain, end, distance: Math.round(+r.total_km).toLocaleString(lang === "en" ? "en-US" : "de-DE") + " km"};
    }),
  };
}
const pages = new Map();
for (const lang of ["en", "de"]) {
  const ruby = `require "json"; require "liquid"; d=JSON.parse($stdin.read); print Liquid::Template.parse(d.fetch("template"), error_mode: :strict).render!(d.fetch("context"), strict_filters: true)`;
  const run = spawnSync("ruby", ["-e", ruby], {input: JSON.stringify({template, context: contexts[lang]}), encoding: "utf8"});
  if (run.status) throw new Error(run.stderr);
  pages.set(`/comparison-${lang}`, `<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/fw/plugins.css"><script src="/fw/plugins.js"></script></head><body class="environment trmnl"><div class="screen screen--og screen--md screen--1bit"><div class="view view--full">${run.stdout}</div></div></body></html>`);
}
const server = http.createServer((req, res) => {
  if (pages.has(req.url)) { res.setHeader("content-type", "text/html; charset=utf-8"); return res.end(pages.get(req.url)); }
  const f = req.url.startsWith("/fw/") ? path.join(fw, path.basename(req.url)) : req.url.startsWith("/fonts/") ? path.join(fw, "fonts", path.basename(req.url)) : null;
  if (!f || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.setHeader("content-type", f.endsWith(".css") ? "text/css" : f.endsWith(".js") ? "text/javascript" : f.endsWith(".woff2") ? "font/woff2" : "font/ttf");
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const browser = await chromium.launch({executablePath: process.env.CHROME || "/usr/bin/chromium"});
try {
  for (const lang of ["en", "de"]) {
    const page = await browser.newPage({viewport: {width: 800, height: 480}});
    await page.goto(`http://127.0.0.1:${server.address().port}/comparison-${lang}`);
    await page.waitForFunction(() => window.TRMNL_PLUGINS_READY === true);
    const trimmed = await page.locator("[data-clamp-lines-trimmed]").count();
    if (trimmed) throw new Error("comparison concept text was trimmed");
    await page.screenshot({path: path.join(review, `comparison-${lang}.png`)});
    await page.close();
  }

  const png = f => "data:image/png;base64," + fs.readFileSync(f).toString("base64");
  const views = {};
  for (const [device, label] of [["og_1bit", "OG landscape"], ["og_1bit_port", "OG portrait"], ["x_land", "TRMNL X landscape"], ["x_port", "TRMNL X portrait"]]) {
    views[device] = {label};
    for (const lang of ["en", "de"]) for (const enabled of [false, true]) views[device][`${lang}-${enabled}`] = png(path.join(out, `full.${device}.Munich.${lang}.metric${enabled ? ".globe" : ""}.png`));
  }
  const insight = Object.fromEntries(["en", "de"].map(lang => [lang, png(path.join(review, "insight", `full.og_1bit.Munich.${lang}.metric.globe.png`))]));
  const comparisons = Object.fromEntries(["en", "de"].map(lang => [lang, png(path.join(review, `comparison-${lang}.png`))]));
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Downstream: globe and two ideas</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f2ed;color:#171713;font:16px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:44px 28px 64px}h1{font-size:40px;line-height:1.12;margin:10px 0 20px;letter-spacing:-1.5px}h2{font-size:25px;line-height:1.2;margin:12px 0}p{max-width:760px}section{margin-top:40px;padding-top:28px;border-top:1px solid #ccc8bd}.eyebrow{font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:1.8px}.badge{display:inline-block;font-size:12px;font-weight:700;border:1px solid;padding:3px 9px;border-radius:30px}button,select{font:inherit;background:white;border:1px solid #777;padding:7px 12px;border-radius:5px}button{cursor:pointer}button[aria-pressed=true]{background:#171713;color:white}nav{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:18px 0}.frame{background:white;border:1px solid #999;padding:8px;box-shadow:0 5px 20px #00000008}.frame img{display:block;width:100%;height:auto}.frame.portrait{max-width:420px;margin:auto}.two{display:grid;grid-template-columns:1fr 1fr;gap:22px}.caption{font-size:14px;color:#515148;margin:10px 0}.note{padding:14px 18px;border-left:3px solid #777;background:#eae7df;font-size:14px}.steps{display:flex;gap:14px;flex-wrap:wrap}.step{flex:1;min-width:200px;background:white;border:1px solid #ccc8bd;padding:18px}.step strong{display:block;font-size:18px;margin:8px 0}.step small{font-size:14px} @media(max-width:700px){.two{grid-template-columns:1fr}h1{font-size:30px}main{padding:25px 18px}}
</style></head><body><main>
<div class="eyebrow">Downstream · visual walkthrough · 13 November 2026</div>
<h1>A little more context.<br>A little more to discover.</h1>
<p>The globe is implemented. The other two examples are proposals, shown here to make the ideas concrete. No change to the time model, town rotation, or production wording is included.</p>
<nav><label>Language <select id="lang"><option value="en">English</option><option value="de">Deutsch</option></select></label></nav>
<section><span class="badge">Implemented</span><h2>1. The Ridgelines globe, centred on the town</h2><p>The same outlined, centre-magnified globe sits bottom right. It is optional, off by default, and larger on TRMNL X. The main map still shows the whole river journey.</p>
<nav><label>Device <select id="device">${Object.entries(views).map(([key,v])=>`<option value="${key}">${v.label}</option>`).join("")}</select></label><button id="off" aria-pressed="false">Globe off</button><button id="on" aria-pressed="true">Globe on</button></nav><div class="frame" id="device-frame"><img id="globe" alt="Actual Downstream template render with the optional globe"></div>
<p class="caption">Real Liquid templates, Framework 3.4.0, MapLibre 5.24.0 and the committed Munich route. The offline basemap shows Natural Earth coastlines; hosted TRMNL tile details are not shown.</p></section>
<section><span class="badge">Proposal, not implemented</span><h2>2. Explain one surprising thing</h2><p>Munich already shows an estimated 3–8 weeks. The payload also says lakes and reservoirs add about 10 days. One short sentence explains why that number is interesting.</p><div class="frame"><img id="insight" alt="Proposed extra fact beneath Munich's route and estimated time"></div><p class="caption">A draft variant of the real template, rendered with the real Munich payload. The extra sentence is proposed copy. The current time model still needs its documented validation work.</p></section>
<section><span class="badge">Proposal, not implemented</span><h2>3. Put two journeys next to each other</h2><p>Munich drains to the Black Sea; Nuremberg drains to the North Sea. Showing them together makes the geographic connection easier to notice than encountering the two towns hours apart.</p><div class="frame"><img id="comparison" alt="Comparison sketch showing Munich and Nuremberg ending in different seas"></div><p class="caption">A real Framework render of a comparison sketch, using the published build report captured on 13 November. These are two verified German examples. A “nearby towns” edition would select closer pairs and verify both routes before shipping.</p></section>
<section><h2>How the other ideas would work</h2><div class="steps"><div class="step"><span class="eyebrow">Journey chapters</span><strong>Keep the same town for a few turns</strong><small>Show the overview, then a lake or river detail, then the destination. It tells a story across refreshes and never claims to track a moving drop.</small></div><div class="step"><span class="eyebrow">Companion atlas</span><strong>Scan to see the complete journey</strong><small>An optional QR in the full view opens the unabridged chain, a larger map and the method. The screen stays simple; extra detail lives on the phone.</small></div><div class="step"><span class="eyebrow">Familiar places</span><strong>Mix a favourite town into the tour</strong><small>Choose an already computed town. Its occasional return creates a personal connection without needing an address, account or live location.</small></div></div></section>
<p class="note">These previews are browser renders, not photographs of a device. The comparison has no second route map because that geometry is not included in the captured report. No geography was invented to fill that gap.</p>
<p class="caption">Coastlines: Natural Earth, public domain. Route facts: HydroATLAS, HydroLAKES, GeoNames and OpenStreetMap. Source details and ODbL notice are in fixtures/review/NOTICE.md in the repository.</p>
</main><script>const views=${JSON.stringify(views)},insights=${JSON.stringify(insight)},comparisons=${JSON.stringify(comparisons)};let enabled=true;function update(){const lang=document.getElementById('lang').value,d=document.getElementById('device').value;document.getElementById('globe').src=views[d][lang+'-'+enabled];document.getElementById('device-frame').classList.toggle('portrait',d.includes('port'));document.getElementById('insight').src=insights[lang];document.getElementById('comparison').src=comparisons[lang];document.getElementById('off').setAttribute('aria-pressed',String(!enabled));document.getElementById('on').setAttribute('aria-pressed',String(enabled));}document.getElementById('lang').onchange=update;document.getElementById('device').onchange=update;document.getElementById('off').onclick=()=>{enabled=false;update()};document.getElementById('on').onclick=()=>{enabled=true;update()};update();</script></body></html>`;
  const file = path.join(review, "walkthrough.html");
  fs.writeFileSync(file, html);
  const page = await browser.newPage({viewport: {width: 1100, height: 900}});
  await page.setContent(html);
  await page.locator("img").evaluateAll(imgs => Promise.all(imgs.map(img => img.decode())));
  await page.screenshot({path: path.join(review, "walkthrough.png"), fullPage: true});
  await page.close();
  console.log(`Wrote ${file}, walkthrough.png and two comparison renders`);
} finally {
  await browser.close();
  server.close();
}
