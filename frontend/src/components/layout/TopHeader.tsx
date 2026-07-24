import { Bell, Menu, Moon, RefreshCw, Sun } from "lucide-react";

import { useTheme } from "../../providers/theme";
import { useToast } from "../../providers/toast";

interface TopHeaderProps {
  mobileOpen: boolean;
  onMenu: () => void;
}

export function TopHeader({ mobileOpen, onMenu }: TopHeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const { notify } = useToast();

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
        <button
          className="icon-button"
          onClick={() =>
            notify({
              title: "Notifications unavailable",
              message: "A notification API has not been connected.",
              type: "info",
            })
          }
          aria-label="Notifications"
        >
          <Bell size={18} />
          <span className="notification-dot" />
        </button>
        <button className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div className="session-indicator" title="Current session">
          <span className="avatar">LS</span>
          <div>
            <strong>Local session</strong>
            <span>Unauthenticated</span>
          </div>
        </div>
      </div>
    </header>
  );
}
