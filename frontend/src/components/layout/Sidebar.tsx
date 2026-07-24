import { NavLink } from "react-router-dom";

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          N
        </span>
        <div>
          <strong>NorseAI</strong>
          <span>Governance Platform</span>
        </div>
      </div>
      <nav>
        <NavLink
          className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          to="/dashboard"
        >
          Overview
        </NavLink>
      </nav>
      <p className="phase-label">Foundation · Phase 1</p>
    </aside>
  );
}
