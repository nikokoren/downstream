// Replay real accepted pairs through the shipping callout code and MapLibre camera.
// A blank style isolates placement from tile/GPU timing; hosted maps are checked separately.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import {chromium} from "playwright-core";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const fw=path.join(root,"data/raw/framework/3.4.0"),site=path.join(root,"data/site/mix/p");
const slots=JSON.parse(fs.readFileSync(path.join(site,"plan.json"),"utf8")).slots;
const seen=new Set(),contexts=[];
for(const [slot,id] of slots.entries()) {
  if(!id||seen.has(id))continue;
  seen.add(id);
  const packet=JSON.parse(fs.readFileSync(path.join(site,`${slot}.json`),"utf8"));
  if(packet.routes?.length!==2)continue;
  for(const language of ["en","de"])contexts.push({id,language,context:{...packet,
    trmnl:{plugin_settings:{custom_fields_values:{language,units:"metric",watershed_pairs:true}}}}});
}
if(process.env.DS_PAIR_LIMIT)contexts.splice(Number(process.env.DS_PAIR_LIMIT)*2);
const ruby=String.raw`
require "json";require "liquid"
src=File.join(ARGV.fetch(0),"recipe/src");partials={}
shared=File.read(File.join(src,"shared.liquid")).gsub(/\{%-?\s*template\s+(\w+)\s*-?%\}(.*?)\{%-?\s*endtemplate\s*-?%\}/m){partials[Regexp.last_match(1)]=Regexp.last_match(2);""}
shared=shared.gsub(/<script\b[^>]*>.*?<\/script>/m,"")
shared=shared.gsub(/<link\b[^>]*>/m,"")
loader=Object.new;loader.define_singleton_method(:read_template_file){|name|partials.fetch(name)}
env=Liquid::Environment.build{|e|e.file_system=loader}
t=Liquid::Template.parse(shared+File.read(File.join(src,"full.liquid")),environment:env,error_mode: :strict)
print JSON.generate(JSON.parse($stdin.read).map{|c|t.render!(c.fetch("context"),strict_filters:true)})
`;
const rendered=spawnSync("ruby",["-e",ruby,root],{input:JSON.stringify(contexts),encoding:"utf8",maxBuffer:256*1024*1024});
if(rendered.status!==0)throw new Error(rendered.stderr);
const htmls=JSON.parse(rendered.stdout);
console.log(`Rendered ${htmls.length} real catalogue contexts`);
const server=http.createServer((req,res)=>{
  const file=req.url.startsWith("/fonts/")?path.join(fw,"fonts",path.basename(req.url)):path.join(fw,path.basename(req.url));
  if(!fs.existsSync(file)){res.writeHead(404);return res.end();}
  res.writeHead(200,{"access-control-allow-origin":"*","content-type":file.endsWith(".css")?"text/css":file.endsWith(".js")?"text/javascript":"font/ttf"});
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(0,resolve));
const base=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({executablePath:process.env.CHROME||"/usr/bin/chromium",
  args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]});
console.log("Projection browser ready");
try {
  const page=await browser.newPage({viewport:{width:1872,height:1872}});
  page.on("pageerror",e=>console.log("page error:",e.message));
  if(process.env.DEBUG)page.on("console",m=>console.log(m.text()));
  await page.setContent(`<!doctype html><html><head><link rel="stylesheet" href="${base}/plugins.css"><script src="${base}/plugins.js"></script><script src="${base}/maplibre-gl.js"></script></head><body class="environment trmnl"><div id="screen" class="screen screen--og screen--md screen--1bit screen--portrait"><div id="view" class="view view--full">${htmls[0]}</div></div></body></html>`);
  await page.addScriptTag({path:path.join(root,"recipe/tools/map-labels.js")});
  console.log("Framework and callout script loaded");
  await page.evaluate(async()=>{
    await document.fonts.ready;
    const node=document.createElement("div");node.className="absolute top--0 left--0 w--full h--full";
    document.querySelector("[data-downstream-map]").appendChild(node);
    window.projection=new maplibregl.Map({container:node,style:{version:8,sources:{},layers:[]},attributionControl:false,interactive:false});
  });
  console.log("Projection ready");
  const frames=process.env.DS_LABEL_FRAMES==="all" ? ["screen--og screen--md screen--1bit","screen--og screen--md screen--1bit screen--portrait",
    "screen--v2 screen--lg screen--density-2x screen--4bit","screen--v2 screen--lg screen--density-2x screen--4bit screen--portrait"] : ["screen--og screen--md screen--1bit screen--portrait"];
  await page.evaluate(async frames=>{
    for(const frame of frames){document.getElementById("screen").className="screen "+frame;await document.fonts.ready;}
  },frames);
  const out=path.join(root,"recipe/tools/out/label-clearance");fs.mkdirSync(out,{recursive:true});
  let checks=0,omittedChanges=0;const failures=[];
  for(let start=0;start<htmls.length;start+=16) {
    const result=await page.evaluate(({batch,frames})=>{
      const fails=[];let omitted=0;
      for(const [index,html] of batch.entries()) {
        const node=projection.getContainer(),view=document.getElementById("view");
        node.remove();view.innerHTML=html;
        const el=view.querySelector("[data-downstream-map]");el.appendChild(node);
        const credit=document.createElement("div");credit.className="map__attribution";credit.textContent="© OpenStreetMap contributors";el.appendChild(credit);
        for(const frame of frames) {
          document.getElementById("screen").className="screen "+frame;
          projection.resize();
          const routes=DownstreamLabels.read(el),g=DownstreamLabels.fitGap(el);
          const bottom=Math.max(...[...el.querySelectorAll("[data-downstream-box]")].map(b=>el.clientHeight-b.offsetTop+g));
          TRMNLMaps.fit(projection,routes.flatMap(r=>r.coords),{padding:{top:g,left:g,right:g,bottom},maxZoom:12});
          const report=DownstreamLabels.draw(projection,el,routes);
          if(report.labels.filter(l=>l.kind==="town").length!==2)fails.push({index,frame,reason:"start town omitted",omitted:report.omitted});
          omitted+=report.omitted.length;
        }
      }
      return {fails,omitted};
    },{batch:htmls.slice(start,start+16),frames});
    checks+=Math.min(16,htmls.length-start)*frames.length;omittedChanges+=result.omitted;
    for(const item of result.fails)failures.push({...contexts[start+item.index],context:undefined,...item});
    fs.writeFileSync(path.join(out,"catalogue-placement.json"),JSON.stringify({pairs:contexts.length/2,checks,complete:false,failures,omitted_change_callouts:omittedChanges},null,1));
    if(start%160===0)console.log(`${checks} placement cases checked; ${failures.length} town omissions`);
  }
  fs.writeFileSync(path.join(out,"catalogue-placement.json"),JSON.stringify({pairs:contexts.length/2,checks,complete:true,failures,omitted_change_callouts:omittedChanges},null,1));
  console.log(`${checks} placement cases; ${failures.length} town omissions`);
  if(failures.length)process.exitCode=1;
} finally {await browser.close();server.close();}
