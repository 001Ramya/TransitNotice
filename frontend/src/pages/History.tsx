import { ArrowUpRight, Clock3, GitCommitHorizontal, RotateCcw } from "lucide-react";
import type { Revision } from "../types";

interface Props { revisions: Revision[]; loading: boolean; }

export default function History({ revisions, loading }: Props) {
  return (
    <div className="page-stack">
      <section className="page-heading compact-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" />UPDATE HISTORY</div><h1>See what <em>changed.</em></h1><p className="page-subtitle">A clear timeline of new, changed and closed service updates.</p></div>
        <div className="heading-count"><strong>{revisions.length.toString().padStart(2, "0")}</strong><span>saved revisions</span></div>
      </section>
      <section className="history-intro">
        <div className="history-intro-icon"><Clock3 size={20} /></div>
        <div><strong>Every revision stays attached to its notice</strong><span>Repeated collection is idempotent. A new history entry appears only when source content changes.</span></div>
        <div className="history-intro-stat"><span>RETAINED</span><strong>Full timeline</strong></div>
      </section>
      <section className="panel history-panel">
        <div className="register-toolbar"><div><span className="panel-kicker">AUDIT TRAIL</span><h2>Latest changes</h2></div><span className="register-sort"><GitCommitHorizontal size={15} /> Newest first</span></div>
        {loading ? <div className="page-loading"><span className="loading-spinner" />Loading notice history</div> : revisions.length === 0 ? <div className="empty-state"><div className="empty-state-icon"><Clock3 size={21} /></div><strong>No changes recorded yet</strong><span>Source runs and notice revisions will appear here.</span></div> : (
          <div className="timeline">
            {revisions.map((revision) => (
              <article className="timeline-entry" key={revision.id}>
                <div className={"timeline-mark " + (revision.revision_number === 1 ? "timeline-new" : "timeline-update")}>{revision.revision_number === 1 ? <ArrowUpRight size={15} /> : <RotateCcw size={15} />}</div>
                <div className="timeline-content">
                  <div className="timeline-top"><span className={revision.revision_number === 1 ? "event-label event-new" : "event-label event-update"}>{revision.revision_number === 1 ? "NEW ADVISORY" : "REVISION " + revision.revision_number}</span><time>{new Date(revision.observed_at).toLocaleString()}</time></div>
                  <h3>{revision.summary}</h3>
                  <p>{revision.change_summary}</p>
                  <div className="timeline-meta"><span>{revision.agency}</span><span>Route {revision.route_ids.join(", ") || "network-wide"}</span>{revision.is_demo && <b className="sample-row-tag">SAMPLE</b>}</div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
