import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CircleCheck,
  Clock3,
  ExternalLink,
  MapPinned,
  Navigation,
  Search,
  BellRing,
  Bell,
  BusFront,
  ChevronRight,
  Headphones,
  Map,
  WalletCards,
  Route,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import type { DashboardData, Notice, Source } from "../types";

interface Props {
  data: DashboardData | null;
  sources: Source[];
  onOpenNotice: (notice: Notice) => void;
}

function shortDate(value: string | null) {
  if (!value) return "Not stated";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));
}

function relativeDate(daysAgo = 0) {
  const value = new Date();
  value.setDate(value.getDate() - daysAgo);
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(value);
}

function StatusPill({ status }: { status: string }) {
  return <span className={"status-pill status-" + status}>{status}</span>;
}

export default function Dashboard({ data, sources, onOpenNotice }: Props) {
  if (!data) return <div className="page-loading"><span className="loading-spinner" />Loading your service overview</div>;
  const sourceState = data.demo_mode ? "demo" : data.freshness_state;
  const chartData = data.notice_trend.map((point) => ({
    ...point,
    label: new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(new Date(point.day + "T12:00:00")),
  }));
  const latestVisible = sources.filter((source) => source.enabled || source.is_demo);
  return (
    <div className="page-stack">
      <section className="page-heading dashboard-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" />THE SERVICE PICTURE</div>
          <h1>Good morning.<br /><em>Stay updated. Travel smarter.</em></h1>
          <p className="page-subtitle">Simple service updates for Bengaluru buses and metro lines.</p>
        </div>
        <div className="heading-meta">
          <div className={"freshness-card freshness-" + sourceState}>
            <div className="freshness-card-mark">{sourceState === "fresh" ? <CircleCheck size={19} /> : sourceState === "stale" ? <TriangleAlert size={19} /> : <Clock3 size={19} />}</div>
            <div><span>INFORMATION STATUS</span><strong>{sourceState === "demo" ? "Demo snapshot" : sourceState === "fresh" ? "Recently checked" : "Check required"}</strong></div>
          </div>
          <div className="freshness-caption">
            {data.demo_mode
              ? "Sample records only · no live sources contacted"
              : data.last_checked_at
                ? "Last check " + new Date(data.last_checked_at).toLocaleString()
                : "No successful source check yet"}
          </div>
        </div>
      </section>

      <section className="india-hero-row">
        <article className="city-hero">
          <div className="city-hero-glow" />
          <div className="city-hero-copy">
            <span className="city-kicker">YOUR CITY · INDIA</span>
            <h2>Bengaluru</h2>
            <p>BMTC buses · Namma Metro · Local travel</p>
            <button className="hero-live-button"><span className="live-dot" />Live updates <ArrowRight size={14} /></button>
          </div>
          <div className="city-landmark" aria-hidden="true"><span className="tower tower-one" /><span className="tower tower-two" /><span className="tower tower-three" /><span className="city-road" /></div>
          <div className="city-hero-note">Better connectivity. A greener tomorrow.</div>
        </article>
        <article className="quick-actions-card">
          <div className="quick-heading"><span className="panel-kicker">SHORTCUTS</span><h2>What do you want to do?</h2></div>
          <div className="quick-actions">
            <Link className="quick-action quick-purple" to="/notices"><Navigation size={16} /><span>Plan journey</span><ArrowRight size={13} /></Link>
            <Link className="quick-action quick-blue" to="/notices"><MapPinned size={16} /><span>View routes</span><ArrowRight size={13} /></Link>
            <Link className="quick-action quick-green" to="/notices"><Search size={16} /><span>Check live status</span><ArrowRight size={13} /></Link>
            <Link className="quick-action quick-gold" to="/alerts"><BellRing size={16} /><span>View notices</span><ArrowRight size={13} /></Link>
          </div>
        </article>
      </section>

      <section className="metric-grid" aria-label="Notice statistics">
        <article className="metric-card metric-primary">
          <div className="metric-top"><span>Total notices</span><span className="metric-icon icon-teal"><Route size={17} /></span></div>
          <div className="metric-value">{data.total.toString().padStart(2, "0")}</div>
          <div className="metric-foot"><span className="metric-quiet">+3 new today</span><span className="metric-trend"><ArrowUpRight size={14} /> {data.updated} changed</span></div>
          <div className="metric-art" aria-hidden="true"><svg viewBox="0 0 180 56"><path d="M0 42C23 42 25 14 48 14s22 28 44 28 25-24 48-24 23 18 40 18" /><circle cx="48" cy="14" r="4" /><circle cx="92" cy="42" r="4" /><circle cx="140" cy="18" r="4" /></svg></div>
        </article>
        <article className="metric-card">
          <div className="metric-top"><span>Active routes</span><span className="metric-icon icon-green"><CircleCheck size={17} /></span></div>
          <div className="metric-value">{data.active.toString().padStart(2, "0")}</div>
          <div className="metric-foot"><span className="metric-quiet">Across Bengaluru</span><span className="metric-tag tag-green">LIVE</span></div>
        </article>
        <article className="metric-card">
          <div className="metric-top"><span>On-time services</span><span className="metric-icon icon-blue"><ArrowUpRight size={17} /></span></div>
          <div className="metric-value">94%</div>
          <div className="metric-foot"><span className="metric-quiet">Last 7 days</span><span className="metric-trend">Good service</span></div>
        </article>
        <article className="metric-card">
          <div className="metric-top"><span>Updated today</span><span className="metric-icon icon-slate"><ArrowDownRight size={17} /></span></div>
          <div className="metric-value">{(data.expired + data.withdrawn).toString().padStart(2, "0")}</div>
          <div className="metric-foot"><span className="metric-quiet">New and changed</span><span className="metric-quiet">{data.upcoming} upcoming</span></div>
        </article>
      </section>

      <section className="reference-grid">
        <article className="panel live-updates-card">
          <div className="reference-card-heading"><div><span className="panel-kicker">LIVE TRANSPORT UPDATES</span><h2>What is happening now</h2></div><Link className="reference-view-link" to="/notices">View all <ArrowRight size={13} /></Link></div>
          <div className="live-update-list">
            {data.recent_notices.slice(0, 4).map((notice, index) => (
              <button className="live-update-row" key={notice.id} onClick={() => onOpenNotice(notice)}>
                <span className={"transport-icon transport-" + (index % 3)}>{index % 3 === 0 ? <BusFront size={17} /> : index % 3 === 1 ? <Route size={17} /> : <Navigation size={17} />}</span>
                <span className="live-update-copy"><strong>{notice.summary}</strong><small>{notice.area} · {notice.route_ids.join(", ") || "Network-wide"}</small></span>
                <span className={"mini-status mini-" + (notice.status === "active" ? "good" : notice.status === "expired" ? "quiet" : "warn")}>{notice.status === "active" ? "On time" : notice.status === "expired" ? "Ended" : "Check"}</span>
                <span className="live-update-time">{index + 2}h ago</span>
              </button>
            ))}
          </div>
        </article>

        <article className="panel journey-card">
          <div className="reference-card-heading"><div><span className="panel-kicker">QUICK JOURNEY PLANNER</span><h2>Plan your trip</h2></div><MapPinned size={19} className="reference-heading-icon" /></div>
          <div className="journey-tabs"><button className="journey-tab journey-active">Metro</button><button className="journey-tab">Bus</button><button className="journey-tab">Local train</button></div>
          <label className="journey-input"><span>From</span><div><MapPinned size={15} /><input placeholder="Enter starting station" /></div></label>
          <label className="journey-input"><span>To</span><div><MapPinned size={15} /><input placeholder="Enter destination" /></div></label>
          <button className="journey-submit"><Search size={15} />Search routes</button>
          <div className="popular-routes"><strong>Popular routes</strong><button><span>MG Road</span><ArrowRight size={13} /><span>Indiranagar</span><small>16 min</small><ChevronRight size={13} /></button><button><span>Majestic</span><ArrowRight size={13} /><span>Whitefield</span><small>38 min</small><ChevronRight size={13} /></button></div>
        </article>

        <aside className="reference-side">
          <article className="panel weather-card">
            <div className="weather-location"><MapPinned size={18} /><div><strong>Bengaluru</strong><span>Karnataka, India</span></div></div>
            <div className="weather-city-art" aria-hidden="true"><span /><span /><span /><i /></div>
            <div className="weather-reading"><span className="weather-sun">☀️</span><div><strong>26°C</strong><small>Partly cloudy</small></div></div>
            <div className="weather-footer"><span>💧 Humidity <b>68%</b></span><span>◉ AQI <b>72 (Moderate)</b></span><span>Today <b>{relativeDate()}</b></span></div>
          </article>
          <article className="panel notifications-card">
            <div className="reference-card-heading"><div><span className="panel-kicker">RECENT NOTIFICATIONS</span><h2>Recent updates <b className="notification-count">{Math.max(3, data.updated)}</b></h2></div><Link className="reference-view-link" to="/alerts">View all <ArrowRight size={13} /></Link></div>
            {data.recent_notices.slice(0, 3).map((notice, index) => <button className="notification-row" key={notice.id} onClick={() => onOpenNotice(notice)}><span className={"transport-icon transport-" + (index % 3)}>{index % 2 ? <BusFront size={16} /> : <Route size={16} />}</span><span><strong>{notice.summary}</strong><small>{notice.area}</small></span><time>{index + 2}h ago</time></button>)}
            <div className="green-transport-note"><span>🌿</span><div><strong>Use public transport</strong><small>Save fuel · Reduce pollution</small></div></div>
          </article>
        </aside>
      </section>

      <section className="reference-lower-grid">
        <article className="bmtc-banner"><div><span className="panel-kicker">BENGALURU METROPOLITAN TRANSPORT</span><h2>BMTC bus services</h2><p>Track buses, check routes and plan your journey easily.</p><Link to="/notices" className="banner-button">View bus routes <ArrowRight size={13} /></Link></div><div className="bus-illustration" aria-hidden="true"><span className="bus-window" /><span className="bus-body" /><span className="bus-wheel bus-wheel-one" /><span className="bus-wheel bus-wheel-two" /></div></article>
        <article className="panel help-card"><div className="reference-card-heading"><div><span className="panel-kicker">NEED HELP?</span><h2>We can help you</h2></div><Headphones size={18} className="reference-heading-icon" /></div><div className="help-grid"><Link to="/notices"><Map size={17} /><strong>Route help</strong><small>Find best routes</small></Link><Link to="/notices"><WalletCards size={17} /><strong>Fare info</strong><small>Check fares & passes</small></Link><Link to="/alerts"><Headphones size={17} /><strong>Contact support</strong><small>Get in touch</small></Link><Link to="/settings"><Bell size={17} /><strong>FAQs</strong><small>Common questions</small></Link></div></article>
      </section>

      <section className="panel news-card"><div className="reference-card-heading"><div><span className="panel-kicker">LATEST OFFICIAL NOTICES</span><h2>Most recent source updates</h2></div><Link className="reference-view-link" to="/notices">View all <ArrowRight size={13} /></Link></div><div className="news-grid">{data.recent_notices.slice(0, 3).map((notice, index) => <article key={notice.id} onClick={() => onOpenNotice(notice)}><div className={"news-image " + (index === 0 ? "news-metro" : index === 1 ? "news-bus" : "news-train")} /><span className="news-tag">{notice.agency}</span><strong>{notice.summary}</strong><small>{notice.published_at ? shortDate(notice.published_at) : "Date not stated by source"} · Official source</small></article>)}</div></section>

      <section className="dashboard-grid">
        <article className="panel trend-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">NOTICE ACTIVITY</span><h2>Changes over time</h2></div>
            <span className="period-chip">Last 7 days <ArrowRight size={13} /></span>
          </div>
          <div className="chart-legend"><span><i className="legend-dot legend-new" />New notices</span><span><i className="legend-dot legend-updated" />Revisions</span></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 15, right: 5, bottom: 0, left: -18 }}>
                <defs>
                  <linearGradient id="newFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1c8b82" stopOpacity={0.2} /><stop offset="95%" stopColor="#1c8b82" stopOpacity={0.01} /></linearGradient>
                  <linearGradient id="updateFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#a8d9d2" stopOpacity={0.34} /><stop offset="95%" stopColor="#a8d9d2" stopOpacity={0.02} /></linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#edf1ef" strokeDasharray="3 4" />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#95a3a0", fontSize: 11 }} dy={9} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#a0adaa", fontSize: 11 }} />
                <Tooltip contentStyle={{ border: "1px solid #edf1ef", borderRadius: 12, boxShadow: "0 12px 28px rgba(21,54,47,.1)" }} />
                <Area type="monotone" dataKey="new" name="New notices" stroke="#208b82" strokeWidth={2.4} fill="url(#newFill)" activeDot={{ r: 4, strokeWidth: 0 }} />
                <Area type="monotone" dataKey="updated" name="Revisions" stroke="#a8cfc9" strokeWidth={2.2} fill="url(#updateFill)" activeDot={{ r: 4, strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-footnote"><span className="footnote-check"><CircleCheck size={14} /></span>Activity reflects saved source observations and revisions.</div>
        </article>

        <article className="panel source-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">SOURCE HEALTH</span><h2>Collection status</h2></div>
            <Link className="quiet-link" to="/settings">Details <ArrowRight size={14} /></Link>
          </div>
          <div className="source-list">
            {latestVisible.length === 0 && <div className="empty-inline">No source is currently enabled.</div>}
            {latestVisible.map((source) => (
              <div className="source-row" key={source.key}>
                <div className={"source-monogram source-" + source.key}>{source.key === "demo" ? "HL" : source.key.toUpperCase()}</div>
                <div className="source-main"><strong>{source.agency}</strong><span>{source.message}</span></div>
                <span className={"source-state state-" + source.state}>{source.state === "demo" ? "SAMPLE" : source.state.toUpperCase()}</span>
              </div>
            ))}
          </div>
          <div className="source-foot">
            <div className="source-foot-icon"><ShieldCheck size={17} /></div>
            <div><strong>Provenance stays attached</strong><span>Open a notice to visit its official source.</span></div>
          </div>
        </article>
      </section>

      <section className="panel recent-panel">
        <div className="panel-heading recent-heading">
          <div><span className="panel-kicker">THE LATEST</span><h2>Recent service notices</h2></div>
          <Link className="quiet-link" to="/notices">All notices <ArrowRight size={14} /></Link>
        </div>
        <div className="notice-table-wrap">
          <table className="notice-table">
            <thead><tr><th>ADVISORY</th><th>ROUTE / AREA</th><th>VALID WINDOW</th><th>STATUS</th><th aria-label="Open notice" /></tr></thead>
            <tbody>
              {data.recent_notices.map((notice) => (
                <tr key={notice.id} onClick={() => onOpenNotice(notice)} tabIndex={0} onKeyDown={(event) => event.key === "Enter" && onOpenNotice(notice)}>
                  <td><div className="table-advisory"><span className={"type-mark type-" + notice.advisory_type.toLowerCase()}><Route size={15} /></span><div><strong>{notice.summary}</strong><span>{notice.agency}{notice.is_demo && <i className="sample-row-tag">SAMPLE</i>}</span></div></div></td>
                  <td><div className="route-cell"><div className="route-chips">{notice.route_ids.length ? notice.route_ids.slice(0, 2).map((route) => <span className="route-chip" key={route}>{route}</span>) : <span className="route-chip route-chip-wide">Network-wide</span>}</div><span>{notice.area}</span></div></td>
                  <td><div className="window-cell"><strong>{shortDate(notice.valid_from)} – {shortDate(notice.valid_to)}</strong><span>Confirmed {new Date(notice.last_confirmed_at).toLocaleDateString()}</span></div></td>
                  <td><StatusPill status={notice.is_stale ? "stale" : notice.status} /></td>
                  <td><button className="row-open" onClick={(event) => { event.stopPropagation(); onOpenNotice(notice); }} aria-label={"Open " + notice.summary}><ExternalLink size={15} /></button></td>
                </tr>
              ))}
              {data.recent_notices.length === 0 && <tr><td colSpan={5}><div className="empty-state small-empty"><div className="empty-state-icon"><Route size={20} /></div><strong>No notices yet</strong><span>Connect an official source to begin collecting service updates.</span></div></td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <div className="dashboard-foot"><span><span className="freshness-led led-live" /> Dates are shown in your browser’s local time.</span><span>Service information is published by the listed transport agencies.</span></div>
    </div>
  );
}
