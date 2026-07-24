import { useCallback, useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobileNavigation = useCallback(() => {
    setMobileOpen(false);
    window.requestAnimationFrame(() => document.getElementById("mobile-menu-button")?.focus());
  }, []);

  useEffect(() => {
    if (!mobileOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeMobileNavigation();
    };
    document.getElementById("sidebar-close-button")?.focus();
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [closeMobileNavigation, mobileOpen]);

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCollapse={() => setCollapsed((value) => !value)}
        onNavigate={closeMobileNavigation}
      />
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          className="sidebar-backdrop"
          onClick={closeMobileNavigation}
        />
      )}
      <div className="app-workspace">
        <TopHeader mobileOpen={mobileOpen} onMenu={() => setMobileOpen(true)} />
        <main className="main-content" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
