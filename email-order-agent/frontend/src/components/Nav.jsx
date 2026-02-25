import { Link, useLocation, useNavigate } from "react-router-dom";

const baseTabs = [
  { to: "/", label: "Dashboard" },
  { to: "/activity", label: "Activity" },
  { to: "/inbox", label: "Inbox" },
  { to: "/review", label: "Human Review" },
  { to: "/orders", label: "Orders" },
];

export default function Nav() {
  const loc = useLocation();
  const nav = useNavigate();
  const role = localStorage.getItem("role") || "viewer";

  const tabs = [...baseTabs, ...(role === "admin" ? [{ to: "/settings", label: "Settings" }] : [])];

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    nav("/login");
  }

  return (
    <div className="topbar">
      <div className="navInner">
        <div className="brand">
          <div className="brandLogo" />
          <div className="brandTitle">
            <b>Email Order Agent</b>
            <span>Cyber Ops Console</span>
          </div>
        </div>

        <div className="tabs">
          {tabs.map((t) => (
            <Link key={t.to} to={t.to} className={`tab ${loc.pathname === t.to ? "active" : ""}`}>
              {t.label}
            </Link>
          ))}
        </div>

        <div className="spacer" />
        <span className="pill">ROLE: {role.toUpperCase()}</span>
        <button className="btn" onClick={logout}>Logout</button>
      </div>
    </div>
  );
}