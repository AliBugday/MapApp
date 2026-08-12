"use client";

import { useEffect, useState } from "react";

import { ApiError, createComment, fetchComments, type Comment } from "@/lib/api";
import { useUser } from "@/lib/auth";

/** Dates come from the API as ISO strings; the locale format is decided in the browser. */
function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function CommentSection({ reportId }: { reportId: number }) {
  const { user } = useUser();
  const [comments, setComments] = useState<Comment[] | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchComments(reportId)
      .then(setComments)
      .catch((err: Error) => setError(err.message));
  }, [reportId]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await createComment(reportId, body.trim());
      // Appended, not refetched: the endpoint returns the saved comment, so the list
      // stays correct without a second round trip.
      setComments((current) => [...(current ?? []), created]);
      setBody("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not post that comment.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section style={{ marginTop: "2rem" }}>
      <h2 style={{ fontSize: "1rem" }}>Comments{comments ? ` (${comments.length})` : ""}</h2>

      {comments === null && !error && <p style={{ color: "var(--muted)" }}>Loading comments…</p>}

      {comments?.length === 0 && (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          No comments yet. Be the first to add one.
        </p>
      )}

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {comments?.map((comment) => (
          <li
            key={comment.id}
            style={{
              borderTop: "1px solid var(--border)",
              padding: "0.6rem 0",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
              <strong style={{ color: "inherit" }}>{comment.author_username}</strong> ·{" "}
              {formatWhen(comment.created_at)}
            </div>
            <p style={{ margin: "0.25rem 0 0", whiteSpace: "pre-wrap" }}>{comment.body}</p>
          </li>
        ))}
      </ul>

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

      {user ? (
        <form onSubmit={handleSubmit} style={{ marginTop: "1rem" }}>
          <label>
            <span style={{ fontSize: "0.85rem" }}>Add a comment</span>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={3}
              required
              style={{ width: "100%", font: "inherit" }}
            />
          </label>
          <button
            type="submit"
            disabled={submitting || !body.trim()}
            style={{
              background: "var(--accent)",
              color: "white",
              border: 0,
              borderRadius: 4,
              padding: "0.45rem 0.9rem",
              marginTop: "0.5rem",
            }}
          >
            {submitting ? "Posting…" : "Post comment"}
          </button>
        </form>
      ) : (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: "1rem" }}>
          Sign in on the map page to join the discussion.
        </p>
      )}
    </section>
  );
}
