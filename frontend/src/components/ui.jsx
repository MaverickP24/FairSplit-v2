// Shared UI primitives used across all pages

export function Card({ children, style = {} }) {
  return (
    <div style={{
      background: "var(--color-background-secondary)",
      border: "1px solid var(--color-border-tertiary)",
      borderRadius: 12,
      padding: 20,
      ...style,
    }}>
      {children}
    </div>
  );
}

export function Badge({ children, color = "gray" }) {
  const palettes = {
    gray:   { bg: "#F1EFE8", text: "#444441" },
    teal:   { bg: "#E1F5EE", text: "#085041" },
    purple: { bg: "#EEEDFE", text: "#3C3489" },
    amber:  { bg: "#FAEEDA", text: "#633806" },
    coral:  { bg: "#FAECE7", text: "#712B13" },
    pink:   { bg: "#FBEAF0", text: "#72243E" },
    blue:   { bg: "#E6F1FB", text: "#0C447C" },
    red:    { bg: "#FCEBEB", text: "#791F1F" },
  };
  const p = palettes[color] || palettes.gray;
  return (
    <span style={{
      background: p.bg, color: p.text,
      borderRadius: 5, padding: "2px 8px",
      fontSize: 11, fontWeight: 500,
      display: "inline-block",
    }}>
      {children}
    </span>
  );
}

export function Alert({ type = "error", children }) {
  const styles = {
    error:   { bg: "var(--color-background-danger)",   text: "var(--color-text-danger)" },
    success: { bg: "var(--color-background-success)",  text: "var(--color-text-success)" },
    info:    { bg: "var(--color-background-info)",     text: "var(--color-text-info)" },
    warning: { bg: "var(--color-background-warning)",  text: "var(--color-text-warning)" },
  };
  const s = styles[type] || styles.error;
  return (
    <div style={{
      background: s.bg, color: s.text,
      padding: "11px 16px", borderRadius: 8,
      fontSize: 13, lineHeight: 1.5,
      marginBottom: 16,
    }}>
      {children}
    </div>
  );
}

export function Btn({ children, onClick, disabled, variant = "primary", size = "md", style = {} }) {
  const base = {
    borderRadius: 8, border: "none", cursor: disabled ? "not-allowed" : "pointer",
    fontWeight: 500, transition: "opacity .15s",
    opacity: disabled ? 0.5 : 1,
    fontSize: size === "sm" ? 12 : size === "lg" ? 15 : 13,
    padding: size === "sm" ? "5px 12px" : size === "lg" ? "10px 28px" : "7px 18px",
  };
  const variants = {
    primary:  { background: "#1D9E75", color: "#fff" },
    secondary:{ background: "var(--color-background-primary)", color: "var(--color-text-primary)", border: "1px solid var(--color-border-secondary)" },
    ghost:    { background: "transparent", color: "var(--color-text-secondary)", border: "1px dashed var(--color-border-secondary)" },
    danger:   { background: "#E24B4A", color: "#fff" },
  };
  return (
    <button onClick={onClick} disabled={disabled} style={{ ...base, ...variants[variant], ...style }}>
      {children}
    </button>
  );
}

export function Skeleton({ width = "100%", height = 16, radius = 6, style = {} }) {
  return (
    <div style={{
      width, height,
      borderRadius: radius,
      background: "var(--color-border-tertiary)",
      animation: "pulse 1.4s ease-in-out infinite",
      ...style,
    }} />
  );
}

export function SkeletonTable({ rows = 8, cols = 6 }) {
  return (
    <div>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }`}</style>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: "1px solid var(--color-border-tertiary)" }}>
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} width={`${[8, 10, 8, 16, 28, 10][j] || 12}%`} height={14} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function StatCard({ label, value, unit = "", sub, color = "default" }) {
  return (
    <div style={{
      background: "var(--color-background-secondary)",
      border: "1px solid var(--color-border-tertiary)",
      borderRadius: 12, padding: "16px 20px",
      flex: "1 1 160px",
    }}>
      <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 6, textTransform: "uppercase", letterSpacing: ".04em" }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 500, letterSpacing: -0.5, color: "var(--color-text-primary)" }}>
        {value}<span style={{ fontSize: 14, fontWeight: 400, color: "var(--color-text-secondary)" }}>{unit}</span>
      </div>
      {sub && <div style={{ fontSize: 12, marginTop: 5, color: "var(--color-text-secondary)" }}>{sub}</div>}
    </div>
  );
}

export const SECTION_PALETTE = {
  A: { bg: "#EEEDFE", text: "#3C3489", border: "#AFA9EC", bar: "#7F77DD" },
  B: { bg: "#E1F5EE", text: "#085041", border: "#5DCAA5", bar: "#1D9E75" },
  C: { bg: "#FAEEDA", text: "#633806", border: "#EF9F27", bar: "#BA7517" },
  D: { bg: "#FAECE7", text: "#712B13", border: "#F0997B", bar: "#D85A30" },
  E: { bg: "#FBEAF0", text: "#72243E", border: "#ED93B1", bar: "#D4537E" },
};
