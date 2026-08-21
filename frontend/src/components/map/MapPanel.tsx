"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Image from "next/image";

import {
  ApiError,
  createReport,
  fetchReports,
  setUpvote,
  uploadReportImage,
  type Report,
} from "@/lib/api";
import { useUser } from "@/lib/auth";
import { STATUS_LABELS } from "@/lib/statusLabels";
import { TYPE_LABELS } from "@/lib/typeLabels";
import AuthPanel from "@/components/auth/AuthPanel";
import MapLegend from "./MapLegend";
import type { LatLng } from "./types";
import NewReportForm from "./NewReportForm";
import TypeFilter from "./TypeFilter";

const ALL_TYPES = Object.keys(TYPE_LABELS) as Array<Report["type"]>;

// Leaflet touches `window` while it is being imported, which crashes server
// rendering, so the map is loaded only in the browser.
const ReportMap = dynamic(() => import("./ReportMap"), {
  ssr: false,
  loading: () => <p style={{ padding: "1rem", color: "var(--muted)" }}>Harita yükleniyor…</p>,
});

// Çankaya / Kızılay — matches CENTER in backend/apps/reports/management/commands/seed_demo_data.py.
const DEFAULT_CENTER: LatLng = { latitude: 39.91, longitude: 32.855 };

export default function MapPanel() {
  const {
    user,
    loading: userLoading,
    pickingLocation,
    pendingLocationPoint,
    setPendingLocationPoint,
    cancelLocationPicking,
    confirmLocationPicking,
  } = useUser();
  const [reports, setReports] = useState<Report[]>([]);
  const [activeTypes, setActiveTypes] = useState<Set<Report["type"]>>(new Set(ALL_TYPES));
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [pending, setPending] = useState<LatLng | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // null until the map reports its first viewport — the fetch below waits for that
  // rather than guessing at a bbox, so it never issues an unbounded "everything" query.
  const [bbox, setBbox] = useState<string | null>(null);

  useEffect(() => {
    // has_upvoted is per-user, so a fetch taken while signed in as one user is wrong for
    // the next: refetch whenever the signed-in identity changes, not just once at mount.
    // Waiting for userLoading also skips an extra anonymous-then-authenticated round trip
    // for a visitor who is already signed in on page load.
    if (userLoading || bbox === null) return;

    const controller = new AbortController();
    // Debounced, not the moveend listener itself — a fast pan/zoom fires many bounds
    // updates in a row, and only the settled one should trigger a request.
    const timer = setTimeout(() => {
      setLoading(true);
      fetchReports({ bbox, signal: controller.signal })
        .then((page) => setReports(page.results))
        .catch((err: Error) => {
          // A pan that lands before the previous fetch's response arrives aborts that
          // older request — its rejection is expected, not a real failure to surface.
          if (err.name === "AbortError") return;
          setError(err.message);
        })
        .finally(() => setLoading(false));
    }, 300);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [userLoading, user?.id, bbox]);

  // Location picking is armed from the header, not here — this just yields to it: only
  // one "click the map to do X" mode makes sense at a time.
  useEffect(() => {
    if (pickingLocation) setPending(null);
  }, [pickingLocation]);

  const handleCreate = useCallback(
    async (input: {
      title: string;
      description: string;
      type: Report["type"];
      visibility?: Report["visibility"];
      event_starts_at?: string;
      event_ends_at?: string;
      images: File[];
    }) => {
      if (!pending) return;
      const { images, ...reportInput } = input;
      let created: Report;
      try {
        created = await createReport({ ...reportInput, ...pending });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Bildirim kaydedilemedi.");
        return;
      }
      // Prepend so it matches the API's newest-first ordering.
      setReports((current) => [created, ...current]);
      setPending(null);
      setError(null);

      // The report itself is already saved at this point — a failed upload shouldn't look
      // like the whole submission failed, just that a photo didn't attach. Sequential rather
      // than Promise.all: simpler to reason about, and a demo report only ever carries a
      // handful of photos, so there's no throughput reason to parallelize.
      let failedUploads = 0;
      for (const file of images) {
        try {
          const attachedImage = await uploadReportImage(created.id, file);
          setReports((current) =>
            current.map((r) =>
              r.id === created.id ? { ...r, images: [...r.images, attachedImage] } : r,
            ),
          );
        } catch {
          failedUploads += 1;
        }
      }
      if (failedUploads > 0) {
        setError(
          failedUploads === 1
            ? "Bir fotoğraf yüklenemedi."
            : `${failedUploads} fotoğraf yüklenemedi.`,
        );
      }
    },
    [pending],
  );

  const handleMapClick = useCallback(
    (position: LatLng) => {
      if (pickingLocation) {
        setPendingLocationPoint(position);
      } else {
        setPending(position);
      }
    },
    [pickingLocation, setPendingLocationPoint],
  );

  const handleConfirmLocation = useCallback(async () => {
    try {
      await confirmLocationPicking();
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Konum kaydedilemedi.");
    }
  }, [confirmLocationPicking]);

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

  const handleToggleType = useCallback((type: Report["type"]) => {
    setActiveTypes((current) => {
      // Never allow the last active type to be turned off — an empty set would silently
      // blank both the map and the list with no visible way to tell why.
      if (current.has(type) && current.size === 1) return current;
      const next = new Set(current);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }, []);

  const visibleReports = reports.filter((report) => activeTypes.has(report.type));

  const homeLocation =
    user?.home_latitude != null && user?.home_longitude != null
      ? { latitude: user.home_latitude, longitude: user.home_longitude }
      : null;
  const workLocation =
    user?.work_latitude != null && user?.work_longitude != null
      ? { latitude: user.work_latitude, longitude: user.work_longitude }
      : null;

  return (
    <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
      <div style={{ flex: 1, position: "relative" }}>
        <ReportMap
          reports={visibleReports}
          pending={pending}
          onMapClick={handleMapClick}
          onToggleUpvote={handleToggleUpvote}
          center={DEFAULT_CENTER}
          zoom={13}
          onBoundsChange={setBbox}
          homeLocation={homeLocation}
          workLocation={workLocation}
          selectedReportId={selectedReportId}
        />
        <MapLegend />
      </div>

      <aside
        style={{
          width: 320,
          borderLeft: "1px solid var(--border)",
          padding: "1rem",
          overflowY: "auto",
          background: "var(--surface)",
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
        ) : pendingLocationPoint && pickingLocation ? (
          <div style={{ border: "1px solid var(--border)", borderRadius: 4, padding: "0.75rem" }}>
            <p style={{ fontSize: "0.85rem", marginTop: 0 }}>
              Bu noktayı {pickingLocation === "home" ? "ev" : "iş/okul"} konumu olarak kaydet?
            </p>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => void handleConfirmLocation()}
                style={{
                  background: "var(--accent)",
                  color: "white",
                  border: 0,
                  borderRadius: 4,
                  padding: "0.5rem 0.9rem",
                }}
              >
                Kaydet
              </button>
              <button
                type="button"
                onClick={cancelLocationPicking}
                style={{
                  background: "transparent",
                  border: "1px solid var(--border)",
                  borderRadius: 4,
                  padding: "0.5rem 0.9rem",
                }}
              >
                İptal
              </button>
            </div>
          </div>
        ) : pending ? (
          <NewReportForm
            position={pending}
            onSubmit={handleCreate}
            onCancel={() => setPending(null)}
          />
        ) : pickingLocation ? (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            {pickingLocation === "home" ? "Ev" : "İş/okul"} konumu için haritada bir yere tıklayın.
          </p>
        ) : (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Bildirim eklemek için haritada bir yere tıklayın.
          </p>
        )}

        <h2 style={{ fontSize: "0.95rem", marginTop: "1.5rem" }}>
          Bildirimler {loading ? "" : `(${visibleReports.length})`}
        </h2>

        <TypeFilter allTypes={ALL_TYPES} activeTypes={activeTypes} onToggleType={handleToggleType} />

        {loading && <p style={{ color: "var(--muted)" }}>Yükleniyor…</p>}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {visibleReports.map((report) => (
            <li key={report.id}>
              <button
                type="button"
                className="report-list-item"
                onClick={() => setSelectedReportId(report.id)}
              >
                {report.images[0]?.thumbnail_url && (
                  <Image
                    src={report.images[0].thumbnail_url}
                    alt=""
                    width={40}
                    height={40}
                    className="report-list-thumb"
                  />
                )}
                <div>
                  <strong style={{ fontSize: "0.9rem" }}>{report.title}</strong>
                  <div style={{ color: "var(--muted)", fontSize: "0.78rem" }}>
                    {TYPE_LABELS[report.type]} · {STATUS_LABELS[report.status]} · ▲{" "}
                    {report.upvote_count}
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
