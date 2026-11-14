// Native Liquid: the opt-in comparison renders only in Full; other cases retain one journey.
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const data=process.env.DS_PAIR_PAYLOADS?{status:0,stdout:fs.readFileSync(process.env.DS_PAIR_PAYLOADS,"utf8")}:
  spawnSync(process.env.DS_PYTHON||path.join(root,"pipeline/.venv/bin/python"),[path.join(root,"recipe/tools/battle-payload.py")],{encoding:"utf8"});
assert.equal(data.status,0,data.stderr);
const packets=JSON.parse(data.stdout),cases=[];
const values=[null,false,"false","no","",true,"true","yes"];
function addCase(kind,view,language,units,pairValue,labelValue) {
  const expected=kind==="pair"&&view==="full"&&[true,"true","yes"].includes(pairValue)?2:1;
  const labelsExpected=![false,"false","no"].includes(labelValue);
  cases.push({view,kind,language,expected,labelsExpected,context:{...packets[kind],trmnl:{plugin_settings:{custom_fields_values:{language,units,watershed_pairs:pairValue,map_labels:labelValue}}}}});
}
for(const kind of (process.env.DS_CASE_KINDS?process.env.DS_CASE_KINDS.split(","):["single","pair"]))for(const view of ["full","half_horizontal","half_vertical","quadrant"])
  for(const language of ["en","de"])for(const units of ["metric","imperial"]) {
    for(const value of values)addCase(kind,view,language,units,value,undefined);
    for(const pairValue of [false,true])for(const labelValue of values)addCase(kind,view,language,units,pairValue,labelValue);
  }
const code=String.raw`
require "json"; require "liquid"
src=File.join(ARGV.fetch(0),"recipe","src"); partials={}
shared=File.read(File.join(src,"shared.liquid")).gsub(/\{%-?\s*template\s+(\w+)\s*-?%\}(.*?)\{%-?\s*endtemplate\s*-?%\}/m) { partials[Regexp.last_match(1)]=Regexp.last_match(2); "" }
loader=Object.new; loader.define_singleton_method(:read_template_file) { |name| partials.fetch(name) }
env=Liquid::Environment.build { |e| e.file_system=loader }
templates=%w[full half_horizontal half_vertical quadrant].to_h { |v| [v,Liquid::Template.parse(shared+File.read(File.join(src,"#{v}.liquid")),environment:env,error_mode: :strict)] }
print JSON.generate(JSON.parse($stdin.read).map { |c| templates.fetch(c.fetch("view")).render!(c.fetch("context"),strict_filters:true) })
`;
const run=spawnSync("ruby",["-e",code,root],{input:JSON.stringify(cases),encoding:"utf8",maxBuffer:128*1024*1024});
assert.equal(run.status,0,run.stderr);
JSON.parse(run.stdout).forEach((html,i)=>{
  const c=cases[i];
  assert.equal([...html.matchAll(/<div[^>]+ data-downstream-route /g)].length,c.expected,`routes: ${JSON.stringify(c)}`);
  assert.equal([...html.matchAll(/<div[^>]+ data-downstream-box>/g)].length,c.expected,`cards: ${JSON.stringify(c)}`);
  assert.ok(!/<div[^>]+ data-downstream-obstacle/.test(html),"heading removed");
  assert.ok(html.includes(`data-map-labels="${c.labelsExpected?"yes":"no"}"`),"map labels default on and respect false values");
  const town=(c.kind==="pair"?packets.pair.routes[0]:packets.single).town[c.language];
  assert.ok(html.includes(`data-town="${town}"`),"primary town survives the fallback");
});
console.log(`${cases.length} strict Liquid cases pass: independent label/comparison settings, defaults, full-only comparison, fallbacks, languages and units`);
