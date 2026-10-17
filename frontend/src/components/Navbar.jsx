import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  { path: "/", label: "Practice" },
  { path: "/mock", label: "Mock interview" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/history", label: "History" },
  { path: "/model-info", label: "Models" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const doLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate("/login");
  };

  const initials = (user?.full_name || user?.email || "?")
    .split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <nav style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 2rem", height: 52,
      borderBottom: "0.5px solid var(--color-border-tertiary)",
      background: "var(--color-background-primary)", position: "sticky", top: 0, zIndex: 100,
    }}>
      <button onClick={() => navigate(isAuthenticated ? "/" : "/login")}
        style={{ display: "flex", alignItems: "center", gap: 8, background: "none",
                 border: "none", cursor: "pointer" }}>
        <div style={{ width: 26, height: 26, borderRadius: 7, background: "#534AB7",
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="5" r="2.5" fill="white" />
            <path d="M2 12c0-2.761 2.239-4 5-4s5 1.239 5 4" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </div>
        <span style={{ fontSize: 14, fontWeight: 500, color: "var(--color-text-primary)", letterSpacing: "-0.01em" }}>
          AceIt
        </span>
      </button>

      {isAuthenticated && (
        <div style={{ display: "flex", gap: 2 }}>
          {links.map(({ path, label }) => {
            const active = pathname === path;
            return (
              <button key={path} onClick={() => navigate(path)} style={{
                fontSize: 13, padding: "5px 12px", borderRadius: 8, cursor: "pointer",
                border: "0.5px solid", borderColor: active ? "#534AB7" : "transparent",
                background: active ? "#EEEDFE" : "transparent",
                color: active ? "#3C3489" : "var(--color-text-secondary)",
                fontWeight: active ? 500 : 400, transition: "all 0.15s",
              }}>{label}</button>
            );
          })}
        </div>
      )}

      {isAuthenticated ? (
        <div ref={menuRef} style={{ position: "relative" }}>
          <button onClick={() => setMenuOpen((o) => !o)} aria-haspopup="menu" aria-expanded={menuOpen}
            style={{ display: "flex", alignItems: "center", gap: 8, background: "none",
                     border: "none", cursor: "pointer", padding: 2 }}>
            <span style={{ width: 30, height: 30, borderRadius: "50%", background: "#EEEDFE",
              color: "#3C3489", fontSize: 12, fontWeight: 600, display: "flex",
              alignItems: "center", justifyContent: "center" }}>{initials}</span>
          </button>
          {menuOpen && (
            <div role="menu" style={{ position: "absolute", right: 0, top: 40, minWidth: 200,
              background: "var(--color-background-primary)", borderRadius: 10,
              border: "0.5px solid var(--color-border-tertiary)",
              boxShadow: "0 8px 24px rgba(0,0,0,0.12)", padding: 6, zIndex: 200 }}>
              <div style={{ padding: "8px 10px", borderBottom: "0.5px solid var(--color-border-tertiary)", marginBottom: 4 }}>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.full_name}
                </p>
                <p style={{ margin: 0, fontSize: 11, color: "var(--color-text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.email}
                </p>
              </div>
              <MenuItem onClick={() => { setMenuOpen(false); navigate("/account"); }}>Account settings</MenuItem>
              <MenuItem onClick={() => { setMenuOpen(false); navigate("/comparison"); }}>Model comparison</MenuItem>
              <MenuItem onClick={doLogout} danger>Log out</MenuItem>
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => navigate("/login")} style={ghostBtn}>Log in</button>
          <button onClick={() => navigate("/signup")} style={primaryBtn}>Sign up</button>
        </div>
      )}
    </nav>
  );
}

function MenuItem({ children, onClick, danger }) {
  return (
    <button role="menuitem" onClick={onClick} style={{
      display: "block", width: "100%", textAlign: "left", fontSize: 13, padding: "8px 10px",
      borderRadius: 7, border: "none", cursor: "pointer", background: "transparent",
      color: danger ? "#D94848" : "var(--color-text-primary)",
    }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-background-secondary)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
      {children}
    </button>
  );
}

const ghostBtn = { fontSize: 13, padding: "6px 14px", borderRadius: 8, cursor: "pointer",
  border: "0.5px solid var(--color-border-tertiary)", background: "transparent",
  color: "var(--color-text-primary)" };
const primaryBtn = { fontSize: 13, padding: "6px 14px", borderRadius: 8, cursor: "pointer",
  border: "0.5px solid #534AB7", background: "#534AB7", color: "#fff", fontWeight: 500 };
