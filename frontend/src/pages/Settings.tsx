import { ArrowUpRight, Check, CircleAlert, Clock3, ExternalLink, KeyRound, LockKeyhole, RadioTower, ShieldCheck } from "lucide-react";
import type { AppSettings, Source } from "../types";

interface Props { settings: AppSettings | null; sources: Source[]; }

function stateLabel(source: Source) {
  if (source.state === "demo") return "Sample only";
  if (source.state === "locked") return "Permission needed";
  if (source.state === "waiting") return "Waiting for check";
  if (source.state === "success") return "Connected";
  if (source.state === "error") return "Source unavailable";
  if (source.state === "paused") return "Paused";
  return source.state;
}

export default function Settings({ settings, sources }: Props) {
  return (
    <div className="page-stack">
      <section className="page-heading compact-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" />APP SETTINGS</div><h1>Clear updates.<br /><em>Safe information.</em></h1><p className="page-subtitle">Choose how sources are checked and how alerts are saved.</p></div>
        <div className="heading-count"><div className="setting-shield"><ShieldCheck size={20} /></div><span>Safety first</span></div>
      </section>

      <section className="settings-overview">
        <article className="setting-overview-card"><span className="setting-overview-icon"><RadioTower size={18} /></span><span>MODE</span><strong>{settings?.demo_mode ? "Safe demo" : "Live sources"}</strong><small>{settings?.demo_mode ? "Sample records only" : "Official source APIs"}</small></article>
        <article className="setting-overview-card"><span className="setting-overview-icon"><Clock3 size={18} /></span><span>REFRESH</span><strong>{settings?.scheduler_enabled ? "Every " + settings.refresh_interval_minutes + " min" : "Manual"}</strong><small>Rate-conscious schedule</small></article>
        <article className="setting-overview-card"><span className="setting-overview-icon"><KeyRound size={18} /></span><span>ALERTS</span><strong>{settings?.alert_mode === "email" ? "Email enabled" : "Local log"}</strong><small>{settings?.smtp_configured ? "SMTP configured" : "No mail credentials"}</small></article>
      </section>

      <section className="panel settings-panel">
        <div className="settings-section-heading"><div><span className="panel-kicker">OFFICIAL SOURCES</span><h2>Collection permissions</h2></div><span className="verified-badge"><ShieldCheck size={14} />Reviewed source routes</span></div>
        <div className="source-setting-list">
          {sources.filter((source) => !source.is_demo).map((source) => (
            <article className="source-setting" key={source.key}>
              <div className={"source-monogram source-" + source.key}>{source.key.toUpperCase()}</div>
              <div className="source-setting-main">
                <div className="source-setting-title"><strong>{source.agency}</strong><span className={"source-state state-" + source.state}>{stateLabel(source)}</span></div>
                <p>{source.key === "cta" && settings?.cta_terms_accepted ? "Developer terms acknowledged for this project. Requests remain limited and source health is tracked." : source.message}</p>
                <a href={source.source_url} target="_blank" rel="noreferrer">Official developer source <ExternalLink size={13} /></a>
              </div>
              <div className="source-check-detail"><span>LAST CHECK</span><strong>{source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : "Not checked"}</strong><small>{source.last_success_at ? "Last successful " + new Date(source.last_success_at).toLocaleString() : "No successful check recorded"}</small></div>
            </article>
          ))}
        </div>
      </section>

      <section className="settings-grid">
        <article className="panel settings-panel">
          <div className="settings-section-heading"><div><span className="panel-kicker">FRESHNESS POLICY</span><h2>When information goes stale</h2></div><span className="setting-icon-pill"><Clock3 size={17} /></span></div>
          <div className="policy-callout"><div className="policy-check"><Check size={15} /></div><div><strong>Old source data is never called live</strong><span>A source failure preserves the last confirmed snapshot and changes the freshness label.</span></div></div>
          <div className="policy-rows">
            <div><span>Mark source stale after</span><strong>{settings?.stale_after_minutes ?? 30} minutes without a successful check</strong></div>
            <div><span>Requests retry</span><strong>Up to 3 times with backoff</strong></div>
            <div><span>Withdrawn detection</span><strong>After 2 complete source checks</strong></div>
          </div>
        </article>
        <article className="panel settings-panel">
          <div className="settings-section-heading"><div><span className="panel-kicker">ALERT SAFETY</span><h2>Delivery controls</h2></div><span className="setting-icon-pill"><LockKeyhole size={17} /></span></div>
          <div className="policy-callout policy-callout-blue"><div className="policy-check"><Check size={15} /></div><div><strong>{settings?.alert_mode === "email" ? "Email delivery selected" : "Local demo log selected"}</strong><span>One delivery key per notice, revision, channel and recipient prevents duplicate alerts.</span></div></div>
          <div className="policy-rows">
            <div><span>Recipients</span><strong>{settings?.alert_mode === "email" ? "Configured on the server" : "None; local log only"}</strong></div>
            <div><span>Secrets</span><strong>Stored in backend .env, never shown here</strong></div>
            <div><span>CTA lock</span><strong>Terms acknowledgment required</strong></div>
          </div>
        </article>
      </section>

      <section className="source-approval-note">
        <div className="approval-icon"><CircleAlert size={18} /></div>
        <div><strong>Before switching to live collection</strong><p>Review the source approval note, read each agency’s current terms, then add keys to the local .env file. CTA data use stays disabled until its terms acknowledgment is recorded.</p></div>
        <a href="/docs/source-approval.md" target="_blank" rel="noreferrer">Read source notes <ArrowUpRight size={15} /></a>
      </section>
    </div>
  );
}
