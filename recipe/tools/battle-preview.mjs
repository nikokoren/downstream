// Render the approved paired cards and normal view through the shipping Liquid template.
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import {chromium} from "playwright-core";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const out=path.join(root,"recipe/tools/out/battle"),fw=path.join(root,"data/raw/framework/3.4.0");
fs.mkdirSync(out,{recursive:true});
const basemap=JSON.parse(fs.readFileSync(path.join(root,"fixtures/review/battle-basemap.geojson"),"utf8"));
const packetProcess=spawnSync(process.env.DS_PYTHON||path.join(root,"pipeline/.venv/bin/python"),[path.join(root,"recipe/tools/battle-payload.py"),process.env.DS_BATTLE_PAYLOAD||path.join(root,"fixtures/review/battle-reference.json")],{encoding:"utf8"});
if(packetProcess.status)throw new Error(packetProcess.stderr);
const packets=JSON.parse(packetProcess.stdout);
fs.writeFileSync(path.join(out,"pair-payload.json"),JSON.stringify(packets.pair,null,2));
const pairBytes=Buffer.byteLength(JSON.stringify(packets.pair));
if(pairBytes>6000)throw new Error(`Pair exceeds the payload budget: ${pairBytes} bytes`);
const script=fs.readFileSync(path.join(root,"recipe/tools/battle-map.js"),"utf8");
const devices={
  og:{cls:"screen--og screen--md screen--1bit",w:800,h:480,label:"OG landscape"},
  og_port:{cls:"screen--og screen--md screen--1bit screen--portrait",w:480,h:800,label:"OG portrait"},
  x:{cls:"screen--v2 screen--lg screen--density-2x screen--4bit",w:1872,h:1404,label:"X landscape"},
  x_port:{cls:"screen--v2 screen--lg screen--density-2x screen--4bit screen--portrait",w:1404,h:1872,label:"X portrait"},
};
const pages=new Map();
function markup(c) {
  const packet=structuredClone(packets[c.mode==="single"?"single":"pair"]);
  const ctx={...packet,trmnl:{plugin_settings:{custom_fields_values:{language:c.lang,units:c.units,world_map:c.mode==="single",watershed_pairs:c.mode==="cards",map_labels:c.labels}}}};
  const r=spawnSync("ruby",[path.join(root,"recipe/tools/render.rb"),"full"],{input:JSON.stringify(ctx),encoding:"utf8",maxBuffer:4e6});
  if(r.status)throw new Error(r.stderr);return r.stdout;
}
function html(c) {
  const cfg={mode:c.mode==="single"?"single":"pair",lang:c.lang,units:c.units,labels:c.labels,routes:c.mode==="single"?[packets.single]:packets.pair.routes};
  return `<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/fw/plugins.css"><script src="/fw/plugins.js"></script>
<script src="/fw/maplibre-gl.js"></script><link rel="stylesheet" href="/fw/maplibre-gl.css">
<script>window.WATERSHED_REVIEW=${JSON.stringify(cfg).replaceAll("<","\\u003c")};
const originalOptions=TRMNLMaps.options;TRMNLMaps.options=function(arg){const opts=originalOptions(arg),p={el:arg.el};const ink=TRMNLPaint.textColor("default",p),paper=TRMNLPaint.semantic("canvas",p).color;
opts.style={version:8,sources:{geography:{type:"geojson",data:${JSON.stringify(basemap)}}},layers:[{id:"paper",type:"background",paint:{"background-color":paper}},{id:"borders",type:"line",source:"geography",filter:["==",["get","kind"],"border"],paint:{"line-color":ink,"line-width":.5,"line-dasharray":[1,5]}},{id:"coasts",type:"line",source:"geography",filter:["==",["get","kind"],"coast"],paint:{"line-color":ink,"line-width":.75}}]};return opts;};</script>
</head><body class="environment trmnl"><div class="screen ${devices[c.device].cls}"><div class="view view--full">${markup(c)}</div></div><script>${script}</script></body></html>`;
}
const server=http.createServer((req,res)=>{
  if(pages.has(req.url)){res.setHeader("content-type","text/html; charset=utf-8");return res.end(pages.get(req.url));}
  const f=req.url.startsWith("/fw/")?path.join(fw,path.basename(req.url)):req.url.startsWith("/fonts/")?path.join(fw,"fonts",path.basename(req.url)):null;
  if(!f||!fs.existsSync(f)){res.writeHead(404);return res.end();}
  res.setHeader("content-type",f.endsWith(".css")?"text/css":f.endsWith(".js")?"text/javascript":f.endsWith(".woff2")?"font/woff2":"font/ttf");fs.createReadStream(f).pipe(res);
});
await new Promise(r=>server.listen(0,"127.0.0.1",r));
const browser=await chromium.launch({executablePath:process.env.CHROME||"/usr/bin/chromium",args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"]});
const cases=[];
for(const mode of (process.env.BATTLE_MODES||"single,cards").split(","))for(const device of (process.env.BATTLE_DEVICES||Object.keys(devices).join(",")).split(","))for(const lang of (process.env.BATTLE_LANGS||"en,de").split(","))for(const units of (process.env.BATTLE_UNITS||"metric,imperial").split(","))for(const labels of [true,false])cases.push({mode,device,lang,units,labels});
const results=[];
try {
  const queue=[...cases];
  await Promise.all(Array.from({length:2},async()=>{
    while(queue.length) {
      const c=queue.shift(),id=`${c.mode}.${c.device}.${c.lang}${c.units==="imperial"?".imperial":""}${c.labels?"":".plain"}`;
      pages.set("/"+id,html(c));
      const ctx=await browser.newContext({viewport:{width:devices[c.device].w,height:devices[c.device].h},deviceScaleFactor:1});
      const p=await ctx.newPage(),errors=[];
      p.on("pageerror",e=>errors.push(e.message));
      await p.route("https://trmnl.com/js/maplibre-gl/5.24.0/*",route=>route.fulfill({path:path.join(fw,path.basename(new URL(route.request().url()).pathname))}));
      try {
        await p.goto(`http://127.0.0.1:${server.address().port}/${id}`);
        await p.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true&&window.__reviewMap?.loaded(),null,{timeout:30000});
        await p.waitForFunction(()=>document.querySelector('[data-downstream-map],[data-review-map]')?.__reviewReport,null,{timeout:15000});
        await p.evaluate(()=>TRMNLMaps.ready(window.__reviewMap));
        const report=await p.evaluate(()=>{
          const el=document.querySelector('[data-downstream-map],[data-review-map]'),map=window.__reviewMap;
          const r=el.__reviewReport,box=el.getBoundingClientRect(),sx=box.width/el.clientWidth,sy=box.height/el.clientHeight;
          const obstacles=[...el.querySelectorAll('[data-downstream-box],[data-downstream-obstacle],.map__attribution')].map(n=>{const a=n.getBoundingClientRect();return{x:(a.left-box.left)/sx,y:(a.top-box.top)/sy,w:a.width/sx,h:a.height/sy}});
          for(const g of el.querySelectorAll('[data-world-rect]'))obstacles.push(JSON.parse(g.dataset.worldRect));
          const hits=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
          const fails=[];
          if(el.querySelector('[data-downstream-obstacle]'))fails.push('comparison heading still present');
          for(const l of r.labels){if(obstacles.some(o=>hits(l.rect,o)))fails.push('label overlaps caption/credit: '+l.text);if(l.rect.x<0||l.rect.y<0||l.rect.x+l.rect.w>el.clientWidth||l.rect.y+l.rect.h>el.clientHeight)fails.push('label outside map');}
          const shortened=[...el.querySelectorAll('[data-clamp-lines-trimmed]')].map(n=>n.textContent);
          if(shortened.length)fails.push('caption truncated: '+shortened.join('|'));
          if(r.omitted.length)fails.push('labels omitted: '+r.omitted.join('|'));
          const cfg=window.WATERSHED_REVIEW;
          const expectedLabels=cfg.labels?cfg.routes.length+cfg.routes.reduce((n,r)=>n+r.changes.length,0):0;
          if(r.labels.length!==expectedLabels)fails.push('map-label setting not respected');
          if(!cfg.labels&&(el.querySelector('[data-downstream-labels]')||r.enabled!==false))fails.push('labels-off still draws the callout layer');
          if(r.labels.some(l=>l.kind==='sea'||/^[AB] /.test(l.text)))fails.push('sea label or A/B badge present');
          const captions=[...el.querySelectorAll('[data-downstream-box]')];
          for(const [i,route] of cfg.routes.entries()) {
            const text=captions[i]?.textContent.replace(/\s+/g,' ');
            const expected=[route.place[cfg.lang],route.end_text[cfg.lang],route.distance[cfg.lang][cfg.units],route.travel[cfg.lang],...route.chain.filter(s=>s.name).map(s=>s.name[cfg.lang]||s.name.local)];
            for(const value of expected)if(!text?.includes(value))fails.push('caption value missing: '+value);
          }
          const strokes=map.getStyle().layers.filter(l=>/trmnl-route/.test(l.id)&&!l.id.endsWith('-casing'));
          if(new Set(strokes.map(l=>JSON.stringify(l.paint))).size>1)fails.push('route styles differ');
          const routes=window.WATERSHED_REVIEW.routes.map(r=>r.coords||TRMNLMaps.decodePolyline(r.polyline));
          const off=routes.flatMap(r=>r).filter(c=>{const p=map.project(c);return p.x<0||p.y<0||p.x>el.clientWidth||p.y>el.clientHeight}).length;
          if(off)fails.push(off+' route points outside map');
          const under=routes.flatMap(r=>r).filter(c=>{const p=map.project(c);return obstacles.some(o=>p.x>=o.x&&p.x<=o.x+o.w&&p.y>=o.y&&p.y<=o.y+o.h)}).length;
          if(under)fails.push(under+' route points behind captions/globe/credit');
          return{...r,fails,zoom:map.getZoom(),routeLayers:map.getStyle().layers.filter(l=>/route/.test(l.id)).map(l=>l.id)};
        });
        const image=await p.screenshot({path:path.join(out,id+".png")});
        const ink=await p.evaluate(async b64=>{
          const im=new Image();im.src='data:image/png;base64,'+b64;await im.decode();
          const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;
          const g=cv.getContext('2d');g.drawImage(im,0,0);const pixels=g.getImageData(0,0,cv.width,cv.height).data;
          const el=document.querySelector('[data-downstream-map],[data-review-map]'),r=el.getBoundingClientRect(),m=window.__reviewMap;
          return window.WATERSHED_REVIEW.routes.map(route=>{
            const cs=route.coords||TRMNLMaps.decodePolyline(route.polyline);let painted=0;
            for(const c of cs){const q=m.project(c),x=Math.round(r.left+q.x*r.width/el.clientWidth),y=Math.round(r.top+q.y*r.height/el.clientHeight);let hit=false;
              for(let dy=-3;dy<=3&&!hit;dy++)for(let dx=-3;dx<=3&&!hit;dx++){const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=cv.width||yy>=cv.height)continue;const i=(yy*cv.width+xx)*4;if(pixels[i]+pixels[i+1]+pixels[i+2]<150)hit=true;}if(hit)painted++;}
            return{id:route.id,painted,total:cs.length};
          });
        },image.toString('base64'));
        const fails=[...report.fails,...errors];
        if(report.routeLayers.filter(id=>!id.endsWith('-casing')).length!==report.routes)fails.push('route layer missing');
        for(const r of ink)if(r.painted<.9*r.total)fails.push(`route ${r.id} not painted: ${r.painted}/${r.total}`);
        results.push({...c,id,ok:!fails.length,fails,report,ink});
        console.log(`${fails.length?"FAIL":"ok"} ${id} ${fails.join('; ')}`);
      } catch(e) {results.push({...c,id,ok:false,fails:[e.message]});console.log('FAIL',id,e.message.slice(0,160));}
      await ctx.close();
    }
  }));
} finally {await browser.close();server.close();}
const previous=process.env.BATTLE_APPEND==="1"?JSON.parse(fs.readFileSync(path.join(out,"results.json"),"utf8")):[];
const replaced=new Set(results.map(r=>r.id));
const combined=[...previous.filter(r=>!replaced.has(r.id)),...results].sort((a,b)=>a.id.localeCompare(b.id));
fs.writeFileSync(path.join(out,"results.json"),JSON.stringify(combined,null,2));
console.log(`${results.filter(r=>r.ok).length}/${results.length} preview cases pass; stored ${combined.filter(r=>r.ok).length}/${combined.length}; pair payload ${pairBytes} bytes`);
process.exitCode=combined.every(r=>r.ok)?0:1;
