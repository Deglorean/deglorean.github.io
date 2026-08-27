(()=>{"use strict";const search=document.getElementById("resourceSearch"),grid=document.getElementById("resourceGrid"),filters=document.getElementById("filters"),empty=document.getElementById("emptyState");if(!grid)return;let active="all";function apply(){const q=(search?.value||"").trim().toLowerCase();let n=0;grid.querySelectorAll(".card").forEach(c=>{const tags=(c.dataset.tags||"").split("|"),ok=(active==="all"||tags.includes(active))&&(!q||(c.dataset.search||"").includes(q));c.style.display=ok?"":"none";if(ok)n++});if(empty)empty.style.display=n?"none":"block"}filters?.querySelectorAll(".filter").forEach(b=>b.addEventListener("click",()=>{active=b.dataset.filter;filters.querySelectorAll(".filter").forEach(x=>x.classList.toggle("active",x===b));apply()}));search?.addEventListener("input",apply)})();

(()=>{"use strict";const toggle=document.querySelector("[data-mobile-menu-toggle]"),layer=document.querySelector("[data-mobile-menu-layer]");if(!toggle||!layer)return;const closeButtons=layer.querySelectorAll("[data-mobile-menu-close]");const firstLink=()=>layer.querySelector(".mobile-menu-links a");function setOpen(open){layer.hidden=!open;toggle.setAttribute("aria-expanded",String(open));toggle.setAttribute("aria-label",open?"Close navigation menu":"Open navigation menu");document.body.classList.toggle("mobile-menu-open",open);if(open)setTimeout(()=>firstLink()?.focus(),0);else toggle.focus({preventScroll:true})}toggle.addEventListener("click",()=>setOpen(layer.hidden));closeButtons.forEach(button=>button.addEventListener("click",()=>setOpen(false)));layer.querySelectorAll("a").forEach(link=>link.addEventListener("click",()=>setOpen(false)));document.addEventListener("keydown",event=>{if(event.key==="Escape"&&!layer.hidden)setOpen(false)});window.addEventListener("resize",()=>{if(window.innerWidth>1000&&!layer.hidden)setOpen(false)})})();

(()=>{
  "use strict";
  const DRAW_UNITS_PER_SECOND=160;
  const LIFT_UNITS_PER_SECOND=260;
  const LETTER_PAUSE_SECONDS=.25;
  const LIFT_HEIGHT=126;
  const TARGET_DRAW_SECONDS=5.0;
  const COMPLETE_HOLD_MS=320;
  const FADE_MS=680;
  const activeFrames=new WeakMap();
  const activeTimers=new WeakMap();

  const lengthOf=points=>points.slice(1).reduce((total,point,index)=>{
    const previous=points[index];
    return total+Math.hypot(point.x-previous.x,point.y-previous.y);
  },0);

  function pointAt(points,targetDistance){
    let travelled=0;
    for(let index=1;index<points.length;index+=1){
      const start=points[index-1],end=points[index];
      const dx=end.x-start.x,dy=end.y-start.y,part=Math.hypot(dx,dy);
      if(part<.001)continue;
      if(travelled+part>=targetDistance){
        const ratio=Math.max(0,Math.min(1,(targetDistance-travelled)/part));
        return{x:start.x+dx*ratio,y:start.y+dy*ratio,ux:dx/part,uy:dy/part};
      }
      travelled+=part;
    }
    const end=points.at(-1),before=points.at(-2)||end;
    const dx=end.x-before.x,dy=end.y-before.y,part=Math.hypot(dx,dy)||1;
    return{x:end.x,y:end.y,ux:dx/part,uy:dy/part};
  }

  function prefixTo(points,targetDistance){
    const result=[points[0]];
    let travelled=0;
    for(let index=1;index<points.length;index+=1){
      const start=points[index-1],end=points[index];
      const part=Math.hypot(end.x-start.x,end.y-start.y);
      if(part<.001)continue;
      if(travelled+part<=targetDistance){result.push(end);travelled+=part;continue}
      const ratio=Math.max(0,Math.min(1,(targetDistance-travelled)/part));
      result.push({x:start.x+(end.x-start.x)*ratio,y:start.y+(end.y-start.y)*ratio});
      break;
    }
    return result;
  }

  const pathData=points=>points.length?`M ${points.map(point=>`${point.x.toFixed(3)} ${point.y.toFixed(3)}`).join(" L ")}`:"";

  function segmentsFor(demo){
    return Array.from(demo.querySelectorAll(".writing-stroke")).map(path=>{
      const points=JSON.parse(path.dataset.writingPoints||"[]").map(([x,y])=>({x:Number(x),y:Number(y)}));
      return{path,points,start:points[0],end:points.at(-1),length:lengthOf(points),characterIndex:Number(path.dataset.characterIndex)};
    }).filter(segment=>segment.points.length>1&&segment.length>.01);
  }

  function timelineFor(segments){
    const timeline=[];
    let totalDuration=0,previous=null;
    segments.forEach((segment,index)=>{
      const next=segments[index+1];
      if(previous){
        const travel=Math.hypot(segment.start.x-previous.end.x,segment.start.y-previous.end.y);
        if(travel>1.4){
          const duration=Math.max(.18,travel/LIFT_UNITS_PER_SECOND);
          timeline.push({type:"lift",startTime:totalDuration,endTime:totalDuration+duration,from:previous.end,to:segment.start});
          totalDuration+=duration;
        }
      }
      const drawDuration=Math.max(.12,segment.length/DRAW_UNITS_PER_SECOND);
      segment.startTime=totalDuration;
      segment.endTime=totalDuration+drawDuration;
      timeline.push({type:"draw",startTime:segment.startTime,endTime:segment.endTime,segment});
      totalDuration+=drawDuration;
      if(next&&next.characterIndex!==segment.characterIndex){
        timeline.push({type:"pause",startTime:totalDuration,endTime:totalDuration+LETTER_PAUSE_SECONDS,point:segment.end});
        totalDuration+=LETTER_PAUSE_SECONDS;
      }
      previous=segment;
    });
    const scale=totalDuration>0?TARGET_DRAW_SECONDS/totalDuration:1;
    timeline.forEach(step=>{step.startTime*=scale;step.endTime*=scale});
    segments.forEach(segment=>{segment.startTime*=scale;segment.endTime*=scale});
    return{timeline,totalDuration:totalDuration*scale};
  }

  function setPen(pen,point,lifted=false){
    if(!pen||!point)return;
    const angle=Math.atan2(point.uy||0,point.ux||1)*180/Math.PI;
    pen.style.display="";
    pen.classList.toggle("is-lifted",lifted);
    pen.setAttribute("transform",`translate(${point.x.toFixed(3)} ${point.y.toFixed(3)}) rotate(${angle.toFixed(3)})`);
  }

  function showFull(demo,segments){
    segments.forEach(segment=>{segment.path.setAttribute("d",pathData(segment.points));segment.path.style.opacity="1"});
    const pen=demo.querySelector("[data-writing-pen]");
    if(pen)pen.style.display="none";
  }

  function applyFrame(demo,segments,data,elapsed){
    const active=data.timeline.find(step=>elapsed>=step.startTime&&elapsed<=step.endTime);
    segments.forEach(segment=>{
      if(elapsed<=segment.startTime){segment.path.setAttribute("d",`M ${segment.start.x.toFixed(3)} ${segment.start.y.toFixed(3)}`);segment.path.style.opacity="0";return}
      if(elapsed>=segment.endTime){segment.path.setAttribute("d",pathData(segment.points));segment.path.style.opacity="1";return}
      const progress=Math.max(0,Math.min(1,(elapsed-segment.startTime)/Math.max(.0001,segment.endTime-segment.startTime)));
      const visible=prefixTo(segment.points,segment.length*progress);
      segment.path.setAttribute("d",pathData(visible));
      segment.path.style.opacity="1";
    });
    const pen=demo.querySelector("[data-writing-pen]");
    if(active?.type==="draw"){
      const progress=Math.max(0,Math.min(1,(elapsed-active.startTime)/Math.max(.0001,active.endTime-active.startTime)));
      setPen(pen,pointAt(active.segment.points,active.segment.length*progress),false);
    }else if(active?.type==="lift"){
      const progress=Math.max(0,Math.min(1,(elapsed-active.startTime)/Math.max(.0001,active.endTime-active.startTime)));
      const dx=active.to.x-active.from.x,dy=active.to.y-active.from.y;
      setPen(pen,{x:active.from.x+dx*progress,y:active.from.y+dy*progress-Math.sin(progress*Math.PI)*LIFT_HEIGHT,ux:dx,uy:dy},true);
    }else if(active?.type==="pause")setPen(pen,{...active.point,ux:1,uy:0},false);
  }

  function play(demo){
    const segments=segmentsFor(demo);
    if(!segments.length)return;
    const previousFrame=activeFrames.get(demo);
    if(previousFrame)cancelAnimationFrame(previousFrame);
    (activeTimers.get(demo)||[]).forEach(clearTimeout);
    activeTimers.delete(demo);
    demo.classList.remove("is-fading");
    demo.classList.add("is-playing");
    const data=timelineFor(segments);
    const startedAt=performance.now();
    applyFrame(demo,segments,data,0);
    const step=timestamp=>{
      const elapsed=Math.max(0,(timestamp-startedAt)/1000);
      applyFrame(demo,segments,data,elapsed);
      if(elapsed<data.totalDuration){activeFrames.set(demo,requestAnimationFrame(step));return}
      activeFrames.delete(demo);
      showFull(demo,segments);
      demo.classList.remove("is-playing");
      const timers=[];
      timers.push(setTimeout(()=>{
        demo.classList.add("is-fading");
        timers.push(setTimeout(()=>play(demo),FADE_MS));
      },COMPLETE_HOLD_MS));
      activeTimers.set(demo,timers);
    };
    activeFrames.set(demo,requestAnimationFrame(step));
  }

  document.querySelectorAll("[data-writing-demo]").forEach(demo=>{
    const segments=segmentsFor(demo);
    showFull(demo,segments);
    if(demo.hasAttribute("data-writing-autoplay")&&!matchMedia("(prefers-reduced-motion: reduce)").matches){
      requestAnimationFrame(()=>play(demo));
    }
  });
})();
