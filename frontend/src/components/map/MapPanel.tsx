"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";

import { ApiError, createReport, fetchReports, type Report } from "@/lib/api";
import type { LatLng } from "./types";
import NewReportForm from "./NewReportForm";

// Leaflet touches `window` while it is being imported, which crashes server
// rendering, so the map is loaded only in the browser.
const ReportMap = dynamic(() => import("./ReportMap"), {
  ssr: false,
  loading: () => <p style={{ padding: "1rem", color: "var(--muted)" }}>Loading map…</p>,
});

const ISTANBUL: LatLng = { latitude: 41.0082, longitude: 28.9784 };

export default function MapPanel() {
  const [reports, setReports] = useState<Report[]>([]);
  const [pending, setPending] = useState<LatLng | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports()
      .then((page) => setReports(page.results))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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
        setError(err instanceof ApiError ? err.message : "Could not save the report.");
      }
    },
    [pending],
  );

  const center = useMemo(() => reports[0] ?? ISTANBUL, [reports]);

  return (
    <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
      <div style={{ flex: 1, position: "relative" }}>
        <ReportMap
          reports={reports}
          pending={pending}
          onMapClick={setPending}
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

        {pending ? (
          <NewReportForm
            position={pending}
            onSubmit={handleCreate}
            onCancel={() => setPending(null)}
          />
        ) : (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Click anywhere on the map to add a report.
          </p>
        )}

        <h2 style={{ fontSize: "0.95rem", marginTop: "1.5rem" }}>
          Reports {loading ? "" : `(${reports.length})`}
        </h2>
        {loading && <p style={{ color: "var(--muted)" }}>Loading…</p>}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {reports.map((report) => (
            <li
              key={report.id}
              style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}
            >
              <strong style={{ fontSize: "0.9rem" }}>{report.title}</strong>
              <div style={{ color: "var(--muted)", fontSize: "0.78rem" }}>
                {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)} · {report.status}
              </div>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
