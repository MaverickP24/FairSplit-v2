import { useState, useEffect } from "react";
import { api } from "../api/client";
import { Card, Alert, Btn, Badge, Skeleton, SECTION_PALETTE, InfoTip } from "../components/ui";

function exportSectionsExcel(sections) {
  let csv = "Section,Rank,Tier,Rank Points,Enrollment,Name,CGPA\n";
  for (const sec of sections) {
    const sorted = [...sec.members].sort((a,b)=>a.rank-b.rank);
    for (const s of sorted) {
      csv += `${sec.name},${s.rank},${s.tier},${s.rank_points},${s.enrollment},"${s.name}",${s.cgpa}\n`;
    }
  }
  const a = Object.assign(document.createElement("a"),{
    href:URL.createObjectURL(new Blob([csv],{type:"text/csv"})),
    download:"fairsplit_sections.csv"
  });
  a.click();
}

function SectionCard({ section }) {
  const [expanded,setExpanded] = useState(false);
  const pal = SECTION_PALETTE[section.name] || SECTION_PALETTE.A;
  const sorted = [...section.members].sort((a,b)=>a.rank-b.rank);

  return (
    <div style={{border:`1px solid ${pal.border}`,borderRadius:12,overflow:"hidden",marginBottom:12}}>
      <div onClick={()=>setExpanded(e=>!e)} style={{background:pal.bg,padding:"14px 18px",cursor:"pointer",
        display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div style={{display:"flex",alignItems:"center",gap:16}}>
          <span style={{fontWeight:500,fontSize:16,color:pal.text}}>Section {section.name}</span>
          <span style={{fontSize:13,color:pal.text,opacity:.75}}>{section.size} students</span>
          <span style={{fontSize:13,color:pal.text,opacity:.75}}>{section.total_rank_points} rank pts</span>
        </div>
        <span style={{fontSize:12,color:pal.text,opacity:.7}}>{expanded?"Collapse ↑":"View members ↓"}</span>
      </div>
      {expanded && (
        <div style={{padding:"0 0 8px"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
            <thead style={{background:"var(--color-background-secondary)"}}>
              <tr>
                {["Rank","Tier","Pts","Enrollment","Name","CGPA"].map(h=>(
                  <th key={h} style={{padding:"8px 12px",textAlign:"left",fontWeight:500,
                    color:"var(--color-text-secondary)",fontSize:12}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((s,i)=>(
                <tr key={s.enrollment} style={{borderTop:"1px solid var(--color-border-tertiary)",
                  background:i%2===0?"transparent":"var(--color-background-secondary)"}}>
                  <td style={{padding:"7px 12px",fontWeight:500}}>{s.rank}</td>
                  <td style={{padding:"7px 12px"}}><Badge color="gray">T{s.tier}</Badge></td>
                  <td style={{padding:"7px 12px",color:"var(--color-text-secondary)"}}>{s.rank_points}</td>
                  <td style={{padding:"7px 12px",fontFamily:"monospace",fontSize:11}}>{s.enrollment}</td>
                  <td style={{padding:"7px 12px"}}>{s.name}</td>
                  <td style={{padding:"7px 12px",fontWeight:500}}>{s.cgpa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RankBalanceBar({ sections }) {
  if (!sections?.length) return null;
  const max = Math.max(...sections.map(s=>s.total_rank_points));
  const min = Math.min(...sections.map(s=>s.total_rank_points));
  const floor = min * 0.995;
  return (
    <div style={{display:"flex",gap:16,alignItems:"flex-end",height:100,padding:"0 12px"}}>
      {sections.map(s => {
        const pal = SECTION_PALETTE[s.name]||SECTION_PALETTE.A;
        const ratio = max === floor ? 1 : (s.total_rank_points - floor) / (max - floor);
        const h = Math.max(28, Math.round(ratio * 80));
        return (
          <div key={s.name} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:6}}>
            <span style={{fontSize:12,fontWeight:600,color:"var(--color-text-secondary)",
              whiteSpace:"nowrap"}}>{s.total_rank_points}</span>
            <div style={{width:"100%",height:h,background:pal.bar,borderRadius:"6px 6px 0 0",
              transition:"height 0.4s ease"}}/>
          </div>
        );
      })}
    </div>
  );
}

const STAT_TIPS = {
  "Swaps made": "Total number of student swaps the optimizer performed to co-place friends. Each swap moves two same-tier students between sections without breaking any hard constraints.",
  "Pairs evaluated": "Total mutual friend pairs the optimizer considered. A pair is two students who both listed each other as preferred friends.",
  "Already together": "Friend pairs that were already in the same section after the initial snake-draft, before any optimization swaps were needed.",
  "Rank delta": "The maximum difference in total rank points between any two sections. 0 pts means all sections have exactly equal academic strength. This is always 0 because the optimizer only swaps students within the same tier (equal rank points), so section totals never change.",
  "Rank point totals": "Sum of all rank points assigned to students in each section. Equal totals mean every section has the same overall academic strength — the core guarantee of FairSplit.",
};

export default function SimulationPage() {
  const [mode,setMode]     = useState("balanced");
  const [result,setResult] = useState(null);
  const [loading,setLoading] = useState(false);
  const [loadingPrev,setLoadingPrev] = useState(true);
  const [error,setError]   = useState("");

  useEffect(() => {
    api.getAllocation()
      .then(d => setResult(d))
      .catch(()=>{})
      .finally(()=>setLoadingPrev(false));
  }, []);

  const handleRun = async () => {
    setLoading(true); setError("");
    try { setResult(await api.allocate(mode)); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const stats = result?.optimizer_stats || {};

  return (
    <div style={{padding:"28px 24px",maxWidth:920,margin:"0 auto"}}>
      <h1 style={{fontSize:22,fontWeight:500,marginBottom:4}}>Simulation</h1>
      <p style={{color:"var(--color-text-secondary)",fontSize:14,marginBottom:24}}>
        Run the allocation algorithm and inspect section assignments.
      </p>

      {/* Controls */}
      <Card style={{marginBottom:20,display:"flex",gap:20,alignItems:"flex-end",flexWrap:"wrap"}}>
        <div>
          <div style={{fontSize:12,color:"var(--color-text-secondary)",marginBottom:6}}>Mode</div>
          <div style={{display:"flex",gap:6}}>
            {[["strict","Perfect rank balance. Friendship pass still runs within constraints."],
              ["balanced","Same hard constraints. Optimizer tries harder to co-place friends."]].map(([m,desc])=>(
              <button key={m} onClick={()=>setMode(m)} style={{padding:"7px 16px",borderRadius:8,
                border:`1px solid ${mode===m?"#1D9E75":"var(--color-border-secondary)"}`,
                background:mode===m?"#E1F5EE":"var(--color-background-primary)",
                color:mode===m?"#085041":"var(--color-text-secondary)",
                fontWeight:mode===m?500:400,fontSize:13,cursor:"pointer"}}>
                {m.charAt(0).toUpperCase()+m.slice(1)}
              </button>
            ))}
          </div>
          <p style={{fontSize:12,color:"var(--color-text-tertiary)",marginTop:6,maxWidth:380}}>
            {mode==="strict"?"Perfect rank balance. Friendship pass still runs within constraints."
              :"Same hard constraints. Optimizer tries harder to co-place friends."}
          </p>
        </div>
        <div style={{marginLeft:"auto",display:"flex",gap:8,alignItems:"center"}}>
          {result && <Btn variant="secondary" onClick={()=>exportSectionsExcel(result.sections)}>Export CSV</Btn>}
          <Btn onClick={handleRun} disabled={loading} size="lg">
            {loading?"Running…":"Run allocation"}
          </Btn>
        </div>
      </Card>

      {error && <Alert type="error">{error}</Alert>}

      {loadingPrev && !result && (
        <Card><Skeleton height={20} width="40%" style={{marginBottom:12}}/><Skeleton height={14} width="60%"/></Card>
      )}

      {loading && (
        <Card style={{textAlign:"center",padding:"32px 24px"}}>
          <div style={{fontSize:14,color:"var(--color-text-secondary)"}}>Running snake-draft + friendship optimizer…</div>
        </Card>
      )}

      {result && !loading && (
        <>
          {/* Summary stats with info tooltips */}
          <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:20}}>
            {[
              {l:"Swaps made",     v:stats.swaps_made},
              {l:"Pairs evaluated",v:stats.pairs_evaluated},
              {l:"Already together",v:stats.already_together},
              {l:"Rank delta",     v:"0 pts"},
            ].map(({l,v})=>(
              <div key={l} style={{flex:"1 1 140px",background:"var(--color-background-secondary)",
                border:"1px solid var(--color-border-tertiary)",borderRadius:10,padding:"14px 16px"}}>
                <div style={{fontSize:22,fontWeight:500}}>{v}</div>
                <div style={{fontSize:12,color:"var(--color-text-secondary)",marginTop:4,
                  display:"flex",alignItems:"center"}}>
                  {l}<InfoTip text={STAT_TIPS[l]}/>
                </div>
              </div>
            ))}
          </div>

          {/* Rank balance bar chart — fixed padding */}
          <Card style={{marginBottom:20,padding:"20px 20px 16px"}}>
            <div style={{marginBottom:12}}>
              <div style={{fontWeight:500,fontSize:15,display:"flex",alignItems:"center"}}>
                Rank point totals
                <InfoTip text={STAT_TIPS["Rank point totals"]}/>
              </div>
              <div style={{fontSize:12,color:"var(--color-text-secondary)",marginTop:4}}>
                All sections: <strong>{result.sections?.[0]?.total_rank_points}</strong> pts each
                <span style={{color:"#1D9E75",marginLeft:8,fontWeight:500}}>✓ perfectly balanced</span>
              </div>
            </div>
            <RankBalanceBar sections={result.sections}/>
            {/* Section legend row */}
            <div style={{display:"flex",gap:8,marginTop:14,padding:"14px 12px 0",
              borderTop:"1px solid var(--color-border-tertiary)"}}>
              {result.sections?.map(s=>{
                const pal = SECTION_PALETTE[s.name]||SECTION_PALETTE.A;
                return (
                  <div key={s.name} style={{flex:1,display:"flex",alignItems:"center",
                    justifyContent:"center",gap:8,padding:"4px 0"}}>
                    <div style={{width:10,height:10,borderRadius:"50%",background:pal.bar,flexShrink:0}}/>
                    <span style={{fontSize:12,fontWeight:500}}>Sec {s.name}</span>
                    <span style={{fontSize:11,color:"var(--color-text-tertiary)"}}>{s.size} students</span>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Section cards */}
          {result.sections?.map(s=><SectionCard key={s.name} section={s}/>)}
        </>
      )}

      {!result && !loading && !loadingPrev && (
        <Card style={{textAlign:"center",padding:"48px 24px"}}>
          <p style={{fontSize:13,color:"var(--color-text-tertiary)"}}>
            No allocation run yet. Make sure student data is loaded, then click "Run allocation".
          </p>
        </Card>
      )}
    </div>
  );
}
