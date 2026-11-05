import {
  Activity,
  Bell,
  BusFront,
  Clock3,
  LayoutDashboard,
  Menu,
  Route,
  Settings2,
  ShieldCheck,
  TrainFront,
  X,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import type { AppSettings } from "../types";

const navigation = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/notices", label: "Notices", icon: BusFront },
  { to: "/notices", label: "Routes", icon: Route },
  { to: "/notices", label: "Live updates", icon: Activity },
  { to: "/history", label: "History", icon: Clock3 },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

interface ShellProps {
  settings: AppSettings | null;
  demoMode: boolean;
  lastChecked: string | null;
  refreshing: boolean;
  onRefresh: () => void;
  refreshMessage: string | null;
  error: string | null;
}

export function Shell({ settings, demoMode, lastChecked, refreshing, onRefresh, refreshMessage, error }: ShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const liveBadge = demoMode ? "Demo workspace" : "Live monitoring";
  return (
    <div className="app-frame">
      <aside className={"sidebar " + (menuOpen ? "sidebar-open" : "")}>
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true">
            <TrainFront size={21} strokeWidth={2.4} />
          </div>
          <div>
            <div className="brand-name">TransitNotice</div>
            <div className="brand-caption">INDIA TRANSIT UPDATES</div>
          </div>
          <button className="icon-button sidebar-close" aria-label="Close navigation" onClick={() => setMenuOpen(false)}>
            <X size={19} />
          </button>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">HL</div>
          <div className="workspace-copy">
            <strong>Bengaluru network</strong>
            <span>BMTC · Namma Metro</span>
          </div>
          <Activity size={16} className="workspace-pulse" />
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) => "nav-link" + (isActive ? " nav-link-active" : "")}
            >
              <Icon size={18} strokeWidth={1.9} />
              <span>{label}</span>
              {label === "Notices" && <span className="nav-dot" />}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-source-card">
          <div className="source-card-icon"><ShieldCheck size={17} /></div>
          <div>
            <strong>Source-first updates</strong>
            <p>Each notice keeps its origin and freshness visible.</p>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="avatar">TN</div>
          <div className="profile-copy">
            <strong>TransitNotice</strong>
            <span>Local workspace</span>
          </div>
          <button className="sidebar-help" aria-label="Open settings" onClick={() => (window.location.href = "/settings")}>
            <Settings2 size={17} />
          </button>
        </div>
      </aside>

      {menuOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button menu-toggle" aria-label="Open navigation" onClick={() => setMenuOpen(true)}>
            <Menu size={20} />
          </button>
          <div className="breadcrumb"><span>TransitNotice</span><i>/</i><strong>Bengaluru, Karnataka</strong></div>
          <div className="topbar-actions">
            <div className="freshness-top">
              <span className={"freshness-led " + (demoMode ? "led-demo" : lastChecked ? "led-live" : "led-stale")} />
              <span>{demoMode ? "Demo snapshot" : lastChecked ? "Source checked" : "Awaiting source check"}</span>
              {lastChecked && !demoMode && <small>{new Date(lastChecked).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>}
            </div>
            <button className="button button-refresh" onClick={onRefresh} disabled={refreshing || demoMode}>
              <Activity size={16} className={refreshing ? "spin" : ""} />
              <span>{demoMode ? "Demo mode" : refreshing ? "Checking" : "Check sources"}</span>
            </button>
            <div className="top-avatar" title={settings?.alert_mode === "email" ? "Email alerts configured" : "Local alert log"}>TN</div>
          </div>
        </header>

        <div className="content-wrap">
          {demoMode && (
            <div className="demo-banner">
              <div className="demo-banner-icon"><ShieldCheck size={17} /></div>
              <div><strong>Demonstration workspace</strong><span>Sample notices are fictional and are not live transport updates.</span></div>
              <span className="demo-pill">{liveBadge}</span>
            </div>
          )}
          {error && <div className="notice-banner banner-error"><strong>Connection issue</strong><span>{error}</span></div>}
          {refreshMessage && <div className="notice-banner banner-info"><strong>Source check</strong><span>{refreshMessage}</span></div>}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
