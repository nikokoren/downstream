// Native Ruby Liquid URL contract, using the same fixed capacities as the built feed.
import assert from "node:assert/strict";
import path from "node:path";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const python=spawnSync(process.env.DS_PYTHON||path.join(root,"pipeline/.venv/bin/python"),["-c",String.raw`
import json,sys
sys.path.insert(0,'pipeline')
from downstream.site import polling_url,SLOTS,PAIR_SLOTS,BASE_URL
print(json.dumps({'template':polling_url(),'normal':SLOTS,'paired':PAIR_SLOTS,'base':BASE_URL}))
`],{cwd:root,encoding:"utf8"});
assert.equal(python.status,0,python.stderr);
const ruby=String.raw`
require "json";require "liquid"
data=JSON.parse($stdin.read);template=Liquid::Template.parse(data.fetch("template"),error_mode: :strict)
regions=[[nil,"mix"],[[],"mix"],[["eu"],"eu"],[["us"],"us"],[["ca"],"ca"],[["eu","us"],"eu-us"],[["eu","ca"],"eu-ca"],[["us","ca"],"us-ca"],["eu,us,ca","mix"],["ca,us","us-ca"]]
count=0
regions.each do |region,folder|
  [nil,false,"","false","no",true,"true","yes"].each do |value|
    enabled=[true,"true","yes"].include?(value);mode=enabled ? "p" : "t"
    capacity=data.fetch(enabled ? "paired" : "normal").fetch(folder)
    before=Time.now.to_i/900
    url=template.render!({"region"=>region,"watershed_pairs"=>value},strict_filters:true).strip
    after=Time.now.to_i/900
    expected=[before,after].map{|slot|"#{data.fetch('base')}/#{folder}/#{mode}/#{slot%capacity}.json"}
    raise "Wrong polling URL: #{url}" unless expected.include?(url)
    count+=1
  end
end
puts "#{count} native Ruby Liquid polling-URL cases pass"
`;
const result=spawnSync("ruby",["-e",ruby],{input:python.stdout,encoding:"utf8"});
assert.equal(result.status,0,result.stderr);
process.stdout.write(result.stdout);
