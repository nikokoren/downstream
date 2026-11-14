// Check every generated pair's actual cards in every distinct Full frame/language/unit.
// Maps are covered separately by render-check.mjs; this pass measures the untrimmed copy.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";
import {chromium} from "playwright-core";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const site=path.join(root,"data/site/mix/p"),fw=path.join(root,"data/raw/framework/3.4.0");
const out=path.join(root,"recipe/tools/out/pair-feed");
const plan=JSON.parse(fs.readFileSync(path.join(site,"plan.json"),"utf8")).slots;
const seen=new Set(),packets=[];
plan.forEach((id,index)=>{
  if(!id||seen.has(id))return;
  const packet=JSON.parse(fs.readFileSync(path.join(site,`${index}.json`),"utf8"));
  if(packet.routes?.length!==2)return;
  seen.add(id);packets.push({id,packet});
});
const contexts=[];
for(const {id,packet} of packets)for(const language of ["en","de"])for(const units of ["metric","imperial"])
  contexts.push({id,language,units,context:{...packet,trmnl:{plugin_settings:{custom_fields_values:{language,units,watershed_pairs:true}}}}});
const ruby=String.raw`
require "json";require "liquid"
src=File.join(ARGV.fetch(0),"recipe/src");partials={}
shared=File.read(File.join(src,"shared.liquid")).gsub(/\{%-?\s*template\s+(\w+)\s*-?%\}(.*?)\{%-?\s*endtemplate\s*-?%\}/m){partials[Regexp.last_match(1)]=Regexp.last_match(2);""}
shared=shared.gsub(/<script\b[^>]*>.*?<\/script>/m,"")
loader=Object.new;loader.define_singleton_method(:read_template_file){|name|partials.fetch(name)}
env=Liquid::Environment.build{|e|e.file_system=loader}
t=Liquid::Template.parse(shared+File.read(File.join(src,"full.liquid")),environment:env,error_mode: :strict)
print JSON.generate(JSON.parse($stdin.read).map{|c|t.render!(c.fetch("context"),strict_filters:true)})
`;
const rendered=spawnSync("ruby",["-e",ruby,root],{input:JSON.stringify(contexts),encoding:"utf8",maxBuffer:256*1024*1024});
if(rendered.status!==0)throw new Error(rendered.stderr);
const htmls=JSON.parse(rendered.stdout);
const server=http.createServer((req,res)=>{
  const file=req.url.startsWith("/fonts/")?path.join(fw,"fonts",path.basename(req.url)):path.join(fw,path.basename(req.url));
  if(!fs.existsSync(file)){res.writeHead(404);return res.end();}
  res.writeHead(200,{"content-type":file.endsWith(".css")?"text/css":file.endsWith(".js")?"text/javascript":"font/ttf"});
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(0,resolve));
const base=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({executablePath:process.env.CHROME||"/usr/bin/chromium"});
const page=await browser.newPage({viewport:{width:1872,height:1872}});
await page.setContent(`<!doctype html><html><head><link rel="stylesheet" href="${base}/plugins.css"><script src="${base}/plugins.js"></script></head><body class="environment trmnl"><div id="screen" class="screen screen--og screen--md screen--1bit"><div id="view" class="view view--full">${htmls[0]}</div></div></body></html>`);
await page.evaluate(()=>document.fonts.ready);
const frames=["screen--og screen--md screen--1bit","screen--og screen--md screen--1bit screen--portrait",
  "screen--v2 screen--lg screen--density-2x screen--4bit","screen--v2 screen--lg screen--density-2x screen--4bit screen--portrait"];
let checks=0;const failures=[],accepted=[];
for(let start=0;start<htmls.length;start+=64){
  const batch=htmls.slice(start,start+64);
  const result=await page.evaluate(({batch,frames})=>{
    const fails=[],accepted=[];const screen=document.getElementById("screen"),view=document.getElementById("view");
    batch.forEach((html,index)=>{
      view.innerHTML=html;
      for(const frame of frames){
        screen.className="screen "+frame;
        const boxes=[...view.querySelectorAll("[data-downstream-box]")];
        if(boxes.length!==2){fails.push({index,frame,reason:"missing card"});continue;}
        boxes.forEach((box,side)=>{
          for(const el of box.children){
            const max=Number(el.dataset.clamp||1),probe=el.cloneNode(true);
            probe.removeAttribute("data-clamp");
            probe.style.cssText=`position:absolute;width:${el.clientWidth}px;height:auto;max-height:none;-webkit-line-clamp:unset;overflow:visible;`;
            probe.textContent=el.dataset.clampOriginal||el.textContent;
            box.appendChild(probe);
            const line=parseFloat(getComputedStyle(probe).lineHeight);
            const clipped=probe.scrollHeight>line*max+1||probe.scrollWidth>probe.clientWidth+2;
            if(clipped){
              const record={index,frame,side,text:probe.textContent,reason:"copy exceeds line budget",height:probe.scrollHeight,line,max,width:probe.clientWidth};
              if(Number(el.dataset.downstreamPlace)>45)accepted.push(record);else fails.push(record);
            }
            probe.remove();
          }
          const r=box.getBoundingClientRect(),s=screen.getBoundingClientRect();
          if(r.top<s.top-1||r.bottom>s.bottom+1)fails.push({index,frame,side,reason:"card outside screen"});
        });
      }
    });
    return {fails,accepted};
  },{batch,frames});
  for(const item of result.fails)failures.push({...contexts[start+item.index],context:undefined,...item});
  for(const item of result.accepted)accepted.push({...contexts[start+item.index],context:undefined,...item});
  checks+=batch.length*frames.length;
}
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,"all-pair-card-checks.json"),JSON.stringify({pairs:packets.length,checks,failures,accepted_long_town_lines:accepted},null,1));
console.log(`${checks} actual-card cases across ${packets.length} pairs; ${failures.length} failures; ${accepted.length} permitted long-town truncations`);
await browser.close();server.close();
if(failures.length)process.exitCode=1;
