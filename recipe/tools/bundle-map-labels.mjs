// Keep Shared self-contained for TRMNL's editor. --check verifies the checked-in bundle.
import fs from "node:fs";
import {fileURLToPath} from "node:url";

const source=fs.readFileSync(new URL("./map-labels.js",import.meta.url),"utf8");
const sharedPath=fileURLToPath(new URL("../src/shared.liquid",import.meta.url));
const shared=fs.readFileSync(sharedPath,"utf8");
const begin="    // BEGIN bundled map labels (recipe/tools/map-labels.js).\n",end="    // END bundled map labels.";
const a=shared.indexOf(begin)+begin.length,b=shared.indexOf(end,a);
if(a<begin.length||b<0)throw new Error("Shared is missing the map-label bundle markers");
const bundled=source.trimEnd().split("\n").map(line=>"    "+line+"\n").join("");
if(process.argv.includes("--check")) {
  if(shared.slice(a,b)!==bundled)throw new Error("Rebuild Shared with node recipe/tools/bundle-map-labels.mjs");
  console.log("Shared map-label bundle matches its source");
} else {
  fs.writeFileSync(sharedPath,shared.slice(0,a)+bundled+shared.slice(b));
  console.log("Updated Shared map labels");
}
