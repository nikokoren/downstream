// Read-only preview adapter: the shipping Shared script draws both paths and all callouts.
(function () {
  function start() {
    const el=document.querySelector("[data-downstream-map]");
    if(!el?.__downstreamMap || !el.__downstreamLabels) {setTimeout(start,50);return;}
    window.__reviewMap=el.__downstreamMap;
    const report=()=>{el.__reviewReport=el.__downstreamLabels;};
    el.__downstreamMap.on("idle",report);report();
  }
  (document.fonts?document.fonts.ready:Promise.resolve()).then(start);
})();
