import { useState, useEffect, useCallback, useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap, Handle, Position, BackgroundVariant, MarkerType } from "@xyflow/react";
import type { Node, Edge, NodeProps } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion, AnimatePresence } from "framer-motion";
import { components, nodePositions, statusColors, typeIcons } from "./data/mockData";
import type { Component, Status } from "./data/mockData";

const sLabel: Record<Status,string> = {ok:"Healthy",warning:"Degraded",critical:"Critical",offline:"Offline"};
const sBg: Record<Status,string> = {ok:"#f0fdf4",warning:"#fffbeb",critical:"#fef2f2",offline:"#f8fafc"};
const sTxt: Record<Status,string> = {ok:"#15803d",warning:"#b45309",critical:"#b91c1c",offline:"#64748b"};
const Dot = ({status,size=8}:{status:Status;size?:number}) => (
  <span style={{position:"relative",display:"inline-flex",alignItems:"center",justifyContent:"center",width:size,height:size,flexShrink:0}}>
    {status!=="ok" && <span style={{position:"absolute",inset:-3,borderRadius:"50%",background:statusColors[status],opacity:0.18,animation:"sdot 2s ease infinite"}} />}
    <span style={{width:size,height:size,borderRadius:"50%",background:statusColors[status],display:"block"}} />
  </span>
);
const ComponentNode = ({data}:NodeProps) => {
  const comp = data.component as Component;
  if (!comp) return null;
  const sc = statusColors[comp.status] || '#94a3b8';
  return (
    <motion.div whileHover={{y:-2,boxShadow:"0 4px 6px rgba(0,0,0,0.05),0 12px 32px rgba(0,0,0,0.09)"}} transition={{duration:0.15}}
      onClick={()=>(data.onSelect as (c:Component)=>void)(comp)}
      style={{width:300,background:"white",borderRadius:12,border:"1px solid #e5e7eb",boxShadow:"0 1px 2px rgba(0,0,0,0.04),0 4px 16px rgba(0,0,0,0.05)",cursor:"pointer",overflow:"hidden"}}>
      <Handle type="target" position={Position.Top} style={{background:sc,border:"2px solid white",width:9,height:9,top:-4}} />
      <Handle type="source" position={Position.Bottom} style={{background:sc,border:"2px solid white",width:9,height:9,bottom:-4}} />
      <div style={{height:4,background:sc,width:"100%"}} />
      <div style={{padding:"20px 22px 20px"}}>
        <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:10}}>
          <div style={{width:42,height:42,borderRadius:12,background:"#f3f4f6",display:"flex",alignItems:"center",justifyContent:"center",fontSize:20,flexShrink:0}}>{typeIcons[comp.type]}</div>
          <div style={{flex:1,minWidth:0}}>
            <div style={{fontSize:16,fontWeight:600,color:"#111827",letterSpacing:"-0.025em",lineHeight:1.3}}>{comp.name}</div>
            <div style={{fontSize:11,color:"#9ca3af",fontFamily:"JetBrains Mono,monospace",textTransform:"uppercase",letterSpacing:"0.06em",marginTop:3}}>{comp.type}</div>
          </div>
          <div style={{fontSize:10,fontWeight:600,background:sBg[comp.status],color:sTxt[comp.status],borderRadius:20,padding:"4px 10px",border:"1px solid "+sc+"40",whiteSpace:"nowrap",flexShrink:0,display:"flex",alignItems:"center",gap:4}}>
            <Dot status={comp.status} size={5} />{sLabel[comp.status]}
          </div>
        </div>
        <div style={{height:1,background:"#f1f2f5",margin:"16px 0"}} />
        <div style={{display:"flex",gap:0}}>
          {(comp.metrics||[]).slice(0,3).map((m,i)=>(
            <div key={m.label} style={{flex:1,paddingLeft:i>0?18:0,paddingRight:4,borderLeft:i>0?"1px solid #eff0f2":"none"}}>
              <div style={{fontSize:10,color:"#9ca3af",textTransform:"uppercase",letterSpacing:"0.07em",fontFamily:"JetBrains Mono,monospace",fontWeight:500,marginBottom:5}}>{m.label}</div>
              <div style={{fontSize:18,fontWeight:700,color:"#111827",fontFamily:"JetBrains Mono,monospace",letterSpacing:"-0.025em",lineHeight:1}}>{m.value}{m.unit&&<span style={{fontSize:9,color:"#9ca3af",marginLeft:2,fontWeight:400}}>{m.unit}</span>}</div>
            </div>
          ))}
        </div>
        <div style={{marginTop:18,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
          <span style={{fontSize:10,color:"#d1d5db",fontFamily:"JetBrains Mono,monospace"}}>&#8635; {comp.lastChecked}</span>
          <span style={{fontSize:10,color:"#6b7280"}}>{(comp.subComponents||[]).length} services</span>
        </div>
      </div>
    </motion.div>
  );
};
const DetailPanel = ({comp,onClose}:{comp:Component;onClose:()=>void}) => {
  const sc = statusColors[comp.status];
  return (
    <motion.div initial={{x:380,opacity:0}} animate={{x:0,opacity:1}} exit={{x:380,opacity:0}} transition={{type:"spring",damping:30,stiffness:240}}
      style={{position:"absolute",right:0,top:0,bottom:0,width:380,background:"white",borderLeft:"1px solid #e5e7eb",boxShadow:"-8px 0 32px rgba(0,0,0,0.07)",zIndex:10,overflowY:"auto"}}>
      <div style={{borderBottom:"1px solid #f3f4f6",padding:"20px 24px"}}>
        <div style={{display:"flex",alignItems:"flex-start",justifyContent:"space-between",gap:12}}>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <div style={{width:44,height:44,borderRadius:10,background:"#f3f4f6",display:"flex",alignItems:"center",justifyContent:"center",fontSize:22,flexShrink:0}}>{typeIcons[comp.type]}</div>
            <div>
              <div style={{fontSize:18,fontWeight:700,color:"#111827",letterSpacing:"-0.025em"}}>{comp.name}</div>
              <div style={{fontSize:11,color:"#6b7280",marginTop:3}}>{comp.description}</div>
            </div>
          </div>
          <button onClick={onClose} style={{width:28,height:28,border:"1px solid #e5e7eb",borderRadius:8,background:"white",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",color:"#9ca3af",fontSize:14,flexShrink:0}}>&#x2715;</button>
        </div>
        <div style={{marginTop:14,display:"inline-flex",alignItems:"center",gap:6,background:sBg[comp.status],color:sTxt[comp.status],border:"1px solid "+sc+"40",borderRadius:20,padding:"5px 12px",fontSize:12,fontWeight:600}}>
          <Dot status={comp.status} size={7} />{sLabel[comp.status]}{comp.uptime&&<span style={{color:"#9ca3af",fontWeight:400,marginLeft:4}}>&#183; up {comp.uptime}</span>}
        </div>
      </div>
      <div style={{padding:"20px 24px"}}>
        <div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:12}}>Metrics</div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:24}}>
          {comp.metrics.map(m=>(
            <div key={m.label} style={{background:"#f9fafb",border:"1px solid #f3f4f6",borderRadius:10,padding:"12px 14px"}}>
              <div style={{fontSize:10,color:"#9ca3af",textTransform:"uppercase",letterSpacing:"0.08em",fontFamily:"JetBrains Mono,monospace",fontWeight:500,marginBottom:5}}>{m.label}</div>
              <div style={{fontSize:20,fontWeight:800,color:"#111827",fontFamily:"JetBrains Mono,monospace",letterSpacing:"-0.03em"}}>{m.value}{m.unit&&<span style={{fontSize:11,color:"#9ca3af",marginLeft:3,fontWeight:400}}>{m.unit}</span>}</div>
            </div>
          ))}
        </div>
        <div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:12}}>Services</div>
        <div style={{display:"flex",flexDirection:"column",gap:6,marginBottom:24}}>
          {comp.subComponents.map(s=>(
            <div key={s.id} style={{display:"flex",alignItems:"flex-start",gap:10,padding:"11px 14px",background:"#f9fafb",border:"1px solid #f3f4f6",borderRadius:10}}>
              <Dot status={s.status} size={7} />
              <div>
                <div style={{fontSize:13,fontWeight:600,color:"#111827",marginBottom:2}}>{s.name}</div>
                <div style={{fontSize:11,color:"#6b7280",fontFamily:"JetBrains Mono,monospace",lineHeight:1.4}}>{s.detail}</div>
              </div>
            </div>
          ))}
        </div>
        {(comp.connects||[]).length>0&&<><div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:12}}>Connections</div>
        <div style={{display:"flex",flexWrap:"wrap",gap:6}}>{(comp.connects||[]).map(x=>(<span key={x} style={{fontSize:11,background:"#f3f4f6",border:"1px solid #e5e7eb",borderRadius:6,padding:"4px 10px",color:"#374151",fontFamily:"JetBrains Mono,monospace"}}>{typeIcons[x]||"○"} {x}</span>))}</div></>}
      </div>
    </motion.div>
  );
};
const Header = () => {
  const healthy = components.filter(c=>c.status==="ok").length;
  const warnings = components.filter(c=>c.status==="warning").length;
  const critical = components.filter(c=>c.status==="critical").length;
  return (
    <div style={{height:60,background:"white",borderBottom:"1px solid #e5e7eb",display:"flex",alignItems:"center",padding:"0 24px",gap:20,flexShrink:0,zIndex:20,position:"relative"}}>
      <style>{`@keyframes sdot{0%,100%{opacity:1}50%{opacity:0.4}}`}</style>
      <div style={{display:"flex",alignItems:"center",gap:9}}>
        <div style={{width:32,height:32,borderRadius:8,background:"#111827",display:"flex",alignItems:"center",justifyContent:"center",color:"white",fontSize:15}}>&#x2B21;</div>
        <span style={{fontSize:14,fontWeight:700,color:"#111827",letterSpacing:"-0.02em"}}>OriginClaw</span>
        <span style={{fontSize:12,color:"#9ca3af",fontWeight:400}}>Monitor</span>
      </div>
      <div style={{width:1,height:24,background:"#e5e7eb"}} />
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        <div style={{width:26,height:26,borderRadius:6,background:"#f3f4f6",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:"#374151"}}>W</div>
        <span style={{fontSize:13,fontWeight:500,color:"#374151"}}>Wayne Bos</span>
        <span style={{fontSize:11,color:"#9ca3af"}}>/ openclaw.local</span>
      </div>
      <div style={{width:1,height:24,background:"#e5e7eb"}} />
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        <span style={{fontSize:12,background:"#f0fdf4",color:"#15803d",border:"1px solid #bbf7d0",borderRadius:20,padding:"3px 10px",fontWeight:600}}>{healthy} healthy</span>
        {warnings>0&&<span style={{fontSize:12,background:"#fffbeb",color:"#b45309",border:"1px solid #fde68a",borderRadius:20,padding:"3px 10px",fontWeight:600}}>{warnings} warning</span>}
        {critical>0&&<span style={{fontSize:12,background:"#fef2f2",color:"#b91c1c",border:"1px solid #fecaca",borderRadius:20,padding:"3px 10px",fontWeight:600}}>{critical} critical</span>}
      </div>
      <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:14}}>
        <div style={{display:"flex",alignItems:"center",gap:6,fontSize:12,color:"#15803d",fontWeight:500}}>
          <div style={{width:7,height:7,borderRadius:"50%",background:"#10b981",animation:"sdot 2s ease infinite"}} />Live
        </div>
        <span style={{fontSize:12,color:"#9ca3af",fontFamily:"JetBrains Mono,monospace"}}>{new Date().toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit",hour12:false})}</span>
      </div>
    </div>
  );
};
const nodeTypes = {component:ComponentNode};
export default function App() {
  const [selected,setSelected] = useState<Component|null>(null);
  const [hoveredId, setHoveredId] = useState<string|null>(null);
  const [nodePosOverrides, setNodePosOverrides] = useState<Record<string,{x:number,y:number}>>({});
  const [live, setLive] = useState<Component[]>([]);

  const fetchLive = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8787/api/status', {cache: 'no-store'});
      if (!res.ok) return;
      const d = await res.json();
      if (d.components?.length) {
        setLive(prev => {
          if (prev.length === 0) return d.components;
          const changed = d.components.some((nc: Component, i: number) =>
            prev[i]?.status !== nc.status
          );
          return changed ? d.components : prev;
        });
      }
    } catch {}
  }, []);

  useEffect(() => { fetchLive(); const t = setInterval(fetchLive, 60000); return () => clearInterval(t); }, [fetchLive]);

  const active = live.length > 0 ? live : components;
  const nodes:Node[] = active.map(comp=>({id:comp.id,type:"component",position:nodePosOverrides[comp.id]||nodePositions[comp.id]||{x:(active.indexOf(comp)%3)*340+80,y:Math.floor(active.indexOf(comp)/3)*280+80},data:{component:comp,onSelect:setSelected,onHover:setHoveredId,hoveredId},draggable:true}));
  const edges:Edge[] = useMemo(() => active.flatMap(comp=>(comp.connects||[]).map(target=>({id:comp.id+"-"+target,source:comp.id,target,type:"smoothstep",markerEnd:{type:MarkerType.ArrowClosed,width:10,height:10,color:"#d1d5db"},style:{stroke:comp.status!=="ok"?statusColors[comp.status]+"99":"#d1d5db",strokeWidth:1.5,strokeDasharray:comp.status!=="ok"?"5 3":undefined},animated:comp.status!=="ok"}))
  ).filter((e,i,arr)=>arr.findIndex(x=>x.id===e.id)===i), [active, hoveredId]);
  return (
    <div style={{display:"flex",flexDirection:"column",height:"100vh",background:"#f9fafb",transition:"opacity 0.1s ease"}}>
      <Header />
      <div style={{flex:1,position:"relative"}}>
        <ReactFlow key="canvas" nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{padding:0.12}} minZoom={0.25} maxZoom={2} proOptions={{hideAttribution:true}} nodesDraggable={true} elementsSelectable={true}
          onNodeDragStop={(_evt, node) => setNodePosOverrides(prev => ({...prev, [node.id]: node.position}))}>
          <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#e5e7eb" />
          <Controls />
          <MiniMap nodeColor={n=>statusColors[(n.data?.component as Component)?.status||"offline"]} maskColor="rgba(249,250,251,0.8)" style={{border:"1px solid #e5e7eb",borderRadius:10}} />
        </ReactFlow>
        <AnimatePresence>{selected&&<DetailPanel comp={selected} onClose={()=>setSelected(null)} />}</AnimatePresence>
      </div>
    </div>
  );
}
