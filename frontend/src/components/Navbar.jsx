import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  { path: "/", label: "Practice" },
  { path: "/mock", label: "Mock" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/history", label: "History" },
  { path: "/model-info", label: "Models" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);   // avatar dropdown
  const [mobileOpen, setMobileOpen] = useState(false); // hamburger drawer
  const menuRef = useRef(null);

  // Close avatar dropdown on outside click
  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  const doLogout = async () => {
    setMenuOpen(false);
    setMobileOpen(false);
    await logout();
    navigate("/login");
  };

  const initials = (user?.full_name || user?.email || "?")
    .split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <>
      <nav style={navStyle}>
        {/* Logo */}
        <button onClick={() => navigate(isAuthenticated ? "/" : "/login")} style={logoBtn}>
          <div style={logoIcon}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="5" r="2.5" fill="white" />
              <path d="M2 12c0-2.761 2.239-4 5-4s5 1.239 5 4"
                stroke="white" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
          </div>
          <span style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-primary)", letterSpacing: "-0.01em" }}>
            AceIt
          </span>
        </button>

        {/* Desktop nav links — hidden on mobile */}
        {isAuthenticated && (
          <div className="nav-desktop-links" style={desktopLinks}>
            {links.map(({ path, label }) => {
              const active = pathname === path;
              return (
                <button key={path} onClick={() => navigate(path)} style={{
                  fontSize: 13, padding: "5px 12px", borderRadius: 8, cursor: "pointer",
                  border: "0.5px solid",
                  borderColor: active ? "#534AB7" : "transparent",
                  background: active ? "#EEEDFE" : "transparent",
                  color: active ? "#3C3489" : "var(--color-text-secondary)",
                  fontWeight: active ? 500 : 400,
                  transition: "all 0.15s",
                  minHeight: "unset",   /* override global 44px min on desktop */
                }}>{label}</button>
              );
            })}
          </div>
        )}

        {/* Right side */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isAuthenticated ? (
            <>
              {/* Avatar / dropdown — always visible */}
              <div ref={menuRef} style={{ position: "relative" }}>
                <button onClick={() => setMenuOpen((o) => !o)}
                  aria-haspopup="menu" aria-expanded={menuOpen}
                  style={{ display: "flex", alignItems: "center", gap: 6,
                           background: "none", border: "none", cursor: "pointer", padding: 2 }}>
                  <span style={avatarStyle}>{initials}</span>
                </button>
                {menuOpen && (
                  <div role="menu" style={dropdownStyle}>
                    <div style={{ padding: "8px 10px",
                      borderBottom: "0.5px solid var(--color-border-tertiary)", marginBottom: 4 }}>
                      <p style={{ margin: 0, fontSize: 13, fontWeight: 500,
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {user.full_name}
                      </p>
                      <p style={{ margin: 0, fontSize: 11,
                        color: "var(--color-text-secondary)",
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {user.email}
                      </p>
                    </div>
                    <MenuItem onClick={() => { setMenuOpen(false); navigate("/account"); }}>
                      Account settings
                    </MenuItem>
                    <MenuItem onClick={() => { setMenuOpen(false); navigate("/comparison"); }}>
                      Model comparison
                    </MenuItem>
                    <MenuItem onClick={doLogout} danger>Log out</MenuItem>
                  </div>
                )}
              </div>

              {/* Hamburger — only on mobile */}
              <button onClick={() => setMobileOpen(o => !o)}
                aria-label="Open navigation menu"
                className="nav-hamburger"
                style={hamburgerBtn}>
                <HamburgerIcon open={mobileOpen} />
              </button>
            </>
          ) : (
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => navigate("/login")} style={ghostBtn}>Log in</button>
              <button onClick={() => navigate("/signup")} style={primaryBtn}>Sign up</button>
            </div>
          )}
        </div>
      </nav>

      {/* Mobile drawer */}
      {isAuthenticated && mobileOpen && (
        <div style={drawerStyle}>
          {links.map(({ path, label }) => {
            const active = pathname === path;
            return (
              <button key={path} onClick={() => navigate(path)} style={{
                display: "block", width: "100%", textAlign: "left",
                fontSize: 15, padding: "14px 20px",
                borderBottom: "0.5px solid var(--color-border-tertiary)",
                border: "none",
                borderBottomWidth: "0.5px",
                borderBottomStyle: "solid",
                borderBottomColor: "var(--color-border-tertiary)",
                background: active ? "#EEEDFE" : "var(--color-background-primary)",
                color: active ? "#3C3489" : "var(--color-text-primary)",
                fontWeight: active ? 500 : 400,
                cursor: "pointer",
              }}>{label}</button>
            );
          })}
          <button onClick={() => { setMobileOpen(false); navigate("/account"); }}
            style={drawerItemStyle}>Account settings</button>
          <button onClick={() => { setMobileOpen(false); navigate("/comparison"); }}
            style={drawerItemStyle}>Model comparison</button>
          <button onClick={doLogout}
            style={{ ...drawerItemStyle, color: "#D94848" }}>Log out</button>
        </div>
      )}

      <style>{`
        @media (min-width: 641px) {
          .nav-hamburger { display: none !important; }
        }
        @media (max-width: 640px) {
          .nav-desktop-links { display: none !important; }
        }
      `}</style>
    </>
  );
}

function HamburgerIcon({ open }) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      {open ? (
        <>
          <line x1="4" y1="4" x2="16" y2="16" />
          <line x1="16" y1="4" x2="4" y2="16" />
        </>
      ) : (
        <>
          <line x1="3" y1="6" x2="17" y2="6" />
          <line x1="3" y1="10" x2="17" y2="10" />
          <line x1="3" y1="14" x2="17" y2="14" />
        </>
      )}
    </svg>
  );
}

function MenuItem({ children, onClick, danger }) {
  return (
    <button role="menuitem" onClick={onClick} style={{
      display: "block", width: "100%", textAlign: "left",
      fontSize: 13, padding: "9px 10px", borderRadius: 7,
      border: "none", cursor: "pointer", background: "transparent",
      color: danger ? "#D94848" : "var(--color-text-primary)",
      minHeight: "unset",
    }}
      onMouseEnter={e => e.currentTarget.style.background = "var(--color-background-secondary)"}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
      {children}
    </button>
  );
}

const navStyle = {
  display: "flex", alignItems: "center", justifyContent: "space-between",
  padding: "0 1rem", height: 52,
  borderBottom: "0.5px solid var(--color-border-tertiary)",
  background: "var(--color-background-primary)",
  position: "sticky", top: 0, zIndex: 100,
};

const logoBtn = {
  display: "flex", alignItems: "center", gap: 8,
  background: "none", border: "none", cursor: "pointer", padding: 0, minHeight: "unset",
};

const logoIcon = {
  width: 26, height: 26, borderRadius: 7, background: "#534AB7",
  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
};

// Applied via className to allow CSS media query to hide on mobile
const desktopLinks = {
  display: "flex", gap: 2,
  // Hidden on mobile via the <style> tag above using class .nav-desktop-links
  // We set className directly in JSX below
};

const avatarStyle = {
  width: 32, height: 32, borderRadius: "50%", background: "#EEEDFE",
  color: "#3C3489", fontSize: 12, fontWeight: 600,
  display: "flex", alignItems: "center", justifyContent: "center",
};

const hamburgerBtn = {
  display: "flex", alignItems: "center", justifyContent: "center",
  background: "none", border: "none", cursor: "pointer",
  padding: 6, borderRadius: 8, color: "var(--color-text-primary)",
  minHeight: "unset",
};

const dropdownStyle = {
  position: "absolute", right: 0, top: 42, minWidth: 200,
  background: "var(--color-background-primary)", borderRadius: 10,
  border: "0.5px solid var(--color-border-tertiary)",
  boxShadow: "0 8px 24px rgba(0,0,0,0.12)", padding: 6, zIndex: 200,
};

const drawerStyle = {
  position: "fixed", top: 52, left: 0, right: 0, bottom: 0,
  background: "var(--color-background-primary)",
  zIndex: 99, overflowY: "auto",
  borderTop: "0.5px solid var(--color-border-tertiary)",
};

const drawerItemStyle = {
  display: "block", width: "100%", textAlign: "left",
  fontSize: 15, padding: "14px 20px", border: "none",
  borderBottom: "0.5px solid var(--color-border-tertiary)",
  background: "var(--color-background-primary)",
  color: "var(--color-text-primary)", cursor: "pointer",
};

const ghostBtn = {
  fontSize: 13, padding: "6px 14px", borderRadius: 8, cursor: "pointer",
  border: "0.5px solid var(--color-border-tertiary)", background: "transparent",
  color: "var(--color-text-primary)", minHeight: "unset",
};

const primaryBtn = {
  fontSize: 13, padding: "6px 14px", borderRadius: 8, cursor: "pointer",
  border: "0.5px solid #534AB7", background: "#534AB7", color: "#fff",
  fontWeight: 500, minHeight: "unset",
};
