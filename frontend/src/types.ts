export type NoticeStatus = "active" | "upcoming" | "expired" | "withdrawn";

export interface Notice {
  id: string;
  agency: string;
  route_ids: string[];
  area: string;
  source_url: string | null;
  advisory_type: string;
  summary: string;
  content_text: string;
  published_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  status: NoticeStatus;
  last_observed_at: string;
  last_confirmed_at: string;
  revision_number: number;
  change_summary: string;
  is_demo: boolean;
  is_stale: boolean;
}

export interface Revision {
  id: number;
  notice_id: string;
  revision_number: number;
  change_summary: string;
  observed_at: string;
  summary: string;
  agency: string;
  route_ids: string[];
  is_demo: boolean;
  snapshot?: Record<string, unknown>;
}

export interface Delivery {
  id: number;
  notice_id: string;
  revision_number: number;
  channel: string;
  recipient: string;
  status: string;
  subject: string;
  created_at: string;
  delivered_at: string | null;
  error_message: string | null;
}

export interface Source {
  key: string;
  agency: string;
  source_url: string;
  enabled: boolean;
  state: string;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_notice_count: number;
  message: string;
  is_demo: boolean;
}

export interface AppSettings {
  demo_mode: boolean;
  scheduler_enabled: boolean;
  refresh_interval_minutes: number;
  stale_after_minutes: number;
  alert_mode: string;
  smtp_configured: boolean;
  mbta_enabled: boolean;
  mbta_key_configured: boolean;
  cta_key_configured: boolean;
  cta_terms_accepted: boolean;
}

export interface DashboardData {
  active: number;
  upcoming: number;
  expired: number;
  withdrawn: number;
  updated: number;
  stale: number;
  demo: number;
  total: number;
  alerts_last_7_days: number;
  last_checked_at: string | null;
  freshness_state: "fresh" | "stale" | "demo";
  demo_mode: boolean;
  notice_trend: { day: string; new: number; updated: number }[];
  recent_notices: Notice[];
}
