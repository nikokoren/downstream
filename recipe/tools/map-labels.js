// Shared map callouts. Bundled in Shared; all names come from the payload.
var DownstreamLabels = (() => {
  const ns = "http://www.w3.org/2000/svg";
  function svg(tag, attrs, text) {
    const n = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (text != null) n.textContent = text;
    return n;
  }
  function overlaps(a, b, pad = 0) {
    return a.x < b.x + b.w + pad && a.x + a.w + pad > b.x && a.y < b.y + b.h + pad && a.y + a.h + pad > b.y;
  }
  function segmentHits(a, b, r) {
    let lo = 0, hi = 1;
    const dx = b.x - a.x, dy = b.y - a.y;
    for (const [p, q] of [[-dx, a.x-r.x], [dx, r.x+r.w-a.x], [-dy, a.y-r.y], [dy, r.y+r.h-a.y]]) {
      if (!p) { if (q < 0) return false; continue; }
      const t = q / p;
      if (p < 0) lo = Math.max(lo, t); else hi = Math.min(hi, t);
      if (lo > hi) return false;
    }
    return true;
  }
  function padded(r, pad) {
    return {x:r.x-pad,y:r.y-pad,w:r.w+2*pad,h:r.h+2*pad};
  }
  function pointDistance2(p, a, b) {
    const dx=b.x-a.x, dy=b.y-a.y;
    const t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy||1)));
    return (p.x-a.x-t*dx)**2+(p.y-a.y-t*dy)**2;
  }
  function segmentsNear(a, b, c, d, gap) {
    if (Math.min(a.x,b.x)>Math.max(c.x,d.x)+gap || Math.max(a.x,b.x)<Math.min(c.x,d.x)-gap ||
        Math.min(a.y,b.y)>Math.max(c.y,d.y)+gap || Math.max(a.y,b.y)<Math.min(c.y,d.y)-gap) return false;
    const cross=(p,q,r)=>(q.x-p.x)*(r.y-p.y)-(q.y-p.y)*(r.x-p.x);
    if (cross(a,b,c)*cross(a,b,d)<=0 && cross(c,d,a)*cross(c,d,b)<=0) return true;
    return Math.min(pointDistance2(a,c,d),pointDistance2(b,c,d),pointDistance2(c,a,b),pointDistance2(d,a,b))<gap*gap;
  }
  function localRect(node, el) {
    const a = node.getBoundingClientRect(), b = el.getBoundingClientRect();
    return {x:(a.left-b.left)*el.clientWidth/b.width, y:(a.top-b.top)*el.clientHeight/b.height,
      w:a.width*el.clientWidth/b.width, h:a.height*el.clientHeight/b.height};
  }
  function read(el) {
    return [...el.querySelectorAll("[data-downstream-route]")].map(node => {
      const coords = TRMNLMaps.decodePolyline(node.dataset.polyline || "");
      const labels = [];
      if (node.dataset.town && coords.length) labels.push({kind:"town", text:node.dataset.town, at:coords[0]});
      for (const n of node.querySelectorAll("[data-downstream-change]")) {
        const at = [Number(n.dataset.lon), Number(n.dataset.lat)];
        if (at.every(Number.isFinite) && Math.abs(at[0]) <= 180 && Math.abs(at[1]) <= 90 && n.dataset.text) {
          labels.push({kind:"change", text:n.dataset.text, at});
        }
      }
      return {coords, labels};
    }).filter(r => r.coords.length);
  }
  function fitGap(el) {
    // Give labels a row of space outside the whole-route bounds in Full. Small
    // mashups keep their existing fit and omit optional changes when crowded.
    return TRMNLPaint.px(el.closest(".view--full") && el.dataset.mapLabels!=="no" ? 40 : 16, {el});
  }
  function draw(map, el, routes) {
    el.querySelector("[data-downstream-labels]")?.remove();
    // Restore native place labels before remeasuring after a camera/size/font change.
    const background = [...el.querySelectorAll(".map__labels .map__label")];
    background.forEach(n=>n.classList.remove("hidden"));
    if (el.dataset.mapLabels === "no") {
      el.__downstreamLabels = {labels:[], omitted:[], routes:routes.length, enabled:false};
      return el.__downstreamLabels;
    }
    const paint = {el}, px = n => TRMNLPaint.px(n, paint);
    const ink = TRMNLPaint.textColor("default", paint), paper = TRMNLPaint.semantic("canvas", paint).color;
    const layer = svg("svg", {class:"absolute top--0 left--0 w--full h--full z--2", viewBox:`0 0 ${el.clientWidth} ${el.clientHeight}`,
      "pointer-events":"none", "aria-hidden":"true", "data-downstream-labels":""});
    el.appendChild(layer);
    const font = document.createElement("span");
    font.className = "absolute label label--small lg:label";
    el.appendChild(font);
    const f = getComputedStyle(font), typography = {"font-family":f.fontFamily, "font-size":f.fontSize, "font-weight":f.fontWeight};
    const fontSize = parseFloat(f.fontSize); font.remove();
    const occupied = [...el.querySelectorAll("[data-downstream-box],[data-downstream-obstacle],.map__attribution")].map(n=>localRect(n,el));
    for (const globe of el.querySelectorAll("[data-world-rect]")) occupied.push(JSON.parse(globe.dataset.worldRect));
    function project(c) {
      const lng=c[0]+360*Math.round((map.getCenter().lng-c[0])/360);
      return map.project([lng,c[1]]);
    }
    const projected = routes.map(r=>r.coords.map(project));
    const labels = [], omitted = [], leaders = [];
    const margin = px(6), pad = px(4), gap = px(10);
    // px() probes Framework styles; resolve once, outside the geometry searches.
    const leaderGap=px(3), labelGap=px(2), markerGap=px(8), markerRadius=px(7), nearby=px(35), unlinkedPenalty=px(15), crossingPenalty=px(200);
    // Reserve the full route stroke/casing and start/end discs, not just centre lines.
    const segments = projected.flatMap(line=>line.slice(1).map((b,i)=>({a:line[i],b})));
    const markerPoints = projected.flatMap(line=>[line[0],line[line.length-1]]);
    const markers = markerPoints.map(p=>({x:p.x-markerGap,y:p.y-markerGap,w:2*markerGap,h:2*markerGap}));
    // Rivers always keep their ink and casing. Mask connecting lines around the
    // paths/markers, including the rare town connector that must cross a loop.
    const maskId=(el.id||"downstream-preview")+"-label-route-clearance";
    const defs=svg("defs",{}), mask=svg("mask",{id:maskId,maskUnits:"userSpaceOnUse",x:0,y:0,width:el.clientWidth,height:el.clientHeight});
    mask.appendChild(svg("rect",{x:0,y:0,width:el.clientWidth,height:el.clientHeight,fill:"white"}));
    for(const line of projected) mask.appendChild(svg("path",{d:"M"+line.map(p=>`${p.x},${p.y}`).join(" L"),fill:"none",stroke:"black","stroke-width":px(10),"stroke-linejoin":"round","stroke-linecap":"round"}));
    for(const p of markerPoints) mask.appendChild(svg("circle",{cx:p.x,cy:p.y,r:markerGap,fill:"black"}));
    defs.appendChild(mask);layer.appendChild(defs);
    function nearestRoutePoint(c, line) {
      const p = project(c);
      let best = null;
      for (let i=1; i<line.length; i++) {
        const a=line[i-1], b=line[i], dx=b.x-a.x, dy=b.y-a.y;
        const t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy||1)));
        const q={x:a.x+t*dx,y:a.y+t*dy}, d=(p.x-q.x)**2+(p.y-q.y)**2;
        if (!best || d<best.d) best={...q,d};
      }
      return best || p;
    }
    function prepare(item, routeIndex) {
      const anchor = nearestRoutePoint(item.at, projected[routeIndex]);
      const text = svg("text", {...typography, x:0, y:0, "dominant-baseline":"central", fill:ink}, item.text);
      layer.appendChild(text);
      const bounds = text.getBBox(), w=bounds.width+2*pad, h=Math.max(bounds.height,fontSize)+2*pad;
      const candidates = [];
      for (const distance of [gap,px(20),px(35),px(55),px(80),px(115)]) {
        for (const [sx,sy] of [[1,-1],[-1,-1],[1,1],[-1,1],[1,0],[-1,0],[0,-1],[0,1]]) {
          candidates.push({x:anchor.x+(sx===1?distance:sx===-1?-distance-w:-w/2),y:anchor.y+(sy===1?distance:sy===-1?-distance-h:-h/2),w,h});
        }
        // Slide along each edge too: a diagonal-only search can miss a clear nearby slot.
        for (const f of [.2,.35,.65,.8]) {
          candidates.push({x:anchor.x-w*f,y:anchor.y-distance-h,w,h}, {x:anchor.x-w*f,y:anchor.y+distance,w,h},
            {x:anchor.x-distance-w,y:anchor.y-h*f,w,h}, {x:anchor.x+distance,y:anchor.y-h*f,w,h});
        }
      }
      const options=[];
      for (const r of candidates) {
        if (r.x<margin || r.y<margin || r.x+r.w>el.clientWidth-margin || r.y+r.h>el.clientHeight-margin) continue;
        if (occupied.some(o=>overlaps(r,o,leaderGap))) continue;
        if (markers.some(o=>overlaps(r,o))) continue;
        const routeSpace=padded(r,pad);
        if (segments.some(s=>segmentHits(s.a,s.b,routeSpace))) continue;
        if (leaders.some(l=>segmentHits(l.a,l.b,padded(r,labelGap)))) continue;
        const nearest={x:Math.max(r.x,Math.min(r.x+r.w,anchor.x)),y:Math.max(r.y,Math.min(r.y+r.h,anchor.y))};
        const distance=Math.hypot(nearest.x-anchor.x,nearest.y-anchor.y);
        // At tightly clustered starts, a conventional nearby place label can remain
        // readable even when no connector can leave the dot without crossing ink.
        if (item.kind==="town" && distance<=nearby) options.push({...r,anchor,end:anchor,free:anchor,score:distance+unlinkedPenalty,connected:false});
        // A different entry point on the same clear box can leave a bend safely
        // when the nearest edge would force the connector along the river.
        const ends=[nearest,...[r.x+labelGap,r.x+r.w-labelGap].flatMap(x=>[r.y+labelGap,r.y+r.h-labelGap].map(y=>({x,y})))];
        for (const end of ends) {
          const length=Math.hypot(end.x-anchor.x,end.y-anchor.y);
          // Only the short attachment at the anchor may touch a river or its marker.
          const attach=Math.min(1,markerGap/length);
          const free={x:anchor.x+(end.x-anchor.x)*attach,y:anchor.y+(end.y-anchor.y)*attach};
          const crosses=segments.some(s=>segmentsNear(free,end,s.a,s.b,leaderGap)) || markerPoints.some(p=>pointDistance2(p,free,end)<markerRadius**2);
          if (crosses && item.kind!=="town") continue;
          if (occupied.some(o=>segmentHits(anchor,end,padded(o,labelGap)))) continue;
          if (leaders.some(l=>segmentsNear(free,end,l.a,l.b,labelGap) || segmentsNear(anchor,end,l.free,l.b,labelGap))) continue;
          options.push({...r,anchor,end,free,score:length+(crosses?crossingPenalty:0),connected:true});
        }
      }
      options.sort((a,b)=>a.score-b.score);
      return {item,anchor,text,w,h,options};
    }
    function commit(spec, best) {
      const {item,anchor,text,w,h}=spec;
      if (!best) { text.remove(); omitted.push(item.text); return; }
      const g=svg("g", {"data-downstream-callout":item.kind, "data-downstream-label":item.text});
      g.appendChild(svg("path", {d:`M${anchor.x},${anchor.y} L${best.end.x},${best.end.y}`,fill:"none",stroke:ink,"stroke-width":px(.75),mask:`url(#${maskId})`}));
      g.appendChild(svg("circle", {cx:anchor.x,cy:anchor.y,r:px(2),fill:ink}));
      g.appendChild(svg("rect", {x:best.x,y:best.y,width:w,height:h,rx:px(2),fill:paper,stroke:ink,"stroke-width":px(.5)}));
      text.setAttribute("x",best.x+pad); text.setAttribute("y",best.y+h/2);
      g.appendChild(text); layer.appendChild(g);
      occupied.push(best);
      if (best.connected) leaders.push({a:anchor,b:best.end,free:best.free});
      labels.push({text:item.text,kind:item.kind,rect:{x:best.x,y:best.y,w,h},anchor:{x:anchor.x,y:anchor.y},connected:best.connected,sourceOffsetPx:Math.sqrt(anchor.d||0)});
    }
    function compatible(a,b) {
      if (overlaps(a,b,leaderGap)) return false;
      if (a.connected && segmentHits(a.anchor,a.end,padded(b,labelGap))) return false;
      if (b.connected && segmentHits(b.anchor,b.end,padded(a,labelGap))) return false;
      return !a.connected || !b.connected || !(segmentsNear(a.free,a.end,b.anchor,b.end,labelGap) || segmentsNear(a.anchor,a.end,b.free,b.end,labelGap));
    }
    // Plan both towns together, so the first cannot consume the other's only clear
    // position. River changes use the remaining space; no callout is added at the sea.
    const towns=routes.flatMap((r,i)=>r.labels.filter(l=>l.kind==="town").map(l=>prepare(l,i)));
    if (towns.length===2) {
      let pair=null;
      for (const a of towns[0].options) for (const b of towns[1].options) {
        const score=a.score+b.score;
        if (pair && score>=pair.score) break;
        if (compatible(a,b)) pair={a,b,score};
      }
      if (pair) { commit(towns[0],pair.a); commit(towns[1],pair.b); }
      else {
        // Safe degradation if the viewport genuinely cannot hold both labels.
        commit(towns[0],towns[0].options[0]);
        towns[1].text.remove();
        const retry=prepare(towns[1].item,1); commit(retry,retry.options[0]);
      }
    } else towns.forEach(t=>commit(t,t.options[0]));
    routes.forEach((r,i)=>r.labels.filter(l=>l.kind==="change").forEach(l=>{
      const spec=prepare(l,i); commit(spec,spec.options[0]);
    }));
    // Keep useful geographic context, but give journeys and their callouts priority
    // over native city names (whose text halos can otherwise erase a river stroke).
    const suppressedBackground = [];
    for (const node of background) {
      const r=padded(localRect(node,el),leaderGap);
      if (occupied.some(o=>overlaps(r,o)) || markers.some(o=>overlaps(r,o)) ||
          segments.some(s=>segmentHits(s.a,s.b,r)) || leaders.some(l=>segmentHits(l.a,l.b,r))) {
        node.classList.add("hidden"); suppressedBackground.push(node.textContent);
      }
    }
    el.__downstreamLabels = {labels,omitted,routes:routes.length,enabled:true,suppressedBackground};
    return el.__downstreamLabels;
  }
  return {read, draw, fitGap};
})();
