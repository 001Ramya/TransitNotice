import { ArrowDownUp, ArrowRight, CalendarDays, Search, SlidersHorizontal, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { Notice, NoticeStatus } from "../types";

interface Props {
  notices: Notice[];
  loading: boolean;
  onOpenNotice: (notice: Notice) => void;
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value)) : "Not stated";
}

function Label({ status, stale }: { status: NoticeStatus; stale: boolean }) {
  const label = stale ? "Stale" : status.charAt(0).toUpperCase() + status.slice(1);
  return <span className={"status-pill " + (stale ? "status-stale" : "status-" + status)}>{label}</span>;
}

export default function Notices({ notices, loading, onOpenNotice }: Props) {
  const [search, setSearch] = useState("");
  const [agency, setAgency] = useState("");
  const [area, setArea] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [serviceDate, setServiceDate] = useState("");
  const agencies = useMemo(() => [...new Set(notices.map((notice) => notice.agency))].sort(), [notices]);
  const types = useMemo(() => [...new Set(notices.map((notice) => notice.advisory_type))].sort(), [notices]);
  const filtered = useMemo(() => notices.filter((notice) => {
    const text = [notice.summary, notice.content_text, notice.area, notice.agency, ...notice.route_ids].join(" ").toLowerCase();
    if (search && !text.includes(search.toLowerCase())) return false;
    if (agency && notice.agency !== agency) return false;
    if (area && !notice.area.toLowerCase().includes(area.toLowerCase())) return false;
    if (type && notice.advisory_type !== type) return false;
    if (status && (notice.is_stale ? "stale" : notice.status) !== status) return false;
    if (serviceDate) {
      const day = new Date(serviceDate + "T00:00:00");
      if (notice.valid_from && day < new Date(notice.valid_from)) return false;
      if (notice.valid_to && day > new Date(notice.valid_to)) return false;
    }
    return true;
  }), [notices, search, agency, area, type, status, serviceDate]);
  const activeFilters = [search, agency, area, type, status, serviceDate].filter(Boolean).length;
  function clearFilters() {
    setSearch(""); setAgency(""); setArea(""); setType(""); setStatus(""); setServiceDate("");
  }

  return (
    <div className="page-stack">
      <section className="page-heading compact-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" />SERVICE UPDATES</div><h1>Every update,<br /><em>easy to find.</em></h1><p className="page-subtitle">Find Bengaluru bus and metro updates in seconds.</p></div>
        <div className="heading-count"><strong>{filtered.length.toString().padStart(2, "0")}</strong><span>notices in view</span></div>
      </section>

      <section className="filter-panel">
        <div className="filter-head"><div className="filter-head-icon"><SlidersHorizontal size={16} /></div><div><strong>Find an update</strong><span>Use one or more filters</span></div>{activeFilters > 0 && <button className="clear-filters" onClick={clearFilters}><X size={13} />Clear {activeFilters}</button>}</div>
        <div className="filter-grid">
          <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search route, notice or area" aria-label="Search notices" /></label>
          <label className="select-field"><span>Agency</span><select value={agency} onChange={(event) => setAgency(event.target.value)}><option value="">All agencies</option>{agencies.map((value) => <option key={value}>{value}</option>)}</select></label>
          <label className="select-field"><span>Advisory type</span><select value={type} onChange={(event) => setType(event.target.value)}><option value="">All types</option>{types.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
          <label className="select-field"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Any status</option><option value="active">Active</option><option value="upcoming">Upcoming</option><option value="expired">Expired</option><option value="withdrawn">Withdrawn</option><option value="stale">Stale source</option></select></label>
          <label className="date-field"><CalendarDays size={16} /><input type="date" value={serviceDate} onChange={(event) => setServiceDate(event.target.value)} aria-label="Filter by service date" /></label>
          <label className="area-field"><input value={area} onChange={(event) => setArea(event.target.value)} placeholder="Area or station" aria-label="Filter by area" /><ArrowDownUp size={15} /></label>
        </div>
        <div className="filter-summary"><span>{filtered.length} {filtered.length === 1 ? "notice" : "notices"} match your filters</span><span><span className="freshness-led led-live" />Source status shown on each notice</span></div>
      </section>

      <section className="panel register-panel">
          <div className="register-toolbar"><div><span className="panel-kicker">SERVICE UPDATES</span><h2>All updates</h2></div><span className="register-sort"><ArrowDownUp size={14} /> Newest first</span></div>
        {loading ? <div className="page-loading"><span className="loading-spinner" />Loading notices</div> : (
          <div className="register-list">
            {filtered.map((notice) => (
              <article className="register-item" key={notice.id} onClick={() => onOpenNotice(notice)}>
                <div className={"register-icon type-" + notice.advisory_type.toLowerCase()}><SlidersHorizontal size={17} /></div>
                <div className="register-copy">
                  <div className="register-title-line"><h3>{notice.summary}</h3><Label status={notice.status} stale={notice.is_stale} /></div>
                  <div className="register-meta"><span>{notice.agency}</span><i />{notice.route_ids.length ? <span>Route {notice.route_ids.join(", ")}</span> : <span>Network-wide</span>}<i /><span>{notice.area}</span>{notice.is_demo && <b className="sample-row-tag">SAMPLE DATA</b>}</div>
                  <p>{notice.content_text}</p>
                  <div className="register-dates"><span><strong>From</strong> {formatDate(notice.valid_from)}</span><span><strong>To</strong> {formatDate(notice.valid_to)}</span><span className="revision-note">Revision {notice.revision_number} · {notice.change_summary}</span></div>
                </div>
                <button className="register-open" onClick={(event) => { event.stopPropagation(); onOpenNotice(notice); }} aria-label={"View details for " + notice.summary}><ArrowRight size={17} /></button>
              </article>
            ))}
            {filtered.length === 0 && <div className="empty-state"><div className="empty-state-icon"><Search size={21} /></div><strong>No matching notices</strong><span>Adjust your search or clear a filter to see more results.</span>{activeFilters > 0 && <button className="button button-soft" onClick={clearFilters}>Clear filters</button>}</div>}
          </div>
        )}
      </section>
    </div>
  );
}
