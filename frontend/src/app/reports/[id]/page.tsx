"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ApiError, fetchReport, setUpvote, type Report } from "@/lib/api";
import { useUser } from "@/lib/auth";
import { STATUS_LABELS } from "@/lib/statusLabels";
import { TYPE_LABELS } from "@/lib/typeLabels";
import AppHeader from "@/components/AppHeader";
import UpvoteButton from "@/components/UpvoteButton";
import CommentSection from "@/components/reports/CommentSection";

/**
 * A client component, so it shares the UserProvider in the root layout and can reuse
 * UpvoteButton directly. Server-rendering this for OpenGraph share tags is a later
 * concern — sharing is not part of this step.
 */
export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const reportId = Number(params.id);
  const { user, loading: userLoading } = useUser();

  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!Number.isInteger(reportId)) {
      setError("Bu bildirim kimliği geçerli değil.");
      setLoading(false);
      return;
    }
    // has_upvoted is per-user: refetch whenever the signed-in identity changes, e.g. a
    // login/logout without leaving this page, not just once when the id first appears.
    if (userLoading) return;
    setLoading(true);
    fetchReport(reportId)
      .then(setReport)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [reportId, userLoading, user?.id]);

  const handleToggleUpvote = useCallback(async () => {
    if (!report) return;
    if (!user) {
      setError("Oy vermek için harita sayfasından giriş yapın.");
      return;
    }
    const previous = report;
    const next = !previous.has_upvoted;

    // Same optimistic-then-reconcile approach as the map, on a single report rather than
    // a list: move the count now, apply the server's numbers when they arrive.
    setReport({
      ...previous,
      has_upvoted: next,
      upvote_count: previous.upvote_count + (next ? 1 : -1),
    });
    try {
      const confirmed = await setUpvote(previous.id, next);
      setReport((current) => (current ? { ...current, ...confirmed } : current));
      setError(null);
    } catch (err) {
      setReport(previous);
      setError(err instanceof ApiError ? err.message : "Oy kaydedilemedi.");
    }
  }, [report, user]);

  return (
    <main style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppHeader />

      <div style={{ padding: "1.5rem", maxWidth: 680, width: "100%", margin: "0 auto" }}>
        <Link href="/" style={{ fontSize: "0.85rem" }}>
          ← Haritaya dön
        </Link>

        {loading && <p style={{ color: "var(--muted)" }}>Bildirim yükleniyor…</p>}

        {error && !report && (
          <p
            role="alert"
            style={{
              background: "#fdecea",
              border: "1px solid #f5c2bd",
              borderRadius: 4,
              padding: "0.6rem",
            }}
          >
            {error}
          </p>
        )}

        {report && (
          <>
            <h1 style={{ marginBottom: "0.25rem" }}>{report.title}</h1>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
              {TYPE_LABELS[report.type]}
              {report.type === "issue" || report.type === "request"
                ? ` · ${STATUS_LABELS[report.status]}`
                : report.visibility === "members"
                  ? " · Yalnızca üyelere"
                  : " · Herkese açık"}
              {report.organization_name ? ` · ${report.organization_name}` : ""}
              {report.author_username ? ` · bildiren: ${report.author_username}` : ""} ·{" "}
              {new Date(report.created_at).toLocaleDateString()}
            </p>

            {report.description ? (
              <p style={{ whiteSpace: "pre-wrap" }}>{report.description}</p>
            ) : (
              <p style={{ color: "var(--muted)", fontStyle: "italic" }}>Açıklama verilmedi.</p>
            )}

            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <UpvoteButton report={report} onToggle={handleToggleUpvote} />
              <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                {report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}
              </span>
            </div>

            {/* An upvote error belongs next to the button, not above the title. */}
            {error && (
              <p role="alert" style={{ color: "#b3261e", fontSize: "0.85rem" }}>
                {error}
              </p>
            )}

            <CommentSection reportId={report.id} />
          </>
        )}
      </div>
    </main>
  );
}
