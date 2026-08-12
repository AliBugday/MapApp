"use client";

import type { Report } from "@/lib/api";

/**
 * Presentational only — the count and pressed state come from the report, and the parent
 * that owns the report list handles the request and the optimistic update. Keeping the
 * state in one place means the map popup and the detail page can't disagree.
 */
export default function UpvoteButton({
  report,
  onToggle,
  disabled = false,
}: {
  report: Pick<Report, "id" | "upvote_count" | "has_upvoted">;
  onToggle: (report: Pick<Report, "id" | "has_upvoted">) => void;
  disabled?: boolean;
}) {
  const upvoted = report.has_upvoted;

  return (
    <button
      type="button"
      onClick={() => onToggle(report)}
      disabled={disabled}
      // aria-pressed rather than just a colour change, so the state is available to
      // screen readers and not conveyed by styling alone.
      aria-pressed={upvoted}
      aria-label={upvoted ? "Remove your upvote" : "Upvote this report"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        background: upvoted ? "var(--accent)" : "transparent",
        color: upvoted ? "white" : "var(--accent)",
        border: "1px solid var(--accent)",
        borderRadius: 999,
        padding: "0.2rem 0.6rem",
        font: "inherit",
        fontSize: "0.8rem",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      <span aria-hidden="true">▲</span>
      {report.upvote_count}
    </button>
  );
}
