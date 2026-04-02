import { useState, useEffect } from "react";
import { api } from "../api/client";
import { Card, Alert, Btn, Skeleton, SECTION_PALETTE, InfoTip } from "../components/ui";

const METRIC_TIPS = {
  "Satisfaction score": "Weighted percentage of friend preferences satisfied. Priority 1 friends carry 10x the weight of Priority 10.",
  "At-least-1 friend": "Percentage of students placed with at least one preferred friend.",
  "Isolation rate": "Percentage of students with zero preferred friends in their section. Lower is better.",
  "Avg friends": "Average count of co-placed preferred friends per student.",
  "Rank point balance": "Max rank-point difference between any two sections. Snake-draft guarantees 0.",
};

function CompareBar({ label, value, baseline, unit = "%", higherIsBetter = true }) {
  const diff = baseline !== undefined ? (value - baseline) : null;
  const improved = diff !== null && (higherIsBetter ? diff > 0 : diff < 0);
  const worse    = diff !== null && (higherIsBetter ? diff < 0 : diff > 0);
  const maxVal   = Math.max(value, baseline || 0, 1);

  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ fontSize: 13, fontWeight: 500, display: "flex", alignItems: "center" }}>
          {label}<InfoTip text={METRIC_TIPS[label] || ""} />
        </span>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {diff !== null && (
            <span style={{ fontSize: 12, color: improved ? "var(--color-text-success)" : worse ? "var(--color-text-danger)" : "var(--color-text-secondary)" }}>
              {improved ? "↑" : "↓"} {Math.abs(diff).toFixed(1)}{unit} vs baseline
            </span>
          )}
          <span style={{ fontSize: 16, fontWeight: 500 }}>{value}{unit}</span>
        </div>
      </div>
      <div style={{ height: 10, background: "var(--color-border-tertiary)", borderRadius: 5, overflow: "hidden", marginBottom: 3 }}>
        <div style={{ height: "100%", width: `${(value / maxVal) * 100}%`, background: "#1D9E75", borderRadius: 5, transition: "width .5s" }} />
      </div>
      {baseline !== undefined && (
        <>
          <div style={{ height: 6, background: "var(--color-border-tertiary)", borderRadius: 4, overflow: "hidden", opacity: .5 }}>
            <div style={{ height: "100%", width: `${(baseline / maxVal) * 100}%`, background: "#888780", borderRadius: 4 }} />
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 4, fontSize: 11, color: "var(--color-text-tertiary)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: "#1D9E75", borderRadius: 2, display: "inline-block" }} />FairSplit: {value}{unit}</span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 8, height: 8, background: "#888780", borderRadius: 2, display: "inline-block" }} />Random: {baseline}{unit}</span>
          </div>
        </>
      )}
    </div>
  );
}

function PointsBar({ sectionPoints }) {
  if (!sectionPoints) return null;
  const entries = Object.entries(sectionPoints);
  const max = Math.max(...entries.map(([, v]) => v));
  return (
    <div>
      {entries.map(([name, pts]) => {
        const pal = SECTION_PALETTE[name] || SECTION_PALETTE.A;
        return (
          <div key={name} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <span style={{ width: 18, fontSize: 13, fontWeight: 500, color: pal.text }}>{name}</span>
            <div style={{ flex: 1, height: 20, background: "var(--color-border-tertiary)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${(pts / max) * 100}%`, background: pal.bar, borderRadius: 4 }} />
            </div>
            <span style={{ fontSize: 12, color: "var(--color-text-secondary)", width: 56, textAlign: "right" }}>{pts}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try { setMetrics(await api.getMetrics()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={{ padding: "28px 24px", maxWidth: 900, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 500, marginBottom: 4 }}>Metrics dashboard</h1>
          <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
            How FairSplit compares against purely random assignment.
            {metrics && ` Based on ${metrics.students_with_preferences} students who submitted preferences.`}
          </p>
        </div>
        <Btn variant="secondary" onClick={load} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</Btn>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {loading && !metrics && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><Skeleton height={16} width="50%" style={{ marginBottom: 8 }} /><Skeleton height={10} /><Skeleton height={6} style={{ marginTop: 4, opacity: .5 }} /></Card>
          ))}
        </div>
      )}

      {metrics && !loading && (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
            {[
              { l: "Satisfaction score", v: metrics.satisfaction_score, u: "%", desc: "Weighted friend co-placement" },
              { l: "At-least-1 friend",  v: metrics.at_least_one_rate, u: "%", desc: "Students not alone" },
              { l: "Isolation rate",     v: metrics.isolation_rate, u: "%", desc: "Students with 0 friends" },
              { l: "Avg friends",        v: metrics.avg_friends_per_student, u: "", desc: "Per student in section" },
            ].map(({ l, v, u, desc }) => (
              <div key={l} style={{ flex: "1 1 150px", background: "var(--color-background-secondary)", border: "1px solid var(--color-border-tertiary)", borderRadius: 12, padding: "16px 18px" }}>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: ".04em", marginBottom: 6, display: "flex", alignItems: "center" }}>
                  {l}<InfoTip text={METRIC_TIPS[l]} />
                </div>
                <div style={{ fontSize: 28, fontWeight: 500, letterSpacing: -.5 }}>{v}<span style={{ fontSize: 13, fontWeight: 400, color: "var(--color-text-secondary)" }}>{u}</span></div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>{desc}</div>
              </div>
            ))}
          </div>

          <Card style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 16 }}>FairSplit vs random baseline</div>
            <CompareBar label="Satisfaction score" value={metrics.satisfaction_score} baseline={metrics.baseline_satisfaction_score} higherIsBetter />
            <CompareBar label="Isolation rate" value={metrics.isolation_rate} baseline={metrics.baseline_isolation_rate} higherIsBetter={false} />
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div>
                <div style={{ fontWeight: 500, fontSize: 14, display: "flex", alignItems: "center" }}>
                  Rank point balance<InfoTip text={METRIC_TIPS["Rank point balance"]} />
                </div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 2 }}>
                  Max delta: {metrics.balance_score} pts
                  {metrics.balance_score === 0 && <span style={{ color: "var(--color-text-success)", marginLeft: 8 }}>— perfect</span>}
                </div>
              </div>
              <div style={{ fontSize: 24, fontWeight: 500 }}>
                {metrics.balance_score}<span style={{ fontSize: 13, fontWeight: 400, color: "var(--color-text-secondary)" }}> pts</span>
              </div>
            </div>
            <PointsBar sectionPoints={metrics.section_rank_points} />
          </Card>

          <Card>
            <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 12 }}>Section sizes</div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {Object.entries(metrics.section_sizes || {}).map(([name, size]) => {
                const pal = SECTION_PALETTE[name] || SECTION_PALETTE.A;
                return (
                  <div key={name} style={{ flex: "1 1 100px", background: pal.bg, border: `1px solid ${pal.border}`, borderRadius: 10, padding: "14px 18px", textAlign: "center" }}>
                    <div style={{ fontSize: 26, fontWeight: 500, color: pal.text }}>{size}</div>
                    <div style={{ fontSize: 12, color: pal.text, opacity: .8 }}>Section {name}</div>
                  </div>
                );
              })}
            </div>
          </Card>
        </>
      )}

      {!metrics && !loading && (
        <Card style={{ textAlign: "center", padding: "48px 24px" }}>
          <p style={{ fontSize: 13, color: "var(--color-text-tertiary)" }}>
            No allocation found. Run the allocation from the Simulation page first.
          </p>
        </Card>
      )}
    </div>
  );
}
