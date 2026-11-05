import { ArrowUpRight, CalendarDays, Clock3, Copy, ExternalLink, MapPin, Route, X } from "lucide-react";
import { useEffect, useState } from "react";
import type { Notice, Revision } from "../types";

interface Props { notice: Notice | null; onClose: () => void; }

function date(value: string | null) {
  if (!value) return "Not stated by source";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export default function NoticeDialog({ notice, onClose }: Props) {
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!notice) return;
    setRevisions([]);
    fetch("/api/notices/" + notice.id + "/revisions").then((response) => response.ok ? response.json() : []).then(setRevisions).catch(() => setRevisions([]));
  }, [notice]);
  useEffect(() => {
    if (!notice) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [notice, onClose]);
  if (!notice) return null;
  const activeNotice = notice;
  const safeSource = notice.source_url && /^https:\/\/(www\.)?(mtcbus\.tn\.gov\.in|chennaimetrorail\.org)\//i.test(notice.source_url);
  const officialWebsite = notice.agency.toLowerCase().includes("metro")
    ? "https://chennaimetrorail.org/press-release/"
    : notice.agency.toLowerCase().includes("mtc")
      ? "https://mtcbus.tn.gov.in/Home/news"
      : notice.source_url;
  async function copyId() {
    await navigator.clipboard?.writeText(activeNotice.id);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="notice-dialog" role="dialog" aria-modal="true" aria-labelledby="notice-dialog-title">
        <div className="dialog-accent" />
        <div className="dialog-topline"><span className="panel-kicker">NOTICE DETAILS</span><button className="icon-button dialog-close" onClick={onClose} aria-label="Close notice details"><X size={19} /></button></div>
        <div className="dialog-status-row"><span className={"status-pill " + (activeNotice.is_stale ? "status-stale" : "status-" + activeNotice.status)}>{activeNotice.is_stale ? "Stale source" : activeNotice.status}</span>{activeNotice.is_demo && <span className="sample-row-tag">SAMPLE DATA</span>}<span className="revision-badge">Revision {activeNotice.revision_number}</span></div>
        <h2 id="notice-dialog-title">{notice.summary}</h2>
        <div className="dialog-agency">{notice.agency}<span />{notice.advisory_type.replaceAll("_", " ")}</div>
        <p className="dialog-description">{notice.content_text}</p>
        <div className="dialog-detail-grid">
          <div><span><Route size={14} /> ROUTE IDS</span><strong>{notice.route_ids.length ? notice.route_ids.join(", ") : "Network-wide"}</strong></div>
          <div><span><MapPin size={14} /> AFFECTED AREA</span><strong>{notice.area}</strong></div>
          <div><span><CalendarDays size={14} /> PUBLISHED</span><strong>{date(notice.published_at)}</strong></div>
          <div><span><CalendarDays size={14} /> VALID FROM</span><strong>{date(notice.valid_from)}</strong></div>
          <div><span><CalendarDays size={14} /> VALID TO</span><strong>{date(notice.valid_to)}</strong></div>
          <div><span><Clock3 size={14} /> LAST CONFIRMED</span><strong>{date(notice.last_confirmed_at)}</strong></div>
          <div><span><Clock3 size={14} /> LAST OBSERVED</span><strong>{date(notice.last_observed_at)}</strong></div>
          <div><span><ArrowUpRight size={14} /> CHANGE SUMMARY</span><strong>{notice.change_summary}</strong></div>
        </div>
        <a className={"dialog-provenance " + (safeSource ? "provenance-clickable" : "")} href={safeSource ? officialWebsite! : undefined} target={safeSource ? "_blank" : undefined} rel={safeSource ? "noreferrer" : undefined}>
          <div className="provenance-icon"><ExternalLink size={16} /></div>
          <div><strong>Open official website</strong><span>{safeSource ? "Go to the official Tamil Nadu transport website" : notice.is_demo ? "Fictional sample record; no external source" : "The source did not provide a verified detail link"}</span></div>
          {safeSource && <ArrowUpRight size={17} aria-label="Open official source" />}
        </a>
        {safeSource && notice.source_url !== officialWebsite && <a className="original-notice-link" href={notice.source_url!} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Open original notice document</a>}
        <div className="dialog-history">
          <div className="dialog-section-heading"><strong>Revision history</strong><button className="copy-id" onClick={copyId}><Copy size={13} />{copied ? "Copied" : "Copy notice ID"}</button></div>
          <span className="notice-id">ID {notice.id}</span>
          {revisions.slice(0, 4).map((item) => <div className="dialog-revision" key={item.id}><i /><span><strong>Revision {item.revision_number}</strong>{item.change_summary}</span><time>{new Date(item.observed_at).toLocaleString()}</time></div>)}
        </div>
        <div className="dialog-footer"><span>Freshness is calculated from the source’s last successful check.</span><button className="button button-soft" onClick={onClose}>Done</button></div>
      </section>
    </div>
  );
}
