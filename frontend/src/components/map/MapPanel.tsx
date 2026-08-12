"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";

import { ApiError, createReport, fetchReports, setUpvote, type Report } from "@/lib/api";
import { useUser } from "@/lib/auth";
import { STATUS_LABELS } from "@/lib/statusLabels";
import AuthPanel from "@/components/auth/AuthPanel";
import type { LatLng } from "./types";
import NewReportForm from "./NewReportForm";

// Leaflet touches `window` while it is being imported, which crashes server
// rendering, so the map is loaded only in the browser.
const ReportMap = dynamic(() => import("./ReportMap"), {
  ssr: false,
  loading: () => <p style={{ padding: "1rem", color: "var(--muted)" }}>Harita yükleniyor…</p>,
});

const ISTANBUL: LatLng = { latitude: 41.0082, longitude: 28.9784 };

export default function MapPanel() {
  const { user, loading: userLoading } = useUser();
  const [reports, setReports] = useState<Report[]>([]);
  const [pending, setPending] = useState<LatLng | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // has_upvoted is per-user, so a fetch taken while signed in as one user is wrong for
    // the next: refetch whenever the signed-in identity changes, not just once at mount.
    // Waiting for userLoading also skips an extra anonymous-then-authenticated round trip
    // for a visitor who is already signed in on page load.
    if (userLoading) return;
    setLoading(true);
    fetchReports()
      .then((page) => setReports(page.results))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userLoading, user?.id]);

  const handleCreate = useCallback(
    async (input: { title: string; description: string }) => {
      if (!pending) return;
      try {
        const created = await createReport({ ...input, ...pending });
        // Prepend so it matches the API's newest-first ordering.
        setReports((current) => [created, ...current]);
        setPending(null);
        setError(null);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Bildirim kaydedilemedi.");
      }
    },
    [pending],
  );

  const handleToggleUpvote = useCallback(
    async (target: Pick<Report, "id" | "has_upvoted">) => {
      if (!user) {
        setError("Oy vermek için giriş yapmalısınız — giriş formu yan panelde.");
        return;
      }
      const previous = reports.find((r) => r.id === target.id);
      if (!previous) return;
      const next = !previous.has_upvoted;

      const patch = (changes: Partial<Report>) =>
        setReports((current) =>
          current.map((r) => (r.id === target.id ? { ...r, ...changes } : r)),
        );

      // Optimistic: the count moves immediately, because waiting on a round trip for a
      // single tap feels broken. The server's own numbers are applied on success, which
      // also picks up votes other people cast since this page loaded.
      patch({ has_upvoted: next, upvote_count: previous.upvote_count + (next ? 1 : -1) });
      try {
        patch(await setUpvote(target.id, next));
        setError(null);
      } catch (err) {
        // Roll back to what the server last told us, rather than leaving a count the
        // database does not agree with.
        patch({ has_upvoted: previous.has_upvoted, upvote_count: previous.upvote_count });
        setError(err instanceof ApiError ? err.message : "Oy kaydedilemedi.");
      }
    },
    [user, reports],
  );

  const center = useMemo(() => reports[0] ?? ISTANBUL, [reports]);

  return (
    <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
      <div style={{ flex: 1, position: "relative" }}>
        <ReportMap
          reports={reports}
          pending={pending}
          onMapClick={setPending}
          onToggleUpvote={handleToggleUpvote}
          center={center}
          zoom={13}
        />
      </div>

      <aside
        style={{
          width: 320,
          borderLeft: "1px solid var(--border)",
          padding: "1rem",
          overflowY: "auto",
        }}
      >
        {error && (
          <p
            role="alert"
            style={{
              background: "#fdecea",
              border: "1px solid #f5c2bd",
              borderRadius: 4,
              padding: "0.5rem",
              fontSize: "0.85rem",
            }}
          >
            {error}
          </p>
        )}

        {/* A signed-out visitor gets the auth form here rather than a "go to /admin" dead
            end. Any pending map click is kept, so signing in drops them straight into the
            new-report form for the spot they picked. */}
        {userLoading ? null : !user ? (
          <AuthPanel />
        ) : pending ? (
          <NewReportForm
            position={pending}
            onSubmit={handleCreate}
            onCancel={() => setPending(null)}
          />
        ) : (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Bildirim eklemek için haritada bir yere tıklayın.
          </p>
        )}

        <h2 style={{ fontSize: "0.95rem", marginTop: "1.5rem" }}>
          Bildirimler {loading ? "" : `(${reports.length})`}
        </h2>
        {loading && <p style={{ color: "var(--muted)" }}>Yükleniyor…</p>}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {reports.map((report) => (
            <li
              key={report.id}
              style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}
            >
              <strong style={{ fontSize: "0.9rem" }}>{report.title}</strong>
              <div style={{ color: "var(--muted)", fontSize: "0.78rem" }}>
                {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)} ·{" "}
                {STATUS_LABELS[report.status]}
              </div>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
