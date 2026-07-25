import { LogOut, Menu, Moon, RefreshCw, Sun } from "lucide-react";

import { useAuth } from "../../features/auth/auth";
import { useTheme } from "../../providers/theme";
import { useToast } from "../../providers/toast";

interface TopHeaderProps {
  mobileOpen: boolean;
  onMenu: () => void;
}

export function TopHeader({ mobileOpen, onMenu }: TopHeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const { notify } = useToast();
  const { session, logout } = useAuth();

  const handleRefresh = () => {
    window.dispatchEvent(new Event("norse:refresh"));
    notify({
      title: "Status check requested",
      message: "The dashboard is checking available backend services.",
      type: "info",
    });
  };

  return (
    <header className="top-header">
      <div className="header-left">
        <button
          className="icon-button menu-button"
          id="mobile-menu-button"
          onClick={onMenu}
          aria-controls="primary-sidebar"
          aria-expanded={mobileOpen}
          aria-label="Open navigation"
        >
          <Menu size={19} />
        </button>
        <div>
          <span className="header-kicker">Control center</span>
          <strong>NorseAI</strong>
        </div>
      </div>
      <div className="header-actions">
        <div className="system-pill" title="See dashboard for live backend status">
          <span>Live status on dashboard</span>
        </div>
        <button className="icon-button" onClick={handleRefresh} aria-label="Refresh dashboard">
          <RefreshCw size={18} />
        </button>
        <button className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div className="session-indicator" title="Current session">
          <span className="avatar">{session?.username.slice(0, 2).toUpperCase()}</span>
          <div>
            <strong>{session?.username}</strong>
            <span>{session?.role}</span>
          </div>
        </div>
        <button className="icon-button" onClick={logout} aria-label="Log out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
