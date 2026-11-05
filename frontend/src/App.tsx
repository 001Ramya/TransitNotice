import { useCallback, useEffect, useMemo, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { apiGet, apiPost } from "./api";
import NoticeDialog from "./components/NoticeDialog";
import { Shell } from "./components/Shell";
import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Notices from "./pages/Notices";
import Settings from "./pages/Settings";
import type { AppSettings, DashboardData, Delivery, Notice, Revision, Source } from "./types";
import { indiaDelivery, indiaNotice, indiaRevision, indiaSource } from "./uiText";

export default function App() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [alerts, setAlerts] = useState<Delivery[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [selectedNotice, setSelectedNotice] = useState<Notice | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [dashboardData, noticeData, historyData, alertData, sourceData, settingsData] = await Promise.all([
        apiGet<DashboardData>("/dashboard"),
        apiGet<Notice[]>("/notices"),
        apiGet<Revision[]>("/history"),
        apiGet<Delivery[]>("/alerts"),
        apiGet<Source[]>("/sources"),
        apiGet<AppSettings>("/settings"),
      ]);
      setDashboard({ ...dashboardData, recent_notices: dashboardData.recent_notices.map(indiaNotice) });
      setNotices(noticeData.map(indiaNotice));
      setRevisions(historyData.map(indiaRevision));
      setAlerts(alertData.map(indiaDelivery));
      setSources(sourceData.map(indiaSource));
      setSettings(settingsData);
      setError(null);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "Could not connect to the TransitNotice server.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
    const timer = window.setInterval(() => void loadAll(), 60_000);
    return () => window.clearInterval(timer);
  }, [loadAll]);

  async function refreshSources() {
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      const result = await apiPost<{ results: { source: string; state: string; message?: string }[] }>("/refresh");
      const failures = result.results.filter((item) => item.state === "error" || item.state === "paused").length;
      setRefreshMessage(failures ? "Source check finished with " + failures + " source(s) unavailable or paused. Last confirmed data remains marked." : "Source check completed.");
      await loadAll();
    } catch (problem) {
      setRefreshMessage(problem instanceof Error ? problem.message : "Source check did not complete.");
    } finally {
      setRefreshing(false);
    }
  }

  const demoMode = settings?.demo_mode ?? true;
  const lastChecked = dashboard?.last_checked_at ?? null;
  const shellProps = useMemo(() => ({
    settings,
    demoMode,
    lastChecked,
    refreshing,
    onRefresh: refreshSources,
    refreshMessage,
    error,
  }), [settings, demoMode, lastChecked, refreshing, refreshMessage, error]);

  return (
    <>
      <Routes>
        <Route element={<Shell {...shellProps} />}>
          <Route path="/" element={<Dashboard data={dashboard} sources={sources} onOpenNotice={setSelectedNotice} />} />
          <Route path="/notices" element={<Notices notices={notices} loading={loading} onOpenNotice={setSelectedNotice} />} />
          <Route path="/history" element={<History revisions={revisions} loading={loading} />} />
          <Route path="/alerts" element={<Alerts alerts={alerts} loading={loading} demoMode={demoMode} />} />
          <Route path="/settings" element={<Settings settings={settings} sources={sources} />} />
          <Route path="*" element={<Dashboard data={dashboard} sources={sources} onOpenNotice={setSelectedNotice} />} />
        </Route>
      </Routes>
      <NoticeDialog notice={selectedNotice} onClose={() => setSelectedNotice(null)} />
    </>
  );
}
