import { useState, useEffect, useMemo } from "react";
import { api, devApi } from "../api/client";
import { Card, Alert, Btn, SkeletonTable, Badge, SECTION_PALETTE } from "../components/ui";

const TIER_COLORS = ["purple","teal","amber","coral","pink","blue","gray"];
const tierColor = (t) => TIER_COLORS[(t - 1) % TIER_COLORS.length];

function exportCSV(students) {
  const header = ["Rank","Tier","Rank Points","Enrollment","Name","CGPA","Section"];
  const rows = students.map(s => [s.rank,s.tier,s.rank_points,s.enrollment,`"${s.name}"`,s.cgpa,s.section||""]);
  const csv = [header,...rows].map(r=>r.join(",")).join("\n");
  const a = Object.assign(document.createElement("a"),{href:URL.createObjectURL(new Blob([csv],{type:"text/csv"})),download:"fairsplit_ranks.csv"});
  a.click();
}

const SortTh = ({ label, k, sortKey, sortAsc, onSort }) => (
  <th onClick={() => onSort(k)} style={{padding:"9px 12px",textAlign:"left",fontWeight:500,
    color:sortKey===k?"var(--color-text-primary)":"var(--color-text-secondary)",
    fontSize:12,cursor:"pointer",userSelect:"none",whiteSpace:"nowrap"}}>
    {label}{sortKey===k?(sortAsc?" ↑":" ↓"):""}
  </th>
);

export default function RankDashboard() {
  const [students,setStudents]     = useState([]);
  const [loading,setLoading]       = useState(true);
  const [error,setError]           = useState("");
  const [success,setSuccess]       = useState("");
  const [search,setSearch]         = useState("");
  const [sortKey,setSortKey]       = useState("rank");
  const [sortAsc,setSortAsc]       = useState(true);
  const [jsonFile,setJsonFile]     = useState(null);
  const [ingesting,setIngesting]   = useState(false);
  const [dummyLoading,setDummy]    = useState(false);
  const [page,setPage]             = useState(0);
  const PG = 50;

  useEffect(() => {
    api.getStudents().then(d=>setStudents(d.students)).catch(()=>{}).finally(()=>setLoading(false));
  }, []);

  const handleIngest = async () => {
    if (!jsonFile) return;
    setIngesting(true); setError(""); setSuccess("");
    try {
      const r = await api.ingestJson(jsonFile);
      const d = await api.getStudents();
      setStudents(d.students); setPage(0);
      setSuccess(`Loaded ${r.total_students} students.`);
    } catch(e){setError(e.message);}
    finally{setIngesting(false);}
  };

  const handleDummy = async () => {
    setDummy(true); setError(""); setSuccess("");
    try {
      const r = await devApi.loadDummy(576,42);
      const d = await api.getStudents();
      setStudents(d.students); setPage(0);
      setSuccess(`Loaded ${r.total_students} dummy students.`);
    } catch(e){setError(e.message);}
    finally{setDummy(false);}
  };

  const handleSort = (k) => { if(sortKey===k)setSortAsc(a=>!a); else{setSortKey(k);setSortAsc(true);} setPage(0); };

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const list = q ? students.filter(s=>s.name.toLowerCase().includes(q)||s.enrollment.includes(q)||(s.section||"").toLowerCase().includes(q)) : students;
    return [...list].sort((a,b)=>{
      let va=a[sortKey],vb=b[sortKey];
      if(typeof va==="string"){va=va.toLowerCase();vb=vb.toLowerCase();}
      return sortAsc?(va>vb?1:-1):(va<vb?1:-1);
    });
  },[students,search,sortKey,sortAsc]);

  const totalPages = Math.ceil(filtered.length/PG);
  const slice = filtered.slice(page*PG,(page+1)*PG);
  const allocated = students.filter(s=>s.section).length;

  return (
    <div style={{padding:"28px 24px",maxWidth:1100,margin:"0 auto"}}>
      <h1 style={{fontSize:22,fontWeight:500,marginBottom:4}}>Rank dashboard</h1>
      <p style={{color:"var(--color-text-secondary)",fontSize:14,marginBottom:24}}>Upload a JSON file (name, enrollment_number, sgpa) to load student data, or use dummy data.</p>

      <Card style={{marginBottom:20}}>
        <div style={{display:"flex",gap:20,flexWrap:"wrap",alignItems:"flex-end"}}>
          <div>
            <label style={{fontSize:12,color:"var(--color-text-secondary)",display:"block",marginBottom:5}}>Students JSON</label>
            <input type="file" accept=".json" onChange={e=>setJsonFile(e.target.files[0])} style={{fontSize:13}}/>
          </div>
          <Btn onClick={handleIngest} disabled={!jsonFile||ingesting}>{ingesting?"Processing…":"Load data"}</Btn>
          <div style={{borderLeft:"1px solid var(--color-border-tertiary)",paddingLeft:20}}>
            <div style={{fontSize:11,color:"var(--color-text-tertiary)",marginBottom:5}}>Dev mode</div>
            <Btn variant="ghost" onClick={handleDummy} disabled={dummyLoading}>{dummyLoading?"Generating…":"Load 576 dummy students"}</Btn>
          </div>
        </div>
      </Card>

      {error&&<Alert type="error">{error}</Alert>}
      {success&&<Alert type="success">{success}</Alert>}

      {students.length>0&&(
        <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:20}}>
          {[{l:"Total students",v:students.length},{l:"Tiers",v:Math.ceil(students.length/5)},{l:"Allocated",v:allocated||"—"}].map(({l,v})=>(
            <div key={l} style={{flex:"1 1 110px",background:"var(--color-background-secondary)",border:"1px solid var(--color-border-tertiary)",borderRadius:10,padding:"12px 16px"}}>
              <div style={{fontSize:22,fontWeight:500}}>{v}</div>
              <div style={{fontSize:12,color:"var(--color-text-secondary)"}}>{l}</div>
            </div>
          ))}
          {allocated>0&&["A","B","C","D","E"].map(n=>(
            <div key={n} style={{flex:"1 1 80px",background:SECTION_PALETTE[n].bg,border:`1px solid ${SECTION_PALETTE[n].border}`,borderRadius:10,padding:"12px 16px"}}>
              <div style={{fontSize:22,fontWeight:500,color:SECTION_PALETTE[n].text}}>{students.filter(s=>s.section===n).length}</div>
              <div style={{fontSize:12,color:SECTION_PALETTE[n].text,opacity:.8}}>Sec {n}</div>
            </div>
          ))}
        </div>
      )}

      {students.length>0&&(
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10,gap:10,flexWrap:"wrap"}}>
          <span style={{fontSize:13,color:"var(--color-text-secondary)"}}>{filtered.length} of {students.length} students</span>
          <div style={{display:"flex",gap:8}}>
            <input placeholder="Search name or enrollment…" value={search} onChange={e=>{setSearch(e.target.value);setPage(0);}}
              style={{padding:"7px 12px",borderRadius:8,border:"1px solid var(--color-border-secondary)",fontSize:13,
              background:"var(--color-background-primary)",color:"var(--color-text-primary)",width:210}}/>
            <Btn variant="secondary" size="sm" onClick={()=>exportCSV(students)}>Export CSV</Btn>
          </div>
        </div>
      )}

      {loading ? (
        <Card><SkeletonTable rows={10} cols={7}/></Card>
      ) : students.length>0 ? (
        <>
          <div style={{overflowX:"auto",border:"1px solid var(--color-border-tertiary)",borderRadius:10}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
              <thead style={{background:"var(--color-background-secondary)"}}>
                <tr>
                  {[["Rank","rank"],["Tier","tier"],["Pts","rank_points"],["Enrollment","enrollment"],["Name","name"],["CGPA","cgpa"],["Section","section"]].map(([l,k])=>(
                    <SortTh key={k} label={l} k={k} sortKey={sortKey} sortAsc={sortAsc} onSort={handleSort}/>
                  ))}
                </tr>
              </thead>
              <tbody>
                {slice.map((s,i)=>(
                  <tr key={s.enrollment} style={{borderTop:"1px solid var(--color-border-tertiary)",
                    background:i%2===0?"transparent":"var(--color-background-secondary)"}}>
                    <td style={{padding:"8px 12px",fontWeight:500}}>{s.rank}</td>
                    <td style={{padding:"8px 12px"}}><Badge color={tierColor(s.tier)}>T{s.tier}</Badge></td>
                    <td style={{padding:"8px 12px",color:"var(--color-text-secondary)"}}>{s.rank_points}</td>
                    <td style={{padding:"8px 12px",fontFamily:"monospace",fontSize:12}}>{s.enrollment}</td>
                    <td style={{padding:"8px 12px"}}>{s.name}</td>
                    <td style={{padding:"8px 12px",fontWeight:500}}>{s.cgpa}</td>
                    <td style={{padding:"8px 12px"}}>
                      {s.section
                        ? <Badge color={["teal","purple","amber","coral","pink"]["ABCDE".indexOf(s.section)]||"gray"}>Sec {s.section}</Badge>
                        : <span style={{color:"var(--color-text-tertiary)"}}>—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages>1&&(
            <div style={{display:"flex",gap:6,justifyContent:"center",marginTop:16,alignItems:"center"}}>
              <Btn variant="secondary" size="sm" onClick={()=>setPage(p=>Math.max(0,p-1))} disabled={page===0}>← Prev</Btn>
              <span style={{fontSize:13,color:"var(--color-text-secondary)",padding:"0 8px"}}>Page {page+1} of {totalPages}</span>
              <Btn variant="secondary" size="sm" onClick={()=>setPage(p=>Math.min(totalPages-1,p+1))} disabled={page>=totalPages-1}>Next →</Btn>
            </div>
          )}
        </>
      ) : (
        <Card style={{textAlign:"center",padding:"48px 24px"}}>
          <p style={{fontSize:13,color:"var(--color-text-tertiary)"}}>No data loaded. Upload files or click "Load 576 dummy students" above.</p>
        </Card>
      )}
    </div>
  );
}
