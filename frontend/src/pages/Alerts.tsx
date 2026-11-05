import { Bell, Check, CircleAlert, Mail, ShieldCheck } from "lucide-react";
import type { Delivery } from "../types";

interface Props { alerts: Delivery[]; loading: boolean; demoMode: boolean; }

export default function Alerts({ alerts, loading, demoMode }: Props) {
  return (
    <div className="page-stack">
      <section className="page-heading compact-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" />YOUR ALERTS</div><h1>Updates that <em>reach you.</em></h1><p className="page-subtitle">See every new or changed update in one place.</p></div>
        <div className="heading-count"><strong>{alerts.length.toString().padStart(2, "0")}</strong><span>delivery records</span></div>
      </section>
      <section className={"alert-mode-card " + (demoMode ? "alert-mode-demo" : "alert-mode-live")}>
        <div className="alert-mode-icon">{demoMode ? <ShieldCheck size={21} /> : <Bell size={21} />}</div>
        <div><span className="panel-kicker">{demoMode ? "SAFE DEMO MODE" : "ALERT CHANNEL"}</span><strong>{demoMode ? "No email is sent from this workspace" : "Every delivery attempt is logged"}</strong><p>{demoMode ? "New and revised sample notices appear in this local log only. This keeps demonstrations safe." : "A unique notice and revision pair is logged before delivery, which prevents repeat alerts on unchanged checks."}</p></div>
        <div className="alert-mode-chip">{demoMode ? "LOCAL ONLY" : "TRACKED"}</div>
      </section>
      <section className="panel alert-log-panel">
        <div className="register-toolbar"><div><span className="panel-kicker">DELIVERY HISTORY</span><h2>Recent alert activity</h2></div><span className="register-sort"><Bell size={14} /> Newest first</span></div>
        {loading ? <div className="page-loading"><span className="loading-spinner" />Loading alert log</div> : alerts.length === 0 ? <div className="empty-state"><div className="empty-state-icon"><Bell size={21} /></div><strong>No alerts delivered</strong><span>New and revised advisories will appear here.</span></div> : (
          <div className="alert-log-list">
            {alerts.map((alert) => (
              <article className="alert-log-item" key={alert.id}>
                <div className={"delivery-icon delivery-" + alert.status}>{alert.status === "sent" || alert.status === "logged" ? <Check size={16} /> : alert.status === "blocked" || alert.status === "failed" ? <CircleAlert size={16} /> : <Mail size={16} />}</div>
                <div className="delivery-main"><div className="delivery-title"><strong>{alert.subject}</strong><span className={"delivery-status delivery-status-" + alert.status}>{alert.status}</span></div><p>Notice revision {alert.revision_number} · {alert.channel === "demo" ? "Local demonstration log" : "Email to " + alert.recipient}</p>{alert.error_message && <p className="delivery-error">{alert.error_message}</p>}</div>
                <time>{new Date(alert.created_at).toLocaleString()}</time>
                {alert.channel === "demo" && <span className="sample-row-tag">SAMPLE</span>}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
