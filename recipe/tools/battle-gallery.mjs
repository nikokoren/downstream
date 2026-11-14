// Lightweight review board. Load one PNG at a time; never embed the screenshot corpus.
// Custom CSS is outside the native Framework screen captures.
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import {fileURLToPath} from "node:url";
import {chromium} from "playwright-core";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const out=path.join(root,"recipe/tools/out/battle");
const modes={cards:"Two journeys · full text cards",single:"Normal view · town and river labels"};
const devices={og:"OG landscape",og_port:"OG portrait",x:"X landscape",x_port:"X portrait"};
const captures=new Set();
for(const mode of Object.keys(modes))for(const device of Object.keys(devices))for(const lang of ["en","de"])for(const units of ["metric","imperial"])for(const labels of [true,false]) {
  const id=`${mode}.${device}.${lang}${units==="imperial"?".imperial":""}${labels?"":".plain"}`;
  if(!fs.existsSync(path.join(out,id+".png")))throw new Error(`Missing capture: ${id}`);
  captures.add(id+".png");
}
const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Downstream: river changes and watershed battle</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f1eb;color:#181816;font:16px/1.5 system-ui,sans-serif}main{max-width:1100px;padding:38px 30px 50px;margin:auto}h1{font-size:38px;line-height:1.15;letter-spacing:-1px;margin:10px 0 18px}h2{font-size:22px;margin:0 0 10px}p{max-width:790px}.eyebrow{font-size:12px;font-weight:750;letter-spacing:1.5px;text-transform:uppercase}.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:25px 0 18px}select{font:inherit;border:1px solid #777;border-radius:4px;padding:7px;background:white}label{font-size:14px;display:flex;gap:7px;align-items:center}.frame{background:white;border:1px solid #888;padding:8px;width:100%;max-width:820px;margin:auto}.frame img{width:100%;height:auto;display:block}.frame.portrait{max-width:480px}.caption{font-size:13px;color:#55534b}.notes{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}.note{padding:18px;background:#fff;border:1px solid #d0ccbf}.note p{font-size:14px;margin:8px 0}.source{margin-top:28px;padding-top:18px;border-top:1px solid #d0ccbf;font-size:13px;color:#55534b}a{color:inherit} @media(max-width:700px){main{padding:22px 16px}h1{font-size:29px}.notes{grid-template-columns:1fr}}</style></head><body><main>
<div class="eyebrow">Downstream · geographic prototypes · 13 November 2026</div>
<h1>Follow the river changes.<br>See two journeys on one map.</h1>
<p>The selected bottom-edge layout now uses the existing sentence twice: town, river steps, destination, distance and estimated duration. Town names identify the paths. River-change labels stay; letters and labels at the sea are gone.</p>
<div class="controls"><label>Layout <select id="mode">${Object.entries(modes).map(([k,v])=>`<option value="${k}" ${k==="cards"?"selected":""}>${v}</option>`).join("")}</select></label><label>Device <select id="device">${Object.entries(devices).map(([k,v])=>`<option value="${k}">${v}</option>`).join("")}</select></label><label>Language <select id="lang"><option value="de">Deutsch</option><option value="en">English</option></select></label><label>Units <select id="units"><option value="metric">km</option><option value="imperial">mi</option></select></label><label><input id="labels" type="checkbox" checked> Map labels</label></div>
<div class="frame" id="frame"><img id="screen" src="cards.og.de.png" alt="A geographic prototype showing river hand-offs and the two raindrop paths"></div>
<p class="caption" id="caption"></p>
<div class="notes"><div class="note"><h2>Follow the river names</h2><p>Town names and named hand-offs appear on both the shared map and the normal view. Labels avoid the paths, cards, globe and map credit.</p></div><div class="note"><h2>Read the full journey</h2><p>Both cards use the same text-box component as the normal view, including intermediate rivers and the distance / duration line.</p></div><div class="note"><h2>Keep the map quiet</h2><p>Matching route strokes and town names replace the letter key. The destination stays in each card; the map keeps only its endpoint ring.</p></div></div>
<p class="source">Rendered from the recipe's Liquid with Framework 3.4.0 and MapLibre 5.24.0. Munich uses its model path and its real estimate, about 3–8 weeks. Nürnberg uses captured OSM / Natural Earth reference geometry and the model report's distance; that capture has no travel duration, so its card explicitly marks the estimate unavailable. Its published model data remains blocked in this environment. The pair is a review packet; the current town rotation has not been changed.</p>
<p class="source">The normal preview includes the approved optional globe. The basemap is offline Natural Earth geography. Sources and limits are recorded in the fixtures. Hosted tiles and physical devices still need validation.</p>
</main><script>const names=${JSON.stringify(modes)};function update(){const mode=document.getElementById('mode').value,device=document.getElementById('device').value,lang=document.getElementById('lang').value,units=document.getElementById('units').value,labels=document.getElementById('labels').checked;document.getElementById('screen').src=mode+'.'+device+'.'+lang+(units==='imperial'?'.imperial':'')+(labels?'':'.plain')+'.png';document.getElementById('frame').classList.toggle('portrait',device.includes('port'));document.getElementById('caption').textContent=names[mode]+(labels?' · map labels shown':' · map labels hidden')+'.';}for(const id of ['mode','device','lang','units','labels'])document.getElementById(id).onchange=update;update();</script></body></html>`;
if(Buffer.byteLength(html)>12000||html.includes("data:image"))throw new Error("Gallery must stay small and load screenshots separately");
fs.writeFileSync(path.join(out,"watershed-battle-light.html"),html);
fs.writeFileSync(path.join(out,"watershed-battle.html"),html);
const comparison=`<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:white;color:#171713;font:16px/1.35 system-ui,sans-serif}main{width:800px;padding:24px}h1{font-size:24px;margin:0 0 18px}h2{font-size:18px;margin:18px 0 8px}img{display:block;width:800px;height:480px;outline:1px solid #bbb}p{font-size:12px;margin:18px 0 0}main{box-sizing:content-box}
</style></head><body><main><h1>Updated Downstream views</h1><h2>1. Two full text cards at the bottom edges</h2><img src="cards.og.de.png" alt="Nürnberg and Munich, each with a bottom-edge caption"><h2>2. Normal view with town and river-change labels</h2><img src="single.og.de.png" alt="The normal Munich view with town and river-change labels"><p>Nürnberg uses reference geometry; its travel estimate is unavailable in the capture. Munich uses its model path and estimate.</p></main></body></html>`;
const server=http.createServer((req,res)=>{
  if(req.url==="/"||req.url==="/comparison") {res.setHeader("content-type","text/html; charset=utf-8");return res.end(req.url==="/"?html:comparison);}
  const name=req.url.slice(1);
  if(!captures.has(name)){res.writeHead(404);return res.end();}
  res.setHeader("content-type","image/png");fs.createReadStream(path.join(out,name)).pipe(res);
});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({executablePath:process.env.CHROME||"/usr/bin/chromium"});
try {
  const p=await browser.newPage({viewport:{width:1100,height:900}});
  const initialPngs=[];
  p.on("request",req=>{if(req.url().endsWith(".png"))initialPngs.push(req.url());});
  await p.goto(origin);await p.locator("#screen").evaluate(img=>img.decode());
  if(initialPngs.length!==1)throw new Error(`Expected one initial PNG request, got ${initialPngs.length}`);
  await p.screenshot({path:path.join(out,"watershed-battle-light.png"),fullPage:true});
  let combinations=0;
  for(const mode of Object.keys(modes))for(const device of Object.keys(devices))for(const lang of ["en","de"])for(const units of ["metric","imperial"])for(const labels of [true,false]) {
    await p.selectOption('#mode',mode);await p.selectOption('#device',device);await p.selectOption('#lang',lang);await p.selectOption('#units',units);await p.locator('#labels').setChecked(labels);
    await p.locator('#screen').evaluate(img=>img.decode());combinations++;
  }
  const sheet=await browser.newPage({viewport:{width:848,height:900},deviceScaleFactor:1});
  await sheet.goto(origin+"/comparison");await sheet.locator("img").evaluateAll(imgs=>Promise.all(imgs.map(img=>img.decode())));
  await sheet.screenshot({path:path.join(out,"layout-comparison.png"),fullPage:true});
  const bytes=fs.statSync(path.join(out,"layout-comparison.png")).size;
  if(bytes>400000)throw new Error(`Comparison PNG unexpectedly large: ${bytes}`);
  for(const [source,target] of [["cards.og.de.plain.png","watershed-pair-labels-off-v4.png"],["cards.og.de.png","watershed-pair-v4.png"],["single.og.de.png","normal-labels-v4.png"],["cards.og_port.de.png","watershed-pair-portrait-v4.png"]])fs.copyFileSync(path.join(out,source),path.join(out,target));
  console.log(`${combinations} gallery combinations decoded; HTML ${Buffer.byteLength(html)} bytes; initial load: one PNG; comparison PNG ${bytes} bytes`);
} finally {await browser.close();server.close();}
