import { useState, useEffect, useRef } from "react";
import { api, devApi } from "../api/client";
import { Card, Alert, Btn, Badge, Skeleton } from "../components/ui";

// Searchable friend picker row
function FriendRow({ index, onEnrollment, allStudents, selfEnrollment }) {
  const [query,setQuery]     = useState("");
  const [selected,setSelected] = useState(null);
  const [open,setOpen]       = useState(false);
  const [results,setResults] = useState([]);
  const ref = useRef();

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const search = (q) => {
    setQuery(q);
    setSelected(null);
    if (!q.trim()) { setResults([]); setOpen(false); return; }
    const lower = q.toLowerCase();
    const hits = allStudents
      .filter(s => s.enrollment !== selfEnrollment && (
        s.name.toLowerCase().includes(lower) || s.enrollment.includes(q)
      ))
      .slice(0, 8);
    setResults(hits);
    setOpen(hits.length > 0);
  };

  const select = (student) => {
    setQuery(student.name);
    setSelected(student);
    setOpen(false);
    onEnrollment(student.enrollment, student.name);
  };

  const clear = () => {
    setQuery("");
    setSelected(null);
    setResults([]);
    onEnrollment("", "");
  };

  return (
    <div style={{display:"flex",gap:10,alignItems:"center"}}>
      <span style={{minWidth:28,textAlign:"center",fontSize:12,fontWeight:600,
        color:"var(--color-text-on-primary)",background:"var(--color-primary)",
        borderRadius:6,padding:"4px 0",flexShrink:0}}>P{index}</span>
      <div ref={ref} style={{flex:1,position:"relative"}}>
        <div style={{display:"flex",alignItems:"center",gap:4}}>
          <input
            value={query}
            onChange={e => search(e.target.value)}
            onFocus={() => { if (results.length) setOpen(true); }}
            placeholder={`Priority ${index} friend — search by name or enrollment…`}
            style={{flex:1,padding:"7px 12px",borderRadius:8,
              border:"1px solid var(--color-border-secondary)",fontSize:13,
              background:"var(--color-background-primary)",color:"var(--color-text-primary)"}}
          />
          {query && (
            <button onClick={clear} style={{background:"none",border:"none",cursor:"pointer",
              color:"var(--color-text-tertiary)",fontSize:16,padding:"0 4px",lineHeight:1}}>×</button>
          )}
        </div>
        {open && (
          <div style={{position:"absolute",top:"calc(100% + 4px)",left:0,right:0,zIndex:100,
            background:"var(--color-background-primary)",border:"1px solid var(--color-border-secondary)",
            borderRadius:8,overflow:"hidden",boxShadow:"0 4px 16px rgba(0,0,0,.1)"}}>
            {results.map(s => (
              <div key={s.enrollment} onMouseDown={() => select(s)}
                style={{padding:"9px 14px",cursor:"pointer",fontSize:13,
                  borderBottom:"1px solid var(--color-border-tertiary)"}}
                onMouseEnter={e=>e.currentTarget.style.background="var(--color-background-secondary)"}
                onMouseLeave={e=>e.currentTarget.style.background=""}>
                <span style={{fontWeight:500}}>{s.name}</span>
                <span style={{color:"var(--color-text-tertiary)",fontSize:12,marginLeft:8,fontFamily:"monospace"}}>{s.enrollment}</span>
                <span style={{float:"right"}}><Badge color="teal">Rank {s.rank}</Badge></span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SurveyPage() {
  const [enrollment,setEnrollment] = useState("");
  const [verified,setVerified]     = useState(false);
  const [verifying,setVerifying]   = useState(false);
  const [verifyError,setVerifyError] = useState("");
  const [allStudents,setAllStudents] = useState([]);
  const [loadingStudents,setLoadingStudents] = useState(false);

  // prefs: array of {enrollment, name, priority}
  const [prefs,setPrefs] = useState(Array(10).fill(null).map(()=>({enrollment:"",name:""})));
  const [submitting,setSubmitting]   = useState(false);
  const [submitted,setSubmitted]     = useState(false);
  const [submitError,setSubmitError] = useState("");
  const [surveyStatus,setSurveyStatus] = useState(null);
  const [genLoading,setGenLoading]     = useState(false);
  const [genResult,setGenResult]       = useState(null);

  useEffect(() => {
    setLoadingStudents(true);
    api.getStudents()
      .then(d => setAllStudents(d.students))
      .catch(() => {})
      .finally(() => setLoadingStudents(false));
    api.getSurveyStatus().then(setSurveyStatus).catch(()=>{});
  }, []);

  const handleVerify = async () => {
    if (!enrollment.trim()) return;
    setVerifying(true); setVerifyError("");
    try {
      await api.submitSurvey(enrollment.trim(), {});
      setVerified(true);
    } catch(e) { setVerifyError(e.message); }
    finally { setVerifying(false); }
  };

  const updateEnrollment = (idx, enr, name) => {
    setPrefs(p => p.map((x,i) => i===idx ? {...x,enrollment:enr,name} : x));
  };

  const handleSubmit = async () => {
    const preferences = {};
    prefs.forEach((p, idx) => {
      if (p.enrollment && p.enrollment !== enrollment)
        preferences[p.enrollment] = idx + 1; // row position = priority
    });
    if (!Object.keys(preferences).length) {
      setSubmitError("Add at least one friend preference."); return;
    }
    setSubmitting(true); setSubmitError("");
    try {
      await api.submitSurvey(enrollment.trim(), preferences);
      setSubmitted(true);
      const status = await api.getSurveyStatus();
      setSurveyStatus(status);
    } catch(e) { setSubmitError(e.message); }
    finally { setSubmitting(false); }
  };


  const handleGenerateRandom = async () => {
    setGenLoading(true); setGenResult(null);
    try {
      const r = await devApi.generateRandomSurveys();
      setGenResult(r);
      const status = await api.getSurveyStatus();
      setSurveyStatus(status);
    } catch(e) { setGenResult({ error: e.message }); }
    finally { setGenLoading(false); }
  };

  if (submitted) return (
    <div style={{padding:40,maxWidth:560,margin:"0 auto",textAlign:"center"}}>
      <div style={{width:56,height:56,borderRadius:"50%",background:"#E1F5EE",display:"flex",
        alignItems:"center",justifyContent:"center",margin:"0 auto 20px",fontSize:24,color:"#085041"}}>✓</div>
      <h2 style={{fontWeight:500,marginBottom:8}}>Preferences saved</h2>
      <p style={{color:"var(--color-text-secondary)",fontSize:14,lineHeight:1.6}}>
        Your friend preferences have been recorded. The admin will run the allocation after the survey closes.
      </p>
      {surveyStatus && (
        <div style={{marginTop:24,padding:"12px 20px",background:"var(--color-background-secondary)",
          borderRadius:10,border:"1px solid var(--color-border-tertiary)",fontSize:13,color:"var(--color-text-secondary)"}}>
          {surveyStatus.submitted} of {surveyStatus.total_students} students have submitted so far.
        </div>
      )}
    </div>
  );

  return (
    <div style={{padding:"28px 24px",maxWidth:680,margin:"0 auto"}}>
      <h1 style={{fontSize:22,fontWeight:500,marginBottom:4}}>Friend preference survey</h1>
      <p style={{color:"var(--color-text-secondary)",marginBottom:24,fontSize:14}}>
        Search for friends by name and set your priority. Priority 1 = most wanted.
      </p>

      {surveyStatus && (
        <div style={{display:"flex",gap:8,marginBottom:20}}>
          <div style={{flex:1,background:"var(--color-background-secondary)",border:"1px solid var(--color-border-tertiary)",borderRadius:10,padding:"12px 16px"}}>
            <div style={{fontSize:20,fontWeight:500}}>{surveyStatus.submitted}</div>
            <div style={{fontSize:12,color:"var(--color-text-secondary)"}}>Submitted</div>
          </div>
          <div style={{flex:1,background:"var(--color-background-secondary)",border:"1px solid var(--color-border-tertiary)",borderRadius:10,padding:"12px 16px"}}>
            <div style={{fontSize:20,fontWeight:500}}>{surveyStatus.pending}</div>
            <div style={{fontSize:12,color:"var(--color-text-secondary)"}}>Pending</div>
          </div>
          <div style={{flex:1,background:"var(--color-background-secondary)",border:"1px solid var(--color-border-tertiary)",borderRadius:10,padding:"12px 16px"}}>
            <div style={{fontSize:20,fontWeight:500}}>{surveyStatus.total_students}</div>
            <div style={{fontSize:12,color:"var(--color-text-secondary)"}}>Total</div>
          </div>
        </div>
      )}

      {loadingStudents && (
        <Card style={{marginBottom:16}}>
          <Skeleton height={14} width="60%" style={{marginBottom:8}}/>
          <Skeleton height={14} width="40%"/>
        </Card>
      )}

      {/* Dev mode — random survey generation */}
      <div style={{background:"var(--color-background-secondary)",border:"1px dashed var(--color-border-secondary)",
        borderRadius:12,padding:16,marginBottom:20,display:"flex",gap:14,alignItems:"center",flexWrap:"wrap"}}>
        <div style={{flex:1,minWidth:180}}>
          <div style={{fontSize:12,color:"var(--color-text-tertiary)",marginBottom:2}}>Dev mode</div>
          <div style={{fontSize:13,color:"var(--color-text-secondary)"}}>Auto-generate random preferences for all students</div>
        </div>
        <Btn variant="ghost" onClick={handleGenerateRandom} disabled={genLoading}>
          {genLoading ? "Generating…" : "Generate random surveys"}
        </Btn>
        {genResult && !genResult.error && (
          <div style={{fontSize:12,color:"var(--color-text-success)",width:"100%"}}>
            Done — {genResult.submitted} of {genResult.total_students} students assigned preferences.
          </div>
        )}
        {genResult?.error && (
          <div style={{fontSize:12,color:"var(--color-text-danger)",width:"100%"}}>{genResult.error}</div>
        )}
      </div>

      {/* Enrollment verify */}
      {!verified ? (
        <Card style={{marginBottom:24}}>
          <label style={{fontSize:13,fontWeight:500,display:"block",marginBottom:8}}>Your enrollment number</label>
          <div style={{display:"flex",gap:10}}>
            <input value={enrollment} onChange={e=>setEnrollment(e.target.value)}
              onKeyDown={e=>e.key==="Enter"&&handleVerify()}
              placeholder="e.g. 20211001000"
              style={{flex:1,padding:"8px 12px",borderRadius:8,border:"1px solid var(--color-border-secondary)",
                fontSize:14,background:"var(--color-background-primary)",color:"var(--color-text-primary)"}}/>
            <Btn onClick={handleVerify} disabled={verifying||!enrollment.trim()}>
              {verifying?"Checking…":"Verify"}
            </Btn>
          </div>
          {verifyError && <p style={{color:"var(--color-text-danger)",fontSize:13,marginTop:8}}>{verifyError}</p>}
        </Card>
      ) : (
        <Alert type="success" style={{marginBottom:20}}>
          Verified: {enrollment}. Now pick your friends below.
        </Alert>
      )}

      {/* Preference rows */}
      {verified && (
        <>
          <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:24}}>
            {prefs.map((pref,idx) => (
              <FriendRow
                key={idx}
                index={idx+1}
                onEnrollment={(enr,name) => updateEnrollment(idx,enr,name)}
                allStudents={allStudents}
                selfEnrollment={enrollment}
              />
            ))}
          </div>
          {submitError && <Alert type="error">{submitError}</Alert>}
          <Btn size="lg" onClick={handleSubmit} disabled={submitting}>
            {submitting?"Submitting…":"Submit preferences"}
          </Btn>
          <p style={{fontSize:12,color:"var(--color-text-tertiary)",marginTop:10}}>
            Leave rows blank if you have fewer than 10 friends to list.
          </p>
        </>
      )}
    </div>
  );
}
