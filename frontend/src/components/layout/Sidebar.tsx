import {
  BarChart3,
  Bot,
  ChevronLeft,
  Clock3,
  Gauge,
  Landmark,
  MessageSquareText,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigation = [
  { label: "Dashboard", path: "/dashboard", icon: Gauge },
  { label: "Chat", path: "/chat", icon: MessageSquareText },
  { label: "Simulator", path: "/simulator", icon: Bot },
  { label: "Governance", path: "/governance", icon: ShieldCheck },
  { label: "Analytics", path: "/analytics", icon: BarChart3 },
  { label: "History", path: "/history", icon: Clock3 },
  { label: "Settings", path: "/settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onCollapse: () => void;
  onNavigate: () => void;
}

export function Sidebar({ collapsed, mobileOpen, onCollapse, onNavigate }: SidebarProps) {
  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`} id="primary-sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <Landmark size={19} strokeWidth={2.2} />
        </span>
        <div className="brand-copy">
          <strong>NorseAI</strong>
          <span>Agent governance</span>
        </div>
        <button
          className="icon-button mobile-close"
          id="sidebar-close-button"
          onClick={onNavigate}
          aria-label="Close menu"
        >
          <X size={18} />
        </button>
      </div>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        <span className="nav-label">Workspace</span>
        {navigation.map(({ label, path, icon: Icon }) => (
          <NavLink
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            key={path}
            onClick={onNavigate}
            title={collapsed ? label : undefined}
            to={path}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="workspace-chip">
          <span className="avatar avatar-small">NW</span>
          <div>
            <strong>Local workspace</strong>
            <span>Session unavailable</span>
          </div>
        </div>
        <button className="collapse-button" onClick={onCollapse} aria-label="Collapse sidebar">
          <ChevronLeft size={17} />
          <span>Collapse sidebar</span>
        </button>
      </div>
    </aside>
  );
}
