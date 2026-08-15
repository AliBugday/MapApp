"use client";

import type { Report } from "@/lib/api";

/**
 * Presentational only — same shape as UpvoteButton. The count and pressed state come
 * from the report, the parent owns the request and the optimistic update.
 */
export default function RsvpButton({
  report,
  onToggle,
  disabled = false,
}: {
  report: Pick<Report, "id" | "rsvp_count" | "has_rsvped">;
  onToggle: (report: Pick<Report, "id" | "has_rsvped">) => void;
  disabled?: boolean;
}) {
  const attending = report.has_rsvped;

  return (
    <button
      type="button"
      onClick={() => onToggle(report)}
      disabled={disabled}
      aria-pressed={attending}
      aria-label={attending ? "Katılımınızı geri çekin" : "Bu etkinliğe katılım bildirin"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        background: attending ? "var(--accent)" : "transparent",
        color: attending ? "white" : "var(--accent)",
        border: "1px solid var(--accent)",
        borderRadius: 999,
        padding: "0.2rem 0.6rem",
        font: "inherit",
        fontSize: "0.8rem",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      <span aria-hidden="true">🎫</span>
      {attending ? "Katılıyorum" : "Katıl"} · {report.rsvp_count}
    </button>
  );
}
