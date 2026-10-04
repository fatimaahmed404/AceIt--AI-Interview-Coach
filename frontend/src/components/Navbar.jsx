import { useNavigate, useLocation } from "react-router-dom";

const links = [
  { path: "/", label: "Practice" },
  { path: "/mock", label: "Mock interview" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/history", label: "History" },
  { path: "/model-info", label: "Models" },
  { path: "/comparison", label: "Comparison" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 2rem",
        height: 52,
        borderBottom: "0.5px solid var(--color-border-tertiary)",
        background: "var(--color-background-primary)",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Logo / brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{
          width: 26, height: 26,
          borderRadius: 7,
          background: "#534AB7",
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="5" r="2.5" fill="white" />
            <path d="M2 12c0-2.761 2.239-4 5-4s5 1.239 5 4" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </div>
        <span style={{ fontSize: 14, fontWeight: 500, color: "var(--color-text-primary)", letterSpacing: "-0.01em" }}>
          Interview coach
        </span>
      </div>

      {/* Nav links */}
      <div style={{ display: "flex", gap: 2 }}>
        {links.map(({ path, label }) => {
          const active = pathname === path;
          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              style={{
                fontSize: 13,
                padding: "5px 12px",
                borderRadius: 8,
                cursor: "pointer",
                border: "0.5px solid",
                borderColor: active ? "#534AB7" : "transparent",
                background:  active ? "#EEEDFE"  : "transparent",
                color:       active ? "#3C3489"  : "var(--color-text-secondary)",
                fontWeight:  active ? 500 : 400,
                transition: "all 0.15s",
              }}
            >
              {label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}