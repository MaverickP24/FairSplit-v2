import { useState, useEffect } from "react";
import RankDashboard    from "./pages/RankDashboard";
import SurveyPage       from "./pages/SurveyPage";
import SimulationPage   from "./pages/SimulationPage";
import MetricsDashboard from "./pages/MetricsDashboard";
import { api } from "./api/client";

const PAGES = [
  { id: "rank",       label: "Rank dashboard",  step: 1 },
  { id: "survey",     label: "Survey",           step: 2 },
  { id: "simulation", label: "Simulation",       step: 3 },
  { id: "metrics",    label: "Metrics",          step: 4 },
];

export default function App() {
  const [page, setPage] = useState("rank");
  const [progress, setProgress] = useState({ dataLoaded: false, surveyOpen: false, allocated: false });

  useEffect(() => {
    const check = async () => {
      try {
        const [students, survey, alloc] = await Promise.allSettled([
          api.getStudents(), api.getSurveyStatus(), api.getAllocation(),
        ]);
        setProgress({
          dataLoaded: students.status === "fulfilled" && students.value.total > 0,
          surveyOpen: survey.status === "fulfilled" && survey.value.submitted > 0,
          allocated:  alloc.status === "fulfilled",
        });
      } catch (_) {}
    };
    check();
    const t = setInterval(check, 8000);
    return () => clearInterval(t);
  }, [page]);

  const stepDone = (step) => {
    if (step === 1) return progress.dataLoaded;
    if (step === 2) return progress.surveyOpen;
    return progress.allocated;
  };

  const renderPage = () => {
    switch (page) {
      case "survey":     return <SurveyPage />;
      case "simulation": return <SimulationPage />;
      case "metrics":    return <MetricsDashboard />;
      default:           return <RankDashboard />;
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-background-tertiary,#f5f5f3)" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: var(--font-sans, system-ui, sans-serif); }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
      `}</style>

      <nav style={{
        background: "var(--color-background-primary)",
        borderBottom: "1px solid var(--color-border-tertiary)",
        padding: "0 24px", display: "flex", alignItems: "center", height: 54, gap: 2,
      }}>
        <div style={{ marginRight: 28, display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8, background: "#1D9E75",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "#fff", fontWeight: 600, fontSize: 14,
          }}>F</div>
          <span style={{ fontWeight: 500, fontSize: 15, color: "var(--color-text-primary)" }}>FairSplit</span>
        </div>

        {PAGES.map((p) => {
          const active = page === p.id;
          const done = stepDone(p.step);
          return (
            <button key={p.id} onClick={() => setPage(p.id)} style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "6px 14px", border: "none",
              background: active ? "var(--color-background-secondary)" : "transparent",
              color: active ? "var(--color-text-primary)" : "var(--color-text-secondary)",
              fontWeight: active ? 500 : 400, fontSize: 13, cursor: "pointer",
              borderBottom: active ? "2px solid #1D9E75" : "2px solid transparent",
              borderRadius: active ? "6px 6px 0 0" : 6,
              transition: "color .15s, background .15s",
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
                background: done ? "#1D9E75" : active ? "#888780" : "var(--color-border-secondary)",
                transition: "background .3s",
              }} />
              {p.label}
            </button>
          );
        })}

        <div style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-text-tertiary)", display: "flex", gap: 10 }}>
          {progress.dataLoaded && <span style={{ color: "var(--color-text-success)" }}>✓ Data</span>}
          {progress.surveyOpen && <span style={{ color: "var(--color-text-success)" }}>✓ Survey</span>}
          {progress.allocated  && <span style={{ color: "var(--color-text-success)" }}>✓ Allocated</span>}
          {!progress.dataLoaded && <span>Step 1: load data</span>}
        </div>
      </nav>

      <main>{renderPage()}</main>
    </div>
  );
}
